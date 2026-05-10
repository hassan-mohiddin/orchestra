"""Schema validation tests for cli.spec_review (S10-S17, S20-S22 slices)."""

from pathlib import Path

import pytest


def _make_doc(tmp_path: Path, iteration: int = 1) -> Path:
    """Create tmp repo with docs/features/008-foo.md @ given iteration."""
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    doc = docs / "008-foo.md"
    doc.write_text(
        "# Feature: foo\n\n"
        f"> **Iteration:** {iteration}\n\n"
        "## Body\n\nHello.\n"
    )
    return doc


def _valid_attestation_yaml(iteration: int = 1) -> str:
    """Minimum-valid attestation YAML for tests."""
    return (
        'schema_version: "1.0"\n'
        "doc_subject:\n"
        "  path: docs/features/008-foo.md\n"
        "  content_hash: sha256:" + "0" * 64 + "\n"
        f"  iteration: {iteration}\n"
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


def _run(tmp_path, monkeypatch, capsys, yaml_outputs, iteration: int = 1, force=False):
    """Helper: dispatch_subagent returns yaml_outputs sequence."""
    from cli import spec_review

    _make_doc(tmp_path, iteration=iteration)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    outputs = list(yaml_outputs)
    calls = {"n": 0}

    def fake_dispatch(prompt):
        i = calls["n"]
        calls["n"] += 1
        return outputs[i]

    monkeypatch.setattr(spec_review, "dispatch_subagent", fake_dispatch)
    argv = ["docs/features/008-foo.md"]
    if force:
        argv.append("--force")
    rc = spec_review.main(argv)
    return rc, capsys.readouterr(), calls["n"]


# ---- S10 (T15): schema_version must be 1.0 -----------------------------------


def test_schema_version_must_be_1_0(tmp_path, monkeypatch, capsys):
    """T15 / S10 — A10: schema_version='1.1' → schema-fail."""
    bad = _valid_attestation_yaml().replace('"1.0"', '"1.1"')
    rc, cap, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1
    assert "schema" in cap.err.lower() or "validation" in cap.err.lower()


# ---- S11-S14 (T9-T12): required + enum violations ----------------------------


def test_missing_required_field_rejected(tmp_path, monkeypatch, capsys):
    """T9 / S11 — A7: drop overall_verdict → schema-fail."""
    bad = _valid_attestation_yaml().replace("overall_verdict: pass\n", "")
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


def test_unknown_gate_name_rejected(tmp_path, monkeypatch, capsys):
    """T10 / S12 — A7: gates.bogus → schema-fail (additionalProperties: false)."""
    bad = _valid_attestation_yaml().replace(
        "  consistency: {verdict: pass, findings: [], justification: 'no contradictions'}\n",
        "  consistency: {verdict: pass, findings: [], justification: 'no contradictions'}\n"
        "  bogus: {verdict: pass, findings: [], justification: 'extra'}\n",
    )
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


def test_severity_enum_violated_rejected(tmp_path, monkeypatch, capsys):
    """T11 / S13 — A7: severity=Info rejected."""
    bad = _valid_attestation_yaml().replace(
        "  completeness: {verdict: pass, findings: [], justification: 'all sections present'}\n",
        "  completeness:\n"
        "    verdict: fail\n"
        "    findings:\n"
        "      - {severity: Info, location: 'Body § Paragraph 1', problem: 'something'}\n",
    )
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


def test_overall_verdict_enum_violated_rejected(tmp_path, monkeypatch, capsys):
    """T12 / S14 — A7: overall_verdict='maybe' rejected."""
    bad = _valid_attestation_yaml().replace(
        "overall_verdict: pass\n", "overall_verdict: maybe\n"
    )
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


# ---- S15 (T14): location regex ----------------------------------------------


def test_location_field_regex_enforced(tmp_path, monkeypatch, capsys):
    """T14 / S15 — A9: location='garbage' → schema-fail (regex enforced)."""
    bad = _valid_attestation_yaml().replace(
        "  completeness: {verdict: pass, findings: [], justification: 'all sections present'}\n",
        "  completeness:\n"
        "    verdict: fail\n"
        "    findings:\n"
        "      - {severity: Important, location: 'garbage', problem: 'something'}\n",
    )
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


# ---- S16-S17 (T19a/b): empty findings + justification rules ------------------


def test_empty_findings_no_justification_rejected(tmp_path, monkeypatch, capsys):
    """T19a / S16 — A18: findings=[] without justification → schema-fail (if/then)."""
    # Drop justification from completeness gate (others stay valid)
    bad = _valid_attestation_yaml().replace(
        "  completeness: {verdict: pass, findings: [], justification: 'all sections present'}\n",
        "  completeness: {verdict: pass, findings: []}\n",
    )
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


def test_empty_findings_short_justification_rejected(tmp_path, monkeypatch, capsys):
    """T19b / S17 — A18: findings=[] with justification='ok' (<10 chars) → fail."""
    bad = _valid_attestation_yaml().replace(
        "justification: 'all sections present'", "justification: 'ok'"
    )
    rc, _, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1


# ---- S20-S22 (T4-T6): happy path + retry --------------------------------------


def test_valid_yaml_passes(tmp_path, monkeypatch, capsys):
    """T4 / S20 — A5: valid attestation → exit 0 + file written."""
    rc, cap, _ = _run(tmp_path, monkeypatch, capsys, [_valid_attestation_yaml()])
    assert rc == 0, f"stderr={cap.err}"
    out_path = tmp_path / "docs" / "reviews" / "008-foo-r1.review.yaml"
    assert out_path.exists()


def test_invalid_yaml_single_attempt_fails(tmp_path, monkeypatch, capsys):
    """T5 / S21 (v1.6.1) — A5 reworded: stdin-bound dispatch has no retry.

    Per v1.6.1 finding #5: sys.stdin.read() returns empty on second call,
    making in-Python retry meaningless. Schema-fail → exit 1 immediately.
    """
    bad = "missing: required\nfields"
    rc, cap, n_calls = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1
    assert n_calls == 1


def test_schema_validation_failed_error_surfaced(tmp_path, monkeypatch, capsys):
    """T6 / S22 (v1.6.1) — A5: schema-fail surfaces explicit error message."""
    bad = "schema_version: '0.0'\n"
    rc, cap, _ = _run(tmp_path, monkeypatch, capsys, [bad])
    assert rc == 1
    assert "schema" in cap.err.lower() or "validation" in cap.err.lower()
