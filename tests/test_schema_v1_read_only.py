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
    p = tmp_path / "v1.orchestra.review.yaml"
    p.write_text(v1_yaml)
    assert spec_review._detect_schema_version(p) == "1.0"


def test_v2_attestation_detected(tmp_path: Path) -> None:
    """Slice 1.6 — _detect_schema_version returns '2.0' for v2 attestations."""
    from cli import spec_review

    v2_yaml = 'schema_version: "2.0"\n'
    p = tmp_path / "v2.orchestra.review.yaml"
    p.write_text(v2_yaml)
    assert spec_review._detect_schema_version(p) == "2.0"


def test_nonexistent_returns_none(tmp_path: Path) -> None:
    """Slice 1.6 — missing file returns None."""
    from cli import spec_review

    p = tmp_path / "missing.orchestra.review.yaml"
    assert spec_review._detect_schema_version(p) is None


def test_malformed_returns_none(tmp_path: Path) -> None:
    """Slice 1.6 — malformed YAML returns None (no crash)."""
    from cli import spec_review

    p = tmp_path / "broken.orchestra.review.yaml"
    p.write_text("not: valid: yaml: structure: [")
    assert spec_review._detect_schema_version(p) is None


def _setup_repo_with_v1_attestation(tmp_path: Path) -> None:
    """Create a tmp repo with a doc + an existing v1.0 attestation."""
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    doc = docs / "008-foo.md"
    doc.write_text("# foo\n\n> **Iteration:** 1\n\n## Body\n\nHello.\n")
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    v1 = reviews / "008-foo-r1.orchestra.review.yaml"
    v1.write_text(
        'schema_version: "1.0"\n'
        "doc_subject:\n"
        "  path: docs/features/008-foo.md\n"
        "  content_hash: sha256:" + "0" * 64 + "\n"
        "  iteration: 1\n"
        "reviewer:\n"
        "  identifier: subagent:general-purpose+spec-review-v1\n"
        "  invoked_at: '2026-05-10T00:00:00Z'\n"
        "  context_isolation: fresh_subagent\n"
        "gates:\n"
        "  completeness: {verdict: pass, findings: [], justification: 'frozen'}\n"
        "  evidence: {verdict: pass, findings: [], justification: 'frozen'}\n"
        "  clarity: {verdict: pass, findings: [], justification: 'frozen'}\n"
        "  consistency: {verdict: pass, findings: [], justification: 'frozen'}\n"
        "overall_verdict: pass\n"
    )


def test_v1_overwrite_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Slice 1.7 — cli.spec_review refuses to overwrite a v1.0 attestation even with --force.

    v1.0 attestations are frozen-historical per LLD-011 §Out-of-scope. Overwriting them
    with a v2.0 review would destroy the audit trail.
    """
    from cli import spec_review

    _setup_repo_with_v1_attestation(tmp_path)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    rc = spec_review.main(["--force", "docs/features/008-foo.md"])

    captured = capsys.readouterr()
    assert rc == 1
    msg = captured.err.lower()
    assert "v1.0" in msg or "frozen" in msg


def test_v1_overwrite_refused_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Slice 1.7 — same refusal applies without --force (v1 cannot be overwritten by any path)."""
    from cli import spec_review

    _setup_repo_with_v1_attestation(tmp_path)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    rc = spec_review.main(["docs/features/008-foo.md"])

    captured = capsys.readouterr()
    assert rc == 1
    msg = captured.err.lower()
    # Could be the v1 refusal OR the generic 'already exists' depending on order;
    # we accept either, since both result in non-overwrite. Critical assertion: rc=1.
    assert "v1.0" in msg or "frozen" in msg or "already exists" in msg
