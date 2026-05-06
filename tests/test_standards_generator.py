"""Tests for STANDARDS.md generator (default-7 / subset-rename / full-custom)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.init import (
    FORMAL_VOCAB_WHITELIST,
    InvariantViolation,
    TEMPLATES_DIR,
    generate_standards_md,
    scaffold_bucket_1,
    validate_custom_type,
    validate_rename,
)


def _config(preset: str = "default-7", renames: dict | None = None,
            custom_types: list | None = None) -> dict:
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
                "doc_types": {
                    "preset": preset,
                    "renames": renames or {},
                    "custom_types": custom_types or [],
                },
            }
        },
    }


def test_default_7_emits_canonical_standards() -> None:
    output = generate_standards_md(_config("default-7"))
    template = (TEMPLATES_DIR / "standards-default-7.md").read_text()
    assert output == template


def test_default_7_scaffold_writes_standards(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config("default-7"), tmp_repo)
    sm = tmp_repo / "docs" / "STANDARDS.md"
    assert sm.exists()
    assert "Doc Types" in sm.read_text()


# ---------------- subset-rename ----------------

def test_rename_feature_lld_to_tech_spec() -> None:
    output = generate_standards_md(_config("subset-rename", renames={"Feature LLD": "Tech Spec"}))
    assert "Tech Spec" in output


def test_informal_rename_rejected() -> None:
    with pytest.raises(InvariantViolation):
        generate_standards_md(_config("subset-rename", renames={"Feature LLD": "doc"}))


def test_rfc_rename_rejected_per_philosophy() -> None:
    with pytest.raises(InvariantViolation):
        generate_standards_md(_config("subset-rename", renames={"Feature LLD": "RFC"}))


def test_validate_rename_passes_canonical() -> None:
    for name in FORMAL_VOCAB_WHITELIST:
        validate_rename(name)


# ---------------- full-custom ----------------

def _ct(**overrides) -> dict:
    base = {
        "name": "Tech Spec",
        "path": "tech-specs",
        "naming_pattern": "NNN-kebab.md",
        "status_enum": ["Draft", "Approved", "Done"],
        "required_sections": ["Status", "Body", "Changelog"],
    }
    base.update(overrides)
    return base


def test_full_custom_emits_correct_sections() -> None:
    output = generate_standards_md(_config("full-custom", custom_types=[_ct()]))
    assert "Tech Spec" in output
    assert "tech-specs" in output


def test_custom_type_missing_changelog_rejected() -> None:
    with pytest.raises(InvariantViolation):
        validate_custom_type(_ct(required_sections=["Status", "Body", "Other"]))


def test_custom_type_2_status_states_rejected() -> None:
    with pytest.raises(InvariantViolation):
        validate_custom_type(_ct(status_enum=["Draft", "Done"]))


def test_custom_type_freeform_naming_rejected() -> None:
    with pytest.raises(InvariantViolation):
        validate_custom_type(_ct(naming_pattern="my-custom-pattern.md"))


def test_custom_type_path_traversal_rejected() -> None:
    with pytest.raises(InvariantViolation):
        validate_custom_type(_ct(path="../evil"))
