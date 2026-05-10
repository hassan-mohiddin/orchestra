"""Stale-state hash gate test for cli.spec_review (S23 slice)."""

from pathlib import Path


def test_doc_modified_between_dispatch_and_write_exits_1(tmp_path, capsys, monkeypatch):
    """T22 / S23 — A21 (F6): doc bytes change between dispatch + write → exit 1."""
    from cli import spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    doc = docs / "008-foo.md"
    doc.write_text("# foo\n\n> **Iteration:** 1\n\n## Body\n")

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

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    def mutate_then_dispatch(prompt):
        doc.write_text("# foo\n\n> **Iteration:** 1\n\n## Body\n\nMUTATED\n")
        return good

    monkeypatch.setattr(spec_review, "dispatch_subagent", mutate_then_dispatch)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    assert "stale_state" in capsys.readouterr().err
