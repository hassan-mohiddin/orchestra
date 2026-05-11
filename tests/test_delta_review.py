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


# ---------------------------------------------------------------------------
# Slice 2.18 — verify attestation_integrity_hash
# ---------------------------------------------------------------------------


def test_integrity_verification_pass(tmp_path):
    """Slice 2.18 — well-formed attestation with valid integrity hash → pass."""
    from cli import delta_review, spec_review

    doc = tmp_path / "docs" / "features" / "008-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("body\n")

    payload = {
        "schema_version": "2.0",
        "doc_subject": {
            "path": "docs/features/008-foo.md",
            "iteration": 1,
            "iter_blob_sha": "a" * 40,
            "iter_commit_sha": "b" * 40,
        },
        "findings_aggregated": [],
        "overall_verdict": "pass",
    }
    payload["attestation_integrity_hash"] = spec_review._compute_attestation_integrity_hash(payload)

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text(yaml.safe_dump(payload))

    attestation = delta_review.load_prior_attestation(doc, current_iteration=2, repo_root=tmp_path)
    delta_review.verify_integrity(attestation)  # no raise = pass


def test_integrity_verification_tampered(tmp_path):
    """Slice 2.18 — attestation with mismatched integrity_hash → SpecReviewError."""
    from cli import delta_review, spec_review

    doc = tmp_path / "docs" / "features" / "008-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("body\n")

    payload = {
        "schema_version": "2.0",
        "doc_subject": {
            "path": "docs/features/008-foo.md",
            "iteration": 1,
            "iter_blob_sha": "a" * 40,
            "iter_commit_sha": "b" * 40,
        },
        "findings_aggregated": [],
        "overall_verdict": "pass",
    }
    payload["attestation_integrity_hash"] = spec_review._compute_attestation_integrity_hash(payload)
    # Tamper post-hash
    payload["overall_verdict"] = "fail"

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text(yaml.safe_dump(payload))

    attestation = delta_review.load_prior_attestation(doc, current_iteration=2, repo_root=tmp_path)
    with pytest.raises(delta_review.SpecReviewError) as exc_info:
        delta_review.verify_integrity(attestation)
    assert "integrity_hash_mismatch" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Slice 2.22-2.23 — git cat-file blob retrieval + cross-check
# ---------------------------------------------------------------------------


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "--quiet", "--initial-branch=main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)


def test_retrieve_iter1_bytes_cross_check(tmp_path):
    """Slice 2.22 + 2.23 — retrieve_iter1_bytes returns blob content; re-hash matches stored SHA."""
    from cli import delta_review, spec_review

    _init_repo(tmp_path)

    iter1_bytes = b"iter-1 doc content\n"
    src = tmp_path / "doc1.md"
    src.write_bytes(iter1_bytes)
    blob_sha = spec_review._persist_doc_blob(src, tmp_path)

    retrieved = delta_review.retrieve_iter1_bytes(blob_sha, tmp_path)
    assert retrieved == iter1_bytes


def test_retrieve_iter1_bytes_cross_check_detects_corruption(tmp_path, monkeypatch):
    """Slice 2.23 — if retrieved bytes hash != stored SHA, SpecReviewError fires."""
    from cli import delta_review, spec_review

    _init_repo(tmp_path)

    src = tmp_path / "doc1.md"
    src.write_bytes(b"real content\n")
    real_sha = spec_review._persist_doc_blob(src, tmp_path)

    # Monkeypatch the low-level retrieval to return wrong bytes
    monkeypatch.setattr(
        spec_review,
        "_retrieve_doc_bytes_by_blob_sha",
        lambda sha, root: b"tampered content\n",
    )

    with pytest.raises(delta_review.SpecReviewError) as exc_info:
        delta_review.retrieve_iter1_bytes(real_sha, tmp_path)
    assert "blob_sha_mismatch" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Slice 2.24 — pruned-blob fails closed
# ---------------------------------------------------------------------------


def test_pruned_blob_fails_closed(tmp_path):
    """Slice 2.24 — `git cat-file -p` on unknown SHA → SpecReviewError(iter1_blob_pruned)."""
    from cli import delta_review

    _init_repo(tmp_path)

    bogus_sha = "0" * 40
    with pytest.raises(delta_review.SpecReviewError) as exc_info:
        delta_review.retrieve_iter1_bytes(bogus_sha, tmp_path)
    assert "iter1_blob_pruned" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Slice 2.25 — diff extraction
# ---------------------------------------------------------------------------


def test_compute_diff_basic():
    """Slice 2.25 — compute_unified_diff returns unified-diff text for changed bytes."""
    from cli import delta_review

    iter1 = "line 1\nline 2\nline 3\n"
    iter2 = "line 1\nline 2 CHANGED\nline 3\n"
    diff = delta_review.compute_unified_diff(iter1, iter2)
    assert "@@" in diff
    assert "-line 2" in diff
    assert "+line 2 CHANGED" in diff


def test_compute_diff_empty():
    """Slice 2.26 — identical iter-1 and iter-2 → empty diff string."""
    from cli import delta_review

    text = "same content\nno changes\n"
    diff = delta_review.compute_unified_diff(text, text)
    assert diff == ""


# ---------------------------------------------------------------------------
# Slice 2.26 — empty-diff no-op decision
# ---------------------------------------------------------------------------


def test_is_noop_iteration_true_for_empty_diff():
    """Slice 2.26 — empty diff string → is_noop_iteration True."""
    from cli import delta_review

    assert delta_review.is_noop_iteration("") is True


def test_is_noop_iteration_false_for_changes():
    """Slice 2.26 — non-empty diff → not a no-op."""
    from cli import delta_review

    assert delta_review.is_noop_iteration("@@ -1,1 +1,1 @@\n-x\n+y\n") is False


# ---------------------------------------------------------------------------
# Slice 2.27 — delta prompt builder
# ---------------------------------------------------------------------------


def test_build_delta_prompt_includes_diff_and_findings():
    """Slice 2.27 — delta-mode sub-judge prompt embeds diff + iter-1 findings as context."""
    from cli import delta_review

    diff = "@@ -1,1 +1,2 @@\n-old\n+new line 1\n+new line 2\n"
    prior_findings = [
        {
            "severity": "Important",
            "location": "Body § X",
            "problem": "shared problem",
            "scope": "instance",
            "raised_by": ["semantic"],
        }
    ]
    prompt = delta_review.build_delta_prompt(
        judge_id="semantic",
        diff_text=diff,
        prior_findings=prior_findings,
        prior_iteration=1,
    )
    assert "delta" in prompt.lower()
    assert diff in prompt
    assert "Body § X" in prompt
    assert "shared problem" in prompt
    assert "iter-1" in prompt.lower() or "iteration 1" in prompt.lower()
    assert "semantic" in prompt


def test_build_delta_prompt_with_no_prior_findings():
    """Slice 2.27 — empty prior findings list still produces a valid prompt."""
    from cli import delta_review

    diff = "@@ -1,1 +1,1 @@\n-x\n+y\n"
    prompt = delta_review.build_delta_prompt(
        judge_id="adversarial",
        diff_text=diff,
        prior_findings=[],
        prior_iteration=1,
    )
    assert "no prior findings" in prompt.lower() or "0 prior" in prompt.lower()
    assert diff in prompt
