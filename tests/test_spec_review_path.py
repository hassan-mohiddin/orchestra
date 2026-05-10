"""Path-related tests for cli.spec_review (S1, S2, S3, S32 slices)."""

from pathlib import Path

import pytest


def test_attestation_path_no_suffix():
    """T7 / S1 — A6: docs/features/007-x.md → docs/reviews/007-r1.review.yaml."""
    from cli.spec_review import compute_attestation_path

    doc_path = Path("docs/features/007-spec-review-architecture.md")
    result = compute_attestation_path(doc_path, iteration=1)
    assert result == Path("docs/reviews/007-spec-review-architecture-r1.review.yaml")


def test_attestation_path_anchored_to_repo_root(tmp_path):
    """T24 / S3 — A23 (F9): caller anchors compute_attestation_path under repo_root.

    Contract: compute_attestation_path returns repo-relative Path. Caller does
    `repo_root / compute_attestation_path(...)` to get absolute out_path.
    Verifies the relative-path contract so cwd-independent callers work.
    """
    from cli.spec_review import compute_attestation_path

    doc_path = Path("docs/features/007-spec-review-architecture.md")
    rel = compute_attestation_path(doc_path, iteration=1)
    assert not rel.is_absolute(), "compute_attestation_path must return repo-relative Path"

    repo_root = tmp_path
    abs_out = repo_root / rel
    assert abs_out.is_absolute()
    assert abs_out.is_relative_to(repo_root)


def test_plans_path_accepted_in_schema():
    """T26 / S32 — A25: docs/plans/... path accepted by schema regex.

    Schema regex must include `plans` in the doc-type alternation so plan
    docs can be valid spec-review targets.
    """
    import json
    import re as _re

    schema_path = (
        Path(__file__).parent.parent
        / "skills"
        / "spec-review"
        / "attestation-schema-v1.0.json"
    )
    schema = json.loads(schema_path.read_text())
    pattern = schema["properties"]["doc_subject"]["properties"]["path"]["pattern"]

    plan_path = "docs/plans/2026-05-10-lld-007-implementation.md"
    assert _re.match(pattern, plan_path), \
        f"docs/plans/ path not matched by schema regex: {pattern}"


def test_attestation_path_with_rN_suffix():
    """T8 / S2 — A6: docs/features/006-foo-r4.md Iter=4 → docs/reviews/006-foo-r4.review.yaml.

    Filename -rN suffix is stripped before re-applying iteration suffix.
    Iteration value comes from doc metadata (Iteration: field), NOT filename.
    """
    from cli.spec_review import compute_attestation_path

    doc_path = Path("docs/features/006-archive-and-supersession-conventions-r4.md")
    result = compute_attestation_path(doc_path, iteration=4)
    assert result == Path(
        "docs/reviews/006-archive-and-supersession-conventions-r4.review.yaml"
    )
