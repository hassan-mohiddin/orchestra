"""Tests for v1.0 → v1.1 config migration."""

from __future__ import annotations

import json
from pathlib import Path

from cli.init import (
    V10Config,
    detect_v10_config,
    migrate_v10_to_v11,
    write_v11_config,
)


def test_detect_v10_config_present(tmp_repo: Path) -> None:
    settings = tmp_repo / ".claude" / "settings.local.json"
    settings.parent.mkdir(exist_ok=True)
    settings.write_text(json.dumps({
        "orchestra": {
            "mode": "team",
            "doc_paths": {"features": "designs/features"},
            "spec_review_skill": "superpowers:requesting-code-review",
        }
    }))
    v10 = detect_v10_config(tmp_repo)
    assert v10 is not None
    assert v10.mode == "team"
    assert v10.doc_paths["features"] == "designs/features"
    assert v10.spec_review_skill == "superpowers:requesting-code-review"


def test_detect_v10_config_absent(tmp_repo: Path) -> None:
    assert detect_v10_config(tmp_repo) is None


def test_detect_v10_no_orchestra_block(tmp_repo: Path) -> None:
    settings = tmp_repo / ".claude" / "settings.local.json"
    settings.parent.mkdir(exist_ok=True)
    settings.write_text(json.dumps({"some_other_setting": True}))
    assert detect_v10_config(tmp_repo) is None


def test_detect_v10_invalid_json(tmp_repo: Path) -> None:
    settings = tmp_repo / ".claude" / "settings.local.json"
    settings.parent.mkdir(exist_ok=True)
    settings.write_text("{not valid")
    assert detect_v10_config(tmp_repo) is None


def test_migrate_preserves_v10_fields() -> None:
    v10 = V10Config(
        mode="team",
        doc_paths={"features": "designs/features", "bugs": "designs/bugs"},
        spec_review_skill="custom:reviewer",
    )
    v11 = migrate_v10_to_v11(v10)
    assert v11["version"] == "1.1"
    assert v11["orchestra"]["mode"] == "team"
    assert v11["skills"]["design-docs"]["doc_paths"]["features"] == "designs/features"
    assert v11["skills"]["design-docs"]["spec_review_skill"] == "custom:reviewer"


def test_migrate_adds_v11_defaults() -> None:
    v10 = V10Config(mode="solo")
    v11 = migrate_v10_to_v11(v10)
    assert v11["skills"]["design-docs"]["doc_types"]["preset"] == "default-7"
    assert v11["skills"]["design-docs"]["doc_types"]["renames"] == {}
    assert v11["skills"]["design-docs"]["doc_types"]["custom_types"] == []
    # All 7 default paths present
    paths = v11["skills"]["design-docs"]["doc_paths"]
    for key in ["features", "bugs", "adr", "design", "postmortems", "runbooks", "plans"]:
        assert key in paths


def test_migrate_does_not_delete_v10(tmp_repo: Path) -> None:
    settings = tmp_repo / ".claude" / "settings.local.json"
    settings.parent.mkdir(exist_ok=True)
    original_content = json.dumps({
        "orchestra": {"mode": "solo"},
        "other": "preserved",
    })
    settings.write_text(original_content)
    v10 = detect_v10_config(tmp_repo)
    assert v10 is not None
    config = migrate_v10_to_v11(v10)
    write_v11_config(tmp_repo, config)
    # v1.0 block still there
    assert settings.read_text() == original_content
    # v1.1 file created alongside
    assert (tmp_repo / ".claude" / "orchestra.json").exists()
