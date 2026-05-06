"""Tests for cli.config — schema validation + load/merge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.config import (
    ConfigError,
    deep_merge,
    load_config,
    validate_config,
)


def _valid_config() -> dict:
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


def _write_config(tmp_repo: Path, data: dict, filename: str = "orchestra.json") -> None:
    claude_dir = tmp_repo / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / filename).write_text(json.dumps(data, indent=2))


def test_load_valid_config(tmp_repo: Path) -> None:
    _write_config(tmp_repo, _valid_config())
    result = load_config(tmp_repo)
    assert result.valid
    assert result.primary_found
    assert not result.local_found
    assert result.config["orchestra"]["mode"] == "solo"


def test_load_invalid_json(tmp_repo: Path) -> None:
    claude_dir = tmp_repo / ".claude"
    claude_dir.mkdir()
    (claude_dir / "orchestra.json").write_text("{not valid json")
    with pytest.raises(ConfigError):
        load_config(tmp_repo)


def test_unknown_mode_rejected() -> None:
    config = _valid_config()
    config["orchestra"]["mode"] = "unicorn"
    errors = validate_config(config)
    assert any("mode" in e.path for e in errors)


def test_unknown_preset_rejected() -> None:
    config = _valid_config()
    config["skills"]["design-docs"]["doc_types"]["preset"] = "wild"
    errors = validate_config(config)
    assert any("preset" in e.path for e in errors)


def test_missing_doc_paths_keys_rejected() -> None:
    config = _valid_config()
    del config["skills"]["design-docs"]["doc_paths"]["features"]
    errors = validate_config(config)
    assert any("doc_paths" in e.path for e in errors)


def test_local_overrides_primary(tmp_repo: Path) -> None:
    _write_config(tmp_repo, _valid_config())
    override = {"orchestra": {"mode": "team"}}
    _write_config(tmp_repo, override, "orchestra.local.json")
    result = load_config(tmp_repo)
    assert result.valid
    assert result.local_found
    assert result.config["orchestra"]["mode"] == "team"


def test_deep_merge_nested() -> None:
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    override = {"a": {"c": 99}, "e": 4}
    merged = deep_merge(base, override)
    assert merged == {"a": {"b": 1, "c": 99}, "d": 3, "e": 4}


def test_custom_type_path_traversal_rejected() -> None:
    config = _valid_config()
    config["skills"]["design-docs"]["doc_types"]["preset"] = "full-custom"
    config["skills"]["design-docs"]["doc_types"]["custom_types"] = [{
        "name": "Tech Spec",
        "path": "../evil",
        "naming_pattern": "NNN-kebab.md",
        "status_enum": ["Draft", "Approved", "Done"],
        "required_sections": ["Status", "Body", "Changelog"],
    }]
    errors = validate_config(config)
    assert any("path" in e.path for e in errors)


def test_custom_type_too_few_status_states() -> None:
    config = _valid_config()
    config["skills"]["design-docs"]["doc_types"]["preset"] = "full-custom"
    config["skills"]["design-docs"]["doc_types"]["custom_types"] = [{
        "name": "Tech Spec",
        "path": "tech-specs",
        "naming_pattern": "NNN-kebab.md",
        "status_enum": ["Draft", "Done"],
        "required_sections": ["Status", "Body", "Changelog"],
    }]
    errors = validate_config(config)
    assert any("status_enum" in e.path for e in errors)


def test_custom_type_missing_changelog() -> None:
    config = _valid_config()
    config["skills"]["design-docs"]["doc_types"]["preset"] = "full-custom"
    config["skills"]["design-docs"]["doc_types"]["custom_types"] = [{
        "name": "Tech Spec",
        "path": "tech-specs",
        "naming_pattern": "NNN-kebab.md",
        "status_enum": ["Draft", "Approved", "Done"],
        "required_sections": ["Status", "Body", "Other"],
    }]
    errors = validate_config(config)
    assert any("Changelog" in e.message for e in errors)


def test_missing_config_file(tmp_repo: Path) -> None:
    result = load_config(tmp_repo)
    assert not result.valid
    assert not result.primary_found
