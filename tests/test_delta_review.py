"""Delta-review module tests (LLD-011 Phase 2 slices 2.17-2.27).

At iter-2 (and any post-iter-1 dispatch), delta-review:
1. Locates the iter-(N-1) attestation file
2. Verifies its attestation_integrity_hash
3. Reads iter_blob_sha from doc_subject
4. Retrieves iter-(N-1) doc bytes via `git cat-file -p <blob_sha>`
5. Cross-checks: re-hash retrieved bytes → must equal stored blob SHA
6. Computes unified diff between iter-(N-1) and current doc
7. Builds sub-judge prompt with diff + iter-(N-1) findings as context
8. Empty diff → no-op iteration (no dispatch, write attestation referencing iter-1 verdict)

Failure modes (fail-closed per LLD-011):
- Missing iter-1 attestation file → SpecReviewError(iter1_attestation_missing)
- Missing iter_blob_sha field → SpecReviewError(iter1_provenance_missing)
- Tampered attestation → SpecReviewError(integrity_hash_mismatch)
- Pruned blob (git gc) → SpecReviewError(iter1_blob_pruned)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Slice 2.17 — locate iter-1 attestation path
# ---------------------------------------------------------------------------


def test_locate_iter1_attestation_path():
    """Slice 2.17 — compute_prior_attestation_path returns repo-relative iter-1 path."""
    from cli import delta_review

    doc = Path("docs/features/008-foo.md")
    path = delta_review.compute_prior_attestation_path(doc, current_iteration=2)
    assert path == Path("docs/reviews/008-foo-r1.review.yaml")


def test_locate_iter1_attestation_path_strips_rev():
    """Slice 2.17 — supersession `-rN` suffix on doc filename is stripped for attestation lookup."""
    from cli import delta_review

    doc = Path("docs/features/008-foo-r3.md")
    # current_iteration here refers to the Iteration: field, not the filename revision
    path = delta_review.compute_prior_attestation_path(doc, current_iteration=2)
    assert path == Path("docs/reviews/008-foo-r1.review.yaml")


def test_locate_prior_for_iter3():
    """Slice 2.17 — current iter=3 → prior iter=2 attestation."""
    from cli import delta_review

    doc = Path("docs/features/008-foo.md")
    path = delta_review.compute_prior_attestation_path(doc, current_iteration=3)
    assert path == Path("docs/reviews/008-foo-r2.review.yaml")


# ---------------------------------------------------------------------------
# Slice 2.21 — fail-closed when iter-1 attestation missing
# ---------------------------------------------------------------------------


def test_missing_attestation_fails_closed(tmp_path):
    """Slice 2.21 — prior attestation path does not exist → SpecReviewError."""
    from cli import delta_review

    doc = tmp_path / "docs" / "features" / "008-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("body\n")

    with pytest.raises(delta_review.SpecReviewError) as exc_info:
        delta_review.load_prior_attestation(doc, current_iteration=2, repo_root=tmp_path)
    assert "iter1_attestation_missing" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Slice 2.20 — fail-closed when iter_blob_sha missing
# ---------------------------------------------------------------------------


def test_missing_provenance_fails_closed(tmp_path):
    """Slice 2.20 — iter-1 attestation lacks iter_blob_sha → SpecReviewError."""
    from cli import delta_review

    doc = tmp_path / "docs" / "features" / "008-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("body\n")

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    # Minimal attestation, missing iter_blob_sha
    (reviews / "008-foo-r1.review.yaml").write_text(yaml.safe_dump({
        "schema_version": "2.0",
        "doc_subject": {
            "path": "docs/features/008-foo.md",
            "iteration": 1,
        },
        "findings_aggregated": [],
        "overall_verdict": "pass",
    }))

    with pytest.raises(delta_review.SpecReviewError) as exc_info:
        delta_review.load_prior_attestation(doc, current_iteration=2, repo_root=tmp_path)
    assert "iter1_provenance_missing" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Slice 2.19 — happy path: read iter_blob_sha
# ---------------------------------------------------------------------------


def test_read_blob_sha(tmp_path):
    """Slice 2.19 — well-formed iter-1 attestation → load_prior_attestation returns dict with iter_blob_sha."""
    from cli import delta_review

    doc = tmp_path / "docs" / "features" / "008-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("body\n")

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text(yaml.safe_dump({
        "schema_version": "2.0",
        "doc_subject": {
            "path": "docs/features/008-foo.md",
            "iteration": 1,
            "iter_blob_sha": "a" * 40,
            "iter_commit_sha": "b" * 40,
        },
        "findings_aggregated": [],
        "overall_verdict": "pass",
    }))

    attestation = delta_review.load_prior_attestation(doc, current_iteration=2, repo_root=tmp_path)
    assert attestation["doc_subject"]["iter_blob_sha"] == "a" * 40
