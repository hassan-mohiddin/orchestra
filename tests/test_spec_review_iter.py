"""Iteration tests for cli.spec_review (S9 slice)."""

from pathlib import Path

import pytest


def test_iteration_mismatch_exits_1(tmp_path, capsys, monkeypatch):
    """T16 / S9 — A11: doc Iteration=2, attestation iteration=1 → exit 1.

    Also exercises parse_iteration_from_text on the > **Iteration:** N format.
    """
    from cli import spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    doc = docs / "008-foo.md"
    doc.write_text(
        "# Feature: foo\n\n"
        "> **Iteration:** 2\n\n"
        "## Body\n\nHello.\n"
    )

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    # Stub dispatch_subagent so we don't need the full schema-validation stack
    canned_yaml = (
        'schema_version: "1.0"\n'
        "doc_subject:\n"
        "  path: docs/features/008-foo.md\n"
        "  content_hash: sha256:" + "0" * 64 + "\n"
        "  iteration: 1\n"  # mismatch — doc says 2
        "reviewer:\n"
        "  identifier: subagent:general-purpose+spec-review-v1\n"
        "  invoked_at: 2026-05-10T00:00:00Z\n"
        "  context_isolation: fresh_subagent\n"
        "gates:\n"
        "  completeness: {verdict: pass, findings: [], justification: 'all sections present'}\n"
        "  evidence: {verdict: pass, findings: [], justification: 'all claims cited'}\n"
        "  clarity: {verdict: pass, findings: [], justification: 'fresh reader can act'}\n"
        "  consistency: {verdict: pass, findings: [], justification: 'no contradictions'}\n"
        "overall_verdict: pass\n"
    )
    monkeypatch.setattr(spec_review, "dispatch_subagent", lambda prompt: canned_yaml)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "iteration_mismatch" in err


def test_parse_iteration_default_is_1():
    """parse_iteration_from_text on doc without Iteration: field → 1."""
    from cli.spec_review import parse_iteration_from_text

    assert parse_iteration_from_text("# foo\nno metadata\n") == 1


def test_parse_iteration_from_metadata():
    """parse_iteration_from_text on standard `> **Iteration:** N` block."""
    from cli.spec_review import parse_iteration_from_text

    text = "# foo\n\n> **Iteration:** 4\n\n## Body\n"
    assert parse_iteration_from_text(text) == 4
