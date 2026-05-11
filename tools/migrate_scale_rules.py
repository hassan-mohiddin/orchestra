"""Transactional SCALE migration helper (orchestra v1.7.0 Phase 4).

Per LLD-008 r7 A8 + plan §Phase 4 Slice 4.1: 2 deletions + 1 partial-edit + 1
registry-append, wrapped in transactional snapshot/rollback with 4-factor
repo-identity + symlink-safe + atomic-replace.

Usage:
    python -m tools.migrate_scale_rules \\
        --scale-root /path/to/SCALE/repo \\
        --expected-remote git@github.com:...:.git \\
        [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Reuse the core migration logic from tests/scale_migration_helper.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.scale_migration_helper import (
    GATE_4_5_POINTER,
    QUICK_REF_GATE_4_5_POINTER,
    REGISTRY_ROW,
    _rewrite_documentation_gate,
)


class MigrationError(Exception):
    """Raised on any pre-flight or invariant failure."""


@dataclass
class MigrationPlan:
    scale_root: Path
    expected_remote: str
    dry_run: bool = False
    backup_dir: Path = field(default=Path("."))


def _check_git_toplevel(scale_root: Path) -> None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=scale_root, text=True, stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as e:
        raise MigrationError(
            f"git rev-parse --show-toplevel failed in {scale_root}: {e.stderr or e}"
        )
    if Path(out).resolve() != scale_root.resolve():
        raise MigrationError(
            f"git toplevel mismatch: --scale-root resolved to {scale_root.resolve()}; "
            f"git rev-parse returned {Path(out).resolve()}"
        )


def _check_expected_remote(scale_root: Path, expected: str) -> None:
    try:
        actual = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=scale_root, text=True, stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as e:
        raise MigrationError(
            f"git config --get remote.origin.url failed: {e.stderr or e}"
        )
    if actual != expected:
        raise MigrationError(
            f"remote.origin.url mismatch: expected {expected!r}; got {actual!r}"
        )


def _check_claude_md_sentinel(scale_root: Path) -> None:
    p = scale_root / ".claude" / "CLAUDE.md"
    if not p.is_file():
        raise MigrationError(f"missing sentinel: {p}")
    head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:100])
    if "SCALE — Claude Code" not in head and "SCALE" not in head:
        raise MigrationError(
            f"sentinel {p}: expected SCALE marker not found in first 100 lines"
        )


def _check_apps_web_sentinel(scale_root: Path) -> None:
    p = scale_root / "apps" / "web" / "package.json"
    if not p.is_file():
        raise MigrationError(f"missing sentinel: {p}")
    text = p.read_text(encoding="utf-8")
    if "scale" not in text.lower():
        raise MigrationError(f"sentinel {p}: 'scale' substring not found")


def _verify_repo_identity(plan: MigrationPlan) -> None:
    _check_git_toplevel(plan.scale_root)
    _check_expected_remote(plan.scale_root, plan.expected_remote)
    _check_claude_md_sentinel(plan.scale_root)
    _check_apps_web_sentinel(plan.scale_root)


def _verify_no_symlinks(paths: list[Path]) -> None:
    for p in paths:
        if p.exists() and p.is_symlink():
            raise MigrationError(
                f"refusing to mutate symlinked path: {p} -> {p.readlink()}"
            )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=str(path.parent), delete=False, encoding="utf-8", suffix=".tmp",
    ) as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _already_migrated(scale_root: Path) -> bool:
    rules_dir = scale_root / ".claude" / "rules"
    registry = scale_root / ".claude" / "skills-registry.md"
    if (rules_dir / "canon-frozen-guard.md").exists():
        return False
    if (rules_dir / "commit-strategy.md").exists():
        return False
    docgate = rules_dir / "documentation-gate.md"
    if not docgate.exists() or "orchestra:commit skill" not in docgate.read_text():
        return False
    if not registry.exists() or "orchestra:commit" not in registry.read_text():
        return False
    return True


def _migration_targets(scale_root: Path) -> list[Path]:
    rules_dir = scale_root / ".claude" / "rules"
    return [
        rules_dir / "canon-frozen-guard.md",
        rules_dir / "commit-strategy.md",
        rules_dir / "documentation-gate.md",
        scale_root / ".claude" / "skills-registry.md",
    ]


def _snapshot(scale_root: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup = scale_root / ".scale-migration-backup" / ts
    if backup.exists():
        raise MigrationError(f"backup dir already exists (collision): {backup}")
    backup.mkdir(parents=True)
    for src in _migration_targets(scale_root):
        if src.is_file():
            rel = src.relative_to(scale_root)
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return backup


def _restore(scale_root: Path, backup: Path) -> None:
    for rel_obj in backup.rglob("*"):
        if not rel_obj.is_file():
            continue
        rel = rel_obj.relative_to(backup)
        dst = scale_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rel_obj, dst)


def migrate(plan: MigrationPlan) -> int:
    """Run the migration. Returns 0 on success, 1 on error."""
    try:
        _verify_repo_identity(plan)
    except MigrationError as e:
        print(f"error: repo-identity check failed: {e}", file=sys.stderr)
        return 1

    targets = _migration_targets(plan.scale_root)
    try:
        _verify_no_symlinks(targets)
    except MigrationError as e:
        print(f"error: symlink-safe check failed: {e}", file=sys.stderr)
        return 1

    if _already_migrated(plan.scale_root):
        print("already-migrated: no changes needed", file=sys.stderr)
        return 0

    rules_dir = plan.scale_root / ".claude" / "rules"
    canon_path = rules_dir / "canon-frozen-guard.md"
    strategy_path = rules_dir / "commit-strategy.md"
    docgate_path = rules_dir / "documentation-gate.md"
    registry = plan.scale_root / ".claude" / "skills-registry.md"

    for p in (canon_path, strategy_path, docgate_path, registry):
        if not p.is_file():
            print(f"error: pre-migration source missing: {p}", file=sys.stderr)
            return 1

    if plan.dry_run:
        print("DRY RUN — planned operations:", file=sys.stderr)
        print(f"  DELETE {canon_path}", file=sys.stderr)
        print(f"  DELETE {strategy_path}", file=sys.stderr)
        print(f"  REWRITE {docgate_path} (collapse Gates 4+5 to pointer)", file=sys.stderr)
        print(f"  APPEND registry row to {registry}", file=sys.stderr)
        return 0

    backup = _snapshot(plan.scale_root)
    print(f"snapshot: {backup}", file=sys.stderr)

    try:
        new_docgate = _rewrite_documentation_gate(docgate_path.read_text(encoding="utf-8"))
        _atomic_write(docgate_path, new_docgate)
        existing = registry.read_text(encoding="utf-8")
        if REGISTRY_ROW not in existing:
            if not existing.endswith("\n"):
                existing += "\n"
            _atomic_write(registry, existing + REGISTRY_ROW + "\n")
        canon_path.unlink()
        strategy_path.unlink()
    except Exception as e:
        print(f"error: mid-flight failure: {e}; rolling back from {backup}",
              file=sys.stderr)
        _restore(plan.scale_root, backup)
        return 1

    if not _already_migrated(plan.scale_root):
        print(f"error: post-flight invariant failed; rolling back from {backup}",
              file=sys.stderr)
        _restore(plan.scale_root, backup)
        return 1

    print(f"migration complete. Backup retained at {backup} (manual cleanup after 1 week).",
          file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="migrate-scale-rules")
    parser.add_argument("--scale-root", required=True, help="SCALE repo root path")
    parser.add_argument("--expected-remote", required=True,
                        help="Expected git remote.origin.url; refuses migration if mismatched")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned ops; modify nothing")
    args = parser.parse_args(argv)

    plan = MigrationPlan(
        scale_root=Path(args.scale_root).resolve(),
        expected_remote=args.expected_remote,
        dry_run=args.dry_run,
    )
    return migrate(plan)


if __name__ == "__main__":
    sys.exit(main())
