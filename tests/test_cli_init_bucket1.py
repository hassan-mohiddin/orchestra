"""Tests for cli.init Bucket 1 scaffold."""

from __future__ import annotations

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
