"""Rubric-freeze tests (LLD-011 Phase 3 slices 3.1-3.6).

At iter-1 each sub-judge uses the latest rubric version available
(`rubric-vN.md` with the highest N). The chosen version is recorded in the
attestation. At iter-2+ the sub-judge MUST replay against the iter-1 frozen
version — even if a newer rubric exists — so verdicts remain comparable
across iterations. Missing iter-1 rubric version at iter-2 → hard fail.

Rubric directory layout per LLD-011:
    skills/spec-review/judges/<judge-id>/rubric-v<N>.md
"""

from __future__ import annotations

from pathlib import Path

import pytest


JUDGES_DIR = Path(__file__).parent.parent / "skills" / "spec-review" / "judges"
SUB_JUDGE_IDS = [
    "structure",
    "semantic",
    "gate-compliance",
    "adversarial",
    "repo-context",
    "architectural-fit",
]


# ---------------------------------------------------------------------------
# Slice 3.1 — rubric-v1.md content present for all 6 sub-judges
# ---------------------------------------------------------------------------


def test_rubric_v1_content_nonempty():
    """Slice 3.1 — every sub-judge has a non-trivial rubric-v1.md."""
    for jid in SUB_JUDGE_IDS:
        path = JUDGES_DIR / jid / "rubric-v1.md"
        text = path.read_text()
        # Must be substantive — at least 200 chars and reference a heading
        assert len(text) > 200, f"rubric-v1 for {jid} too short: {len(text)} chars"
        assert "#" in text, f"rubric-v1 for {jid} has no markdown heading"


# ---------------------------------------------------------------------------
# Slice 3.2 — find_latest_rubric_version helper
# ---------------------------------------------------------------------------


def test_find_latest_rubric_version_v1_only(tmp_path):
    """Slice 3.2 — only rubric-v1.md present → returns 1."""
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)
    (judge / "rubric-v1.md").write_text("# rubric v1\n")

    assert rubric_freeze.find_latest_rubric_version("semantic", judges_root) == 1


def test_find_latest_rubric_version_multi(tmp_path):
    """Slice 3.2 — when v1, v2, v3 present → returns 3."""
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)
    (judge / "rubric-v1.md").write_text("v1")
    (judge / "rubric-v2.md").write_text("v2")
    (judge / "rubric-v3.md").write_text("v3")

    assert rubric_freeze.find_latest_rubric_version("semantic", judges_root) == 3


def test_find_latest_rubric_version_missing(tmp_path):
    """Slice 3.2 — no rubric files → ValueError (no rubric available)."""
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)

    with pytest.raises(ValueError, match="no rubric"):
        rubric_freeze.find_latest_rubric_version("semantic", judges_root)


# ---------------------------------------------------------------------------
# Slice 3.3 — record rubric_version on dispatch
# ---------------------------------------------------------------------------


def test_record_rubric_version_in_dispatch_context(tmp_path):
    """Slice 3.3 — resolve_rubric_for_dispatch returns version + path; used to build attestation."""
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)
    (judge / "rubric-v1.md").write_text("v1 body")
    (judge / "rubric-v2.md").write_text("v2 body")

    info = rubric_freeze.resolve_rubric_for_dispatch(
        "semantic", iteration=1, judges_root=judges_root, prior_rubric_version=None
    )
    assert info.version == 2
    assert info.path == judge / "rubric-v2.md"
    assert info.body == "v2 body"


# ---------------------------------------------------------------------------
# Slice 3.4 — iter-2 reads iter-1 frozen version
# ---------------------------------------------------------------------------


def test_iter2_uses_iter1_rubric_version(tmp_path):
    """Slice 3.4 — iter-2 dispatch resolves to the iter-1 rubric_version, not the latest."""
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)
    (judge / "rubric-v1.md").write_text("v1 body")
    (judge / "rubric-v2.md").write_text("v2 body")

    info = rubric_freeze.resolve_rubric_for_dispatch(
        "semantic", iteration=2, judges_root=judges_root, prior_rubric_version=1
    )
    assert info.version == 1
    assert info.body == "v1 body"


# ---------------------------------------------------------------------------
# Slice 3.5 — iter-2 missing rubric → hard fail
# ---------------------------------------------------------------------------


def test_iter2_missing_rubric_fails(tmp_path):
    """Slice 3.5 — iter-2 prior_rubric_version not on disk → SpecReviewError."""
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)
    (judge / "rubric-v2.md").write_text("v2 only — v1 has been deleted")

    with pytest.raises(rubric_freeze.RubricFreezeError) as exc_info:
        rubric_freeze.resolve_rubric_for_dispatch(
            "semantic", iteration=2, judges_root=judges_root, prior_rubric_version=1
        )
    assert "rubric_version_not_found" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Slice 3.6 — iter-2 with newer rubric ignored
# ---------------------------------------------------------------------------


def test_iter2_ignores_newer_rubric(tmp_path):
    """Slice 3.6 — when v2 exists but iter-1 attested v1, iter-2 uses v1.

    Asserts iter-2 returns body of v1 (frozen) even though v2 is on disk.
    """
    from cli import rubric_freeze

    judges_root = tmp_path / "judges"
    judge = judges_root / "semantic"
    judge.mkdir(parents=True)
    (judge / "rubric-v1.md").write_text("frozen v1 content")
    (judge / "rubric-v2.md").write_text("newer v2 content")

    info = rubric_freeze.resolve_rubric_for_dispatch(
        "semantic", iteration=2, judges_root=judges_root, prior_rubric_version=1
    )
    assert info.version == 1
    assert "frozen v1" in info.body
    assert "newer v2" not in info.body
