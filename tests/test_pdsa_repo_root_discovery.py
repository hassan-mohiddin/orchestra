"""Regression: BUG-019 — PDSA assumes Path.cwd() is repo root.

10-case suite for `_discover_repo_root` + `_resolve_inside_repo` +
`_check_class_audit_attestation` + `_check_refs` working from subdirectory
CWDs and respecting git-rev-parse discovery boundary.

Per BUG-019 r2 §Fix Description item 4.
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

from cli import pdsa


def _git_init(path: Path) -> None:
    """Initialize a git repo at `path`. Stubs identity to avoid global config dependency."""
    subprocess.run(
        ["git", "init", "-q"],
        cwd=str(path),
        check=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def _make_repo_with_doc(tmp_path: Path) -> tuple[Path, Path]:
    """Create a real git repo at tmp_path with cli/spec_review.py + a doc. Returns (repo, doc)."""
    _git_init(tmp_path)
    cli_dir = tmp_path / "cli"
    cli_dir.mkdir()
    (cli_dir / "spec_review.py").write_text(
        "\n".join(f"l{i}" for i in range(1, 600)) + "\n", encoding="utf-8"
    )
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    doc = plans / "sample-plan.md"
    doc.write_text("# Sample\n", encoding="utf-8")
    return tmp_path, doc


@pytest.fixture(autouse=True)
def _clear_discover_cache():
    pdsa._discover_repo_root.cache_clear()
    yield
    pdsa._discover_repo_root.cache_clear()


def test_1_cite_resolution_from_doc_parent_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, doc = _make_repo_with_doc(tmp_path)
    monkeypatch.chdir(doc.parent)
    resolved = pdsa._resolve_inside_repo("cli/spec_review.py", doc)
    assert resolved is not None
    assert resolved == (repo / "cli/spec_review.py").resolve()


def test_2_bare_repo_relative_cite_from_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, doc = _make_repo_with_doc(tmp_path)
    monkeypatch.chdir(doc.parent)
    resolved = pdsa._resolve_inside_repo("cli/spec_review.py", doc)
    assert resolved is not None
    assert resolved.name == "spec_review.py"


def test_3_relative_double_dot_workaround_form_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, doc = _make_repo_with_doc(tmp_path)
    monkeypatch.chdir(doc.parent)
    resolved = pdsa._resolve_inside_repo("../../cli/spec_review.py", doc)
    assert resolved is not None, "deprecated ../../ form must still resolve (backward-compat)"
    assert resolved == (repo / "cli/spec_review.py").resolve()


def test_4_doc_outside_git_repo_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bare = tmp_path / "not-a-repo"
    bare.mkdir()
    (bare / "cli").mkdir()
    (bare / "cli" / "x.py").write_text("hi\n")
    doc = bare / "doc.md"
    doc.write_text("Reference: `cli/x.py:1`\n")
    monkeypatch.chdir(bare)
    resolved = pdsa._resolve_inside_repo("cli/x.py", doc)
    assert resolved is None, "non-git location must fail-closed even if file exists"


def test_5_absolute_path_cite_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, doc = _make_repo_with_doc(tmp_path)
    monkeypatch.chdir(doc.parent)
    assert pdsa._resolve_inside_repo("/etc/passwd", doc) is None


def test_6_escape_with_double_dot_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, doc = _make_repo_with_doc(tmp_path)
    monkeypatch.chdir(doc.parent)
    resolved = pdsa._resolve_inside_repo("../../../etc/shadow", doc)
    assert resolved is None


def test_7_submodule_layout_discovers_inner_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git_init(tmp_path)
    submodule_dir = tmp_path / "vendor" / "sub"
    submodule_dir.mkdir(parents=True)
    _git_init(submodule_dir)
    (submodule_dir / "src").mkdir()
    (submodule_dir / "src" / "inner.py").write_text("x\n")
    doc = submodule_dir / "doc.md"
    doc.write_text("# inside submodule\n")
    monkeypatch.chdir(submodule_dir)
    resolved = pdsa._resolve_inside_repo("src/inner.py", doc)
    assert resolved is not None
    assert resolved == (submodule_dir / "src/inner.py").resolve()
    discovered = pdsa._discover_repo_root(submodule_dir)
    assert discovered == submodule_dir.resolve()


def test_8_class_audit_from_subdir_and_outside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, doc = _make_repo_with_doc(tmp_path)
    iter_2_doc = doc.parent / "iter2.md"
    iter_2_doc.write_text(
        "> **Iteration:** 2\n\n## Audit Attestation\n\nswept.\n", encoding="utf-8"
    )
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "iter2-r1.review.yaml").write_text(
        textwrap.dedent(
            """\
            findings_aggregated:
              - id: 1
                scope: class
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(doc.parent)
    result = pdsa._check_class_audit_attestation(iter_2_doc)
    assert result.passed is True

    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        bare = Path(raw)
        iter_2_outside = bare / "iter2.md"
        iter_2_outside.write_text(
            "> **Iteration:** 2\n\nbody\n", encoding="utf-8"
        )
        pdsa._discover_repo_root.cache_clear()
        monkeypatch.chdir(bare)
        result2 = pdsa._check_class_audit_attestation(iter_2_outside)
        assert result2.passed is False
        assert "cannot discover repo root" in result2.detail


def test_9_refs_resolve_from_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, doc = _make_repo_with_doc(tmp_path)
    body = "## Body\n\nRefs: cli/spec_review.py\n"
    doc.write_text(body, encoding="utf-8")
    monkeypatch.chdir(doc.parent)
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)
    assert report.checks["refs"].passed is True, report.checks["refs"].detail


def test_10_env_var_redirect_attack_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GIT_DIR / GIT_WORK_TREE / GIT_CEILING_DIRECTORIES must NOT redirect discovery."""
    _git_init(tmp_path)
    other_repo = tmp_path.parent / "other-repo-redirected"
    other_repo.mkdir(exist_ok=True)
    try:
        _git_init(other_repo)
        for env_var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_CEILING_DIRECTORIES"):
            monkeypatch.setenv(env_var, str(other_repo))
            pdsa._discover_repo_root.cache_clear()
            discovered = pdsa._discover_repo_root(tmp_path)
            assert discovered == tmp_path.resolve(), (
                f"{env_var}={other_repo} must not redirect — got {discovered}"
            )
            monkeypatch.delenv(env_var)
    finally:
        import shutil
        shutil.rmtree(other_repo, ignore_errors=True)
