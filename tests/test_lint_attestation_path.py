"""LLD-006-r4 v1.5 — L3 attestation path-mutation tests.

Maps to Acceptance A6: doc_subject.path must resolve to existing file under
canon-or-archive. Test IDs: T10a, T10b, T10c.
"""

from __future__ import annotations

from pathlib import Path

from cli.lint import lint_attestation_path_resolution


ATTESTATION_TEMPLATE = """schema_version: "1.0"
doc_subject:
  path: {path}
  content_hash: deadbeef
  iteration: 1
reviewer:
  identifier: test
  invoked_at: 2026-05-08
  context_isolation: fresh
gates:
  completeness:
    verdict: pass
    findings: []
overall_verdict: pass
"""


def _write_attestation(repo: Path, relpath: str, subject_path: str) -> Path:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(ATTESTATION_TEMPLATE.format(path=subject_path), encoding="utf-8")
    return p


def _seed_doc(repo: Path, relpath: str) -> Path:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# stub\n", encoding="utf-8")
    return p


def test_path_under_non_allowed_prefix_rejected(tmp_repo: Path) -> None:
    """T10a — doc_subject.path under docs/investigations/ → reject."""
    _seed_doc(tmp_repo, "docs/investigations/note.md")
    ap = _write_attestation(
        tmp_repo, "docs/reviews/x-r1.review.yaml",
        subject_path="docs/investigations/note.md",
    )
    findings = lint_attestation_path_resolution(tmp_repo, [ap])
    assert any("not under canon-type or archive/canon-type" in f.message for f in findings)


def test_path_under_canon_accepted(tmp_repo: Path) -> None:
    """T10b — doc_subject.path under docs/features/ (exists) → accept."""
    _seed_doc(tmp_repo, "docs/features/001-x.md")
    ap = _write_attestation(
        tmp_repo, "docs/reviews/001-r1.review.yaml",
        subject_path="docs/features/001-x.md",
    )
    findings = lint_attestation_path_resolution(tmp_repo, [ap])
    assert not findings, f"got: {[f.message for f in findings]}"


def test_path_under_archive_accepted(tmp_repo: Path) -> None:
    """T10c — doc_subject.path under docs/archive/features/ (exists) → accept."""
    _seed_doc(tmp_repo, "docs/archive/features/005-old.md")
    ap = _write_attestation(
        tmp_repo, "docs/reviews/005-r1.review.yaml",
        subject_path="docs/archive/features/005-old.md",
    )
    findings = lint_attestation_path_resolution(tmp_repo, [ap])
    assert not findings, f"got: {[f.message for f in findings]}"


def test_path_does_not_exist_rejected(tmp_repo: Path) -> None:
    """A6 sibling — allowed prefix but file missing → reject."""
    ap = _write_attestation(
        tmp_repo, "docs/reviews/099-r1.review.yaml",
        subject_path="docs/features/099-missing.md",
    )
    findings = lint_attestation_path_resolution(tmp_repo, [ap])
    assert any("does not resolve to a real file" in f.message for f in findings)
