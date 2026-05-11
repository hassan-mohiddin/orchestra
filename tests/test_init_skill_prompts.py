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


# ---------------------------------------------------------------------------
# BUG-001 dry-run #3 leaks (G/H/I)
# ---------------------------------------------------------------------------


def test_prompts_md_rerun_mapping_refires_prompts_before_cli_g():
    """Leak G — Re-run init mapping must re-fire STEP 0 + Q1/Q2/Q3 BEFORE cli.init,
    not shortcut directly to cli.init --force (would re-introduce BUG-001 root cause)."""
    body = PROMPTS.read_text()
    # Find the Re-run prompt section
    assert "## Re-run prompt" in body
    rerun_section = body.split("## Re-run prompt")[1].split("##")[0]
    # Re-run init mapping must mention re-firing prompts, not direct cli.init --force
    assert "STEP 0" in rerun_section or "Q1" in rerun_section or "re-fire" in rerun_section.lower(), (
        "Re-run init mapping must explicitly say it re-fires the prompt flow before "
        "invoking cli.init. Direct shortcut to 'python -m cli.init --force' re-introduces "
        "the BUG-001 root cause (CLI uses argparse defaults, no prompts fire)."
    )
    # Must include --force flag passed alongside answer flags (not alone)
    has_force_with_flags = (
        "--force --mode" in rerun_section
        or "--mode" in rerun_section and "--force" in rerun_section
    )
    assert has_force_with_flags, (
        "Re-run init mapping must pass --force ALONGSIDE --mode/--preset/--addons "
        "answers gathered from the re-fired prompts, not --force alone."
    )


def test_prompts_md_q2_mapping_synced_with_v201_fallback_i():
    """Leak I — prompts.md Q2 'Answer mapping' must NOT route subset-rename / full-custom
    to a legacy wizard. Must route to v2.0.1 fallback (Switch / Abort) like SKILL.md."""
    body = PROMPTS.read_text()
    q2_section = body.split("## Q2: Doc types")[1].split("## Q3")[0]
    assert "enter subset-rename wizard" not in q2_section, (
        "Leak I: prompts.md still routes subset-rename to a legacy wizard. "
        "Must point at the v2.0.1 fallback section (see SKILL.md Q2 mapping)."
    )
    assert "enter full-custom wizard" not in q2_section, (
        "Leak I: prompts.md still routes full-custom to a legacy wizard. "
        "Must point at the v2.0.1 fallback section."
    )
    # Should reference fallback section explicitly
    assert "fallback" in q2_section.lower() or "v2.0.1" in q2_section.lower(), (
        "Q2 mapping must reference the v2.0.1 fallback path."
    )


def test_cli_init_migrate_v10_flag_exists_h():
    """Leak H — cli/init.py main() must accept --migrate-v10 flag."""
    import subprocess
    result = subprocess.run(
        [".venv/bin/python", "-m", "cli.init", "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert "--migrate-v10" in result.stdout, (
        "Leak H: cli.init must expose --migrate-v10 flag so the skill STEP 0 Migrate path "
        "actually copies v1.0 fields. Promise of 'Copy fields' currently unkept."
    )


def test_cli_init_migrate_v10_copies_v10_fields_h(tmp_path, monkeypatch):
    """Leak H — running cli.init with --migrate-v10 + v1.0 settings file copies v1.0 fields
    (spec_review_skill, doc_paths) into the new orchestra.json."""
    import json
    import subprocess

    # tmp_path needs to be a git repo for hook bootstrap
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(tmp_path)],
        check=True, capture_output=True,
    )

    # Set up fake v1.0 config under tmp_path/.claude/settings.local.json
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    v10_settings = {
        "orchestra": {
            "mode": "team",  # overridden by --mode flag
            "doc_paths": {"features": "docs/custom-features"},
            "spec_review_skill": "custom:spec-reviewer",
        }
    }
    (claude_dir / "settings.local.json").write_text(json.dumps(v10_settings))

    result = subprocess.run(
        [
            ".venv/bin/python", "-m", "cli.init",
            "--repo", str(tmp_path),
            "--mode", "solo",  # override v1.0's "team"
            "--preset", "default-7",
            "--addons", "yes",
            "--migrate-v10",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"cli.init failed: {result.stderr}"

    orchestra_json_path = tmp_path / ".claude" / "orchestra.json"
    assert orchestra_json_path.exists(), "orchestra.json not written"
    config = json.loads(orchestra_json_path.read_text())

    # --mode flag override wins
    assert config["orchestra"]["mode"] == "solo", "mode override should beat v1.0 value"

    # v1.0 spec_review_skill preserved
    dd = config["skills"]["design-docs"]
    assert dd["spec_review_skill"] == "custom:spec-reviewer", (
        "v1.0 spec_review_skill must be preserved by --migrate-v10"
    )
    # v1.0 doc_paths preserved (merged with defaults)
    assert dd["doc_paths"]["features"] == "docs/custom-features", (
        "v1.0 doc_paths must be preserved by --migrate-v10"
    )
