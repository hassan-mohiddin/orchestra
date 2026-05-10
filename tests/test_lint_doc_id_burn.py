"""LLD-006-r4 v1.5 — L4 doc-id-burn tests.

Maps to Acceptance A4 (first-iteration burn) + A5 (supersession r-suffix).
Test IDs: T6, T7, T8, T9.
"""

from __future__ import annotations

from pathlib import Path

from cli.lint import lint_doc_id_burn


def _seed(repo: Path, relpath: str, body: str = "# stub\n") -> Path:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_first_iter_id_le_max_rejected(tmp_repo: Path) -> None:
    """T6 — first-iter id ≤ existing max → reject (burn)."""
    _seed(tmp_repo, "docs/features/001-a.md")
    _seed(tmp_repo, "docs/features/002-b.md")
    new_doc = _seed(tmp_repo, "docs/features/002-c.md")  # id 2 reused
    findings = lint_doc_id_burn(new_doc, tmp_repo)
    assert any("reuses existing or burned id" in f.message for f in findings)


def test_first_iter_id_max_plus_1_accepted(tmp_repo: Path) -> None:
    """T7 — first-iter id = max+1 → accept."""
    _seed(tmp_repo, "docs/features/001-a.md")
    _seed(tmp_repo, "docs/features/002-b.md")
    new_doc = _seed(tmp_repo, "docs/features/003-c.md")  # next available
    findings = lint_doc_id_burn(new_doc, tmp_repo)
    assert not findings, f"got: {[f.message for f in findings]}"


def test_first_iter_id_skips_archive_in_max(tmp_repo: Path) -> None:
    """A4 sibling — archive ids count toward max."""
    _seed(tmp_repo, "docs/features/001-a.md")
    _seed(tmp_repo, "docs/archive/features/005-old.md")  # archived id 5
    new_doc = _seed(tmp_repo, "docs/features/004-c.md")  # 4 ≤ 5 → reject
    findings = lint_doc_id_burn(new_doc, tmp_repo)
    assert any("reuses existing or burned id" in f.message for f in findings)


def test_supersession_r_suffix_le_max_rejected(tmp_repo: Path) -> None:
    """T8 — supersession r-suffix ≤ existing max r → reject."""
    _seed(tmp_repo, "docs/features/006-foo.md")  # r=1 (first-iteration)
    _seed(tmp_repo, "docs/features/006-foo-r2.md")  # r=2 exists
    _seed(tmp_repo, "docs/features/006-foo-r3.md")  # r=3 exists
    new_doc = _seed(tmp_repo, "docs/features/006-foo-r2-extra.md")  # not supersession pattern
    # Use a real supersession-pattern reuse:
    new_doc = _seed(tmp_repo, "docs/archive/features/006-foo-r3.md")  # duplicate r=3
    findings = lint_doc_id_burn(new_doc, tmp_repo)
    # The new file at archive r3 should compare against canon r3 (existing) → r3 ≤ r3 reject
    assert any("reuses or precedes existing r-suffix" in f.message for f in findings), \
        f"got: {[f.message for f in findings]}"


def test_supersession_r_suffix_max_plus_1_accepted(tmp_repo: Path) -> None:
    """T9 — supersession r-suffix = max r+1 → accept."""
    _seed(tmp_repo, "docs/features/006-foo.md")
    _seed(tmp_repo, "docs/features/006-foo-r2.md")
    _seed(tmp_repo, "docs/features/006-foo-r3.md")
    new_doc = _seed(tmp_repo, "docs/features/006-foo-r4.md")
    findings = lint_doc_id_burn(new_doc, tmp_repo)
    assert not findings, f"got: {[f.message for f in findings]}"


def test_supersession_without_first_iteration_rejected(tmp_repo: Path) -> None:
    """A5 sibling — supersession refers to non-existent first-iteration."""
    new_doc = _seed(tmp_repo, "docs/features/099-nope-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_repo)
    assert any("does not exist in canon or archive" in f.message for f in findings)
