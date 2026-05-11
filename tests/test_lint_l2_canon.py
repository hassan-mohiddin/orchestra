"""L2 lint against canon §4.8 with tolerant prefix-match + conditional handling.

Slice 3 of the vocab-canon migration. Source of truth:
`docs/design/controlled-vocabulary.md § 4.8`.

Algorithm:
- Extract every `## …` / `### …` heading from doc.
- Strip leading number prefix (`4.1 `, `1. `).
- A canon required section is satisfied iff some heading matches via
  bidirectional word-boundary prefix (heading prefix-of canon, or canon
  prefix-of heading; boundary = end-of-string or non-alnum char).
- A canon section ending in `(if any)` / `(where applicable)` / `(optional)`
  may be absent — accept as conditional.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.lint import lint_doc

# Minimal valid metadata block; lint_doc requires Doc ID / Date / Status keys.
_META_FEATURE = (
    "# Feature LLD — Tolerant L2 Test\n\n"
    "> **Doc ID:** 999-tolerant-l2-test\n"
    "> **Date:** 2026-05-11\n"
    "> **Status:** Draft\n\n"
)
_META_BUG = (
    "# Bug Report — Tolerant L2 Test\n\n"
    "> **Doc ID:** BUG-999-tolerant\n"
    "> **Date:** 2026-05-11\n"
    "> **Status:** Investigating\n\n"
)
_META_ADR = (
    "# ADR — Tolerant L2 Test\n\n"
    "> **Doc ID:** ADR-999-tolerant\n"
    "> **Date:** 2026-05-11\n"
    "> **Status:** Proposed\n\n"
)
_META_POSTMORTEM = (
    "# Postmortem — Tolerant L2 Test\n\n"
    "> **Doc ID:** POSTMORTEM-2026-05-11-tolerant\n"
    "> **Date:** 2026-05-11\n"
    "> **Status:** Draft\n\n"
)
_META_RUNBOOK = (
    "# Runbook — Tolerant L2 Test\n\n"
    "> **Doc ID:** RUNBOOK-tolerant\n"
    "> **Date:** 2026-05-11\n"
    "> **Status:** Current\n\n"
)
_META_DESIGN = (
    "# Design — Tolerant L2 Test\n\n"
    "> **Doc ID:** tolerant-l2-test\n"
    "> **Date:** 2026-05-11\n"
    "> **Status:** Current\n\n"
)


def _has_missing_section(findings, section_name: str) -> bool:
    return any(
        "missing required section" in f.message and section_name in f.message
        for f in findings
    )


def _no_section_findings(findings) -> bool:
    return not any("missing required section" in f.message for f in findings)


def _doc(tmp_path: Path, subdir: str, name: str, body: str) -> Path:
    p = tmp_path / "docs" / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    return p


# ---------------------------------------------------------------------------
# Strict canon match works
# ---------------------------------------------------------------------------


def test_feature_with_all_strict_canon_sections_passes(tmp_path):
    body = _META_FEATURE + (
        "## Problem Statement\nx\n"
        "## Success Criteria\nx\n"
        "## Scope\nx\n"
        "## Design\nx\n"
        "## Edge Cases & Error Handling\nx\n"
        "## Security Considerations\nx\n"
        "## Testing Strategy\nx\n"
        "## Related Documents\nx\n"
        "## Changelog\nx\n"
    )
    p = _doc(tmp_path, "features", "999-tolerant.md", body)
    assert _no_section_findings(lint_doc(p))


# ---------------------------------------------------------------------------
# Grandfathered short forms (back-compat)
# ---------------------------------------------------------------------------


def test_feature_grandfather_security_satisfies_security_considerations(tmp_path):
    body = _META_FEATURE + (
        "## Problem Statement\nx\n## Success Criteria\nx\n## Scope\nx\n## Design\nx\n"
        "## Edge Cases\nx\n"  # short form
        "## Security\nx\n"     # short form
        "## Testing\nx\n"      # short form
        "## Related Documents\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "features", "999-grand.md", body)
    assert _no_section_findings(lint_doc(p))


def test_bug_grandfather_root_cause_satisfies_root_cause_analysis(tmp_path):
    body = _META_BUG + (
        "## Observed Behavior\nx\n## Expected Behavior\nx\n## Steps to Reproduce\nx\n"
        "## Environment\nx\n"
        "## Root Cause\nx\n"   # short form
        "## Fix Description\nx\n## Iteration Log\nx\n## Regression Prevention\nx\n"
        "## Related Documents\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "bugs", "BUG-999-grand.md", body)
    assert _no_section_findings(lint_doc(p))


def test_design_grandfather_architecture_satisfies_full_canon(tmp_path):
    body = _META_DESIGN + (
        "## Overview\nx\n"
        "## Architecture\nx\n"  # canon: Architecture/ER/Deployment Diagrams (≥3)
        "## Domain/Module/Endpoint Details\nx\n"
        "## Key Decisions\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "design", "tolerant-design.md", body)
    assert _no_section_findings(lint_doc(p))


# ---------------------------------------------------------------------------
# Missing required (non-conditional) → finding
# ---------------------------------------------------------------------------


def test_feature_missing_problem_statement(tmp_path):
    body = _META_FEATURE + (
        "## Success Criteria\nx\n## Scope\nx\n## Design\nx\n"
        "## Edge Cases\nx\n## Security\nx\n## Testing\nx\n"
        "## Related Documents\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "features", "999-missing.md", body)
    findings = lint_doc(p)
    assert _has_missing_section(findings, "Problem Statement")


def test_bug_missing_iteration_log(tmp_path):
    body = _META_BUG + (
        "## Observed Behavior\nx\n## Expected Behavior\nx\n## Steps to Reproduce\nx\n"
        "## Environment\nx\n## Root Cause\nx\n## Fix Description\nx\n"
        "## Regression Prevention\nx\n## Related Documents\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "bugs", "BUG-999-missing.md", body)
    findings = lint_doc(p)
    assert _has_missing_section(findings, "Iteration Log")


def test_adr_missing_alternatives_briefly_rejected(tmp_path):
    body = _META_ADR + (
        "## Context\nx\n## Decision\nx\n## Consequences\nx\n"
        "## Related Documents\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "adr", "ADR-999-missing.md", body)
    findings = lint_doc(p)
    assert _has_missing_section(findings, "Alternatives Briefly Rejected")


def test_postmortem_missing_where_we_got_lucky(tmp_path):
    body = _META_POSTMORTEM + (
        "## Summary\nx\n## Impact\nx\n## Timeline\nx\n## Root Cause\nx\n"
        "## What Went Well\nx\n## What Went Wrong\nx\n## Action Items\nx\n"
        "## Lessons Learned\nx\n## Related Documents\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "postmortems", "POSTMORTEM-2026-05-11-missing.md", body)
    findings = lint_doc(p)
    assert _has_missing_section(findings, "Where We Got Lucky")


def test_design_missing_key_decisions(tmp_path):
    body = _META_DESIGN + (
        "## Overview\nx\n## Architecture\nx\n## Domain/Module/Endpoint Details\nx\n"
        "## Changelog\nx\n"
    )
    p = _doc(tmp_path, "design", "missing-decisions.md", body)
    findings = lint_doc(p)
    assert _has_missing_section(findings, "Key Decisions")


# ---------------------------------------------------------------------------
# Conditional sections accept absence
# ---------------------------------------------------------------------------


def test_feature_conditional_api_changes_absent_passes(tmp_path):
    """API Changes (if any) — feature doc without API change is valid."""
    body = _META_FEATURE + (
        "## Problem Statement\nx\n## Success Criteria\nx\n## Scope\nx\n## Design\nx\n"
        "## Edge Cases & Error Handling\nx\n## Security Considerations\nx\n"
        "## Testing Strategy\nx\n## Related Documents\nx\n## Changelog\nx\n"
        # NO "API Changes" or "Database Changes" headings
    )
    p = _doc(tmp_path, "features", "999-no-api.md", body)
    findings = lint_doc(p)
    assert _no_section_findings(findings)


def test_runbook_conditional_background_absent_passes(tmp_path):
    body = _META_RUNBOOK + (
        "## When This Fires\nx\n## Quick Reference\nx\n## Diagnosis\nx\n"
        "## Mitigation\nx\n## Verification\nx\n## Escalation\nx\n"
        "## Related Documents\nx\n## Changelog\nx\n"
        # NO "Background"
    )
    p = _doc(tmp_path, "runbooks", "RUNBOOK-no-bg.md", body)
    findings = lint_doc(p)
    assert _no_section_findings(findings)


# ---------------------------------------------------------------------------
# Heading number-prefix stripping
# ---------------------------------------------------------------------------


def test_design_numbered_heading_satisfies_canon(tmp_path):
    """### 4.1 Overview should satisfy canon `Overview`."""
    body = _META_DESIGN + (
        "## Overview\nx\n## Architecture\nx\n"
        "### 4.1 Domain/Module/Endpoint Details\nx\n"
        "## Key Decisions\nx\n## Changelog\nx\n"
    )
    p = _doc(tmp_path, "design", "numbered.md", body)
    assert _no_section_findings(lint_doc(p))


# ---------------------------------------------------------------------------
# REQUIRED_SECTIONS drift gate
# ---------------------------------------------------------------------------


def test_required_sections_canon_match():
    from cli import lint, vocabulary

    assert lint.REQUIRED_SECTIONS == vocabulary.REQUIRED_SECTIONS


# ---------------------------------------------------------------------------
# Investigation type: no required sections, no findings
# ---------------------------------------------------------------------------


def test_investigation_no_section_requirements(tmp_path):
    # investigation isn't currently detected by lint.detect_doc_type, but
    # the canon REQUIRED_SECTIONS["investigation"] is () so even if it
    # were detected, no findings would fire.
    from cli import vocabulary

    assert vocabulary.REQUIRED_SECTIONS["investigation"] == ()
