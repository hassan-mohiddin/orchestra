"""Top-level dispatch + flow integration tests for spec-review v2 (LLD-011)."""

from cli import spec_review


def test_mandatory_map():
    """Slice 1.8 — MANDATORY_SUBJUDGES is a frozenset of {semantic, adversarial}.

    Per LLD-011 §Schema v2.0 Mandatory map: semantic + adversarial are mandatory.
    Their failure forces overall_verdict=fail with reason=mandatory_subjudge_failed.
    """
    assert spec_review.MANDATORY_SUBJUDGES == frozenset({"semantic", "adversarial"})
    assert isinstance(spec_review.MANDATORY_SUBJUDGES, frozenset)
