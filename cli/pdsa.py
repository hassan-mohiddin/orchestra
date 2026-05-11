"""PDSA — Pre-Dispatch Self-Audit (LLD-011 Phase 2).

Mechanical, deterministic checks run before sub-judge dispatch. Each check is
either gating (lint, required sections, citations, placeholders, refs, filename)
or non-gating (glossary, until BUG-016 controlled-vocabulary canon ships).

Lint check (slice 2.1): invokes `python -m cli.lint --doc <path>` and surfaces
the exit code. Zero → pass. Non-zero → fail. Lint failure blocks dispatch.

The module exposes `run_pdsa(doc_path) -> PdsaReport`. Sub-judges run only when
`report.passed is True`. On failure, the caller emits the YAML report to the
author and halts (no attestation is written for PDSA failures — PDSA findings
live in the lint/PDSA log layer, not in attestation YAML).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


_REQUIRED_SECTIONS: dict[str, list[str]] = {
    "feature": [
        "Problem Statement",
        "Success Criteria",
        "Scope",
        "Design",
        "API Changes",
        "Database Changes",
        "Edge Cases",
        "Security Considerations",
        "Testing Strategy",
        "Related Documents",
        "Changelog",
    ],
    "bug": [
        "Observed Behavior",
        "Expected Behavior",
        "Steps to Reproduce",
        "Environment",
        "Root Cause Analysis",
        "Fix Description",
        "Iteration Log",
        "Regression Prevention",
        "Related Documents",
        "Changelog",
    ],
    "adr": [
        "Context",
        "Decision",
        "Consequences",
        "Alternatives",
        "Related Documents",
        "Changelog",
    ],
    "design": [
        "Overview",
        "Changelog",
    ],
    "postmortem": [
        "Summary",
        "Impact",
        "Timeline",
        "Root Cause",
        "What Went Well",
        "What Went Wrong",
        "Action Items",
        "Lessons Learned",
        "Related Documents",
        "Changelog",
    ],
    "runbook": [
        "When This Fires",
        "Quick Reference",
        "Diagnosis",
        "Mitigation",
        "Verification",
        "Escalation",
        "Related Documents",
        "Changelog",
    ],
    "policy": [
        "Policy Statement",
        "Rules",
        "Changelog",
    ],
    "plan": [
        "Header",
        "File Structure",
    ],
}


def _detect_doc_type(doc_path: Path) -> str | None:
    """Map doc_path to one of the keys in _REQUIRED_SECTIONS, or None if unknown."""
    parts = doc_path.parts
    if "features" in parts:
        return "feature"
    if "bugs" in parts:
        return "bug"
    if "adr" in parts:
        return "adr"
    if "design" in parts:
        return "design"
    if "postmortems" in parts:
        return "postmortem"
    if "runbooks" in parts:
        return "runbook"
    if "policies" in parts:
        return "policy"
    if "plans" in parts:
        return "plan"
    return None


def _extract_section_headings(body: str) -> set[str]:
    """Return the set of `## Heading` / `### Heading` text values found in body."""
    headings: set[str] = set()
    for line in body.splitlines():
        m = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if m:
            headings.add(m.group(1).strip())
    return headings


def _check_required_sections(doc_path: Path) -> CheckResult:
    """Verify each required section name is present as a heading in the doc.

    Heuristic match: substring-in-heading-text (handles `## Edge Cases & Error Handling`
    matching the canon "Edge Cases"). Tightens to strict-canon-match when BUG-016 closes.
    """
    doc_type = _detect_doc_type(doc_path)
    if doc_type is None:
        return CheckResult(passed=True, detail="unknown doc type — check skipped")

    required = _REQUIRED_SECTIONS[doc_type]
    headings = _extract_section_headings(doc_path.read_text())
    missing = [
        name for name in required
        if not any(name.lower() in h.lower() for h in headings)
    ]
    if missing:
        return CheckResult(
            passed=False,
            detail=f"missing required sections for {doc_type}: {', '.join(missing)}",
        )
    return CheckResult(passed=True, detail=f"{doc_type}: all {len(required)} sections present")


@dataclass
class CheckResult:
    """One PDSA check outcome."""

    passed: bool
    detail: str = ""


@dataclass
class PdsaReport:
    """Aggregate of all PDSA checks for one doc."""

    doc_path: Path
    checks: dict[str, CheckResult] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """True only when every gating check passed."""
        return all(c.passed for c in self.checks.values())


def _invoke_lint(argv: list[str]) -> int:
    """Shell into cli.lint.main with argv. Returns exit code."""
    from cli import lint

    return lint.main(argv)


def run_pdsa(doc_path: Path) -> PdsaReport:
    """Run the PDSA checks against `doc_path`. Return a PdsaReport.

    Slice 2.1 ships only the lint check. Later slices add sections (2.3),
    citations (2.4-2.5), placeholders (2.6-2.7), Refs: (2.8), filename (2.9),
    glossary non-gating (2.10).
    """
    report = PdsaReport(doc_path=doc_path)

    lint_rc = _invoke_lint(["--doc", str(doc_path)])
    report.checks["lint"] = CheckResult(
        passed=(lint_rc == 0),
        detail=f"cli.lint --doc exit={lint_rc}",
    )

    report.checks["required_sections"] = _check_required_sections(doc_path)

    return report
