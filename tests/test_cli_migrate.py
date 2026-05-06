"""Tests for cli.migrate."""

from __future__ import annotations

import json
from pathlib import Path

from cli.init import default_config, scaffold_bucket_1, write_v11_config
from cli.migrate import migrate_solo_to_team, migrate_team_to_solo


def _seed_config(root: Path, mode: str = "solo") -> None:
    cfg = default_config(mode=mode)
    scaffold_bucket_1(cfg, root)
    write_v11_config(root, cfg)


def _write_adr(root: Path, n: int, with_okr: bool) -> Path:
    adr_dir = root / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    name = f"ADR-{n:03d}-test.md"
    metadata = (
        f"> **Doc ID:** ADR-{n:03d}-test\n"
        "> **Date:** 2026-05-06\n"
        "> **DRI:** Hassan\n"
        "> **Status:** Approved\n"
    )
    if with_okr:
        metadata += "> **OKR Alignment:** Q2-Reliability\n"
    text = f"# ADR-{n:03d}: Test\n\n{metadata}\n## Context\n\nText.\n"
    p = adr_dir / name
    p.write_text(text)
    return p


def test_solo_to_team_flips_mode(tmp_repo: Path) -> None:
    _seed_config(tmp_repo, mode="solo")
    result = migrate_solo_to_team(tmp_repo)
    assert not result.no_op
    assert result.new_mode == "team"
    cfg = json.loads((tmp_repo / ".claude" / "orchestra.json").read_text())
    assert cfg["orchestra"]["mode"] == "team"


def test_solo_to_team_idempotent(tmp_repo: Path) -> None:
    _seed_config(tmp_repo, mode="team")
    result = migrate_solo_to_team(tmp_repo)
    assert result.no_op
    assert "Already" in result.message


def test_solo_to_team_reports_missing_okr(tmp_repo: Path) -> None:
    _seed_config(tmp_repo, mode="solo")
    _write_adr(tmp_repo, 1, with_okr=True)
    _write_adr(tmp_repo, 2, with_okr=False)
    _write_adr(tmp_repo, 3, with_okr=False)
    result = migrate_solo_to_team(tmp_repo)
    assert len(result.adrs_needing_backfill) == 2
    names = {p.name for p in result.adrs_needing_backfill}
    assert "ADR-002-test.md" in names
    assert "ADR-003-test.md" in names


def test_team_to_solo_reverse(tmp_repo: Path) -> None:
    _seed_config(tmp_repo, mode="team")
    result = migrate_team_to_solo(tmp_repo)
    assert result.new_mode == "solo"
    cfg = json.loads((tmp_repo / ".claude" / "orchestra.json").read_text())
    assert cfg["orchestra"]["mode"] == "solo"


def test_team_to_solo_idempotent(tmp_repo: Path) -> None:
    _seed_config(tmp_repo, mode="solo")
    result = migrate_team_to_solo(tmp_repo)
    assert result.no_op


def test_dry_run_no_writes(tmp_repo: Path) -> None:
    _seed_config(tmp_repo, mode="solo")
    _write_adr(tmp_repo, 1, with_okr=False)
    _write_adr(tmp_repo, 2, with_okr=False)
    result = migrate_solo_to_team(tmp_repo, dry_run=True)
    assert not result.no_op
    assert result.new_mode == "team"
    # ADR scan still runs even in dry mode
    assert len(result.adrs_needing_backfill) == 2
    cfg = json.loads((tmp_repo / ".claude" / "orchestra.json").read_text())
    # Mode unchanged because dry_run
    assert cfg["orchestra"]["mode"] == "solo"


def test_migrate_with_no_config(tmp_repo: Path) -> None:
    # No orchestra.json — config invalid
    result = migrate_solo_to_team(tmp_repo)
    assert result.no_op
    assert result.new_mode is None
    # File never created/modified
    assert not (tmp_repo / ".claude" / "orchestra.json").exists()


def test_scan_rejects_traversal_path(tmp_repo: Path) -> None:
    """adr_dir_rel must reject absolute paths and `..` traversal."""
    from cli.migrate import _scan_adrs_for_okr
    assert _scan_adrs_for_okr(tmp_repo, "/etc") == []
    assert _scan_adrs_for_okr(tmp_repo, "../../etc") == []
    assert _scan_adrs_for_okr(tmp_repo, "docs/../../../etc") == []
