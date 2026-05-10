"""Verdict authoritative-compute tests for cli.spec_review (S19 slice)."""

from pathlib import Path


def test_compute_overall_verdict_worst_case():
    """compute_overall_verdict returns worst-case across gates."""
    from cli.spec_review import compute_overall_verdict

    gates_pass = {f"g{i}": {"verdict": "pass"} for i in range(4)}
    assert compute_overall_verdict(gates_pass) == "pass"

    gates_one_cond = {**gates_pass, "g0": {"verdict": "conditional_pass"}}
    assert compute_overall_verdict(gates_one_cond) == "conditional_pass"

    gates_one_fail = {**gates_pass, "g0": {"verdict": "fail"}}
    assert compute_overall_verdict(gates_one_fail) == "fail"

    gates_mixed = {
        "a": {"verdict": "pass"},
        "b": {"verdict": "conditional_pass"},
        "c": {"verdict": "fail"},
        "d": {"verdict": "pass"},
    }
    assert compute_overall_verdict(gates_mixed) == "fail"


def test_overall_verdict_mismatch_exits_1(tmp_path, capsys, monkeypatch):
    """T18 / S19 — A17 (F2): one gate=fail but claimed overall=pass → exit 1."""
    from cli import spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text(
        "# foo\n\n> **Iteration:** 1\n\n## Body\n"
    )

    bad = (
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
        "  completeness:\n"
        "    verdict: fail\n"
        "    findings:\n"
        "      - {severity: Critical, location: 'Body § Paragraph 1', problem: 'broken'}\n"
        "  evidence: {verdict: pass, findings: [], justification: 'all claims cited'}\n"
        "  clarity: {verdict: pass, findings: [], justification: 'fresh reader can act'}\n"
        "  consistency: {verdict: pass, findings: [], justification: 'no contradictions'}\n"
        "overall_verdict: pass\n"  # claimed pass but completeness=fail → mismatch
    )

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(spec_review, "dispatch_subagent", lambda prompt: bad)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    assert "verdict_mismatch" in capsys.readouterr().err
