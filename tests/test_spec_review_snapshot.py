"""Single-snapshot semantics test for cli.spec_review (S24 slice)."""

from pathlib import Path


def test_single_read_for_hash_iter_prompt(tmp_path, monkeypatch):
    """T23 / S24 — A22 (F8): doc bytes read exactly twice (dispatch snapshot + write-time stale check).

    Hash, iteration, prompt all derive from the SAME pre-dispatch snapshot.
    Write-time check re-reads to detect stale state. No 3rd read.
    """
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

    read_calls = {"n": 0}
    real_read_bytes = Path.read_bytes

    def counting_read_bytes(self):
        # Only count reads of the target doc, not schema/template files
        if self == doc.resolve():
            read_calls["n"] += 1
        return real_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", counting_read_bytes)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(spec_review, "dispatch_subagent", lambda prompt: good)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 0
    assert read_calls["n"] == 2, f"expected 2 doc reads (snapshot+stale-check), got {read_calls['n']}"
