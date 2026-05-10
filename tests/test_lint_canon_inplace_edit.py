"""LLD-006-r4 v1.5 — L2 canon-frozen narrow-change tests.

Maps to Acceptance A3. Test IDs: T2, T3, T4, T5, T11.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from cli.lint import lint_commit_no_canon_inplace_edit, is_narrow_change


CANON_FROZEN = """---
Status: Implemented
Iteration: 1
---
# Feature

Some body content.

## Changelog

| Date | Change |
|---|---|
| 2026-05-01 | Initial |
"""


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _setup_repo_with_canon_doc(repo: Path, relpath: str = "docs/features/001-x.md",
                                body: str = CANON_FROZEN) -> Path:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    _git("add", relpath, cwd=repo)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "seed", cwd=repo)
    return p


def test_inplace_body_change_rejected(tmp_repo: Path) -> None:
    """T2 — body modified → not narrow → reject."""
    p = _setup_repo_with_canon_doc(tmp_repo)
    p.write_text(CANON_FROZEN.replace("Some body content.", "Modified body."),
                 encoding="utf-8")
    _git("add", "docs/features/001-x.md", cwd=tmp_repo)
    findings = lint_commit_no_canon_inplace_edit(tmp_repo, ["docs/features/001-x.md"])
    assert any("Non-narrow change" in f.message for f in findings)
    assert any("body content outside Changelog" in f.message for f in findings)


def test_changelog_append_accepted(tmp_repo: Path) -> None:
    """T3 — append a Changelog row → narrow → accept."""
    p = _setup_repo_with_canon_doc(tmp_repo)
    p.write_text(
        CANON_FROZEN + "| 2026-05-08 | Append entry |\n",
        encoding="utf-8",
    )
    _git("add", "docs/features/001-x.md", cwd=tmp_repo)
    findings = lint_commit_no_canon_inplace_edit(tmp_repo, ["docs/features/001-x.md"])
    assert not findings, f"unexpected findings: {[f.message for f in findings]}"


def test_status_field_update_accepted(tmp_repo: Path) -> None:
    """T4 — Status field flip (whitelisted) → narrow → accept."""
    p = _setup_repo_with_canon_doc(tmp_repo)
    p.write_text(
        CANON_FROZEN.replace("Status: Implemented", "Status: Verified"),
        encoding="utf-8",
    )
    _git("add", "docs/features/001-x.md", cwd=tmp_repo)
    findings = lint_commit_no_canon_inplace_edit(tmp_repo, ["docs/features/001-x.md"])
    assert not findings, f"unexpected findings: {[f.message for f in findings]}"


def test_new_doc_unaffected(tmp_repo: Path) -> None:
    """T5 — net-new doc (no HEAD prior) → check skipped."""
    p = tmp_repo / "docs/features/001-new.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(CANON_FROZEN, encoding="utf-8")
    findings = lint_commit_no_canon_inplace_edit(tmp_repo, ["docs/features/001-new.md"])
    assert not findings


def test_reason_field_added_rejected(tmp_repo: Path) -> None:
    """T11 — adding Reason: to canon-frozen frontmatter is non-whitelisted → reject."""
    p = _setup_repo_with_canon_doc(tmp_repo)
    body_with_reason = CANON_FROZEN.replace(
        "Iteration: 1",
        "Iteration: 1\nReason: arbitrary",
    )
    p.write_text(body_with_reason, encoding="utf-8")
    _git("add", "docs/features/001-x.md", cwd=tmp_repo)
    findings = lint_commit_no_canon_inplace_edit(tmp_repo, ["docs/features/001-x.md"])
    assert any("frontmatter fields modified outside whitelist" in f.message
               and "Reason" in f.message
               for f in findings), f"got: {[f.message for f in findings]}"


def test_is_narrow_change_pure_helper() -> None:
    """is_narrow_change reports correct reason for body changes."""
    ok, why = is_narrow_change(
        prior_text=CANON_FROZEN,
        new_text=CANON_FROZEN.replace("Some body", "Different body"),
    )
    assert not ok
    assert "body content outside Changelog" in why
