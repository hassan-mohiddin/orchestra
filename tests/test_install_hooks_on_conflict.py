"""Tests for cli.install_hooks --on-conflict flag + --force precedence (LLD-008 r7 T4a-e)."""

from __future__ import annotations

import os
from pathlib import Path

from cli.install_hooks import SKILL_TEMPLATES_DIR, install_one_hook, main


def _write_differing_hook(tmp_repo: Path, hook_name: str = "pre-commit") -> Path:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / hook_name
    existing.write_text("#!/bin/bash\necho 'user custom hook'\n")
    return existing


def test_on_conflict_skip_leaves_untouched(tmp_repo: Path) -> None:
    existing = _write_differing_hook(tmp_repo)
    rc = install_one_hook(tmp_repo, "pre-commit", on_conflict="skip")
    assert rc == 0
    assert "user custom hook" in existing.read_text()


def test_on_conflict_replace_overwrites(tmp_repo: Path) -> None:
    existing = _write_differing_hook(tmp_repo)
    rc = install_one_hook(tmp_repo, "pre-commit", on_conflict="replace")
    assert rc == 0
    template = (SKILL_TEMPLATES_DIR / "pre-commit.sh").read_text()
    assert existing.read_text() == template


def test_on_conflict_append_concatenates(tmp_repo: Path) -> None:
    existing = _write_differing_hook(tmp_repo)
    rc = install_one_hook(tmp_repo, "pre-commit", on_conflict="append")
    assert rc == 0
    content = existing.read_text()
    assert "cli.lint --pre-commit" in content
    assert "user custom hook" in content


def test_non_tty_no_flag_defaults_to_skip(tmp_repo: Path, monkeypatch) -> None:
    """argparse sentinel None + non-TTY → silent skip (no input() blocking)."""
    existing = _write_differing_hook(tmp_repo)

    def fake_input_raises(prompt: str = "") -> str:
        raise AssertionError("input() must not be called in non-TTY path")

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    rc = install_one_hook(tmp_repo, "pre-commit", input_fn=fake_input_raises)
    assert rc == 0
    assert "user custom hook" in existing.read_text()


def test_force_takes_precedence_over_on_conflict(tmp_repo: Path) -> None:
    """--force wins; --on-conflict=skip ignored; hook replaced."""
    existing = _write_differing_hook(tmp_repo)
    rc = install_one_hook(tmp_repo, "pre-commit", force=True, on_conflict="skip")
    assert rc == 0
    template = (SKILL_TEMPLATES_DIR / "pre-commit.sh").read_text()
    assert existing.read_text() == template


def test_main_argparse_on_conflict_skip_via_cli(tmp_repo: Path, monkeypatch) -> None:
    _write_differing_hook(tmp_repo)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    rc = main(["--repo", str(tmp_repo), "--on-conflict=skip"])
    assert rc == 0


def test_main_argparse_rejects_bad_choice(tmp_repo: Path) -> None:
    """argparse choices restrict to skip/replace/append."""
    import pytest
    with pytest.raises(SystemExit) as exc:
        main(["--repo", str(tmp_repo), "--on-conflict=nuke"])
    assert exc.value.code == 2  # argparse error exit code
