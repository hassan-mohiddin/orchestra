"""Tests for cli.init Bucket 2 scaffold + DECISIONS seeding."""

from __future__ import annotations

from pathlib import Path

from cli.init import scaffold_bucket_1, scaffold_bucket_2


def _config(addons: bool = True) -> dict:
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
                "ci_workflow_installed": addons,
                "agents_md_installed": addons,
                "llms_txt_installed": addons,
            }
        },
    }


def test_bucket2_writes_all_addons(tmp_repo: Path) -> None:
    result = scaffold_bucket_2(_config(addons=True), tmp_repo)
    assert result.ok
    assert (tmp_repo / ".github" / "workflows" / "orchestra-lint.yml").exists()
    assert (tmp_repo / "AGENTS.md").exists()
    assert (tmp_repo / "llms.txt").exists()


def test_bucket2_skips_when_off(tmp_repo: Path) -> None:
    scaffold_bucket_2(_config(addons=False), tmp_repo)
    assert not (tmp_repo / "AGENTS.md").exists()
    assert not (tmp_repo / "llms.txt").exists()
    assert not (tmp_repo / ".github").exists()


def test_bucket2_idempotent(tmp_repo: Path) -> None:
    scaffold_bucket_2(_config(addons=True), tmp_repo)
    second = scaffold_bucket_2(_config(addons=True), tmp_repo)
    assert second.ok
    assert len(second.skipped) == 3


def test_decisions_seeded_on_init(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config(addons=False), tmp_repo)
    assert (tmp_repo / "docs" / "adr" / "DECISIONS.md").exists()


def test_decisions_idempotent(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config(addons=False), tmp_repo)
    scaffold_bucket_1(_config(addons=False), tmp_repo)
    # Should not error; file may be regenerated or skipped
    assert (tmp_repo / "docs" / "adr" / "DECISIONS.md").exists()
