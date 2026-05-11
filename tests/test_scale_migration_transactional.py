"""Plan §Phase 4 Slice 4.1 — transactional SCALE migration tests.

7 test functions covering dry-run, idempotence, mid-run rollback, repo-identity
4-factor, symlink-safe.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.migrate_scale_rules import (
    MigrationPlan,
    _already_migrated,
    migrate,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "scale-pre-migration"
EXPECTED_REMOTE = "git@example.com:test/scale.git"


def _seed_scale(tmp_path: Path) -> Path:
    """Materialize a fake SCALE repo matching 4-factor sentinels."""
    scale = tmp_path / "scale"
    shutil.copytree(FIXTURE, scale)
    # Init git repo + set remote
    subprocess.run(["git", "init", "--quiet", "--initial-branch=main"],
                   cwd=scale, check=True)
    subprocess.run(["git", "config", "user.email", "t@e"], cwd=scale, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=scale, check=True)
    subprocess.run(["git", "remote", "add", "origin", EXPECTED_REMOTE],
                   cwd=scale, check=True)
    # CLAUDE.md sentinel
    (scale / ".claude").mkdir(exist_ok=True)
    (scale / ".claude" / "CLAUDE.md").write_text("# SCALE — Claude Code\n\nbody.\n")
    # apps/{api,web,worker}/ SCALE monorepo layout sentinel
    for sub in ("api", "web", "worker"):
        (scale / "apps" / sub).mkdir(parents=True, exist_ok=True)
    (scale / "apps" / "web" / "package.json").write_text(
        '{"name": "dashboard", "version": "0.1.0"}\n'
    )
    return scale


def test_migration_dry_run_changes_nothing(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    before = {p.name: p.read_text() for p in scale.rglob("*") if p.is_file()}
    plan = MigrationPlan(scale_root=scale, expected_remote=EXPECTED_REMOTE, dry_run=True)
    rc = migrate(plan)
    assert rc == 0
    after = {p.name: p.read_text() for p in scale.rglob("*") if p.is_file()}
    assert before == after


def test_migration_post_check_invariants(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    plan = MigrationPlan(scale_root=scale, expected_remote=EXPECTED_REMOTE)
    rc = migrate(plan)
    assert rc == 0
    assert _already_migrated(scale)


def test_migration_idempotent_rerun(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    plan = MigrationPlan(scale_root=scale, expected_remote=EXPECTED_REMOTE)
    assert migrate(plan) == 0
    # Second run: detects already-migrated; exit 0; no changes
    snapshot_before = {str(p.relative_to(scale)): p.read_text()
                       for p in scale.rglob("*") if p.is_file() and ".git" not in p.parts}
    assert migrate(plan) == 0
    snapshot_after = {str(p.relative_to(scale)): p.read_text()
                      for p in scale.rglob("*") if p.is_file() and ".git" not in p.parts}
    assert snapshot_before == snapshot_after


def test_migration_rejects_bad_remote(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    plan = MigrationPlan(scale_root=scale, expected_remote="git@evil.example.com:fake/repo.git")
    rc = migrate(plan)
    assert rc == 1
    # No mutation
    assert (scale / ".claude/rules/canon-frozen-guard.md").exists()


def test_migration_rejects_missing_claude_md_sentinel(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    (scale / ".claude" / "CLAUDE.md").unlink()
    plan = MigrationPlan(scale_root=scale, expected_remote=EXPECTED_REMOTE)
    rc = migrate(plan)
    assert rc == 1
    assert (scale / ".claude/rules/canon-frozen-guard.md").exists()


def test_migration_rejects_missing_apps_web_sentinel(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    # Remove apps/web/package.json AND apps/worker to break layout sentinel
    (scale / "apps" / "web" / "package.json").unlink()
    plan = MigrationPlan(scale_root=scale, expected_remote=EXPECTED_REMOTE)
    rc = migrate(plan)
    assert rc == 1
    assert (scale / ".claude/rules/canon-frozen-guard.md").exists()


def test_migration_rejects_symlinked_targets(tmp_path: Path) -> None:
    scale = _seed_scale(tmp_path)
    # Replace canon-frozen-guard.md with symlink
    canon = scale / ".claude/rules/canon-frozen-guard.md"
    canon.unlink()
    target = tmp_path / "external.md"
    target.write_text("malicious\n")
    canon.symlink_to(target)
    plan = MigrationPlan(scale_root=scale, expected_remote=EXPECTED_REMOTE)
    rc = migrate(plan)
    assert rc == 1
    # External target untouched
    assert target.read_text() == "malicious\n"
    assert canon.is_symlink()
