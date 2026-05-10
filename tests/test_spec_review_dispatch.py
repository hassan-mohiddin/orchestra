"""Dispatch structural test for SKILL.md prose (S26 slice)."""

from pathlib import Path


def test_skill_md_specifies_general_purpose_subagent():
    """T2 / S26 — A3: SKILL.md prose contains `subagent_type: general-purpose` and Task tool reference.

    Structural prose check — runtime Task-kwargs verification deferred to
    manual dogfood (D4) per A3 honest narrowing.
    """
    skill_md = Path(__file__).parent.parent / "skills" / "spec-review" / "SKILL.md"
    text = skill_md.read_text()
    assert "subagent_type: general-purpose" in text
    assert "Task" in text
