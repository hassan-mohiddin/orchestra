"""Tests for cli.init Bucket 1 scaffold."""

from __future__ import annotations

import subprocess
from pathlib import Path

from cli.init import scaffold_bucket_1


def _config() -> dict:
    return {
        "version": "1.1",
        "orchestra": {"mode": "solo"},
        "skills": {
            "design-docs": {
                "doc_paths": {
                    "features": "docs/features",
                    "bugs": "docs/bugs",
                    "adr": "docs/adr",
                    "design": "docs/design",
                    "postmortems": "docs/postmortems",
                    "runbooks": "docs/runbooks",
                    "plans": "docs/plans",
                },
                "doc_types": {"preset": "default-7", "renames": {}, "custom_types": []},
            }
        },
    }


def test_fresh_scaffold_creates_7_dirs(tmp_repo: Path) -> None:
    result = scaffold_bucket_1(_config(), tmp_repo)
    assert result.ok
    for sub in ["features", "bugs", "adr", "design", "postmortems", "runbooks", "plans"]:
        assert (tmp_repo / "docs" / sub).is_dir()
        assert (tmp_repo / "docs" / sub / ".gitkeep").exists()


def test_scaffold_idempotent(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config(), tmp_repo)
    second = scaffold_bucket_1(_config(), tmp_repo)
    assert second.ok
    assert len(second.skipped) >= 7  # 7 .gitkeep skipped
    # gitignore: also skipped on second run since entries already present


def test_gitignore_append_preserves_existing(tmp_repo: Path) -> None:
    (tmp_repo / ".gitignore").write_text("node_modules/\n.env\n")
    scaffold_bucket_1(_config(), tmp_repo)
    content = (tmp_repo / ".gitignore").read_text()
    assert "node_modules/" in content
    assert ".env" in content
    assert ".claude/orchestra.local.json" in content
    assert "docs/investigations/" in content


def test_gitignore_no_double_append(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config(), tmp_repo)
    scaffold_bucket_1(_config(), tmp_repo)
    content = (tmp_repo / ".gitignore").read_text()
    assert content.count(".claude/orchestra.local.json") == 1


# ---------------------------------------------------------------------------
# BUG-002 — tracked-file safety check before .gitignore append
# ---------------------------------------------------------------------------


def _commit_file(repo: Path, rel: str, body: str = "x") -> None:
    """Helper: create a tracked file in repo at rel path."""
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-m", "seed", "--quiet"],
        check=True, capture_output=True,
    )


def test_gitignore_skips_when_path_has_tracked_files(tmp_repo: Path) -> None:
    """BUG-002 — pre-existing tracked file at docs/investigations/ must SKIP gitignore append."""
    _commit_file(tmp_repo, "docs/investigations/README.md", "preexisting investigation notes")
    result = scaffold_bucket_1(_config(), tmp_repo)
    content = (tmp_repo / ".gitignore").read_text() if (tmp_repo / ".gitignore").exists() else ""
    assert "docs/investigations/" not in content, (
        "BUG-002: pattern with tracked files must NOT be appended to .gitignore by default."
    )
    # Other clean patterns still appended
    assert ".eval-workspace/" in content
    # Warning surfaced
    assert any("docs/investigations" in w for w in result.warnings), (
        "Skipped pattern must surface a warning naming the path + tracked-file count."
    )


def test_gitignore_force_appends_anyway(tmp_repo: Path) -> None:
    """BUG-002 — --force overrides the tracked-file safety check."""
    _commit_file(tmp_repo, "docs/investigations/README.md", "preexisting")
    result = scaffold_bucket_1(_config(), tmp_repo, force=True)
    content = (tmp_repo / ".gitignore").read_text()
    assert "docs/investigations/" in content, "force=True must override tracked-file check"
    # No warning expected with force (action wasn't blocked)
    assert not any("docs/investigations" in w for w in result.warnings), (
        "force=True path must not emit the skip-warning (action was taken)."
    )
    _ = result  # silence


def test_gitignore_no_warning_for_clean_paths(tmp_repo: Path) -> None:
    """BUG-002 — fresh repo, no tracked files at any pattern, no warnings emitted."""
    result = scaffold_bucket_1(_config(), tmp_repo)
    content = (tmp_repo / ".gitignore").read_text()
    # All 3 patterns appended
    assert ".claude/orchestra.local.json" in content
    assert "docs/investigations/" in content
    assert ".eval-workspace/" in content
    # Zero warnings on a clean fresh-repo run
    assert result.warnings == [], f"Unexpected warnings on fresh repo: {result.warnings}"


def test_gitignore_skip_does_not_block_other_patterns(tmp_repo: Path) -> None:
    """BUG-002 — only the offending pattern is skipped; siblings still append."""
    _commit_file(tmp_repo, "docs/investigations/foo.md")
    result = scaffold_bucket_1(_config(), tmp_repo)
    content = (tmp_repo / ".gitignore").read_text() if (tmp_repo / ".gitignore").exists() else ""
    assert ".claude/orchestra.local.json" in content
    assert ".eval-workspace/" in content
    assert "docs/investigations/" not in content
    _ = result
