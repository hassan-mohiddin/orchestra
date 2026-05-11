"""Tests for SKILL_TEMPLATES_DIR + install_hooks reads from skill dir (LLD-008 r7 T3)."""

from __future__ import annotations

from pathlib import Path

from cli.install_hooks import SKILL_TEMPLATES_DIR, install_one_hook


def test_skill_templates_dir_resolves_to_skills_commit_templates() -> None:
    expected = Path(__file__).resolve().parent.parent / "skills" / "commit" / "templates"
    assert SKILL_TEMPLATES_DIR == expected
    assert SKILL_TEMPLATES_DIR.is_dir()
    assert (SKILL_TEMPLATES_DIR / "pre-commit.sh").is_file()
    assert (SKILL_TEMPLATES_DIR / "commit-msg.sh").is_file()


def test_install_hooks_reads_from_skill_dir(tmp_repo: Path) -> None:
    rc = install_one_hook(tmp_repo, "pre-commit")
    assert rc == 0
    hook = tmp_repo / ".git" / "hooks" / "pre-commit"
    content = hook.read_text()
    skill_template = (SKILL_TEMPLATES_DIR / "pre-commit.sh").read_text()
    assert content == skill_template


def test_install_commit_msg_reads_from_skill_dir(tmp_repo: Path) -> None:
    rc = install_one_hook(tmp_repo, "commit-msg")
    assert rc == 0
    hook = tmp_repo / ".git" / "hooks" / "commit-msg"
    content = hook.read_text()
    skill_template = (SKILL_TEMPLATES_DIR / "commit-msg.sh").read_text()
    assert content == skill_template


def test_hook_templates_have_orchestra_fingerprint_in_line_2() -> None:
    """Per LLD-010 r3 A4 RAW_FINGERPRINT substring floor: # orchestra in line 2."""
    for hook in ("pre-commit.sh", "commit-msg.sh"):
        lines = (SKILL_TEMPLATES_DIR / hook).read_text().splitlines()
        assert len(lines) >= 2, f"{hook} too short"
        assert "orchestra" in lines[1].lower(), (
            f"{hook} line 2 missing 'orchestra' fingerprint: {lines[1]!r}"
        )


def test_cli_templates_dir_no_longer_holds_hook_scripts() -> None:
    """Per LLD-008 r7 A3: cli/templates/{pre-commit.sh,commit-msg.sh} removed."""
    cli_templates = Path(__file__).resolve().parent.parent / "cli" / "templates"
    assert not (cli_templates / "pre-commit.sh").exists()
    assert not (cli_templates / "commit-msg.sh").exists()
    assert (cli_templates / "precommit-yaml-patch.txt").is_file()
