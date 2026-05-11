"""Attestation integrity hash tests (LLD-011 Phase 1 slices 1.23-1.25).

`attestation_integrity_hash` is SHA-256 over the canonical YAML payload with
the hash field itself zeroed-out (so the hash field's own value doesn't change
the input). Computed at iter-1 write time; re-verified at iter-2 load time.
Detects post-write tampering with findings/rubric metadata.
"""

import copy

import pytest


def _minimal_payload() -> dict:
    """Minimal v2 attestation payload for integrity-hash tests."""
    return {
        "schema_version": "2.0",
        "doc_subject": {
            "path": "docs/features/x.md",
            "content_hash": "sha256:" + "a" * 64,
            "iter_commit_sha": "a" * 40,
            "iter_blob_sha": "b" * 40,
            "iteration": 1,
        },
        "peer_judge": {
            "id": "orchestra:spec-reviewer",
            "invoked_at": "2026-05-11T12:34:56Z",
            "context_isolation": "fresh_subagent_per_subjudge",
        },
        "sub_judges": [],
        "findings_aggregated": [],
        "overall_verdict": "pass",
        "overall_verdict_basis": {
            "worst_sub_judge_verdict": "pass",
            "excluded_sub_judges": [],
            "mandatory_failures": [],
            "reason": None,
        },
        # attestation_integrity_hash filled in by helper
    }


def test_hash_format(tmp_path) -> None:
    """Slice 1.23 — _compute_attestation_integrity_hash returns sha256:<64-hex>."""
    from cli import spec_review

    payload = _minimal_payload()
    h = spec_review._compute_attestation_integrity_hash(payload)
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 64
    assert all(c in "0123456789abcdef" for c in h[len("sha256:") :])


def test_hash_deterministic() -> None:
    """Slice 1.23 — same payload produces same hash across runs."""
    from cli import spec_review

    p1 = _minimal_payload()
    p2 = _minimal_payload()
    assert spec_review._compute_attestation_integrity_hash(p1) == (
        spec_review._compute_attestation_integrity_hash(p2)
    )


def test_hash_excludes_own_field() -> None:
    """Slice 1.23 — hash field's own value does not affect the hash.

    Whether the payload already has attestation_integrity_hash set or not, the
    computed hash should be the same (the field is zeroed out before hashing).
    """
    from cli import spec_review

    p1 = _minimal_payload()
    p2 = _minimal_payload()
    p2["attestation_integrity_hash"] = "sha256:" + "z" * 64
    assert spec_review._compute_attestation_integrity_hash(p1) == (
        spec_review._compute_attestation_integrity_hash(p2)
    )


def test_hash_changes_on_finding_tamper() -> None:
    """Slice 1.23 — tampering with findings_aggregated changes the hash."""
    from cli import spec_review

    p1 = _minimal_payload()
    p2 = copy.deepcopy(p1)
    p2["findings_aggregated"] = [
        {
            "severity": "Critical",
            "location": "Body § Intro",
            "problem": "tampered",
            "raised_by": ["adversarial"],
        }
    ]
    assert spec_review._compute_attestation_integrity_hash(p1) != (
        spec_review._compute_attestation_integrity_hash(p2)
    )


def test_hash_changes_on_rubric_version_tamper() -> None:
    """Slice 1.23 — tampering with a sub-judge's rubric_version changes the hash."""
    from cli import spec_review

    p1 = _minimal_payload()
    p1["sub_judges"] = [
        {
            "id": "semantic",
            "model": "claude-opus-4-7",
            "mandatory": True,
            "rubric_version": "semantic-v1",
            "status": "completed",
            "verdict": "pass",
            "findings": [],
            "justification": "no findings",
        }
    ]
    p2 = copy.deepcopy(p1)
    p2["sub_judges"][0]["rubric_version"] = "semantic-v999-tampered"
    assert spec_review._compute_attestation_integrity_hash(p1) != (
        spec_review._compute_attestation_integrity_hash(p2)
    )


def test_verify_passes_on_fresh_hash() -> None:
    """Slice 1.24 — verify returns True when stored hash matches computed."""
    from cli import spec_review

    payload = _minimal_payload()
    payload["attestation_integrity_hash"] = (
        spec_review._compute_attestation_integrity_hash(payload)
    )
    assert spec_review._verify_attestation_integrity_hash(payload) is True


def test_verify_fails_on_tampered_findings() -> None:
    """Slice 1.25 — verify returns False after post-hash-write tampering with findings."""
    from cli import spec_review

    payload = _minimal_payload()
    payload["attestation_integrity_hash"] = (
        spec_review._compute_attestation_integrity_hash(payload)
    )
    # Tamper AFTER hash was written
    payload["findings_aggregated"] = [
        {
            "severity": "Critical",
            "location": "Body § Intro",
            "problem": "post-write tamper",
            "raised_by": ["adversarial"],
        }
    ]
    assert spec_review._verify_attestation_integrity_hash(payload) is False


def test_verify_fails_when_hash_field_missing() -> None:
    """Slice 1.24 — verify returns False when the attestation has no hash field."""
    from cli import spec_review

    payload = _minimal_payload()
    # No attestation_integrity_hash field at all
    assert spec_review._verify_attestation_integrity_hash(payload) is False
