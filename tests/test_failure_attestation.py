"""Failure-attestation + output-quarantine tests (LLD-011 Phase 3 slices 3.15-3.22).

Failure-attestation primitives are unit-tested here. Wiring into the main()
dispatch flow happens at self-application time (post-Phase-3).
"""

from __future__ import annotations

from cli import failure_attestation


# ---------------------------------------------------------------------------
# Slice 3.15 — E11 prompt_missing → failure attestation persisted
# ---------------------------------------------------------------------------


def test_e11_prompt_missing_failure_attestation():
    """Slice 3.15 — build_failure_attestation(reason='prompt_missing') yields fail verdict."""
    att = failure_attestation.build_failure_attestation(
        doc_path="docs/features/008-foo.md",
        iteration=1,
        reason="prompt_missing",
        failed_sub_judges=["semantic"],
    )
    assert att["overall_verdict"] == "fail"
    assert att["overall_verdict_basis"]["reason"] == "prompt_missing"
    assert "semantic" in att["overall_verdict_basis"]["mandatory_failures"]


# ---------------------------------------------------------------------------
# Slice 3.16 — E17 optional sub-judge soft-fail
# ---------------------------------------------------------------------------


def test_e17_optional_soft_fail_no_mandatory_listed():
    """Slice 3.16 — optional sub-judge model unavailable → reason recorded, not in mandatory_failures."""
    att = failure_attestation.build_failure_attestation(
        doc_path="docs/features/008-foo.md",
        iteration=1,
        reason="model_unavailable",
        failed_sub_judges=["repo-context"],  # optional
    )
    assert att["overall_verdict_basis"]["reason"] == "model_unavailable"
    assert att["overall_verdict_basis"]["mandatory_failures"] == []


# ---------------------------------------------------------------------------
# Slice 3.17 — E17b mandatory sub-judge hard-fail
# ---------------------------------------------------------------------------


def test_e17b_mandatory_hard_fail():
    """Slice 3.17 — mandatory sub-judge model unavailable → mandatory_failures populated."""
    att = failure_attestation.build_failure_attestation(
        doc_path="docs/features/008-foo.md",
        iteration=1,
        reason="model_unavailable_mandatory",
        failed_sub_judges=["adversarial"],
    )
    assert "adversarial" in att["overall_verdict_basis"]["mandatory_failures"]


# ---------------------------------------------------------------------------
# Slice 3.18 — E18 doc_disappeared writes attestation (was no-attestation in v1)
# ---------------------------------------------------------------------------


def test_e18_doc_disappeared_attestation_built():
    """Slice 3.18 — E18 produces a fail attestation rather than skipping the write."""
    att = failure_attestation.build_failure_attestation(
        doc_path="docs/features/008-foo.md",
        iteration=2,
        reason="doc_disappeared",
    )
    assert att["overall_verdict"] == "fail"
    assert att["overall_verdict_basis"]["reason"] == "doc_disappeared"
    # No specific sub-judges named for this whole-dispatch failure
    assert att["overall_verdict_basis"]["mandatory_failures"] == []


# ---------------------------------------------------------------------------
# Slice 3.19 — E20 tampered attestation triggers failure write
# ---------------------------------------------------------------------------


def test_e20_attestation_tampered_persists_failure():
    """Slice 3.19 — iter-2 load detects tamper → failure attestation built for iter-2."""
    att = failure_attestation.build_failure_attestation(
        doc_path="docs/features/008-foo.md",
        iteration=2,
        reason="attestation_tampered",
        notes=["iter-1 integrity hash mismatch; delta-review aborted"],
    )
    assert att["overall_verdict_basis"]["reason"] == "attestation_tampered"
    assert any("integrity" in n for n in att["notes"])


# ---------------------------------------------------------------------------
# Slice 3.20 — E21 output-quarantine detects credential leak
# ---------------------------------------------------------------------------


