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
import importlib.util
import re
import shutil
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
# Doc-type lifecycle enums (must match STANDARDS.md)
# ---------------------------------------------------------------------------

STATUS_ENUMS: dict[str, set[str]] = {
    "feature": {"Draft", "Proposed", "Approved", "In Progress", "Implemented", "Verified",
                "Rejected", "Superseded"},
    "bug": {"Investigating", "Root Cause Found", "In Progress", "Fix Applied", "Verified",
            "Rejected", "Superseded"},
    "adr": {"Draft", "Proposed", "Approved", "Implemented", "Superseded", "Rejected"},
    "postmortem": {"Draft", "Reviewed", "Action Items Tracked", "Closed",
                   "Rejected", "Superseded"},
    "runbook": {"Current", "Outdated", "Deprecated", "Rejected", "Superseded"},
    "design": {"Current", "Outdated", "Deprecated", "Rejected", "Superseded"},
}

# v1.5 LLD-006-r4 — canon-frozen statuses (Refs:-eligible subset)
CANON_FROZEN_STATUSES: set[str] = {
    "Approved", "Implemented", "Verified", "Fix Applied", "Current",
}

# v1.5 LLD-006-r4 — Refs: must point under one of these prefixes.
# Plans, archive, investigations, reviews are NOT Refs:-eligible.
REFS_ELIGIBLE_PREFIXES: tuple[str, ...] = (
    "docs/features/", "docs/bugs/", "docs/adr/",
    "docs/design/", "docs/postmortems/", "docs/runbooks/",
)

# v1.5 LLD-006-r4 — narrow-change frontmatter whitelist
WHITELIST_FRONTMATTER_FIELDS: set[str] = {"Status", "Iteration", "Superseded by"}

# v1.5 LLD-006-r4 — attestation path-mutation guard (two-locations rule)
ALLOWED_ATTESTATION_PATH_PREFIXES: tuple[str, ...] = (
    "docs/features/", "docs/bugs/", "docs/adr/", "docs/design/",
    "docs/postmortems/", "docs/runbooks/",
    "docs/archive/features/", "docs/archive/bugs/", "docs/archive/adr/",
    "docs/archive/design/", "docs/archive/postmortems/", "docs/archive/runbooks/",
)

# v1.5 LLD-006-r4 — filename pattern recognition
FIRST_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)\.md$")
SUPERSESSION_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$")
# BUG-NNN- prefix variant for bug docs (BUG-NNN-name.md / BUG-NNN-name-rN.md)
FIRST_ITERATION_BUG_RE = re.compile(r"^BUG-(\d+)-([a-z][a-z0-9-]*)\.md$")
SUPERSESSION_ITERATION_BUG_RE = re.compile(r"^BUG-(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$")

REQUIRED_SECTIONS: dict[str, list[str]] = {
    "feature": [
        "Problem Statement", "Success Criteria", "Scope", "Design",
        "Edge Cases", "Security", "Testing", "Related Documents", "Changelog",
    ],
    "bug": [
        "Observed Behavior", "Expected Behavior", "Steps to Reproduce", "Environment",
        "Root Cause", "Fix Description", "Iteration Log", "Regression Prevention",
        "Related Documents", "Changelog",
    ],
    "adr": [
        "Context", "Decision", "Consequences", "Related Documents", "Changelog",
    ],
    "postmortem": [
        "Summary", "Impact", "Timeline", "Root Cause", "What Went Well",
        "What Went Wrong", "Where We Got Lucky", "Action Items", "Lessons Learned",
        "Related Documents", "Changelog",
    ],
    "runbook": [
        "When This Fires", "Quick Reference", "Diagnosis", "Mitigation",
        "Verification", "Escalation", "Related Documents", "Changelog",
    ],
    "design": [
        "Overview", "Changelog",
    ],
}

CONVENTIONAL_PREFIX_RE = re.compile(r"^(fix|feat)(\([^)]+\))?:")
REFS_LINE_RE = re.compile(r"^Refs:\s+(\S+)", re.MULTILINE)
METADATA_BLOCK_RE = re.compile(r"^>\s+\*\*([^:*]+):\*\*\s+(.+)$", re.MULTILINE)


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

    # 3. Required sections
    for section in REQUIRED_SECTIONS.get(doc_type, []):
        # Match section as a heading (## or ###) — case-insensitive partial
        if not re.search(rf"^\s*#{{2,3}}\s+\d*\.?\s*{re.escape(section)}", text, re.MULTILINE | re.IGNORECASE):
            findings.append(Finding(
                "error", str(path),
                f"missing required section '{section}' (per STANDARDS.md for {doc_type})",
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
            return {str(k): str(v) for k, v in post.metadata.items()}
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
            md = {str(k): str(v) for k, v in post.metadata.items()}
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


def is_narrow_change(prior_text: str, new_text: str) -> tuple[bool, str]:
    """Return (ok, reason). Permitted edits per LLD-006-r4 § narrow change:
      1. Metadata: only WHITELIST_FRONTMATTER_FIELDS may differ
      2. Changelog table: append-only (existing rows byte-identical)
      3. Body excluding Changelog: byte-identical

    Handles both YAML frontmatter (`---\\n...\\n---`) and markdown blockquote
    metadata blocks (`> **Key:** value`). orchestra v1.0+ default is the latter.
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

    if prior_no_chlog != new_no_chlog:
        return (False, "body content outside Changelog table modified "
                       "(any heading/paragraph/code-block change requires supersession)")

    if new_chlog[:len(prior_chlog)] != prior_chlog:
        return (False, "Changelog rows modified or removed (only append allowed)")

    return (True, "")


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
# v1.5 LLD-006-r4 — Lint Check L2: canon-frozen narrow-change
# ---------------------------------------------------------------------------


def lint_commit_no_canon_inplace_edit(repo_root: Path,
                                      staged_files: list[str]) -> list[Finding]:
    """L2 — reject in-place edit of canon-frozen doc beyond narrow change."""
    findings: list[Finding] = []
    for path in staged_files:
        if not path.endswith(".md"):
            continue
        if not path.startswith(REFS_ELIGIBLE_PREFIXES):
            continue
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"HEAD:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue  # New file (no prior at HEAD)
        prior_status = parse_status(prior_text)
        if prior_status not in CANON_FROZEN_STATUSES:
            continue
        full_path = repo_root / path
        if not full_path.exists():
            continue
        new_text = full_path.read_text(encoding="utf-8")
        ok, why = is_narrow_change(prior_text, new_text)
        if not ok:
            findings.append(Finding(
                "error", path,
                f"Doc Status was {prior_status!r} (canon-frozen). "
                f"Non-narrow change: {why}. "
                "Use supersession (new file with -rN suffix and Supersedes:) instead.",
            ))
    return findings


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
    """Lint a single commit: subject + body Refs:-eligibility (L1)."""
    try:
        subject = subprocess.check_output(
            ["git", "log", "-1", "--format=%s", commit_sha],
            cwd=repo_root, text=True,
        ).strip()
        body = subprocess.check_output(
            ["git", "log", "-1", "--format=%B", commit_sha],
            cwd=repo_root, text=True,
        )
    except subprocess.CalledProcessError as e:
        return [Finding("error", commit_sha, f"git log failed: {e}")]

    return lint_commit_refs_eligible(subject, body, repo_root)


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

    # L2 — canon-frozen narrow-change check (modifications only)
    findings.extend(lint_commit_no_canon_inplace_edit(repo_root, staged))

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
