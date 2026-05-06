"""Tests for cli.install_hooks."""

from __future__ import annotations

import os
from pathlib import Path

from cli.install_hooks import install_hook


def test_install_in_fresh_repo(tmp_repo: Path) -> None:
    rc = install_hook(tmp_repo)
    assert rc == 0
    hook = tmp_repo / ".git" / "hooks" / "pre-commit"
    assert hook.exists()
    assert os.access(hook, os.X_OK)
    assert "cli.lint --pre-commit" in hook.read_text()


def test_skip_in_non_git_repo(tmp_repo_no_git: Path) -> None:
    rc = install_hook(tmp_repo_no_git)
    assert rc == 1


def test_idempotent_when_content_matches(tmp_repo: Path) -> None:
    install_hook(tmp_repo)
    rc = install_hook(tmp_repo)
    assert rc == 0


def test_existing_hook_prompt_skip(tmp_repo: Path) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'custom hook'\n")
    rc = install_hook(tmp_repo, input_fn=lambda _: "s")
    assert rc == 0
    # Skip = leave existing alone
    assert "custom hook" in existing.read_text()


def test_existing_hook_prompt_replace(tmp_repo: Path) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'old'\n")
    rc = install_hook(tmp_repo, input_fn=lambda _: "r")
    assert rc == 0
    assert "cli.lint --pre-commit" in existing.read_text()
    assert "old" not in existing.read_text()


def test_existing_hook_prompt_append(tmp_repo: Path) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'preserve me'\n")
    rc = install_hook(tmp_repo, input_fn=lambda _: "a")
    assert rc == 0
    content = existing.read_text()
    assert "cli.lint --pre-commit" in content
    assert "preserve me" in content


def test_force_replaces_hook(tmp_repo: Path) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'old'\n")
    rc = install_hook(tmp_repo, force=True)
    assert rc == 0
    assert "cli.lint --pre-commit" in existing.read_text()
    assert "old" not in existing.read_text()
