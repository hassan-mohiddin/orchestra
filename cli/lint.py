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
    "feature": {"Draft", "Proposed", "Approved", "In Progress", "Implemented", "Verified"},
    "bug": {"Investigating", "Root Cause Found", "In Progress", "Fix Applied", "Verified"},
    "adr": {"Draft", "Proposed", "Approved", "Implemented", "Superseded", "Rejected"},
    "postmortem": {"Draft", "Reviewed", "Action Items Tracked", "Closed"},
    "runbook": {"Current", "Outdated", "Deprecated"},
    "design": {"Current", "Outdated", "Deprecated"},
}

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
# Commit validation
# ---------------------------------------------------------------------------


def lint_commit(commit_sha: str, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []

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

    if not CONVENTIONAL_PREFIX_RE.match(subject):
        return findings  # not fix:/feat: — Refs: not required

    refs_match = REFS_LINE_RE.search(body)
    if not refs_match:
        return [Finding(
            "error", commit_sha,
            f"{subject!r} is a fix:/feat: commit with no `Refs:` line — orphan commit not allowed",
        )]

    refs_path = repo_root / refs_match.group(1)
    if not refs_path.exists():
        findings.append(Finding(
            "error", commit_sha,
            f"Refs: {refs_match.group(1)} — file does not exist",
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
# Pre-commit mode — read staged files
# ---------------------------------------------------------------------------


def lint_staged(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        staged = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
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
