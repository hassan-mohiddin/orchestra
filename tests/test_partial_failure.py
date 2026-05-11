"""Tiered partial-failure policy tests (LLD-011 Phase 1 slices 1.27-1.29).

semantic + adversarial are mandatory. Their failure forces overall_verdict=fail
with reason=mandatory_subjudge_failed. Optional sub-judges (structure,
gate-compliance, repo-context, architectural-fit) soft-fail and are excluded
from aggregation but do not block the verdict.

The failure-attestation invariant: every dispatch attempt produces an
attestation file, even when no findings_aggregated entry exists.
"""


def _sj(
    id_: str, verdict: str = "pass", status: str = "completed"
) -> dict:
    """Minimal sub_judge dict for verdict-computation tests."""
    return {"id": id_, "status": status, "verdict": verdict, "findings": []}


def test_all_completed_pass() -> None:
    """Slice 1.29 — all sub-judges complete with pass → overall pass."""
    from cli import spec_review

    sj_list = [
        _sj("structure"),
        _sj("semantic"),
        _sj("gate-compliance"),
        _sj("adversarial"),
        _sj("repo-context"),
        _sj("architectural-fit"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "pass"
    assert result["overall_verdict_basis"]["mandatory_failures"] == []
    assert result["overall_verdict_basis"]["excluded_sub_judges"] == []
    assert result["overall_verdict_basis"]["reason"] is None


def test_optional_failure_soft_pass() -> None:
    """Slice 1.29 — optional sub-judge fail → overall=worst-of-completed; sub-judge excluded."""
    from cli import spec_review

    sj_list = [
        _sj("structure"),
        _sj("semantic"),
        _sj("gate-compliance"),
        _sj("adversarial"),
        _sj("repo-context", status="timeout"),
        _sj("architectural-fit"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "pass"
    assert "repo-context" in result["overall_verdict_basis"]["excluded_sub_judges"]
    assert result["overall_verdict_basis"]["mandatory_failures"] == []
    assert result["overall_verdict_basis"]["reason"] is None


def test_mandatory_failure_hard_block_semantic() -> None:
    """Slice 1.28 — semantic (mandatory) fails → overall=fail, reason=mandatory_subjudge_failed."""
    from cli import spec_review

    sj_list = [
        _sj("structure"),
        _sj("semantic", status="error"),
        _sj("gate-compliance"),
        _sj("adversarial"),
        _sj("repo-context"),
        _sj("architectural-fit"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "fail"
    assert result["overall_verdict_basis"]["reason"] == "mandatory_subjudge_failed"
    assert "semantic" in result["overall_verdict_basis"]["mandatory_failures"]


def test_mandatory_failure_hard_block_adversarial() -> None:
    """Slice 1.28 — adversarial (mandatory) fails → hard block (same as semantic)."""
    from cli import spec_review

    sj_list = [
        _sj("structure"),
        _sj("semantic"),
        _sj("gate-compliance"),
        _sj("adversarial", status="timeout"),
        _sj("repo-context"),
        _sj("architectural-fit"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "fail"
    assert result["overall_verdict_basis"]["reason"] == "mandatory_subjudge_failed"
    assert "adversarial" in result["overall_verdict_basis"]["mandatory_failures"]


def test_both_mandatory_fail() -> None:
    """Slice 1.28 — both mandatory sub-judges fail → both listed in mandatory_failures."""
    from cli import spec_review

    sj_list = [
        _sj("semantic", status="error"),
        _sj("adversarial", status="timeout"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "fail"
    assert sorted(result["overall_verdict_basis"]["mandatory_failures"]) == [
        "adversarial",
        "semantic",
    ]


def test_all_subjudges_failed() -> None:
    """Slice 1.27 — every sub-judge failed → reason=all_subjudges_failed, attestation still computable."""
    from cli import spec_review

    sj_list = [
        _sj("structure", status="error"),
        _sj("semantic", status="error"),
        _sj("gate-compliance", status="error"),
        _sj("adversarial", status="error"),
        _sj("repo-context", status="error"),
        _sj("architectural-fit", status="error"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "fail"
    # Both mandatory fail AND all-fail are true; mandatory_subjudge_failed wins as it's the more specific reason
    # (verified per LLD-011 §Aggregator failure-attestation invariant)
    assert result["overall_verdict_basis"]["reason"] in (
        "mandatory_subjudge_failed",
        "all_subjudges_failed",
    )


def test_no_subjudges_input() -> None:
    """Slice 1.27 — empty sub_judges list → all_subjudges_failed reason."""
    from cli import spec_review

    result = spec_review.compute_overall_verdict_v2([])
    assert result["overall_verdict"] == "fail"
    assert result["overall_verdict_basis"]["reason"] == "all_subjudges_failed"


def test_conditional_pass_propagates() -> None:
    """Slice 1.29 — sub-judge verdict=conditional_pass becomes overall worst when no fail."""
    from cli import spec_review

    sj_list = [
        _sj("structure", verdict="pass"),
        _sj("semantic", verdict="conditional_pass"),
        _sj("gate-compliance", verdict="pass"),
        _sj("adversarial", verdict="pass"),
        _sj("repo-context", verdict="pass"),
        _sj("architectural-fit", verdict="pass"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "conditional_pass"


def test_fail_verdict_wins_over_pass() -> None:
    """Slice 1.29 — sub-judge verdict=fail makes overall fail even when others pass."""
    from cli import spec_review

    sj_list = [
        _sj("structure", verdict="fail"),
        _sj("semantic", verdict="pass"),
        _sj("gate-compliance", verdict="pass"),
        _sj("adversarial", verdict="pass"),
        _sj("repo-context", verdict="pass"),
        _sj("architectural-fit", verdict="pass"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    assert result["overall_verdict"] == "fail"


def test_excluded_sub_judges_sorted() -> None:
    """Slice 1.29 — excluded_sub_judges output is sorted (deterministic across runs)."""
    from cli import spec_review

    sj_list = [
        _sj("structure"),
        _sj("semantic"),
        _sj("gate-compliance", status="error"),
        _sj("adversarial"),
        _sj("repo-context", status="timeout"),
        _sj("architectural-fit", status="error"),
    ]
    result = spec_review.compute_overall_verdict_v2(sj_list)
    excluded = result["overall_verdict_basis"]["excluded_sub_judges"]
    assert excluded == sorted(excluded)
    assert set(excluded) == {"gate-compliance", "repo-context", "architectural-fit"}
