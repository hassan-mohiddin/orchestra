"""Tests for _verify_finding_in_attestation (LLD-009 r6 T4a-h)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cli.lint import _verify_finding_in_attestation


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True)


def _commit_attestation(repo: Path, rel_path: str, content: str) -> None:
    full = repo / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True)


def _initial_commit(repo: Path) -> None:
    subprocess.run(["git", "-c", "user.email=t@e", "-c", "user.name=T",
                    "commit", "-m", "seed", "--allow-empty"],
                   cwd=repo, check=True, capture_output=True)


SAMPLE_ATTESTATION = """schema_version: "1.0"
doc_subject:
  path: docs/features/x.md
gates:
  completeness:
    verdict: pass
    findings:
      - severity: Minor
        location: line 1
        problem: minor wording fix
      - severity: Important
        location: line 2
        problem: important issue
  evidence:
    verdict: pass
    findings: []
  clarity:
    verdict: pass
    findings: []
  consistency:
    verdict: pass
    findings: []
overall_verdict: pass
"""


def test_severity_match_staged(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/008-x-r1.review.yaml", SAMPLE_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/008-x-r1.review.yaml", "completeness", 1, "Minor",
    )
    assert ok, f"unexpected fail: {why}"


def test_severity_mismatch(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.review.yaml", SAMPLE_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.review.yaml", "completeness", 1, "Important",
    )
    assert not ok
    assert "severity_mismatch" in why


def test_out_of_range_finding_n(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.review.yaml", SAMPLE_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.review.yaml", "completeness", 99, "Minor",
    )
    assert not ok
    assert "finding_n_out_of_range" in why


def test_missing_attestation_not_staged(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/missing.review.yaml", "completeness", 1, "Minor",
    )
    assert not ok
    assert "attestation_not_staged" in why or "attestation_read_error" in why


def test_path_traversal_rejected(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/../../etc/passwd", "completeness", 1, "Minor",
    )
    assert not ok


def test_path_prefix_confusion_rejected(tmp_repo: Path) -> None:
    """`docs/reviews_evil/` must NOT pass containment (defense-in-depth at A4)."""
    _initial_commit(tmp_repo)
    (tmp_repo / "docs" / "reviews_evil").mkdir(parents=True)
    fake = tmp_repo / "docs" / "reviews_evil" / "x.review.yaml"
    fake.write_text(SAMPLE_ATTESTATION)
    subprocess.run(["git", "add", str(fake.relative_to(tmp_repo))], cwd=tmp_repo, check=True)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews_evil/x.review.yaml", "completeness", 1, "Minor",
    )
    assert not ok
    assert "outside_docs_reviews" in why


def test_unknown_gate_rejected(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.review.yaml", SAMPLE_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.review.yaml", "banana", 1, "Minor",
    )
    assert not ok
    assert "unknown_gate" in why


def test_working_tree_attestation_with_downgrade_rejected(tmp_repo: Path) -> None:
    """T4h: attestation on working-tree only (not staged) with downgraded severity → reject.

    Closes codex r2 CRITICAL trust-boundary break: attestation read MUST be from
    staged content, not working-tree, else author can keep unstaged downgrade.
    """
    _initial_commit(tmp_repo)
    # Stage attestation with Important severity
    important_att = SAMPLE_ATTESTATION.replace("severity: Minor", "severity: Important", 1)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.review.yaml", important_att)
    # Working-tree edit: downgrade to Minor WITHOUT staging
    (tmp_repo / "docs/reviews/x-r1.review.yaml").write_text(SAMPLE_ATTESTATION)
    # Claimed severity Minor matches WORKING-TREE but NOT staged content
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.review.yaml", "completeness", 1, "Minor",
    )
    # Staged content has Important → claim of Minor must reject
    assert not ok
    assert "severity_mismatch" in why


# ---------------------------------------------------------------------------
# BUG-018 — v2.0+ attestation schema_version branch
# ---------------------------------------------------------------------------


SAMPLE_V2_ATTESTATION = """schema_version: "2.0"
doc_subject:
  path: docs/features/x.md
  iteration: 1
sub_judges:
  - id: structure
    model: claude-sonnet-4-6
    mandatory: false
    status: completed
    verdict: pass
    findings: []
  - id: semantic
    model: claude-opus-4-7
    mandatory: true
    status: completed
    verdict: conditional_pass
    findings:
      - severity: Important
        location: "Section A"
        problem: "needs more detail"
        raised_by: [semantic]
        scope: instance
      - severity: Minor
        location: "Section B"
        problem: "small wording fix"
        raised_by: [semantic]
        scope: instance
  - id: adversarial
    model: claude-opus-4-7
    mandatory: true
    status: completed
    verdict: pass
    findings: []
findings_aggregated: []
overall_verdict: conditional_pass
"""


def test_v2_happy_path_sub_judge_semantic(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
                        SAMPLE_V2_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
        "semantic", 1, "Important",
    )
    assert ok, f"unexpected fail: {why}"


def test_v2_unknown_gate_v1_name_on_v2_att(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
                        SAMPLE_V2_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
        "evidence", 1, "Important",
    )
    assert not ok
    assert "v2" in why.lower() or "sub-judge" in why.lower(), why


def test_v2_finding_n_out_of_range(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
                        SAMPLE_V2_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
        "semantic", 99, "Important",
    )
    assert not ok
    assert "out_of_range" in why
    assert "v2" in why.lower(), why


def test_v2_schema_version_variant_200(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    att = SAMPLE_V2_ATTESTATION.replace('"2.0"', '"2.0.0"')
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml", att)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
        "semantic", 1, "Important",
    )
    assert ok, f"'2.0.0' variant must match v2 path: {why}"


def test_v2_schema_version_variant_21(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    att = SAMPLE_V2_ATTESTATION.replace('"2.0"', '"2.1"')
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml", att)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
        "semantic", 1, "Important",
    )
    assert ok, f"'2.1' must use v2 path: {why}"


def test_unknown_schema_version_v3_fail_closed(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    att = SAMPLE_V2_ATTESTATION.replace('"2.0"', '"3.0"')
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml", att)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.orchestra.review.yaml",
        "semantic", 1, "Important",
    )
    assert not ok
    assert "unknown_schema_version" in why, why
    assert "3.0" in why or "3" in why, why


def test_v1_regression_still_passes_after_branch(tmp_repo: Path) -> None:
    _initial_commit(tmp_repo)
    _commit_attestation(tmp_repo, "docs/reviews/x-r1.review.yaml", SAMPLE_ATTESTATION)
    ok, why = _verify_finding_in_attestation(
        tmp_repo, "docs/reviews/x-r1.review.yaml",
        "completeness", 1, "Minor",
    )
    assert ok, f"v1 regression: {why}"
