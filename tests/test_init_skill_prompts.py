"""BUG-001 regression gate — init skills MUST mandate AskUserQuestion.

Skill markdown that only *describes* prompts (without instructing Claude to
invoke the AskUserQuestion tool) leaves the 3-prompt flow up to improvisation.
These assertions lock the imperative AskUserQuestion contract into the skill
bodies so future edits can't silently regress to descriptive markdown.

Path C from BUG-001 fix: skill body emits 3 AskUserQuestion calls, then
runs `python -m cli.init --mode <a1> --preset <a2> --addons <a3>`.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGN_DOCS_INIT = REPO_ROOT / "skills" / "design-docs" / "init" / "SKILL.md"
MASTER_INIT = REPO_ROOT / "skills" / "init" / "SKILL.md"
PROMPTS = REPO_ROOT / "skills" / "design-docs" / "init" / "prompts.md"


def test_design_docs_init_skill_mandates_ask_user_question():
    """skills/design-docs/init/SKILL.md must instruct Claude to invoke AskUserQuestion."""
    body = DESIGN_DOCS_INIT.read_text()
    assert "AskUserQuestion" in body, (
        "skills/design-docs/init/SKILL.md must reference the AskUserQuestion tool "
        "by name (BUG-001 Path C — Claude must invoke it, not improvise)."
    )


def test_design_docs_init_skill_has_imperative_invocation_language():
    """Skill body must use imperative 'MUST invoke' / 'invoke AskUserQuestion' — not descriptive."""
    body = DESIGN_DOCS_INIT.read_text()
    imperatives = ["MUST invoke AskUserQuestion", "Invoke AskUserQuestion", "invoke AskUserQuestion"]
    assert any(p in body for p in imperatives), (
        "Skill must use imperative language ('MUST invoke AskUserQuestion' or "
        "'Invoke AskUserQuestion') so Claude cannot interpret prompts as descriptive."
    )


def test_design_docs_init_skill_lists_all_three_questions():
    """Q1 (mode), Q2 (doc types), Q3 (add-ons) must all be named in skill body."""
    body = DESIGN_DOCS_INIT.read_text()
    for marker in ["Q1", "Q2", "Q3"]:
        assert marker in body, f"Missing question marker {marker} in skill body."


def test_design_docs_init_skill_references_cli_init_invocation():
    """After 3 prompts the skill must invoke `python -m cli.init` with the answer flags."""
    body = DESIGN_DOCS_INIT.read_text()
    assert "cli.init" in body
    assert "--mode" in body
    assert "--preset" in body
    assert "--addons" in body


def test_master_init_skill_references_ask_user_question_contract():
    """Master skills/init/SKILL.md must reference the AskUserQuestion contract."""
    body = MASTER_INIT.read_text()
    assert "AskUserQuestion" in body, (
        "Master init skill must surface the AskUserQuestion contract so consumers "
        "see the 3-prompt UI fires deterministically."
    )


def test_prompts_md_provides_option_labels_for_each_question():
    """prompts.md remains canonical option-text reference, must list options per question."""
    body = PROMPTS.read_text()
    for question_marker in ["Mode", "Doc types", "Add-ons"]:
        assert question_marker in body, f"prompts.md missing {question_marker} section."
