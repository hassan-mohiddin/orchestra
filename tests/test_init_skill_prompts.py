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


# ---------------------------------------------------------------------------
# BUG-001 edge-path tightening (A-F leak coverage)
# ---------------------------------------------------------------------------


def test_master_step1_is_imperative_read():
    """Issue A — Step-1 must imperatively use the Read tool (not an implicit 'check')."""
    body = MASTER_INIT.read_text()
    assert "Read tool" in body or "via `Read`" in body or "use the `Read` tool" in body, (
        "Master init Step-1 must imperatively name the Read tool — implicit 'check for' "
        "leaves room for Claude to skip the lookup or use Bash."
    )


def test_master_rerun_branch_has_askuserquestion_payload():
    """Issue B — Step-2 re-run branch must spell out AskUserQuestion options, not improvise."""
    body = MASTER_INIT.read_text()
    assert "Re-run" in body, "Re-run branch must surface a Re-run option label."
    assert "Migrate" in body, "Re-run branch must surface a Migrate option label."
    assert "Abort" in body or "Keep current" in body, (
        "Re-run branch must surface an abort/keep-current option."
    )


def test_design_docs_v10_detection_step_is_imperative_before_q1():
    """Issue C — v1.0 detection must be STEP-0, imperative, before Q1."""
    body = DESIGN_DOCS_INIT.read_text()
    assert "STEP 0" in body or "Step 0" in body, (
        "v1.0 detection must be labelled STEP 0 so it precedes Q1 in skill execution order."
    )
    assert ".claude/settings.local.json" in body
    assert "before Q1" in body or "BEFORE Q1" in body, (
        "STEP 0 must explicitly say it fires before Q1."
    )


def test_design_docs_uniform_label_strip_mapping_all_three_questions():
    """Issue D — each Q's mapping must spell out '(Recommended)' stripping (not only Q1)."""
    body = DESIGN_DOCS_INIT.read_text()
    # Each Q must spell out that '(Recommended)' suffix is stripped before mapping
    assert body.count("(Recommended)") >= 3, (
        "Need consistent (Recommended) suffix-handling note across Q1/Q2/Q3."
    )
    assert "strip" in body.lower() or "ignore" in body.lower() or "starts with" in body.lower(), (
        "Mapping must instruct Claude to strip/ignore (Recommended) suffix uniformly."
    )


def test_design_docs_subset_rename_v201_fallback_explicit():
    """Issue E — subset-rename / full-custom v2.0.1 fallback must be operationally crisp."""
    body = DESIGN_DOCS_INIT.read_text()
    # Must explicitly say what to do when user picks subset-rename or full-custom in v2.0.1
    assert "default-7" in body
    fallback_phrases = [
        "fall back to default-7",
        "AskUserQuestion ONCE more",
        "ask the user to confirm switching to default-7",
        "fire a confirm AskUserQuestion",
    ]
    assert any(p.lower() in body.lower() for p in fallback_phrases), (
        "Subset-rename/full-custom branch in v2.0.1 must specify a deterministic fallback "
        "(confirm-switch-to-default-7 prompt or explicit abort), not 'surface ...' improvisation."
    )


def test_master_final_summary_references_prompts_md_section():
    """Issue F — master Step-4 final-summary must point at prompts.md canonical format."""
    body = MASTER_INIT.read_text()
    assert "prompts.md" in body or "Final summary" in body, (
        "Master skill must reference the canonical final-summary format "
        "(prompts.md § Final summary) so Claude doesn't invent a different summary."
    )


def test_prompts_md_has_rerun_payload():
    """Issue B coverage in prompts.md — re-run AskUserQuestion payload defined."""
    body = PROMPTS.read_text()
    assert "Re-run" in body, "prompts.md must define a Re-run option for the master Step-2 branch."