def test_e21_quarantine_redacts_aws_key():
    """Slice 3.20 — AWS access key in sub-judge output is redacted; violations recorded."""
    output = "Found in env file: AKIAIOSFODNN7EXAMPLE in line 12"
    result = failure_attestation.quarantine_output(output)
    assert not result.clean
    assert "AKIAIOSFODNN7EXAMPLE" not in result.redacted_output
    assert "[REDACTED:" in result.redacted_output
    assert any("AKIA" in v for v in result.violations)


def test_e21_quarantine_clean_output():
    """Slice 3.20 — output without violations → clean=True, no redactions."""
    output = "Standard finding text at docs/features/008-foo.md:42 — missing section."
    result = failure_attestation.quarantine_output(output)
    assert result.clean
    assert result.violations == []
    assert result.redacted_output == output


def test_e21_quarantine_ssh_private_key_path():
    """Slice 3.20 — ssh private-key path in output is redacted."""
    output = "Read ~/.ssh/id_rsa for some reason"
    result = failure_attestation.quarantine_output(output)
    assert not result.clean
    assert "id_rsa" not in result.redacted_output


def test_e21_quarantine_stripe_key():
    """Fix #3 — Stripe live/test keys are redacted.

    Fixture string is built via concatenation so the literal token never
    appears in source — GitHub's secret-scanning push protection blocks
    repos containing `sk_live_<24+ alnum>` patterns even in test fixtures.
    """
    secret = "sk_" + "live" + "_" + "FAKE" + "TESTKEYDONOTUSE" + "12345678"
    output = f"Found {secret} in finding text"
    result = failure_attestation.quarantine_output(output)
    assert not result.clean
    assert secret not in result.redacted_output


def test_e21_quarantine_github_token():
    """Fix #3 — GitHub personal access tokens are redacted.

    Fixture built via concatenation (see stripe-key test rationale).
    """
    token = "gh" + "p_" + "FAKETESTTOKEN" + "DONOTUSE" + "123456789012345"
    output = f"Token {token} in commit"
    result = failure_attestation.quarantine_output(output)
    assert not result.clean
    assert token not in result.redacted_output


def test_e21_quarantine_jwt():
    """Fix #3 — JWT tokens (three base64 segments) are redacted."""
    output = (
        "Auth: eyJhbGciOiJIUzI1NiIsInR.eyJzdWIiOiIxMjM0NTY3OD.SflKxwRJSMeKKF2QT4"
    )
    result = failure_attestation.quarantine_output(output)
    assert not result.clean


def test_e21_quarantine_db_connection_uri():
    """Fix #3 — DB URIs with embedded credentials are redacted."""
    output = "Database: postgres://admin:supersecret@db.internal:5432/prod"
    result = failure_attestation.quarantine_output(output)
    assert not result.clean
    assert "supersecret" not in result.redacted_output


def test_e21_quarantine_pem_private_key():
    """Fix #3 — PEM private key markers are redacted."""
    output = "Found:\n-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n"
    result = failure_attestation.quarantine_output(output)
    assert not result.clean


# ---------------------------------------------------------------------------
# Slice 3.21 — E21 optional sub-judge soft-fail
# ---------------------------------------------------------------------------


def test_e21_optional_quarantine_soft_fail():
    """Slice 3.21 — optional sub-judge quarantine event → soft_fail severity."""
    assert failure_attestation.quarantine_severity_for("repo-context") == "soft_fail"
    assert failure_attestation.quarantine_severity_for("architectural-fit") == "soft_fail"
    assert failure_attestation.quarantine_severity_for("structure") == "soft_fail"
    assert failure_attestation.quarantine_severity_for("gate-compliance") == "soft_fail"


# ---------------------------------------------------------------------------
# Slice 3.22 — E21 mandatory sub-judge hard-fail
# ---------------------------------------------------------------------------


def test_e21_mandatory_quarantine_hard_fail():
    """Slice 3.22 — mandatory sub-judge quarantine event → hard_fail severity."""
    assert failure_attestation.quarantine_severity_for("semantic") == "hard_fail"
    assert failure_attestation.quarantine_severity_for("adversarial") == "hard_fail"
