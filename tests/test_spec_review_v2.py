"""Top-level dispatch + flow integration tests for spec-review v2 (LLD-011)."""

from pathlib import Path

from cli import spec_review


JUDGES_DIR = (
    Path(__file__).parent.parent / "skills" / "spec-review" / "judges"
)
SUB_JUDGE_IDS = [
    "structure",
    "semantic",
    "gate-compliance",
    "adversarial",
    "repo-context",
    "architectural-fit",
]


def test_mandatory_map():
    """Slice 1.8 — MANDATORY_SUBJUDGES is a frozenset of {semantic, adversarial}.

    Per LLD-011 §Schema v2.0 Mandatory map: semantic + adversarial are mandatory.
    Their failure forces overall_verdict=fail with reason=mandatory_subjudge_failed.
    """
    assert spec_review.MANDATORY_SUBJUDGES == frozenset({"semantic", "adversarial"})
    assert isinstance(spec_review.MANDATORY_SUBJUDGES, frozenset)


def test_judge_prompt_files_present():
    """Slice 1.9 — every sub-judge has a non-empty prompt.md at the expected path."""
    for jid in SUB_JUDGE_IDS:
        path = JUDGES_DIR / jid / "prompt.md"
        assert path.exists(), f"missing prompt.md for sub-judge {jid}: {path}"
        assert path.read_text().strip(), f"prompt.md is empty for sub-judge {jid}"


def test_judge_rubric_files_present():
    """Slice 1.10 — every sub-judge has a non-empty rubric-v1.md at the expected path."""
    for jid in SUB_JUDGE_IDS:
        path = JUDGES_DIR / jid / "rubric-v1.md"
        assert path.exists(), f"missing rubric-v1.md for sub-judge {jid}: {path}"
        assert path.read_text().strip(), f"rubric-v1.md is empty for sub-judge {jid}"


SKILL_MD = (
    Path(__file__).parent.parent / "skills" / "spec-review" / "SKILL.md"
)


def test_skill_md_describes_v2_dispatch():
    """Slice 1.26 — SKILL.md describes v2 parallel dispatch protocol.

    The skill body is consumed by Claude Code at invocation time. We test by
    content presence: it must mention all 6 sub-judge IDs and the parallel-
    dispatch instruction. The actual dispatch behavior is integration-tested
    at skill-invocation time (outside pytest).
    """
    body = SKILL_MD.read_text()
    # All 6 sub-judges named
    for jid in SUB_JUDGE_IDS:
        assert jid in body, f"SKILL.md missing reference to sub-judge {jid}"
    # Parallel-dispatch instruction
    assert "parallel" in body.lower()
    assert "single message" in body.lower() or "single-message" in body.lower()
    # Schema v2.0 reference
    assert "v2.0" in body
    # Provenance + integrity primitives mentioned
    assert "iter_blob_sha" in body or "git hash-object -w" in body
    assert "attestation_integrity_hash" in body or "integrity hash" in body.lower()
    # Failure-attestation invariant
    assert "failure" in body.lower()
