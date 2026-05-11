"""L5 strict-enum-match lint check — canon §4.5 + §4.1 + §4.3 (slice 5).

Validates metadata enum values against canon. Status + Severity-by-doc-type.
Only fires on types in STATUS_ENUMS (feature/bug/adr/postmortem/runbook/design);
plan/research/investigation/policy pass through.

Value parsing: first token (split on first whitespace/paren) — so
`Severity: SEV3 (process incident — …)` matches enum value `SEV3`.
"""

from __future__ import annotations

from pathlib import Path

from cli.lint import lint_strict_enum_match


_META_BUG = (
    "# Bug — L5 test\n\n"
    "> **Doc ID:** BUG-999-l5\n"
    "> **Date:** 2026-05-11\n"
)
_META_POSTMORTEM = (
    "# Postmortem — L5 test\n\n"
    "> **Doc ID:** POSTMORTEM-2026-05-11-l5\n"
    "> **Date:** 2026-05-11\n"
)
_META_RUNBOOK = (
    "# Runbook — L5 test\n\n"
    "> **Doc ID:** RUNBOOK-l5\n"
    "> **Date:** 2026-05-11\n"
)
_META_FEATURE = (
    "# Feature — L5 test\n\n"
    "> **Doc ID:** 999-l5\n"
    "> **Date:** 2026-05-11\n"
)
_META_DESIGN = (
    "# Design — L5 test\n\n"
    "> **Doc ID:** l5-test\n"
    "> **Date:** 2026-05-11\n"
)


def _doc(tmp_path: Path, subdir: str, name: str, body: str) -> Path:
    p = tmp_path / "docs" / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    return p


def _has_invalid(findings, field: str) -> bool:
    return any(f"invalid {field}" in f.message.lower() for f in findings)


# ---------------------------------------------------------------------------
# Status enum strict match
# ---------------------------------------------------------------------------


def test_feature_valid_status(tmp_path):
    body = _META_FEATURE + "> **Status:** Approved\n"
    p = _doc(tmp_path, "features", "999-ok.md", body)
    assert lint_strict_enum_match(p) == []


def test_feature_invalid_status(tmp_path):
    body = _META_FEATURE + "> **Status:** Frobulating\n"
    p = _doc(tmp_path, "features", "999-bad.md", body)
    findings = lint_strict_enum_match(p)
    assert _has_invalid(findings, "status")


def test_design_invalid_status(tmp_path):
    body = _META_DESIGN + "> **Status:** Draft\n"  # design has no Draft
    p = _doc(tmp_path, "design", "bad-status.md", body)
    findings = lint_strict_enum_match(p)
    assert _has_invalid(findings, "status")


def test_status_with_trailing_comment_accepted(tmp_path):
    body = _META_FEATURE + "> **Status:** Approved       # narrow-change edit allowed\n"
    p = _doc(tmp_path, "features", "999-tcomment.md", body)
    assert lint_strict_enum_match(p) == []


# ---------------------------------------------------------------------------
# Severity enum strict match — bug
# ---------------------------------------------------------------------------


def test_bug_valid_severity_critical(tmp_path):
    body = _META_BUG + "> **Status:** Investigating\n> **Severity:** Critical\n"
    p = _doc(tmp_path, "bugs", "BUG-999-ok.md", body)
    assert lint_strict_enum_match(p) == []


def test_bug_invalid_severity_veryhigh(tmp_path):
    body = _META_BUG + "> **Status:** Investigating\n> **Severity:** VeryHigh\n"
    p = _doc(tmp_path, "bugs", "BUG-999-bad.md", body)
    findings = lint_strict_enum_match(p)
    assert _has_invalid(findings, "severity")


# ---------------------------------------------------------------------------
# Severity enum strict match — postmortem (SEV1-4 axis)
# ---------------------------------------------------------------------------


def test_postmortem_valid_severity_sev2(tmp_path):
    body = _META_POSTMORTEM + "> **Status:** Draft\n> **Severity:** SEV2\n"
    p = _doc(tmp_path, "postmortems", "POSTMORTEM-2026-05-11-ok.md", body)
    assert lint_strict_enum_match(p) == []


def test_postmortem_severity_with_descriptive_parenthetical_accepted(tmp_path):
    body = _META_POSTMORTEM + (
        "> **Status:** Draft\n"
        "> **Severity:** SEV3 (process incident — no production user impact)\n"
    )
    p = _doc(tmp_path, "postmortems", "POSTMORTEM-2026-05-11-paren.md", body)
    assert lint_strict_enum_match(p) == []


def test_postmortem_invalid_severity_critical(tmp_path):
    body = _META_POSTMORTEM + "> **Status:** Draft\n> **Severity:** Critical\n"
    p = _doc(tmp_path, "postmortems", "POSTMORTEM-2026-05-11-bad.md", body)
    findings = lint_strict_enum_match(p)
    assert _has_invalid(findings, "severity")


# ---------------------------------------------------------------------------
# Severity enum strict match — runbook (page-priority axis)
# ---------------------------------------------------------------------------


def test_runbook_valid_severity_p1(tmp_path):
    body = _META_RUNBOOK + "> **Status:** Current\n> **Severity:** P1\n"
    p = _doc(tmp_path, "runbooks", "RUNBOOK-ok.md", body)
    assert lint_strict_enum_match(p) == []


def test_runbook_invalid_severity_sev1(tmp_path):
    body = _META_RUNBOOK + "> **Status:** Current\n> **Severity:** SEV1\n"
    p = _doc(tmp_path, "runbooks", "RUNBOOK-bad.md", body)
    findings = lint_strict_enum_match(p)
    assert _has_invalid(findings, "severity")


# ---------------------------------------------------------------------------
# Severity absent: pass (severity is optional metadata in canon §4.3)
# ---------------------------------------------------------------------------


def test_severity_absent_on_feature_passes(tmp_path):
    body = _META_FEATURE + "> **Status:** Approved\n"
    p = _doc(tmp_path, "features", "999-nosev.md", body)
    assert lint_strict_enum_match(p) == []


# ---------------------------------------------------------------------------
# Skip rules (canon §4.5 lint behavior block)
# ---------------------------------------------------------------------------


def test_l5_skips_non_typed_doc(tmp_path):
    # Path with no recognized doc-type segment
    p = tmp_path / "random" / "thing.md"
    p.parent.mkdir(parents=True)
    p.write_text("# random\n> **Status:** Anything\n")
    assert lint_strict_enum_match(p) == []
