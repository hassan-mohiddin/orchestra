"""design-docs lint — Refs:-line gate + doc metadata validator.

Usage:
    python -m design_docs.lint --commit HEAD
    python -m design_docs.lint --range main..HEAD
    python -m design_docs.lint --doc docs/bugs/BUG-014-auth-leak.md
    python -m design_docs.lint --pre-commit

Validates:
    1. Refs: line on fix:/feat: commits points to a real docs/ file
    2. Required metadata block at top of every doc (Doc ID / Date / Status)
    3. Status enum is valid for the doc type
    4. Required sections present per docs/STANDARDS.md (or plugin's STANDARDS reference)

Exit codes:
    0 — all checks pass
    1 — at least one check fails
    2 — usage error
"""

from __future__ import annotations

import argparse
import datetime as _dt
import getpass
import importlib.util
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_warned_no_npx = False
_extract_mermaid_module = None


def _load_extract_mermaid():
    """Load skills/design-docs/scripts/extract_mermaid.py via importlib path-loading.

    Hyphenated dir + no __init__.py prevents normal import.
    """
    global _extract_mermaid_module
    if _extract_mermaid_module is not None:
        return _extract_mermaid_module
    repo_root = Path(__file__).parent.parent
    em_path = repo_root / "skills" / "design-docs" / "scripts" / "extract_mermaid.py"
    spec = importlib.util.spec_from_file_location("extract_mermaid", em_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {em_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _extract_mermaid_module = module
    return module

# ---------------------------------------------------------------------------
# Canon-sourced vocabularies (BUG-016 slice 2)
# ---------------------------------------------------------------------------
# Canon: docs/design/controlled-vocabulary.md § 4.1, 4.2, 4.6, 4.7, 4.9, 4.13.
# REQUIRED_SECTIONS (canon §4.8) is still defined inline below — slice 3 will
# move it to canon-sourced once conditional-section handling lands.

from cli.vocabulary import (  # noqa: E402
    ALLOWED_ATTESTATION_PATH_PREFIXES,
    CANON_FROZEN_STATUSES,
    REFS_ELIGIBLE_PREFIXES,
    REQUIRED_SECTIONS,
    REVIEW_GATE_NAMES as ALLOWED_GATES,
    STATUS_ENUMS,
    WHITELIST_FRONTMATTER_FIELDS,
)

# v1.5 LLD-006-r4 — filename pattern recognition
FIRST_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)\.md$")
SUPERSESSION_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$")
# BUG-NNN- prefix variant for bug docs (BUG-NNN-name.md / BUG-NNN-name-rN.md)
FIRST_ITERATION_BUG_RE = re.compile(r"^BUG-(\d+)-([a-z][a-z0-9-]*)\.md$")
SUPERSESSION_ITERATION_BUG_RE = re.compile(r"^BUG-(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$")

# ---------------------------------------------------------------------------
# L2 required-section helpers (slice 3 — canon §4.8 + tolerant prefix-match)
# ---------------------------------------------------------------------------

_HEADING_LINE_RE = re.compile(r"^\s*#{2,6}\s+(.+?)\s*$", re.MULTILINE)
_HEADING_NUM_PREFIX_RE = re.compile(r"^[\d.]+\s+")
_CONDITIONAL_MARKERS: tuple[str, ...] = (
    " (if any)", " (where applicable)", " (optional)",
)


def _extract_headings(text: str) -> list[str]:
    out: list[str] = []
    for m in _HEADING_LINE_RE.finditer(text):
        raw = m.group(1).strip()
        raw = _HEADING_NUM_PREFIX_RE.sub("", raw).strip()
        if raw:
            out.append(raw)
    return out


def _strip_conditional(section: str) -> tuple[str, bool]:
    for marker in _CONDITIONAL_MARKERS:
        if section.endswith(marker):
            return section[: -len(marker)].strip(), True
    return section, False


def _heading_satisfies(heading: str, canon_section: str) -> bool:
    h = heading.strip().lower()
    c = canon_section.strip().lower()
    if not h or not c:
        return False
    if h == c:
        return True
    if c.startswith(h):
        rest = c[len(h):]
        if not rest or not rest[0].isalnum():
            return True
    if h.startswith(c):
        rest = h[len(c):]
        if not rest or not rest[0].isalnum():
            return True
    return False


def _find_missing_sections(text: str, required: tuple[str, ...]) -> list[str]:
    headings = _extract_headings(text)
    missing: list[str] = []
    for raw_section in required:
        canon_name, is_conditional = _strip_conditional(raw_section)
        if any(_heading_satisfies(h, canon_name) for h in headings):
            continue
        if is_conditional:
            continue
        missing.append(canon_name)
    return missing

CONVENTIONAL_PREFIX_RE = re.compile(r"^(fix|feat)(\([^)]+\))?:")
REFS_LINE_RE = re.compile(r"^Refs:\s+(\S+)", re.MULTILINE)
METADATA_BLOCK_RE = re.compile(r"^>\s+\*\*([^:*]+):\*\*\s+(.+)$", re.MULTILINE)

# v1.7 LLD-009 r6 — tiered narrow-change attestation citation regex.
# ALLOWED_GATES sourced from canon §4.9 via cli.vocabulary import above.
FINDING_REF_RE = re.compile(
    r"^Addresses:\s+(docs/reviews/[^\s]+\.review\.yaml)\s+gate\s+"
    r"(completeness|evidence|clarity|consistency)\s+finding\s+(\d+)\s+"
    r"\((Minor|Important|Critical)\)\s*$",
    re.MULTILINE,
)
BYPASS_ANNOTATION_RE = re.compile(r"^Bypass:\s+(.+)$", re.MULTILINE)
CI_ENV_VARS: tuple[str, ...] = (
    "CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "CIRCLECI", "TRAVIS", "JENKINS_URL",
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    location: str
    message: str

    def format(self) -> str:
        emoji = "❌" if self.severity == "error" else "⚠️"
        return f"{emoji}  {self.location}: {self.message}"


# ---------------------------------------------------------------------------
# Doc-type detection
# ---------------------------------------------------------------------------


def detect_doc_type(path: Path) -> str | None:
    parts = path.parts
    if "features" in parts:
        return "feature"
    if "bugs" in parts:
        return "bug"
    if "adr" in parts:
        return "adr"
    if "postmortems" in parts:
        return "postmortem"
    if "runbooks" in parts:
        return "runbook"
    if "design" in parts:
        return "design"
    return None


# ---------------------------------------------------------------------------
# Doc validation
# ---------------------------------------------------------------------------


def lint_doc(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not path.exists():
        return [Finding("error", str(path), "file does not exist")]

    text = path.read_text(encoding="utf-8")
    doc_type = detect_doc_type(path)
    if doc_type is None:
        return [Finding(
            "warning", str(path),
            "could not infer doc type from path; skipping section + status checks",
        )]

    # 1. Metadata block — must exist within first 25 lines
    head = "\n".join(text.splitlines()[:25])
    metadata = dict(METADATA_BLOCK_RE.findall(head))
    metadata_keys = {k.strip() for k in metadata}

    required_meta_keys = {"Doc ID", "Date", "Status"}
    missing_meta = required_meta_keys - metadata_keys
    if missing_meta:
        findings.append(Finding(
            "error", str(path),
            f"metadata block missing required keys: {sorted(missing_meta)}",
        ))

    # 2. Status enum
    status = metadata.get("Status", "").strip().split("|")[0].strip()
    if status and status not in STATUS_ENUMS[doc_type]:
        # Allow a value that appears anywhere in the enum (template default lists all options)
        if not any(s in metadata.get("Status", "") for s in STATUS_ENUMS[doc_type]):
            findings.append(Finding(
                "error", str(path),
                f"Status '{status}' not in {doc_type} enum {sorted(STATUS_ENUMS[doc_type])}",
            ))

    # 3. Required sections — canon §4.8 + tolerant prefix-match.
    required = REQUIRED_SECTIONS.get(doc_type, ())
    for section in _find_missing_sections(text, required):
        findings.append(Finding(
            "error", str(path),
            f"missing required section '{section}' "
            f"(per docs/design/controlled-vocabulary.md §4.8 for {doc_type})",
        ))

    # 4. Placeholder text in produced docs
    for placeholder in ("TBD", "[fill in]", "TODO:", "FIXME:"):
        if placeholder in text:
            findings.append(Finding(
                "warning", str(path),
                f"contains placeholder '{placeholder}' — fill in or remove before commit",
            ))

    return findings


def lint_mermaid(path: Path) -> list[Finding]:
    """Validate mermaid blocks in a markdown file.

    Uses npx @mermaid-js/mermaid-cli for full validation if available,
    falls back to MermaidDiagram.basic_syntax_check() otherwise.
    """
    global _warned_no_npx
    findings: list[Finding] = []
    if not path.exists():
        return [Finding("error", str(path), "file does not exist")]

    em = _load_extract_mermaid()
    diagrams = em.extract_diagrams_from_file(path)
    if not diagrams:
        return findings

    npx_available = shutil.which("npx") is not None

    if npx_available:
        for d in diagrams:
            try:
                proc = subprocess.run(
                    ["npx", "-y", "--quiet", "@mermaid-js/mermaid-cli",
                     "-i", "/dev/stdin", "-o", "/tmp/orchestra_mermaid_out.svg"],
                    input=d.content, capture_output=True, text=True, timeout=30,
                )
                if proc.returncode != 0:
                    findings.append(Finding(
                        "error", f"{path}:{d.line_number}",
                        f"mermaid parse error: {proc.stderr.strip().splitlines()[-1] if proc.stderr else 'unknown'}"
                    ))
            except subprocess.TimeoutExpired:
                findings.append(Finding(
                    "error", f"{path}:{d.line_number}",
                    "mermaid validation timed out (30s)"
                ))
    else:
        if not _warned_no_npx:
            print("warning: npx not found — mermaid validation degraded. "
                  "No global install needed; `npx -y @mermaid-js/mermaid-cli` fetches per-invocation.",
                  file=sys.stderr)
            _warned_no_npx = True
        for d in diagrams:
            errors = d.basic_syntax_check()
            for err in errors:
                findings.append(Finding(
                    "error", f"{path}:{d.line_number}",
                    f"mermaid syntax: {err}"
                ))

    return findings


# ---------------------------------------------------------------------------
# v1.5 LLD-006-r4 — Helpers
# ---------------------------------------------------------------------------


_MD_META_LINE_RE = re.compile(r"^>\s+\*\*([^:*]+):\*\*\s+(.+?)\s*$", re.MULTILINE)
_YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_metadata(text: str) -> dict[str, str]:
    """Parse doc metadata as a flat dict.

    Supports two conventions:
      1. YAML frontmatter (`---\\nKey: value\\n---`) — parsed via python-frontmatter
      2. Markdown blockquote metadata block (`> **Key:** value`) — orchestra v1.0+ default

    Returns {} if neither format is present.
    """
    fm_match = _YAML_FRONTMATTER_RE.match(text)
    if fm_match:
        try:
            import frontmatter
            post = frontmatter.loads(text)
            return {k: str(v) for k, v in post.metadata.items()}
        except Exception:
            return {}
    return {m.group(1).strip(): m.group(2).strip()
            for m in _MD_META_LINE_RE.finditer(text)}


def parse_status(text: str) -> str:
    """Extract Status field value from doc text (markdown or YAML frontmatter)."""
    val = parse_metadata(text).get("Status", "")
    return val.split("|")[0].strip()


def resolve_supersession_link(repo_root: Path, link_value: str) -> Path | None:
    """Resolve `Supersedes:` / `Superseded by:` link to actual file location.

    Checks canon-located first, then archive. Returns None if not found.
    """
    canon_path = repo_root / link_value
    if canon_path.exists():
        return canon_path
    parts = Path(link_value).parts
    if parts and parts[0] == "docs" and len(parts) >= 2:
        archive_path = repo_root / "docs" / "archive" / "/".join(parts[1:])
        if archive_path.exists():
            return archive_path
    return None


def extract_changelog_and_strip(body: str) -> tuple[list[str], str]:
    """Locate ## Changelog table; return (list of row lines, body with table block replaced).

    Replaces the captured Changelog block with a sentinel so byte-comparison of
    body-without-changelog is meaningful.
    """
    lines = body.split("\n")
    changelog_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Changelog\s*$", line):
            changelog_idx = i
            break
    if changelog_idx is None:
        return ([], body)
    rows: list[str] = []
    j = changelog_idx + 1
    # Skip blank lines until first table-like line
    while j < len(lines) and not lines[j].startswith("|"):
        j += 1
    # Expect: lines[j] = "| Date | Change |"; lines[j+1] = "|---|---|"
    if (j + 1 < len(lines)
            and lines[j].startswith("|")
            and lines[j + 1].startswith("|---")):
        j += 2
        while j < len(lines) and lines[j].startswith("|"):
            rows.append(lines[j])
            j += 1
    sentinel = "<<CHANGELOG_BLOCK>>"
    body_no_chlog = "\n".join(lines[:changelog_idx] + [sentinel] + lines[j:])
    return (rows, body_no_chlog)


def _split_metadata_and_body(text: str) -> tuple[dict[str, str], str]:
    """Return (metadata_dict, body_after_metadata).

    For YAML frontmatter: body is everything after closing ---.
    For markdown blockquote metadata: body is everything after the metadata block
    (greedy match: the last contiguous metadata-block line).
    """
    fm_match = _YAML_FRONTMATTER_RE.match(text)
    if fm_match:
        try:
            import frontmatter
            post = frontmatter.loads(text)
            md = {k: str(v) for k, v in post.metadata.items()}
            return (md, post.content)
        except Exception:
            return ({}, text)
    md = {m.group(1).strip(): m.group(2).strip()
          for m in _MD_META_LINE_RE.finditer(text)}
    if not md:
        return ({}, text)
    # Find end of last metadata-block line
    last_match = None
    for m in _MD_META_LINE_RE.finditer(text):
        last_match = m
    body_start = last_match.end() if last_match else 0
    return (md, text[body_start:])


def _verify_finding_in_attestation(
    repo_root: Path,
    attestation_path: str,
    gate: str,
    finding_n: int,
    claimed_severity: str,
) -> tuple[bool, str]:
    """Navigate gates[<gate>].findings[finding_n-1].severity; verify == claimed.

    Reads STAGED content (git show :0:) — NOT working-tree — closes codex r2
    CRITICAL trust-boundary break. Path-traversal defense via
    `Path.is_relative_to` (NOT str.startswith — codex r2 HIGH#3).
    """
    import yaml as _yaml

    if not attestation_path.startswith("docs/reviews/"):
        return (False, f"attestation_path_outside_docs_reviews: {attestation_path}")
    if gate not in ALLOWED_GATES:
        return (False, f"unknown_gate: {gate!r} (allowed: {ALLOWED_GATES})")

    try:
        full = (repo_root / attestation_path).resolve()
    except OSError as e:
        return (False, f"attestation_path_resolve_error: {e}")
    reviews_root = (repo_root / "docs" / "reviews").resolve()
    try:
        if not full.is_relative_to(reviews_root):
            return (False, f"attestation_path_outside_docs_reviews: {attestation_path}")
    except ValueError:
        return (False, f"attestation_path_outside_docs_reviews: {attestation_path}")

    try:
        staged_yaml = subprocess.check_output(
            ["git", "show", f":0:{attestation_path}"],
            cwd=repo_root, text=True, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").lower()
        if "exists on disk, but not in" in stderr or "does not exist" in stderr or "no such" in stderr:
            return (False, f"attestation_not_staged: {attestation_path}")
        return (False, f"attestation_read_error: {e}")

    try:
        att = _yaml.safe_load(staged_yaml)
    except _yaml.YAMLError as e:
        return (False, f"attestation_parse_error: {e}")

    findings = (((att or {}).get("gates") or {}).get(gate) or {}).get("findings") or []
    if finding_n < 1 or finding_n > len(findings):
        return (False, f"finding_n_out_of_range: gate {gate} finding {finding_n} "
                       f"(have {len(findings)})")
    actual = (findings[finding_n - 1] or {}).get("severity", "")
    if actual != claimed_severity:
        return (False, f"severity_mismatch: cited {claimed_severity}; attestation "
                       f"{actual} (gate {gate} finding {finding_n})")
    return (True, "")


def _verify_changelog_row_per_finding(
    new_body: str,
    prior_body: str,
    deduped_refs: list[tuple[str, str, int, str]],
) -> tuple[bool, str]:
    """Per ref: assert a NEW Changelog row (not in prior) cites attestation basename + gate + finding N.

    Operates on the delta (new_rows - prior_rows) — defends against false-accept
    where prior Changelog already mentioned same basename+finding from a previous
    narrow-change. Per LLD-009 r6 A5 + sonnet F5.
    """
    new_rows, _ = extract_changelog_and_strip(new_body)
    prior_rows, _ = extract_changelog_and_strip(prior_body)
    prior_set = set(prior_rows)
    delta_rows = [r for r in new_rows if r not in prior_set]

    for att_path, gate, finding_n, _severity in deduped_refs:
        att_basename = Path(att_path).name
        pattern = re.compile(
            rf"{re.escape(att_basename)}.*\bgate\s+{re.escape(gate)}\b.*\bfinding\s+{finding_n}\b",
            re.IGNORECASE,
        )
        if not any(pattern.search(row) for row in delta_rows):
            return (False,
                    f"missing_changelog_row: {att_path} gate {gate} finding {finding_n} "
                    f"(must be NEW row in Changelog, not inherited from prior commit)")
    return (True, "")


def is_narrow_change(
    prior_text: str,
    new_text: str,
    commit_msg: str | None = None,
    repo_root: Path | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason). v1.7 LLD-009 r6 — tiered rule + L2-detect/L2-finalize.

    L2-detect path (commit_msg is None): strict-binary — whitelist + Changelog
    append only. Body change returns (False, reason). Caller annotates pending
    file but does NOT block (lint_staged).

    L2-finalize path (commit_msg + repo_root provided): tiered rule per
    BUG-011 — Critical never bypasses; Minor body edit + Addresses: + new
    Changelog row passes; Important uses ≤3 / ≥4 threshold.
    """
    prior_md, prior_body = _split_metadata_and_body(prior_text)
    new_md, new_body = _split_metadata_and_body(new_text)

    fm_diff_keys = {
        k for k in (set(prior_md.keys()) | set(new_md.keys()))
        if prior_md.get(k) != new_md.get(k)
    }
    forbidden = fm_diff_keys - WHITELIST_FRONTMATTER_FIELDS
    if forbidden:
        return (False, f"frontmatter fields modified outside whitelist: {sorted(forbidden)}")

    prior_chlog, prior_no_chlog = extract_changelog_and_strip(prior_body)
    new_chlog, new_no_chlog = extract_changelog_and_strip(new_body)

    body_unchanged = (prior_no_chlog == new_no_chlog)
    changelog_append_only = (new_chlog[:len(prior_chlog)] == prior_chlog)

    if body_unchanged and changelog_append_only:
        return (True, "whitelist edit")

    if commit_msg is None or repo_root is None:
        # L2-detect path: strict-binary reject
        if not body_unchanged:
            return (False, "body content outside Changelog table modified "
                           "(any heading/paragraph/code-block change requires supersession)")
        return (False, "Changelog rows modified or removed (only append allowed)")

    # L2-finalize path: tiered rule
    if not changelog_append_only:
        return (False, "Changelog rows modified or removed (only append allowed)")

    refs = FINDING_REF_RE.findall(commit_msg)
    if not refs:
        return (False, "canon-inplace body change without Addresses: lines "
                       "(supersession required, OR add `Addresses:` lines per finding)")

    # Dedupe by (path, gate, finding_n) — anti-copy-paste-inflation
    seen: set[tuple[str, str, int]] = set()
    deduped_refs: list[tuple[str, str, int, str]] = []
    for att_path, gate, finding_n_str, severity in refs:
        key = (att_path, gate, int(finding_n_str))
        if key in seen:
            continue
        seen.add(key)
        deduped_refs.append((att_path, gate, int(finding_n_str), severity))

    critical_findings: list[str] = []
    important_count = 0
    for att_path, gate, finding_n, severity in deduped_refs:
        ok, why = _verify_finding_in_attestation(
            repo_root, att_path, gate, finding_n, severity,
        )
        if not ok:
            return (False, why)
        if severity == "Critical":
            critical_findings.append(f"{att_path} gate {gate} finding {finding_n}")
        elif severity == "Important":
            important_count += 1

    if critical_findings:
        listing = "; ".join(critical_findings)
        extra = f" [also {important_count} Important findings present]" if important_count else ""
        return (False, f"Critical finding(s) cannot be fixed via narrow-change "
                       f"(supersession required): {listing}{extra}")

    if important_count >= 4:
        return (False, f"{important_count} Important findings exceed narrow-change "
                       f"threshold (3); supersession required")

    ok, why = _verify_changelog_row_per_finding(new_body, prior_body, deduped_refs)
    if not ok:
        return (False, why)

    return (True, "tiered narrow-change permitted")


# ---------------------------------------------------------------------------
# v1.5 LLD-006-r4 — Lint Check L1: Refs:-eligibility
# ---------------------------------------------------------------------------


def lint_commit_refs_eligible(commit_subject: str, commit_body: str,
                              repo_root: Path) -> list[Finding]:
    """L1 — Refs: line on fix:/feat: must point to Refs:-eligible canon-frozen doc.

    Eligible: docs/{features,bugs,adr,design,postmortems,runbooks}/<id>-name(-rN)?.md
              with Status ∈ canon-frozen-statuses.
    REJECTED: docs/plans/, docs/archive/, docs/investigations/, docs/reviews/,
              any path outside REFS_ELIGIBLE_PREFIXES, or canon doc with non-canon-frozen Status.
    """
    findings: list[Finding] = []
    # Refs: required only on fix:/feat: per existing convention; preserved here.
    if not CONVENTIONAL_PREFIX_RE.match(commit_subject):
        return findings

    refs_lines = REFS_LINE_RE.findall(commit_body)
    if not refs_lines:
        findings.append(Finding(
            "error", "commit-msg",
            f"{commit_subject!r} is a fix:/feat: commit with no `Refs:` line — "
            "orphan commit not allowed",
        ))
        return findings

    for ref in refs_lines:
        if not ref.startswith(REFS_ELIGIBLE_PREFIXES):
            findings.append(Finding(
                "error", "commit-msg",
                f"Refs: {ref} — not in Refs:-eligible prefix list. "
                f"Refs must point to canon-frozen docs in {REFS_ELIGIBLE_PREFIXES}. "
                "Plans, archive, investigations, reviews are NOT Refs:-eligible.",
            ))
            continue
        ref_path = repo_root / ref
        if not ref_path.exists():
            findings.append(Finding(
                "error", "commit-msg",
                f"Refs: {ref} — file does not exist",
            ))
            continue
        status = parse_status(ref_path.read_text(encoding="utf-8"))
        if status not in CANON_FROZEN_STATUSES:
            findings.append(Finding(
                "error", "commit-msg",
                f"Refs: {ref} — Status is {status!r}, not in canon-frozen-statuses "
                f"{sorted(CANON_FROZEN_STATUSES)}. Drafts and archived docs are not "
                "Refs:-eligible.",
            ))
    return findings


# ---------------------------------------------------------------------------
# v1.5 LLD-006-r4 — Lint Check L2 retroactive (BUG-009) runs on committed SHAs
# via `_lint_commit_canon_inplace` below. Pre-commit-time L2 detection moved to
# L2-detect annotate-only path in `_l2_detect_write_pending` (v1.7 LLD-009 r6).
# v1.5 strict-binary pre-commit blocker removed: it false-rejected valid tiered
# Minor / Important narrow-change commits; L2-finalize at commit-msg-time now
# enforces tiered rule with full message context.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# v1.5 LLD-006-r4 — Lint Check L3: attestation path-mutation
# ---------------------------------------------------------------------------


def lint_attestation_path_resolution(repo_root: Path,
                                     attestation_paths: list[Path]) -> list[Finding]:
    """L3 — doc_subject.path must resolve to existing file under canon-or-archive."""
    import yaml as _yaml
    findings: list[Finding] = []
    for ap in attestation_paths:
        if not ap.exists():
            continue
        try:
            attestation = _yaml.safe_load(ap.read_text(encoding="utf-8"))
        except _yaml.YAMLError as e:
            findings.append(Finding("error", str(ap), f"YAML parse error: {e}"))
            continue
        if not isinstance(attestation, dict):
            continue
        subject_path = (attestation.get("doc_subject") or {}).get("path", "")
        if not subject_path:
            continue
        if not subject_path.startswith(ALLOWED_ATTESTATION_PATH_PREFIXES):
            findings.append(Finding(
                "error", str(ap),
                f"attestation doc_subject.path {subject_path!r} not under "
                "canon-type or archive/canon-type. "
                f"Allowed prefixes: {ALLOWED_ATTESTATION_PATH_PREFIXES}",
            ))
            continue
        full = repo_root / subject_path
        if not full.exists():
            findings.append(Finding(
                "error", str(ap),
                f"attestation doc_subject.path {subject_path!r} does not resolve to a real file",
            ))
    return findings


# ---------------------------------------------------------------------------
# v1.5 LLD-006-r4 — Lint Check L4: doc-id-burn
# ---------------------------------------------------------------------------


def _infer_doc_type_dir(path: Path) -> str | None:
    """Infer doc type from path; returns the canon-type segment (features/bugs/...)."""
    parts = path.parts
    for canon_type in ("features", "bugs", "adr", "design", "postmortems", "runbooks"):
        if canon_type in parts:
            return canon_type
    return None


def lint_doc_id_burn(new_doc_path: Path, repo_root: Path) -> list[Finding]:
    """L4 — first-iteration strict-greater id; supersession-iteration r-suffix uniqueness.

    Excludes the file currently being added from the glob (r3 review caught the
    self-defeating bug).
    """
    name = new_doc_path.name
    doc_type = _infer_doc_type_dir(new_doc_path)
    if doc_type is None:
        return []  # Not a typed doc; skip

    canon_dir = repo_root / "docs" / doc_type
    archive_dir = repo_root / "docs" / "archive" / doc_type

    m_first = FIRST_ITERATION_RE.match(name) or FIRST_ITERATION_BUG_RE.match(name)
    m_super = SUPERSESSION_ITERATION_RE.match(name) or SUPERSESSION_ITERATION_BUG_RE.match(name)

    if m_super:
        new_id = int(m_super.group(1))
        base_name = m_super.group(2)
        new_r = int(m_super.group(3))
        first_iter_name_plain = f"{m_super.group(1)}-{base_name}.md"
        first_iter_name_bug = f"BUG-{m_super.group(1)}-{base_name}.md"
        first_exists = any(
            (d / first_iter_name_plain).exists() or (d / first_iter_name_bug).exists()
            for d in (canon_dir, archive_dir)
        )
        if not first_exists:
            return [Finding(
                "error", str(new_doc_path),
                f"supersession-iteration {name} references base "
                f"{first_iter_name_plain!r} which does not exist in canon or archive. "
                "Cannot supersede a non-existent doc.",
            )]
        new_doc_resolved = new_doc_path.resolve() if new_doc_path.exists() else new_doc_path
        existing_rs: list[int] = []
        for d in (canon_dir, archive_dir):
            if not d.exists():
                continue
            patterns = (
                f"{m_super.group(1)}-{base_name}-r*.md",
                f"BUG-{m_super.group(1)}-{base_name}-r*.md",
            )
            for pat in patterns:
                for p in d.glob(pat):
                    if p.exists() and p.resolve() == new_doc_resolved:
                        continue  # Skip file currently being added
                    m = (SUPERSESSION_ITERATION_RE.match(p.name)
                         or SUPERSESSION_ITERATION_BUG_RE.match(p.name))
                    if m and m.group(2) == base_name:
                        existing_rs.append(int(m.group(3)))
        max_r = max(existing_rs, default=1)  # r=1 implicit (the first-iteration file)
        if new_r <= max_r:
            return [Finding(
                "error", str(new_doc_path),
                f"supersession-iteration r{new_r} reuses or precedes existing r-suffix "
                f"(max r={max_r}). Next available: r{max_r + 1}.",
            )]
        return []

    if m_first:
        new_id = int(m_first.group(1))
        existing_ids: list[int] = []
        for d in (canon_dir, archive_dir):
            if not d.exists():
                continue
            for p in d.glob("*.md"):
                m = FIRST_ITERATION_RE.match(p.name) or FIRST_ITERATION_BUG_RE.match(p.name)
                if m and p.resolve() != (new_doc_path.resolve() if new_doc_path.exists() else new_doc_path):
                    existing_ids.append(int(m.group(1)))
        max_id = max(existing_ids, default=0)
        if new_id <= max_id:
            return [Finding(
                "error", str(new_doc_path),
                f"first-iteration doc-id {new_id} reuses existing or burned id "
                f"(max={max_id}). Next available: {max_id + 1}.",
            )]
        return []

    return [Finding(
        "error", str(new_doc_path),
        f"filename {name!r} does not match first-iteration or supersession-iteration pattern",
    )]


# ---------------------------------------------------------------------------
# Commit validation
# ---------------------------------------------------------------------------


def lint_commit(commit_sha: str, repo_root: Path) -> list[Finding]:
    """Lint a single commit: subject+body Refs:-eligibility (L1) + canon-inplace (L2 retroactive).

    L2 retroactive (BUG-009) — read prior file state from `<SHA>~1` and current
    state from `<SHA>`; if prior Status canon-frozen and diff is non-narrow,
    emit Finding. Closes the post-hoc-detection gap that allowed canon-inplace
    commits 653db4e + bc359e7 to retroactively pass cli.lint --commit.
    """
    try:
        subject = subprocess.check_output(
            ["git", "log", "-1", "--format=%s", commit_sha],
            cwd=repo_root, text=True,
        ).strip()
        body = subprocess.check_output(
            ["git", "log", "-1", "--format=%B", commit_sha],
            cwd=repo_root, text=True,
        )
        files = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha],
            cwd=repo_root, text=True,
        ).strip().splitlines()
    except subprocess.CalledProcessError as e:
        return [Finding("error", commit_sha, f"git log/diff failed: {e}")]

    findings = lint_commit_refs_eligible(subject, body, repo_root)
    findings.extend(_lint_commit_canon_inplace(commit_sha, subject, files, repo_root))
    return findings


def _lint_commit_canon_inplace(commit_sha: str, subject: str, files: list[str],
                                repo_root: Path) -> list[Finding]:
    """L2 retroactive — reject canon-frozen body edits in a committed SHA (BUG-009).

    Skip on `revert:` prefix — reverts ARE body changes by design (they restore
    prior state). They are recovery, not new violations. The reverted commit
    itself is what L2 catches; running L2 on the revert would double-flag.
    """
    if subject.startswith("revert:") or subject.startswith("Revert "):
        return []
    findings: list[Finding] = []
    for path in files:
        if not path.endswith(".md") or not path.startswith(REFS_ELIGIBLE_PREFIXES):
            continue
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"{commit_sha}~1:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue  # New file at this commit; nothing to violate
        prior_status = parse_status(prior_text)
        if prior_status not in CANON_FROZEN_STATUSES:
            continue
        try:
            new_text = subprocess.check_output(
                ["git", "show", f"{commit_sha}:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue  # File deleted/moved; archive flow handles separately
        ok, why = is_narrow_change(prior_text, new_text)
        if not ok:
            findings.append(Finding(
                "error", path,
                f"Doc Status was {prior_status!r} (canon-frozen) at {commit_sha}~1. "
                f"Non-narrow change in commit {commit_sha}: {why}. "
                "Use supersession (new file with -rN suffix and Supersedes:) instead.",
            ))
    return findings


def lint_commit_range(rev_range: str, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        shas = subprocess.check_output(
            ["git", "log", "--format=%H", rev_range],
            cwd=repo_root, text=True,
        ).strip().splitlines()
    except subprocess.CalledProcessError as e:
        return [Finding("error", rev_range, f"git log failed: {e}")]

    for sha in shas:
        findings.extend(lint_commit(sha, repo_root))
    return findings


# ---------------------------------------------------------------------------
# v1.7 LLD-009 r6 — L2-detect + L2-finalize helpers
# ---------------------------------------------------------------------------


class UnresolvedMergeError(Exception):
    """Raised when staged path has unresolved merge stages 1/2/3."""


def _pending_file_path(repo_root: Path) -> Path:
    """Resolve `<git-dir>/orchestra-canon-inplace-pending` (worktree-safe)."""
    out = subprocess.check_output(
        ["git", "rev-parse", "--git-path", "orchestra-canon-inplace-pending"],
        cwd=repo_root, text=True,
    ).strip()
    p = Path(out)
    if not p.is_absolute():
        p = repo_root / p
    return p


def _read_staged_content(repo_root: Path, path: str) -> str:
    """Read stage-0 staged content for path. Raises UnresolvedMergeError on merge stages."""
    try:
        return subprocess.check_output(
            ["git", "show", f":0:{path}"],
            cwd=repo_root, text=True, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").lower()
        if "unmerged" in stderr or "exists on disk, but not in" in stderr:
            raise UnresolvedMergeError(path) from e
        raise


def _get_staged_blob_sha(repo_root: Path, path: str) -> str:
    """Return 40-hex sha of staged blob for path; empty if not staged."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--stage", "--", path],
            cwd=repo_root, text=True, stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError:
        return ""
    if not out:
        return ""
    # Format: <mode> <sha> <stage>\t<path>
    fields = out.split()
    return fields[1] if len(fields) >= 2 else ""


def _is_ci_environment() -> tuple[bool, list[str]]:
    """Per LLD-009 r6 A10 r5: ANY of CI_ENV_VARS non-empty → CI detected.

    Returns (is_ci, list_of_set_vars).
    """
    set_vars = [v for v in CI_ENV_VARS if os.environ.get(v)]
    return (bool(set_vars), set_vars)


def _bypass_audit_log_entry(repo_root: Path, msg_subject: str, reason: str) -> None:
    """Append TAB-separated 5-column entry to <git-dir>/orchestra-bypass-audit.log."""
    git_dir_out = subprocess.check_output(
        ["git", "rev-parse", "--git-path", "orchestra-bypass-audit.log"],
        cwd=repo_root, text=True,
    ).strip()
    log_path = Path(git_dir_out)
    if not log_path.is_absolute():
        log_path = repo_root / log_path
    try:
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        head_sha = "INITIAL"
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        user_host = f"{getpass.getuser()}@{socket.gethostname()}"
    except Exception:
        user_host = "unknown@unknown"
    line = "\t".join([ts, head_sha, user_host, msg_subject.replace("\t", " "), reason])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _scan_canon_inplace_candidates(
    repo_root: Path,
    staged: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Shared L2 scan: return [(blob_sha, path), ...] for canon-inplace candidates.

    Walks staged .md files under REFS_ELIGIBLE_PREFIXES; for each whose HEAD
    Status is canon-frozen and whose staged content fails strict-binary
    is_narrow_change, collects (sha, path). Skips unresolved merges silently.

    `staged=None` triggers `git diff --cached` lookup (ORCHESTRA_STRICT recompute
    path); explicit list reuses caller's existing scan (L2-detect path).
    """
    if staged is None:
        try:
            staged = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                cwd=repo_root, text=True,
            ).strip().splitlines()
        except subprocess.CalledProcessError:
            return []
    out: list[tuple[str, str]] = []
    for path in staged:
        if not path.endswith(".md") or not path.startswith(REFS_ELIGIBLE_PREFIXES):
            continue
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"HEAD:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue
        if parse_status(prior_text) not in CANON_FROZEN_STATUSES:
            continue
        try:
            new_text = _read_staged_content(repo_root, path)
        except UnresolvedMergeError:
            continue
        ok, _ = is_narrow_change(prior_text, new_text, commit_msg=None, repo_root=None)
        if ok:
            continue
        sha = _get_staged_blob_sha(repo_root, path)
        if not sha:
            continue
        out.append((sha, path))
    return out


def lint_commit_msg_finalize(msg_file_path: str, repo_root: Path) -> int:
    """L2-finalize entrypoint: read pending + msg + staged-content; apply tiered rule.

    Per LLD-009 r6 A2 + A10 + A10b:
    - ORCHESTRA_BYPASS=1 → multi-var CI-deny + mandatory Bypass: annotation
    - Pending absent + ORCHESTRA_STRICT=1 → recompute candidates inline
    - Pending absent + ORCHESTRA_STRICT unset → fail-open (pre-commit was bypass-OK)
    - Transactional cleanup (r6): success-only unlink; exception/reject preserves pending
    """
    if not msg_file_path:
        print("error: commit-msg arg required for L2-finalize", file=sys.stderr)
        return 1

    msg = Path(msg_file_path).read_text(encoding="utf-8")
    msg_subject = msg.splitlines()[0] if msg.splitlines() else ""

    # ORCHESTRA_BYPASS handling (A10)
    if os.environ.get("ORCHESTRA_BYPASS") == "1":
        is_ci, set_vars = _is_ci_environment()
        if is_ci:
            err = (f"error: ORCHESTRA_BYPASS=1 cannot be used in CI environment "
                   f"(detected via: {set_vars}). Fix the underlying issue or run locally.")
            print(err, file=sys.stderr)
            _bypass_audit_log_entry(repo_root, msg_subject,
                                    f"DENIED_CI_DETECTED({','.join(set_vars)})")
            return 1
        bypass_m = BYPASS_ANNOTATION_RE.search(msg)
        if not bypass_m:
            err = ("error: ORCHESTRA_BYPASS=1 requires 'Bypass: <reason>' annotation "
                   "in commit message body explaining justification.")
            print(err, file=sys.stderr)
            return 1
        reason = bypass_m.group(1).strip()
        print(f"WARNING: ORCHESTRA_BYPASS=1 set; L2-finalize skipped. Reason: {reason}",
              file=sys.stderr)
        _bypass_audit_log_entry(repo_root, msg_subject, reason)
        return 0

    pending_file = _pending_file_path(repo_root)
    pending_entries: list[tuple[str, str]] = []

    if pending_file.exists():
        for line in pending_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                sha, path = line.split("\t", 1)
            except ValueError:
                print(f"warning: pending-file malformed line: {line!r}", file=sys.stderr)
                continue
            pending_entries.append((sha, path))
    elif os.environ.get("ORCHESTRA_STRICT") == "1":
        pending_entries = _scan_canon_inplace_candidates(repo_root)
    else:
        return 0  # fail-open per A2 default

    if not pending_entries:
        return 0

    findings: list[Finding] = []
    for pending_sha, path in pending_entries:
        current_sha = _get_staged_blob_sha(repo_root, path)
        if pending_sha and current_sha != pending_sha:
            findings.append(Finding(
                "error", path,
                f"staged_drift: pending sha {pending_sha[:10]}; current {current_sha[:10]}",
            ))
            continue

        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"HEAD:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            prior_text = ""

        try:
            new_text = _read_staged_content(repo_root, path)
        except UnresolvedMergeError:
            findings.append(Finding("error", path, "unresolved_merge: cannot evaluate canon-inplace"))
            continue

        ok, why = is_narrow_change(prior_text, new_text,
                                    commit_msg=msg, repo_root=repo_root)
        if not ok:
            findings.append(Finding("error", path, why))

    for f in findings:
        print(f.format(), file=sys.stderr)

    # r6 transactional: success-only cleanup (preserve on reject for retry-safety)
    if not findings and pending_file.exists():
        pending_file.unlink(missing_ok=True)

    return 1 if findings else 0


def lint_pre_stage_check(doc_path: str, commit_msg_draft: str, repo_root: Path) -> int:
    """Author-iteration: run L2-finalize logic against working-tree + draft msg."""
    full = repo_root / doc_path
    if not full.exists():
        print(f"error: {doc_path} not found", file=sys.stderr)
        return 1
    try:
        prior_text = subprocess.check_output(
            ["git", "show", f"HEAD:{doc_path}"],
            cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        prior_text = ""
    new_text = full.read_text(encoding="utf-8")

    prior_status = parse_status(prior_text)
    if prior_status not in CANON_FROZEN_STATUSES:
        print(f"PASS — {doc_path} prior Status {prior_status!r} not canon-frozen; no L2 applies",
              file=sys.stderr)
        return 0

    ok, why = is_narrow_change(prior_text, new_text,
                                commit_msg=commit_msg_draft, repo_root=repo_root)
    if ok:
        print(f"PASS — {doc_path} draft message satisfies tiered rule", file=sys.stderr)
        return 0
    print(f"FAIL — {doc_path}: {why}", file=sys.stderr)
    return 1


def _l2_detect_write_pending(repo_root: Path, staged: list[str]) -> None:
    """L2-detect (LLD-009 r6 A1): annotate canon-inplace candidates to pending file.

    Truncates pending file at start; appends one TAB-separated `<sha>\\t<path>` per
    canon-inplace candidate. Does NOT block.
    """
    pending_file = _pending_file_path(repo_root)
    pending_file.parent.mkdir(parents=True, exist_ok=True)
    candidates = _scan_canon_inplace_candidates(repo_root, staged=staged)
    pending_file.write_text(
        "".join(f"{sha}\t{path}\n" for sha, path in candidates),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Pre-commit mode — read staged files
# ---------------------------------------------------------------------------


def lint_staged(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        staged = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=repo_root, text=True,
        ).strip().splitlines()
        added = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
            cwd=repo_root, text=True,
        ).strip().splitlines()
    except subprocess.CalledProcessError as e:
        return [Finding("error", "git", f"diff --cached failed: {e}")]

    for relpath in staged:
        path = repo_root / relpath
        if path.suffix != ".md":
            continue
        if detect_doc_type(path) is None:
            continue
        findings.extend(lint_doc(path))

    # L2-detect (v1.7 LLD-009 r6): annotate pending file; does NOT block
    # (replaces prior strict-binary L2 at pre-commit; L2-finalize at commit-msg-time
    # enforces tiered rule per BUG-011. `lint_commit_no_canon_inplace_edit` retained
    # for direct invocation + `lint_commit` retroactive path BUG-009.)
    try:
        _l2_detect_write_pending(repo_root, staged)
    except subprocess.CalledProcessError:
        pass  # pending file write failure shouldn't block pre-commit

    # L4 — doc-id-burn check (additions only)
    burn_eligible_prefixes = REFS_ELIGIBLE_PREFIXES + (
        "docs/archive/features/", "docs/archive/bugs/", "docs/archive/adr/",
        "docs/archive/design/", "docs/archive/postmortems/", "docs/archive/runbooks/",
    )
    for relpath in added:
        if not relpath.endswith(".md"):
            continue
        if not relpath.startswith(burn_eligible_prefixes):
            continue
        path = repo_root / relpath
        if detect_doc_type(path) is None:
            continue
        findings.extend(lint_doc_id_burn(path, repo_root))

    # L3 — attestation path-mutation guard (staged review yamls)
    staged_attestations = [
        repo_root / p for p in staged
        if p.startswith("docs/reviews/") and p.endswith((".yaml", ".yml"))
    ]
    if staged_attestations:
        findings.extend(lint_attestation_path_resolution(repo_root, staged_attestations))

    return findings


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def repo_root_from_cwd() -> Path:
    return Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True,
    ).strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="design-docs lint")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--commit", help="Lint a single commit by SHA / ref")
    g.add_argument("--range", dest="rev_range", help="Lint a commit range, e.g. main..HEAD")
    g.add_argument("--doc", help="Lint a single doc file")
    g.add_argument("--pre-commit", action="store_true", help="Lint staged docs (for pre-commit hook)")
    g.add_argument("--attestations", action="store_true",
                   help="Lint all attestation YAMLs in docs/reviews/ (L3)")
    g.add_argument("--commit-msg-finalize", metavar="MSG_FILE",
                   help="L2-finalize: read pending + msg + staged; apply tiered rule")
    g.add_argument("--pre-stage-check", metavar="DOC_PATH",
                   help="Author pre-stage check against working tree + draft commit msg")
    parser.add_argument("--commit-msg-draft",
                        help="Draft commit message text (used with --pre-stage-check)")
    parser.add_argument("--mermaid", action="store_true", default=None,
                        help="Validate mermaid blocks (default: on for --doc and --pre-commit)")
    parser.add_argument("--no-mermaid", action="store_true",
                        help="Skip mermaid validation")
    args = parser.parse_args(argv)

    try:
        root = repo_root_from_cwd()
    except subprocess.CalledProcessError:
        print("error: not inside a git repository", file=sys.stderr)
        return 2

    # Mermaid lint default-on for --doc and --pre-commit; off for --commit / --range
    if args.no_mermaid:
        run_mermaid = False
    elif args.mermaid:
        run_mermaid = True
    else:
        run_mermaid = bool(args.doc or args.pre_commit)

    if args.doc:
        doc_path = Path(args.doc).resolve()
        findings = lint_doc(doc_path)
        if run_mermaid:
            findings.extend(lint_mermaid(doc_path))
    elif args.commit:
        findings = lint_commit(args.commit, root)
    elif args.rev_range:
        findings = lint_commit_range(args.rev_range, root)
    elif args.attestations:
        reviews_dir = root / "docs" / "reviews"
        attestations = sorted(reviews_dir.glob("*.review.yaml")) if reviews_dir.exists() else []
        findings = lint_attestation_path_resolution(root, attestations)
    elif args.commit_msg_finalize:
        return lint_commit_msg_finalize(args.commit_msg_finalize, root)
    elif args.pre_stage_check:
        if not args.commit_msg_draft:
            print("error: --pre-stage-check requires --commit-msg-draft <text>", file=sys.stderr)
            return 2
        return lint_pre_stage_check(args.pre_stage_check, args.commit_msg_draft, root)
    elif args.pre_commit:
        findings = lint_staged(root)
        if run_mermaid:
            try:
                staged = subprocess.check_output(
                    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                    cwd=root, text=True,
                ).strip().splitlines()
                for relpath in staged:
                    if relpath.endswith(".md"):
                        findings.extend(lint_mermaid(root / relpath))
            except subprocess.CalledProcessError:
                pass
    else:
        parser.print_help()
        return 2

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    for f in findings:
        print(f.format(), file=sys.stderr)

    if errors:
        print(f"\nFAIL: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    if warnings:
        print(f"\nPASS with {len(warnings)} warning(s)", file=sys.stderr)
        return 0
    print("PASS — all design-docs checks green", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
