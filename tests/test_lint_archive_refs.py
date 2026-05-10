"""LLD-006-r4 v1.5 — L1 Refs:-eligibility tests.

Maps to Acceptance A2: Refs: into docs/archive/ rejected on any commit type.
Test IDs: T1.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from cli.lint import lint_commit_refs_eligible


CANON_FROZEN_DOC = """# Feature: X

> **Doc ID:** 001-x
> **Date:** 2026-05-08
> **Status:** Implemented

Body.
"""


def _seed_canon_doc(repo: Path, relpath: str, body: str = CANON_FROZEN_DOC) -> Path:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_refs_into_archive_rejected(tmp_repo: Path) -> None:
    """T1 — A2. Refs: docs/archive/features/x.md → exit 1."""
    _seed_canon_doc(tmp_repo, "docs/archive/features/005-old.md")
    body = "fix: do thing\n\nDetails.\n\nRefs: docs/archive/features/005-old.md\n"
    findings = lint_commit_refs_eligible("fix: do thing", body, tmp_repo)
    assert any("not in Refs:-eligible prefix list" in f.message for f in findings), \
        f"expected archive Refs rejection, got: {[f.message for f in findings]}"


def test_refs_into_canon_frozen_accepted(tmp_repo: Path) -> None:
    """A2 sibling — Refs: docs/features/<canon-frozen> → no findings."""
    _seed_canon_doc(tmp_repo, "docs/features/001-x.md")
    body = "fix: do thing\n\nDetails.\n\nRefs: docs/features/001-x.md\n"
    findings = lint_commit_refs_eligible("fix: do thing", body, tmp_repo)
    assert not findings, f"expected no findings, got: {[f.message for f in findings]}"


def test_refs_into_plans_rejected(tmp_repo: Path) -> None:
    """A2 sibling — Refs: docs/plans/... never Refs:-eligible per LLD-006-r4."""
    _seed_canon_doc(tmp_repo, "docs/plans/2026-05-08-thing.md", body="# plan")
    body = "feat: ship X\n\nRefs: docs/plans/2026-05-08-thing.md\n"
    findings = lint_commit_refs_eligible("feat: ship X", body, tmp_repo)
    assert any("not in Refs:-eligible prefix list" in f.message for f in findings)


def test_refs_into_draft_rejected(tmp_repo: Path) -> None:
    """A2 sibling — canon-located doc with Status: Draft is NOT Refs:-eligible."""
    draft = CANON_FROZEN_DOC.replace("Status:** Implemented", "Status:** Draft")
    _seed_canon_doc(tmp_repo, "docs/features/001-x.md", body=draft)
    body = "feat: ship X\n\nRefs: docs/features/001-x.md\n"
    findings = lint_commit_refs_eligible("feat: ship X", body, tmp_repo)
    assert any("not in canon-frozen-statuses" in f.message for f in findings)


def test_non_fix_feat_commit_skipped(tmp_repo: Path) -> None:
    """docs:/test:/chore:/refactor: don't require Refs:."""
    body = "docs: tweak readme\n\nNo refs here.\n"
    findings = lint_commit_refs_eligible("docs: tweak readme", body, tmp_repo)
    assert not findings


def test_orphan_fix_commit_rejected(tmp_repo: Path) -> None:
    """fix:/feat: with no Refs: line is rejected."""
    body = "fix: thing\n\nNo refs.\n"
    findings = lint_commit_refs_eligible("fix: thing", body, tmp_repo)
    assert any("orphan commit" in f.message for f in findings)
