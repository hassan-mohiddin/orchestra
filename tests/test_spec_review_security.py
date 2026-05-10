"""Security-related tests for cli.spec_review (S4-S8, S18 slices)."""

import os
from pathlib import Path

import pytest


def _make_docs_tree(tmp_path: Path) -> Path:
    """Create a tmp 'repo' with docs/features/foo.md."""
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "foo.md").write_text("# foo\n")
    return tmp_path


def test_absolute_path_rejected(tmp_path):
    """T17a / S4 — A16: absolute path rejected."""
    from cli.spec_review import canonicalize_doc_path

    repo_root = _make_docs_tree(tmp_path)
    with pytest.raises(ValueError, match="absolute"):
        canonicalize_doc_path("/etc/passwd", repo_root)


def test_dotdot_escape_rejected(tmp_path):
    """T17b / S5 — A16: `..` escape outside docs/ rejected."""
    from cli.spec_review import canonicalize_doc_path

    repo_root = _make_docs_tree(tmp_path)
    (tmp_path / "outside.md").write_text("escaped\n")
    with pytest.raises(ValueError, match="outside repo docs"):
        canonicalize_doc_path("docs/../outside.md", repo_root)


def test_symlink_escape_rejected(tmp_path):
    """T17c / S6 — A16: symlink target outside docs/ rejected."""
    from cli.spec_review import canonicalize_doc_path

    repo_root = _make_docs_tree(tmp_path)
    outside = tmp_path / "secret.md"
    outside.write_text("secret\n")
    link = repo_root / "docs" / "features" / "link.md"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="outside repo docs"):
        canonicalize_doc_path("docs/features/link.md", repo_root)


def test_missing_file_returns_path_traversal_blocked(tmp_path, capsys, monkeypatch):
    """T21a / S7 — A20 (F5): missing file → exit 2 + path_traversal_blocked.

    main() must catch (ValueError, FileNotFoundError, OSError) from
    canonicalize_doc_path and exit 2 with explicit error message.
    """
    from cli import spec_review

    repo_root = _make_docs_tree(tmp_path)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: repo_root)

    rc = spec_review.main(["docs/features/missing.md"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "path_traversal_blocked" in err


def test_broken_symlink_returns_path_traversal_blocked(tmp_path, capsys, monkeypatch):
    """T21b / S8 — A20 (F5): broken symlink → exit 2 + path_traversal_blocked."""
    from cli import spec_review

    repo_root = _make_docs_tree(tmp_path)
    link = repo_root / "docs" / "features" / "broken.md"
    link.symlink_to(tmp_path / "does-not-exist.md")

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: repo_root)

    rc = spec_review.main(["docs/features/broken.md"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "path_traversal_blocked" in err


def test_attestation_path_mismatch_exits_1(tmp_path, capsys, monkeypatch):
    """T20 / S18 — A19 (F4): attestation doc_subject.path ≠ canonical input → exit 1."""
    from cli import spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text(
        "# foo\n\n> **Iteration:** 1\n\n## Body\n"
    )

    bad_yaml = (
        'schema_version: "1.0"\n'
        "doc_subject:\n"
        "  path: docs/features/wrong-doc.md\n"  # mismatch
        "  content_hash: sha256:" + "0" * 64 + "\n"
        "  iteration: 1\n"
        "reviewer:\n"
        '  identifier: "subagent:general-purpose+spec-review-v1"\n'
        '  invoked_at: "2026-05-10T00:00:00Z"\n'
        "  context_isolation: fresh_subagent\n"
        "gates:\n"
        "  completeness: {verdict: pass, findings: [], justification: 'all sections present'}\n"
        "  evidence: {verdict: pass, findings: [], justification: 'all claims cited'}\n"
        "  clarity: {verdict: pass, findings: [], justification: 'fresh reader can act'}\n"
        "  consistency: {verdict: pass, findings: [], justification: 'no contradictions'}\n"
        "overall_verdict: pass\n"
    )

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(spec_review, "dispatch_subagent", lambda prompt: bad_yaml)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    assert "path_mismatch" in capsys.readouterr().err
