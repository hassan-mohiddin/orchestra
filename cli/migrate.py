"""Orchestra solo↔team mode migration.

Flips `orchestra.mode` in `.claude/orchestra.json` and reports ADRs that
need backfilling (`OKR Alignment` field becomes mandatory in team mode).

Usage:
    python -m cli.migrate --solo-to-team
    python -m cli.migrate --team-to-solo
    python -m cli.migrate --solo-to-team --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from cli.config import load_config
from cli.init import write_v11_config


@dataclass
class MigrationResult:
    no_op: bool = False
    new_mode: str | None = None
    adrs_needing_backfill: list[Path] = field(default_factory=list)
    message: str = ""


def _atomic_write_config(root: Path, config: dict) -> Path:
    """Write via .tmp + os.replace (POSIX atomic) to avoid partial corruption."""
    import os
    target = root / ".claude" / "orchestra.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(config, indent=2) + "\n")
    os.replace(tmp, target)
    return target


def _scan_adrs_for_okr(root: Path, adr_dir_rel: str) -> list[Path]:
    """Return ADRs whose metadata block lacks an OKR Alignment field."""
    adr_dir = root / adr_dir_rel
    if not adr_dir.exists():
        return []
    missing: list[Path] = []
    for adr in sorted(adr_dir.glob("ADR-*.md")):
        text = adr.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:25])
        if "OKR Alignment:" not in head:
            missing.append(adr)
    return missing


def migrate_solo_to_team(root: Path, dry_run: bool = False) -> MigrationResult:
    result = load_config(root)
    if not result.valid:
        return MigrationResult(
            no_op=True,
            message=f"Cannot migrate: config errors: {[str(e) for e in result.errors]}",
        )
    config = result.config
    if config["orchestra"]["mode"] == "team":
        return MigrationResult(no_op=True, message="Already in team mode.")

    if not dry_run:
        config["orchestra"]["mode"] = "team"
        _atomic_write_config(root, config)

    adr_rel = config["skills"]["design-docs"]["doc_paths"]["adr"]
    missing = _scan_adrs_for_okr(root, adr_rel)

    return MigrationResult(
        no_op=False,
        new_mode="team",
        adrs_needing_backfill=missing,
        message=(
            f"Mode → team. {len(missing)} ADR(s) missing OKR Alignment — "
            "backfill manually before next commit (lint will enforce)."
        ),
    )


def migrate_team_to_solo(root: Path, dry_run: bool = False) -> MigrationResult:
    result = load_config(root)
    if not result.valid:
        return MigrationResult(
            no_op=True,
            message=f"Cannot migrate: config errors: {[str(e) for e in result.errors]}",
        )
    config = result.config
    if config["orchestra"]["mode"] == "solo":
        return MigrationResult(no_op=True, message="Already in solo mode.")

    if not dry_run:
        config["orchestra"]["mode"] = "solo"
        _atomic_write_config(root, config)

    return MigrationResult(
        no_op=False,
        new_mode="solo",
        message="Mode → solo. OKR Alignment now optional on ADRs.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra migrate")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--solo-to-team", action="store_true")
    g.add_argument("--team-to-solo", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing config")
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()

    if args.solo_to_team:
        result = migrate_solo_to_team(root, dry_run=args.dry_run)
    else:
        result = migrate_team_to_solo(root, dry_run=args.dry_run)

    print(result.message)
    if result.adrs_needing_backfill:
        print("\nADRs needing OKR Alignment backfill:")
        for adr in result.adrs_needing_backfill:
            print(f"  {adr.relative_to(root) if adr.is_relative_to(root) else adr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
