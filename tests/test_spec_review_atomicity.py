"""Atomic-write contract tests (S31/S31b slices)."""

import builtins
from pathlib import Path

import pytest


def _make_doc(tmp_path: Path) -> Path:
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    doc = docs / "008-foo.md"
    doc.write_text("# foo\n\n> **Iteration:** 1\n\n## Body\n")
    return doc


def test_no_partial_write_on_pre_write_failure(tmp_path, capsys, monkeypatch):
    """T25 / S31 — A24: schema-fail twice → no out file + no .tmp.* leftovers."""
    from cli import spec_review

    _make_doc(tmp_path)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(spec_review, "dispatch_subagent", lambda prompt: "broken: yaml: lol")

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1

    out_path = tmp_path / "docs" / "reviews" / "008-foo-r1.orchestra.review.yaml"
    assert not out_path.exists()
    reviews = tmp_path / "docs" / "reviews"
    if reviews.exists():
        leftovers = list(reviews.glob("*.tmp.*"))
        assert not leftovers, f"temp files leaked: {leftovers}"


def test_no_partial_write_on_io_exception(tmp_path, capsys, monkeypatch):
    """T25b / S31b — A24+PF10: IOError mid-write → no out file + temp cleaned."""
    from cli import spec_review

    _make_doc(tmp_path)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    good = (
        'schema_version: "1.0"\n'
        "doc_subject:\n"
        "  path: docs/features/008-foo.md\n"
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
    monkeypatch.setattr(spec_review, "dispatch_subagent", lambda prompt: good)

    real_open = builtins.open

    def failing_open(file, mode="r", *args, **kwargs):
        if "w" in mode and ".tmp." in str(file):
            raise IOError("disk full simulated")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", failing_open)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "atomic_write_failed" in err

    out_path = tmp_path / "docs" / "reviews" / "008-foo-r1.orchestra.review.yaml"
    assert not out_path.exists()
    reviews = tmp_path / "docs" / "reviews"
    leftovers = list(reviews.glob("*.tmp.*"))
    assert not leftovers, f"temp files leaked: {leftovers}"
