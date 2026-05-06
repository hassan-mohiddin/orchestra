"""Sanity smoke test — verifies pytest framework is wired up.

Deleted in Task 1 when real test_config.py lands.
"""

from __future__ import annotations

from pathlib import Path


def test_pytest_works() -> None:
    """pytest framework loads and runs."""
    assert True


def test_tmp_repo_fixture(tmp_repo: Path) -> None:
    """tmp_repo fixture creates a git-initialized directory."""
    assert tmp_repo.exists()
    assert (tmp_repo / ".git").is_dir()


def test_tmp_repo_no_git_fixture(tmp_repo_no_git: Path) -> None:
    """tmp_repo_no_git fixture creates a directory without git."""
    assert tmp_repo_no_git.exists()
    assert not (tmp_repo_no_git / ".git").exists()
