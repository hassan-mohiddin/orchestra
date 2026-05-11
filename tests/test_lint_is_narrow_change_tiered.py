"""Tests for is_narrow_change tiered extension (LLD-009 r6 T3a-h)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cli.lint import is_narrow_change


SAMPLE_ATTESTATION_MINOR = """schema_version: "1.0"
doc_subject:
  path: docs/features/x.md
gates:
  completeness:
    verdict: pass
    findings:
      - severity: Minor
        location: line 1
        problem: minor fix
  evidence: {verdict: pass, findings: []}
  clarity: {verdict: pass, findings: []}
  consistency: {verdict: pass, findings: []}
overall_verdict: pass
"""

SAMPLE_ATTESTATION_CRITICAL = SAMPLE_ATTESTATION_MINOR.replace("severity: Minor", "severity: Critical")
SAMPLE_ATTESTATION_IMPORTANT = SAMPLE_ATTESTATION_MINOR.replace("severity: Minor", "severity: Important")


def _stage_att(repo: Path, rel_path: str, content: str) -> None:
    full = repo / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True)


def _initial(repo: Path) -> None:
    subprocess.run(["git", "-c", "user.email=t@e", "-c", "user.name=T",
                    "commit", "-m", "seed", "--allow-empty"],
                   cwd=repo, check=True, capture_output=True)


PRIOR_DOC = """# Doc

> **Status:** Implemented

Body.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Initial. |
"""

NEW_DOC_TEMPLATE_MINOR = """# Doc

> **Status:** Implemented

Body MODIFIED.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Initial. |
| 2026-05-11 | Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor) — fixed wording |
"""


def test_l2_detect_path_strict_binary_rejects_body_change() -> None:
    """commit_msg=None → strict-binary path: body change rejects."""
    new_doc = NEW_DOC_TEMPLATE_MINOR
    ok, why = is_narrow_change(PRIOR_DOC, new_doc, commit_msg=None, repo_root=None)
    assert not ok
    assert "body" in why.lower() or "Changelog" in why


def test_tiered_minor_with_addresses_and_changelog_passes(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    _stage_att(tmp_repo, "docs/reviews/008-x-r1.review.yaml", SAMPLE_ATTESTATION_MINOR)
    msg = "docs: address minor\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n"
    ok, why = is_narrow_change(PRIOR_DOC, NEW_DOC_TEMPLATE_MINOR,
                                commit_msg=msg, repo_root=tmp_repo)
    assert ok, f"unexpected fail: {why}"


def test_tiered_critical_rejected_even_with_addresses(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    _stage_att(tmp_repo, "docs/reviews/008-x-r1.review.yaml", SAMPLE_ATTESTATION_CRITICAL)
    new_doc = NEW_DOC_TEMPLATE_MINOR.replace("(Minor)", "(Critical)")
    msg = "feat: address crit\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Critical)\n"
    ok, why = is_narrow_change(PRIOR_DOC, new_doc, commit_msg=msg, repo_root=tmp_repo)
    assert not ok
    assert "Critical" in why


def test_tiered_important_le3_passes(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    # 3 Important findings
    atts = {}
    for i in range(1, 4):
        path = f"docs/reviews/008-x-r{i}.review.yaml"
        _stage_att(tmp_repo, path, SAMPLE_ATTESTATION_IMPORTANT)
        atts[path] = i
    new_doc_lines = (NEW_DOC_TEMPLATE_MINOR.replace("(Minor)", "(Important)")
                     .replace("Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Important) — fixed wording",
                              "Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Important) — fix1\n"
                              "| 2026-05-11 | Addresses: docs/reviews/008-x-r2.review.yaml gate completeness finding 1 (Important) — fix2 |\n"
                              "| 2026-05-11 | Addresses: docs/reviews/008-x-r3.review.yaml gate completeness finding 1 (Important) — fix3"))
    msg = ("docs: address 3 important\n\n"
           "Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Important)\n"
           "Addresses: docs/reviews/008-x-r2.review.yaml gate completeness finding 1 (Important)\n"
           "Addresses: docs/reviews/008-x-r3.review.yaml gate completeness finding 1 (Important)\n")
    ok, why = is_narrow_change(PRIOR_DOC, new_doc_lines, commit_msg=msg, repo_root=tmp_repo)
    assert ok, f"unexpected fail: {why}"


def test_tiered_important_ge4_rejects(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    for i in range(1, 5):
        _stage_att(tmp_repo, f"docs/reviews/008-x-r{i}.review.yaml", SAMPLE_ATTESTATION_IMPORTANT)
    msg = ("docs: address 4 important\n\n"
           "Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Important)\n"
           "Addresses: docs/reviews/008-x-r2.review.yaml gate completeness finding 1 (Important)\n"
           "Addresses: docs/reviews/008-x-r3.review.yaml gate completeness finding 1 (Important)\n"
           "Addresses: docs/reviews/008-x-r4.review.yaml gate completeness finding 1 (Important)\n")
    ok, why = is_narrow_change(PRIOR_DOC, NEW_DOC_TEMPLATE_MINOR.replace("(Minor)", "(Important)"),
                                commit_msg=msg, repo_root=tmp_repo)
    assert not ok
    assert "Important" in why or "threshold" in why


def test_tiered_minor_without_changelog_row_rejects(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    _stage_att(tmp_repo, "docs/reviews/008-x-r1.review.yaml", SAMPLE_ATTESTATION_MINOR)
    # Body modified but no Changelog row added
    new_doc_no_chlog = PRIOR_DOC.replace("Body.", "Body MODIFIED.")
    msg = "docs: address minor\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n"
    ok, why = is_narrow_change(PRIOR_DOC, new_doc_no_chlog, commit_msg=msg, repo_root=tmp_repo)
    assert not ok
    assert "missing_changelog_row" in why


def test_tiered_severity_claim_mismatch_rejects(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    _stage_att(tmp_repo, "docs/reviews/008-x-r1.review.yaml", SAMPLE_ATTESTATION_MINOR)
    msg = "feat: lie about severity\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Important)\n"
    ok, why = is_narrow_change(PRIOR_DOC, NEW_DOC_TEMPLATE_MINOR, commit_msg=msg, repo_root=tmp_repo)
    assert not ok
    assert "severity_mismatch" in why


def test_l2_finalize_no_addresses_lines_rejects(tmp_repo: Path) -> None:
    _initial(tmp_repo)
    msg = "docs: body change without addresses\n"
    ok, why = is_narrow_change(PRIOR_DOC, NEW_DOC_TEMPLATE_MINOR, commit_msg=msg, repo_root=tmp_repo)
    assert not ok
    assert "Addresses" in why


def test_tiered_dedupe_anti_copy_paste(tmp_repo: Path) -> None:
    """Duplicate Addresses: lines for same (path, gate, finding_n) counted once."""
    _initial(tmp_repo)
    _stage_att(tmp_repo, "docs/reviews/008-x-r1.review.yaml", SAMPLE_ATTESTATION_IMPORTANT)
    msg = ("docs: dup addresses\n\n" +
           "Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Important)\n" * 6)
    new_doc = NEW_DOC_TEMPLATE_MINOR.replace("(Minor)", "(Important)")
    ok, why = is_narrow_change(PRIOR_DOC, new_doc, commit_msg=msg, repo_root=tmp_repo)
    # 6x duplicate dedupes to 1 Important → passes threshold (≤3); single Changelog row OK
    assert ok, f"unexpected fail (dedupe should have lowered count to 1): {why}"
