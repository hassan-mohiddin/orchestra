"""Shared pytest fixtures for orchestra v1.1+ tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _stub_pdsa_pass_default(monkeypatch, request):
    """LLD-011 slice 2.12 — default stub for `cli.spec_review.run_pdsa`.

    Pre-PDSA spec-review tests test post-dispatch behavior and need PDSA to
    pass-through. Marking a test with `@pytest.mark.real_pdsa` opts out and
    runs the real PDSA pipeline (used by tests in test_spec_review_v2.py
    and test_pdsa.py that exercise PDSA directly).
    """
    if "real_pdsa" in request.keywords:
        return
    try:
        from cli import pdsa, spec_review
    except ImportError:
        return

    def passing_report(doc_path):
        report = pdsa.PdsaReport(doc_path=doc_path)
        report.checks["lint"] = pdsa.CheckResult(passed=True, detail="stubbed by default fixture")
        return report

    monkeypatch.setattr(spec_review, "run_pdsa", passing_report, raising=False)


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
