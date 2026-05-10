"""BUG-009: cli.lint --commit must include L2 retroactive canon-inplace check."""

import subprocess
from pathlib import Path

import pytest


def _git(repo: Path, *args: str, msg: str | None = None) -> str:
    cmd = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    if msg is not None:
        cmd += list(args) + ["-m", msg]
    else:
        cmd += list(args)
    return subprocess.check_output(cmd, cwd=repo, text=True, stderr=subprocess.STDOUT).strip()


def _init_repo_with_canon_doc(tmp_path: Path, status: str = "Implemented") -> Path:
    repo = tmp_path
    _git(repo, "init", "--quiet", "--initial-branch=main")
    feat = repo / "docs" / "features"
    feat.mkdir(parents=True)
    (feat / "001-x.md").write_text(
        "# F\n\n"
        f"> **Status:** {status}\n"
        "> **Iteration:** 1\n\n"
        "## Body\n\nOriginal body content.\n\n"
        "## Changelog\n\n| Date | Change |\n|---|---|\n| 2026 | seed |\n"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", msg="docs: seed canon doc")
    return repo


def test_canon_inplace_violation_in_committed_sha_caught(tmp_path):
    """Body-edit canon-frozen doc; lint_commit(HEAD) returns canon-inplace finding."""
    from cli.lint import lint_commit

    repo = _init_repo_with_canon_doc(tmp_path)
    doc = repo / "docs" / "features" / "001-x.md"
    doc.write_text(doc.read_text().replace("Original body content.", "MUTATED body."))
    _git(repo, "commit", "--quiet", "-am", "fix: violate canon-inplace")

    findings = lint_commit("HEAD", repo)
    assert any("canon-frozen" in f.message.lower() or "non-narrow" in f.message.lower()
               for f in findings), f"L2 should fire; findings={[f.message for f in findings]}"


def test_canon_inplace_narrow_change_committed_passes(tmp_path):
    """Whitelist-only edit (Iteration bump) → lint_commit returns no canon-inplace finding."""
    from cli.lint import lint_commit

    repo = _init_repo_with_canon_doc(tmp_path)
    doc = repo / "docs" / "features" / "001-x.md"
    doc.write_text(doc.read_text().replace("Iteration:** 1", "Iteration:** 2"))
    _git(repo, "commit", "--quiet", "-am", "docs: bump iteration")

    findings = lint_commit("HEAD", repo)
    assert not any("canon-frozen" in f.message.lower() or "non-narrow" in f.message.lower()
                   for f in findings), f"narrow-change should pass; findings={[f.message for f in findings]}"


def test_canon_inplace_new_file_in_commit_passes(tmp_path):
    """New file (no prior at HEAD~1) → lint_commit returns no canon-inplace finding."""
    from cli.lint import lint_commit

    repo = tmp_path
    _git(repo, "init", "--quiet", "--initial-branch=main")
    (repo / "README.md").write_text("seed\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", msg="docs: seed README")

    feat = repo / "docs" / "features"
    feat.mkdir(parents=True)
    (feat / "002-y.md").write_text(
        "# Y\n\n> **Status:** Implemented\n> **Iteration:** 1\n\n## Body\n\nNew.\n"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", msg="docs: add new canon doc")

    findings = lint_commit("HEAD", repo)
    assert not any("canon-frozen" in f.message.lower() or "non-narrow" in f.message.lower()
                   for f in findings), f"new file should pass; findings={[f.message for f in findings]}"


def test_canon_inplace_non_canon_status_committed_passes(tmp_path):
    """Prior Status: Draft (not canon-frozen) → body edit OK; no L2 finding."""
    from cli.lint import lint_commit

    repo = _init_repo_with_canon_doc(tmp_path, status="Draft")
    doc = repo / "docs" / "features" / "001-x.md"
    doc.write_text(doc.read_text().replace("Original body content.", "REWRITTEN body."))
    _git(repo, "commit", "--quiet", "-am", "docs: rewrite Draft body")

    findings = lint_commit("HEAD", repo)
    assert not any("canon-frozen" in f.message.lower() or "non-narrow" in f.message.lower()
                   for f in findings), f"Draft body edit should pass; findings={[f.message for f in findings]}"


def test_canon_inplace_revert_commit_exempted(tmp_path):
    """`revert:` prefix exempts L2 — reverts are recovery, not violations."""
    from cli.lint import lint_commit

    repo = _init_repo_with_canon_doc(tmp_path)
    doc = repo / "docs" / "features" / "001-x.md"
    doc.write_text(doc.read_text().replace("Original body content.", "MUTATED body."))
    _git(repo, "commit", "--quiet", "-am", "fix: violate canon-inplace")
    # Now revert
    _git(repo, "revert", "--no-edit", "HEAD")
    # Override commit msg to ensure "revert:" prefix
    _git(repo, "commit", "--quiet", "--amend", "-m", "revert: undo canon-inplace violation")

    findings = lint_commit("HEAD", repo)
    assert not any("canon-frozen" in f.message.lower() or "non-narrow" in f.message.lower()
                   for f in findings), f"revert: should be exempt; findings={[f.message for f in findings]}"


def test_lint_commit_still_runs_l1(tmp_path):
    """Regression: L1 (Refs eligibility) still fires on fix:/feat: without Refs:."""
    from cli.lint import lint_commit

    repo = tmp_path
    _git(repo, "init", "--quiet", "--initial-branch=main")
    (repo / "README.md").write_text("seed\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", msg="chore: seed")
    (repo / "README.md").write_text("changed\n")
    _git(repo, "commit", "--quiet", "-am", "fix: orphan with no Refs line")

    findings = lint_commit("HEAD", repo)
    assert any("orphan" in f.message.lower() or "refs" in f.message.lower()
               for f in findings), f"L1 should fire on orphan fix:; findings={[f.message for f in findings]}"
