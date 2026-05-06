"""Orchestra config loader + validator.

Reads `.claude/orchestra.json` (primary) + optional `.claude/orchestra.local.json`
(gitignored override). Returns deep-merged config. Validates against schema.

Pure stdlib — no `jsonschema` dependency.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "orchestra.json"
LOCAL_OVERRIDE_FILENAME = "orchestra.local.json"
CLAUDE_DIR = ".claude"

VALID_MODES = {"solo", "team"}
VALID_PRESETS = {"default-7", "subset-rename", "full-custom"}
VALID_NAMING_PATTERNS = {"NNN-kebab.md", "YYYY-MM-DD-kebab.md", "kebab.md"}
REQUIRED_DOC_PATHS = {"features", "bugs", "adr", "design", "postmortems", "runbooks", "plans"}


class ConfigError(Exception):
    """Raised when orchestra.json fails to load or parse."""


@dataclass
class ValidationError:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class ConfigLoadResult:
    config: dict[str, Any] = field(default_factory=dict)
    errors: list[ValidationError] = field(default_factory=list)
    primary_found: bool = False
    local_found: bool = False

    @property
    def valid(self) -> bool:
        return not self.errors


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read {path}: {e}") from e


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge override into base. Override values win on conflict."""
    out = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def validate_config(config: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []

    if not isinstance(config, dict):
        errors.append(ValidationError(".", "config root must be an object"))
        return errors

    version = config.get("version")
    if version != "1.1":
        errors.append(ValidationError("version", f"must be '1.1', got {version!r}"))

    orchestra = config.get("orchestra")
    if not isinstance(orchestra, dict):
        errors.append(ValidationError("orchestra", "must be an object"))
    else:
        mode = orchestra.get("mode")
        if mode not in VALID_MODES:
            errors.append(ValidationError("orchestra.mode",
                                          f"must be one of {sorted(VALID_MODES)}, got {mode!r}"))

    skills = config.get("skills")
    if not isinstance(skills, dict):
        errors.append(ValidationError("skills", "must be an object"))
        return errors

    dd = skills.get("design-docs")
    if dd is None:
        return errors
    if not isinstance(dd, dict):
        errors.append(ValidationError("skills.design-docs", "must be an object"))
        return errors

    doc_paths = dd.get("doc_paths")
    if not isinstance(doc_paths, dict):
        errors.append(ValidationError("skills.design-docs.doc_paths", "must be an object"))
    else:
        missing = REQUIRED_DOC_PATHS - set(doc_paths.keys())
        if missing:
            errors.append(ValidationError("skills.design-docs.doc_paths",
                                          f"missing required keys: {sorted(missing)}"))

    doc_types = dd.get("doc_types")
    if not isinstance(doc_types, dict):
        errors.append(ValidationError("skills.design-docs.doc_types", "must be an object"))
    else:
        preset = doc_types.get("preset")
        if preset not in VALID_PRESETS:
            errors.append(ValidationError("skills.design-docs.doc_types.preset",
                                          f"must be one of {sorted(VALID_PRESETS)}, got {preset!r}"))
        custom_types = doc_types.get("custom_types", [])
        if not isinstance(custom_types, list):
            errors.append(ValidationError("skills.design-docs.doc_types.custom_types",
                                          "must be a list"))
        else:
            for i, ct in enumerate(custom_types):
                errors.extend(_validate_custom_type(ct, f"skills.design-docs.doc_types.custom_types[{i}]"))

    return errors


def _validate_custom_type(ct: Any, base_path: str) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if not isinstance(ct, dict):
        return [ValidationError(base_path, "must be an object")]

    required_keys = {"name", "path", "naming_pattern", "status_enum", "required_sections"}
    missing = required_keys - set(ct.keys())
    if missing:
        errors.append(ValidationError(base_path, f"missing keys: {sorted(missing)}"))

    naming = ct.get("naming_pattern")
    if naming and naming not in VALID_NAMING_PATTERNS:
        errors.append(ValidationError(f"{base_path}.naming_pattern",
                                      f"must be one of {sorted(VALID_NAMING_PATTERNS)}, got {naming!r}"))

    status_enum = ct.get("status_enum", [])
    if isinstance(status_enum, list) and len(status_enum) < 3:
        errors.append(ValidationError(f"{base_path}.status_enum",
                                      f"must have ≥3 states, got {len(status_enum)}"))

    sections = ct.get("required_sections", [])
    if isinstance(sections, list):
        if len(sections) < 3:
            errors.append(ValidationError(f"{base_path}.required_sections",
                                          f"must have ≥3 sections, got {len(sections)}"))
        if "Changelog" not in sections:
            errors.append(ValidationError(f"{base_path}.required_sections",
                                          "must include 'Changelog'"))

    path_value = ct.get("path", "")
    if path_value and not _is_safe_path(path_value):
        errors.append(ValidationError(f"{base_path}.path",
                                      f"must match ^[a-z][a-z0-9-]*$ (no traversal), got {path_value!r}"))

    return errors


def _is_safe_path(p: str) -> bool:
    import re
    return bool(re.match(r"^[a-z][a-z0-9-]*$", p))


def load_config(repo_root: Path) -> ConfigLoadResult:
    """Load orchestra.json + optional local override. Returns deep-merged config."""
    primary = repo_root / CLAUDE_DIR / CONFIG_FILENAME
    local = repo_root / CLAUDE_DIR / LOCAL_OVERRIDE_FILENAME

    result = ConfigLoadResult()

    if primary.exists():
        result.primary_found = True
        primary_data = _read_json(primary)
        if local.exists():
            result.local_found = True
            local_data = _read_json(local)
            result.config = deep_merge(primary_data, local_data)
        else:
            result.config = primary_data
        result.errors = validate_config(result.config)
    else:
        result.errors.append(ValidationError(str(primary), "config file not found"))

    return result
