"""LLD-009 r6 — L2-detect + L2-finalize + STRICT + BYPASS + pre-stage-check.

Covers T1a-e (Slice 2.5), T2a-h + T10a-g + T11 (Slice 2.6), T10b-strict-a/b/c
(Slice 2.7), T9a-c (Slice 2.8).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from cli.lint import (
    _is_ci_environment,
    _pending_file_path,
    lint_commit_msg_finalize,
    lint_pre_stage_check,
    lint_staged,
)


SAMPLE_ATTESTATION_MINOR = """schema_version: "1.0"
doc_subject:
  path: docs/features/x.md
gates:
  completeness:
    verdict: pass
    findings:
      - severity: Minor
        location: line 1
        problem: minor wording
  evidence: {verdict: pass, findings: []}
  clarity: {verdict: pass, findings: []}
  consistency: {verdict: pass, findings: []}
overall_verdict: pass
"""


PRIOR_DOC = """# Doc

> **Status:** Implemented

Body.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Initial. |
"""


NEW_DOC_MINOR = """# Doc

> **Status:** Implemented

Body MODIFIED.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Initial. |
| 2026-05-11 | Addresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor) — fixed wording |
"""


def _commit(repo: Path, msg: str = "seed") -> None:
    subprocess.run(["git", "-c", "user.email=t@e", "-c", "user.name=T",
                    "commit", "-m", msg, "--allow-empty"],
                   cwd=repo, check=True, capture_output=True)


def _seed_canon_doc(repo: Path, rel_path: str = "docs/features/x.md") -> None:
    full = repo / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(PRIOR_DOC)
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True)
    _commit(repo, "seed canon doc")


def _stage_att(repo: Path, rel_path: str = "docs/reviews/008-x-r1.review.yaml",
               content: str = SAMPLE_ATTESTATION_MINOR) -> None:
    full = repo / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True)


def _stage_doc_modification(repo: Path, rel_path: str = "docs/features/x.md",
                             content: str = NEW_DOC_MINOR) -> None:
    (repo / rel_path).write_text(content)
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True)


# ============================================================================
# Slice 2.5 — L2-detect (writes pending file)
# ============================================================================


def test_t1a_pending_truncated_at_pre_commit_start(tmp_repo: Path) -> None:
    """T1a: pending file truncated at pre-commit start."""
    _seed_canon_doc(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text("stale entry from prior run\n")
    lint_staged(tmp_repo)
    # After lint_staged, pending should be truncated (no staged changes → empty)
    assert pending.read_text() == ""


def test_t1b_pending_appended_per_canon_inplace_candidate(tmp_repo: Path) -> None:
    """T1b: pending file appended per canon-inplace candidate."""
    _seed_canon_doc(tmp_repo)
    _stage_doc_modification(tmp_repo)
    lint_staged(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    content = pending.read_text()
    assert "docs/features/x.md" in content


def test_t1c_pending_tab_separated_sha_path(tmp_repo: Path) -> None:
    """T1c: pending entries in `<sha>\\t<path>` tab-separated format."""
    _seed_canon_doc(tmp_repo)
    _stage_doc_modification(tmp_repo)
    lint_staged(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    lines = [ln for ln in pending.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1
    sha, path = lines[0].split("\t", 1)
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)
    assert path == "docs/features/x.md"


def test_t1d_pre_commit_does_not_block_when_pending_non_empty(tmp_repo: Path) -> None:
    """T1d: pre-commit pass (no findings) even when pending non-empty."""
    _seed_canon_doc(tmp_repo)
    _stage_doc_modification(tmp_repo)
    findings = lint_staged(tmp_repo)
    # No L2-detect findings should be raised (annotate-only)
    l2_findings = [f for f in findings if "narrow" in f.message.lower() or "canon-frozen" in f.message.lower()]
    assert not l2_findings, f"L2-detect should not block: {l2_findings}"


def test_t1e_worktree_path_resolution(tmp_repo: Path) -> None:
    """T1e: pending file path resolved via `git rev-parse --git-path`."""
    pending = _pending_file_path(tmp_repo)
    assert pending.is_absolute()
    # Should land under .git/ for standard repo
    assert ".git" in str(pending)


# ============================================================================
# Slice 2.6 — L2-finalize + ORCHESTRA_BYPASS + transactional cleanup
# ============================================================================


def _write_msg(tmp_path: Path, body: str) -> str:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(body)
    return str(msg_file)


def _setup_canon_inplace_commit(tmp_repo: Path) -> str:
    """Seed canon doc + stage attestation + stage doc modification + write pending; return msg path."""
    _seed_canon_doc(tmp_repo)
    _stage_att(tmp_repo)
    _stage_doc_modification(tmp_repo)
    lint_staged(tmp_repo)  # writes pending
    return ""


def test_t2a_pending_matches_sha_proceeds(tmp_repo: Path, tmp_path: Path,
                                            monkeypatch) -> None:
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    monkeypatch.delenv("ORCHESTRA_BYPASS", raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    msg = _write_msg(
        tmp_path,
        "docs: minor fix\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n",
    )
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 0


def test_t2b_staged_drift_rejects(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    # Drift: modify staged content after pending written
    (tmp_repo / "docs/features/x.md").write_text(NEW_DOC_MINOR + "\nadditional drift\n")
    subprocess.run(["git", "add", "docs/features/x.md"], cwd=tmp_repo, check=True)
    msg = _write_msg(
        tmp_path,
        "docs: drift\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n",
    )
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 1


def test_t2c_cleanup_on_success(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    assert pending.exists()
    msg = _write_msg(
        tmp_path,
        "docs: ok\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n",
    )
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 0
    assert not pending.exists(), "pending should be unlinked on success"


def test_t2e_pending_absent_fail_open(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    """T2e: pending absent + no STRICT → fail-open pass."""
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    monkeypatch.delenv("ORCHESTRA_BYPASS", raising=False)
    _seed_canon_doc(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    if pending.exists():
        pending.unlink()
    msg = _write_msg(tmp_path, "docs: nothing\n")
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 0


def test_t2f_double_fire_does_not_false_reject(tmp_repo: Path, tmp_path: Path,
                                                  monkeypatch) -> None:
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    msg = _write_msg(
        tmp_path,
        "docs: ok\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n",
    )
    rc1 = lint_commit_msg_finalize(msg, tmp_repo)
    rc2 = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc1 == 0 and rc2 == 0


def test_t2g_reject_preserves_pending_for_retry(tmp_repo: Path, tmp_path: Path,
                                                   monkeypatch) -> None:
    """T2h: reject-then-retry: rc=1 leaves pending intact (transactional)."""
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    pending_content_before = pending.read_text()
    # No Addresses: line → reject
    msg = _write_msg(tmp_path, "docs: no addresses\n")
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 1
    assert pending.exists(), "pending should be preserved on reject"
    assert pending.read_text() == pending_content_before


def test_t2h_retry_with_valid_msg_succeeds_and_cleans_up(
    tmp_repo: Path, tmp_path: Path, monkeypatch,
) -> None:
    """T2h continued: retry with valid msg → rc=0 → cleanup happens."""
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    bad_msg = _write_msg(tmp_path, "docs: bad\n")
    rc1 = lint_commit_msg_finalize(bad_msg, tmp_repo)
    assert rc1 == 1
    good_msg = _write_msg(
        tmp_path,
        "docs: fix\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n",
    )
    rc2 = lint_commit_msg_finalize(good_msg, tmp_repo)
    assert rc2 == 0
    assert not _pending_file_path(tmp_repo).exists()


def test_t10a_bypass_valid_path(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    """T10a: ORCHESTRA_BYPASS=1 + Bypass: annotation + non-CI → skip + audit + rc=0."""
    monkeypatch.setenv("ORCHESTRA_BYPASS", "1")
    for v in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "CIRCLECI", "TRAVIS", "JENKINS_URL"):
        monkeypatch.delenv(v, raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    msg = _write_msg(
        tmp_path,
        "docs: bypass\n\nBypass: emergency fix per oncall\n",
    )
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 0
    # Audit log written
    audit_path = subprocess.check_output(
        ["git", "rev-parse", "--git-path", "orchestra-bypass-audit.log"],
        cwd=tmp_repo, text=True,
    ).strip()
    audit_file = Path(audit_path)
    if not audit_file.is_absolute():
        audit_file = tmp_repo / audit_file
    assert audit_file.exists()
    log = audit_file.read_text()
    cols = log.strip().split("\t")
    assert len(cols) == 5, f"expected 5 TAB-cols got {len(cols)}: {cols!r}"


def test_t10e_bypass_in_ci_rejected(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    """T10e: CI=true → ORCHESTRA_BYPASS REJECTED."""
    monkeypatch.setenv("ORCHESTRA_BYPASS", "1")
    monkeypatch.setenv("CI", "true")
    _setup_canon_inplace_commit(tmp_repo)
    msg = _write_msg(tmp_path, "docs: bypass\n\nBypass: emergency\n")
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 1


def test_t10f_bypass_missing_annotation_rejected(tmp_repo: Path, tmp_path: Path,
                                                     monkeypatch) -> None:
    """T10f: ORCHESTRA_BYPASS=1 + no Bypass: annotation → REJECT."""
    monkeypatch.setenv("ORCHESTRA_BYPASS", "1")
    for v in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "CIRCLECI", "TRAVIS", "JENKINS_URL"):
        monkeypatch.delenv(v, raising=False)
    _setup_canon_inplace_commit(tmp_repo)
    msg = _write_msg(tmp_path, "docs: no reason\n")
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 1


def test_t10g_multi_var_ci_detection(monkeypatch) -> None:
    """T10g: GITHUB_ACTIONS=true alone → _is_ci_environment returns True."""
    for v in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "CIRCLECI", "TRAVIS", "JENKINS_URL"):
        monkeypatch.delenv(v, raising=False)
    is_ci, _ = _is_ci_environment()
    assert not is_ci
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    is_ci, vars_set = _is_ci_environment()
    assert is_ci
    assert "GITHUB_ACTIONS" in vars_set


def test_t11_commit_msg_arg_required(tmp_repo: Path) -> None:
    """T11: commit-msg without msg-file → fail-closed rc=1."""
    rc = lint_commit_msg_finalize("", tmp_repo)
    assert rc == 1


# ============================================================================
# Slice 2.7 — ORCHESTRA_STRICT opt-in
# ============================================================================


def test_strict_a_no_pending_recompute_passes(tmp_repo: Path, tmp_path: Path,
                                                  monkeypatch) -> None:
    """STRICT=1 + no pending + valid Addresses: → recompute + pass."""
    monkeypatch.setenv("ORCHESTRA_STRICT", "1")
    monkeypatch.delenv("ORCHESTRA_BYPASS", raising=False)
    _seed_canon_doc(tmp_repo)
    _stage_att(tmp_repo)
    _stage_doc_modification(tmp_repo)
    # Do NOT call lint_staged — pending intentionally absent
    pending = _pending_file_path(tmp_repo)
    if pending.exists():
        pending.unlink()
    msg = _write_msg(
        tmp_path,
        "docs: strict ok\n\nAddresses: docs/reviews/008-x-r1.review.yaml gate completeness finding 1 (Minor)\n",
    )
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 0


def test_strict_b_no_pending_missing_addresses_rejects(tmp_repo: Path, tmp_path: Path,
                                                          monkeypatch) -> None:
    """STRICT=1 + no pending + missing Addresses: → reject."""
    monkeypatch.setenv("ORCHESTRA_STRICT", "1")
    monkeypatch.delenv("ORCHESTRA_BYPASS", raising=False)
    _seed_canon_doc(tmp_repo)
    _stage_doc_modification(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    if pending.exists():
        pending.unlink()
    msg = _write_msg(tmp_path, "docs: no addresses\n")
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 1


def test_strict_c_unset_no_pending_fail_open(tmp_repo: Path, tmp_path: Path,
                                                 monkeypatch) -> None:
    """STRICT unset + no pending → fail-open pass (default A2)."""
    monkeypatch.delenv("ORCHESTRA_STRICT", raising=False)
    monkeypatch.delenv("ORCHESTRA_BYPASS", raising=False)
    _seed_canon_doc(tmp_repo)
    _stage_doc_modification(tmp_repo)
    pending = _pending_file_path(tmp_repo)
    if pending.exists():
        pending.unlink()
    msg = _write_msg(tmp_path, "docs: anything\n")
    rc = lint_commit_msg_finalize(msg, tmp_repo)
    assert rc == 0


# ============================================================================
# Slice 2.8 — pre-stage-check
# ============================================================================


def test_t9a_pre_stage_clean_draft_passes(tmp_repo: Path) -> None:
    _seed_canon_doc(tmp_repo)
    _stage_att(tmp_repo)
    # Working-tree-only edit (not staged) — pre-stage-check uses working tree
    (tmp_repo / "docs/features/x.md").write_text(NEW_DOC_MINOR)
    msg = ("docs: minor\n\nAddresses: docs/reviews/008-x-r1.review.yaml "
           "gate completeness finding 1 (Minor)\n")
    rc = lint_pre_stage_check("docs/features/x.md", msg, tmp_repo)
    assert rc == 0


def test_t9b_pre_stage_missing_addresses_rejects(tmp_repo: Path) -> None:
    _seed_canon_doc(tmp_repo)
    (tmp_repo / "docs/features/x.md").write_text(NEW_DOC_MINOR)
    rc = lint_pre_stage_check("docs/features/x.md", "docs: bad\n", tmp_repo)
    assert rc == 1


def test_t9c_pre_stage_critical_bypass_rejects(tmp_repo: Path) -> None:
    _seed_canon_doc(tmp_repo)
    crit_att = SAMPLE_ATTESTATION_MINOR.replace("severity: Minor", "severity: Critical")
    _stage_att(tmp_repo, content=crit_att)
    crit_doc = NEW_DOC_MINOR.replace("(Minor)", "(Critical)")
    (tmp_repo / "docs/features/x.md").write_text(crit_doc)
    msg = ("docs: try crit\n\nAddresses: docs/reviews/008-x-r1.review.yaml "
           "gate completeness finding 1 (Critical)\n")
    rc = lint_pre_stage_check("docs/features/x.md", msg, tmp_repo)
    assert rc == 1


# ============================================================================
# Slice 2.9 — commit-msg.sh template content (T12)
# ============================================================================


def test_t12_commit_msg_sh_template_content() -> None:
    template = (Path(__file__).resolve().parent.parent
                / "skills/commit/templates/commit-msg.sh")
    text = template.read_text()
    lines = text.splitlines()
    assert lines[0] == "#!/usr/bin/env bash"
    assert "orchestra" in lines[1].lower()
    assert "set -euo pipefail" in text
    assert "Refs: docs/" in text
    assert "--commit-msg-finalize" in text


# ============================================================================
# Slice 2.10 — pre-commit.sh template content (T13-pre)
# ============================================================================


def test_t13_pre_commit_sh_template_content() -> None:
    template = (Path(__file__).resolve().parent.parent
                / "skills/commit/templates/pre-commit.sh")
    text = template.read_text()
    lines = text.splitlines()
    assert lines[0] == "#!/usr/bin/env bash"
    assert "orchestra" in lines[1].lower()
    assert "cli.lint --pre-commit" in text


# ============================================================================
# Slice 2.11 — SKILL.md pre-stage checklist (T8)
# ============================================================================


def test_t8_skill_md_pre_stage_checklist_present() -> None:
    skill_md = (Path(__file__).resolve().parent.parent
                / "skills/commit/SKILL.md")
    text = skill_md.read_text()
    assert "Pre-stage checklist" in text
    assert "canon-frozen" in text.lower()
    assert "Addresses:" in text
    assert "Commit attestation YAML FIRST" in text or "commit attestation" in text.lower()
