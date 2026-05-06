"""Shared pytest fixtures for orchestra v1.1+ tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Fresh repo with git init done.

    Used by integration tests that exercise orchestra's scaffold/init paths
    against a real filesystem. Returns the repo root.
    """
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


@pytest.fixture
def tmp_repo_no_git(tmp_path: Path) -> Path:
    """Fresh dir without git init.

    Used by tests that exercise orchestra's behavior in non-git repos
    (e.g., install_hooks should detect missing .git/ and skip).
    """
    return tmp_path
