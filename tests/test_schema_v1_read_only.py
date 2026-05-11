"""v1.0 attestation read-only backward compatibility (LLD-011 Phase 1 slices 1.6-1.7).

v1.0 attestations remain on disk after v2 ships. cli.spec_review v2 must:
- Detect schema_version of any existing attestation before writing (slice 1.6)
- Refuse to overwrite a v1.0 attestation (slice 1.7) — v1 is frozen-historical
"""

from pathlib import Path

import pytest


def test_v1_attestation_readable(tmp_path: Path) -> None:
    """Slice 1.6 — _detect_schema_version returns '1.0' for v1 attestations."""
    from cli import spec_review

    v1_yaml = (
        'schema_version: "1.0"\n'
        "doc_subject:\n"
        "  path: docs/features/example.md\n"
        "  content_hash: sha256:" + "a" * 64 + "\n"
        "  iteration: 1\n"
    )
    p = tmp_path / "v1.review.yaml"
    p.write_text(v1_yaml)
    assert spec_review._detect_schema_version(p) == "1.0"


def test_v2_attestation_detected(tmp_path: Path) -> None:
    """Slice 1.6 — _detect_schema_version returns '2.0' for v2 attestations."""
    from cli import spec_review

    v2_yaml = 'schema_version: "2.0"\n'
    p = tmp_path / "v2.review.yaml"
    p.write_text(v2_yaml)
    assert spec_review._detect_schema_version(p) == "2.0"


def test_nonexistent_returns_none(tmp_path: Path) -> None:
    """Slice 1.6 — missing file returns None."""
    from cli import spec_review

    p = tmp_path / "missing.review.yaml"
    assert spec_review._detect_schema_version(p) is None


def test_malformed_returns_none(tmp_path: Path) -> None:
    """Slice 1.6 — malformed YAML returns None (no crash)."""
    from cli import spec_review

    p = tmp_path / "broken.review.yaml"
    p.write_text("not: valid: yaml: structure: [")
    assert spec_review._detect_schema_version(p) is None
