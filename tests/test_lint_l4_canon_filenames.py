"""L4 — bare-name design + POSTMORTEM/RUNBOOK filename grammar (BUG-014 closure).

Slice 4 of the vocab-canon migration. Canon source:
`docs/design/controlled-vocabulary.md § 4.10`.

Adds three new grammar variants to `lint_doc_id_burn`:
- design bare-name: `name.md` first-iter; `name-rN.md` supersession
- postmortem: `POSTMORTEM-YYYY-MM-DD-name.md`; `…-rN.md` supersession
- runbook: `RUNBOOK-name.md`; `RUNBOOK-name-rN.md` supersession

Existing NNN-name / BUG-NNN-name shapes unchanged.
"""

from __future__ import annotations

from pathlib import Path

from cli.lint import lint_doc_id_burn


def _mk(root: Path, *segments: str) -> Path:
    p = root.joinpath(*segments)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# stub\n")
    return p


# ---------------------------------------------------------------------------
# Design bare-name first-iter
# ---------------------------------------------------------------------------


def test_design_bare_name_first_iter_accepted(tmp_path):
    new_doc = _mk(tmp_path, "docs", "design", "vocabulary-canon.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


# ---------------------------------------------------------------------------
# ADR-NNN-name first-iter + supersession (post-BUG-013 gap closure)
# ---------------------------------------------------------------------------


def test_adr_first_iter_accepted(tmp_path):
    """First-iter ADR with strictly-greater id passes."""
    _mk(tmp_path, "docs", "adr", "ADR-001-foo.md")
    new_doc = _mk(tmp_path, "docs", "adr", "ADR-002-bar.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_adr_first_iter_duplicate_id_rejected(tmp_path):
    """First-iter ADR reusing existing id is rejected."""
    _mk(tmp_path, "docs", "adr", "ADR-001-foo.md")
    new_doc = _mk(tmp_path, "docs", "adr", "ADR-001-collision.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings, "expected duplicate-id rejection"
    assert any("reuses existing or burned id" in f.message for f in findings)


def test_adr_supersession_accepted(tmp_path):
    """Supersession-iteration ADR with base + valid r passes."""
    _mk(tmp_path, "docs", "adr", "ADR-001-foo.md")
    new_doc = _mk(tmp_path, "docs", "adr", "ADR-001-foo-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_adr_supersession_without_base_rejected(tmp_path):
    """Supersession-iteration ADR with no base anywhere rejected."""
    new_doc = _mk(tmp_path, "docs", "adr", "ADR-099-orphan-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings, "expected supersession-without-base rejection"
    assert any("does not exist" in f.message for f in findings)


def test_adr_filename_invalid_rejected(tmp_path):
    """ADR file with malformed name rejected with clear ADR-pattern message."""
    new_doc = _mk(tmp_path, "docs", "adr", "ADR-bogus-no-number.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings, "expected pattern-mismatch rejection"


def test_design_bare_name_supersession_accepted(tmp_path):
    # First-iter base must exist for supersession to be valid.
    _mk(tmp_path, "docs", "design", "vocabulary-canon.md")
    new_doc = _mk(tmp_path, "docs", "design", "vocabulary-canon-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_design_bare_name_supersession_without_base_rejected(tmp_path):
    new_doc = _mk(tmp_path, "docs", "design", "orphan-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings, "expected supersession-without-base finding"
    assert any("does not exist" in f.message for f in findings)


def test_design_bare_name_supersession_reusing_r_rejected(tmp_path):
    _mk(tmp_path, "docs", "design", "phil.md")
    _mk(tmp_path, "docs", "design", "phil-r2.md")
    new_doc = _mk(tmp_path, "docs", "design", "phil-r2.md")
    # The above _mk overwrites, so create a new one in archive
    _mk(tmp_path, "docs", "archive", "design", "phil-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings, "expected r-suffix reuse finding"


# ---------------------------------------------------------------------------
# Postmortem first-iter + supersession
# ---------------------------------------------------------------------------


def test_postmortem_first_iter_accepted(tmp_path):
    new_doc = _mk(tmp_path, "docs", "postmortems", "POSTMORTEM-2026-05-06-auth-leak.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_postmortem_supersession_accepted(tmp_path):
    _mk(tmp_path, "docs", "postmortems", "POSTMORTEM-2026-05-06-auth-leak.md")
    new_doc = _mk(tmp_path, "docs", "postmortems", "POSTMORTEM-2026-05-06-auth-leak-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_postmortem_supersession_without_base_rejected(tmp_path):
    new_doc = _mk(tmp_path, "docs", "postmortems", "POSTMORTEM-2026-05-06-orphan-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings, "expected supersession-without-base finding"


# ---------------------------------------------------------------------------
# Runbook first-iter + supersession
# ---------------------------------------------------------------------------


def test_runbook_first_iter_accepted(tmp_path):
    new_doc = _mk(tmp_path, "docs", "runbooks", "RUNBOOK-celery-queue.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_runbook_supersession_accepted(tmp_path):
    _mk(tmp_path, "docs", "runbooks", "RUNBOOK-celery-queue.md")
    new_doc = _mk(tmp_path, "docs", "runbooks", "RUNBOOK-celery-queue-r2.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


# ---------------------------------------------------------------------------
# Existing NNN- and BUG-NNN- shapes unchanged
# ---------------------------------------------------------------------------


def test_feature_nnn_first_iter_still_accepted(tmp_path):
    new_doc = _mk(tmp_path, "docs", "features", "001-foo.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_bug_nnn_first_iter_still_accepted(tmp_path):
    new_doc = _mk(tmp_path, "docs", "bugs", "BUG-001-foo.md")
    findings = lint_doc_id_burn(new_doc, tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


# ---------------------------------------------------------------------------
# Real canon doc passes (regression — BUG-014 was the chicken-and-egg)
# ---------------------------------------------------------------------------


def test_real_canon_doc_passes(tmp_path):
    """Smoke: against the actual orchestra repo root, the canon Design Doc
    filename passes L4."""
    import subprocess
    repo_root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip())
    canon_doc = repo_root / "docs" / "design" / "controlled-vocabulary.md"
    assert canon_doc.exists()
    findings = lint_doc_id_burn(canon_doc, repo_root)
    assert findings == [], f"expected no findings on canon doc, got: {[f.message for f in findings]}"
