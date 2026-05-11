"""Tests for cli.install_hooks (v1.1 pre-commit + v1.2 commit-msg)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from cli.install_hooks import install_hook, install_one_hook


# ---------------- v1.1 pre-commit (existing) ----------------

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


def test_existing_hook_prompt_skip(tmp_repo: Path, monkeypatch) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'custom hook'\n")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    rc = install_hook(tmp_repo, input_fn=lambda _: "s")
    assert rc == 0
    assert "custom hook" in existing.read_text()


def test_existing_hook_prompt_replace(tmp_repo: Path, monkeypatch) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'old'\n")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    rc = install_hook(tmp_repo, input_fn=lambda _: "r")
    assert rc == 0
    assert "cli.lint --pre-commit" in existing.read_text()


def test_existing_hook_prompt_append(tmp_repo: Path, monkeypatch) -> None:
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing = hooks_dir / "pre-commit"
    existing.write_text("#!/bin/bash\necho 'preserve me'\n")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
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


# ---------------- v1.2 commit-msg ----------------

def test_install_commit_msg_in_fresh_repo(tmp_repo: Path) -> None:
    rc = install_one_hook(tmp_repo, "commit-msg")
    assert rc == 0
    hook = tmp_repo / ".git" / "hooks" / "commit-msg"
    assert hook.exists()
    assert os.access(hook, os.X_OK)
    content = hook.read_text()
    assert "Refs: docs/" in content
    assert "fix|feat" in content


def test_install_commit_msg_skip_in_non_git_repo(tmp_repo_no_git: Path) -> None:
    rc = install_one_hook(tmp_repo_no_git, "commit-msg")
    assert rc == 1


def test_install_all_installs_both(tmp_repo: Path) -> None:
    rc1 = install_one_hook(tmp_repo, "pre-commit")
    rc2 = install_one_hook(tmp_repo, "commit-msg")
    assert rc1 == 0 and rc2 == 0
    assert (tmp_repo / ".git" / "hooks" / "pre-commit").exists()
    assert (tmp_repo / ".git" / "hooks" / "commit-msg").exists()


def _run_hook(hook_path: Path, msg: str, tmp_path: Path) -> int:
    """Invoke commit-msg hook with given message body. Returns exit code."""
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(msg)
    proc = subprocess.run(
        [str(hook_path), str(msg_file)],
        capture_output=True, text=True,
    )
    return proc.returncode


def test_commit_msg_hook_blocks_orphan_feat(tmp_repo: Path, tmp_path: Path) -> None:
    install_one_hook(tmp_repo, "commit-msg")
    hook = tmp_repo / ".git" / "hooks" / "commit-msg"
    rc = _run_hook(hook, "feat: add x\n\nNo refs line.\n", tmp_path)
    assert rc == 1


def test_commit_msg_hook_passes_chore(tmp_repo: Path, tmp_path: Path) -> None:
    install_one_hook(tmp_repo, "commit-msg")
    hook = tmp_repo / ".git" / "hooks" / "commit-msg"
    rc = _run_hook(hook, "chore: update deps\n", tmp_path)
    assert rc == 0


def test_commit_msg_hook_passes_feat_with_refs(tmp_repo: Path, tmp_path: Path) -> None:
    install_one_hook(tmp_repo, "commit-msg")
    hook = tmp_repo / ".git" / "hooks" / "commit-msg"
    msg = "feat: add x\n\nDoes thing.\n\nRefs: docs/features/001-x.md\n"
    rc = _run_hook(hook, msg, tmp_path)
    assert rc == 0


def test_commit_msg_hook_blocks_fix_without_refs(tmp_repo: Path, tmp_path: Path) -> None:
    install_one_hook(tmp_repo, "commit-msg")
    hook = tmp_repo / ".git" / "hooks" / "commit-msg"
    rc = _run_hook(hook, "fix: bad bug\n\nNo refs.\n", tmp_path)
    assert rc == 1
