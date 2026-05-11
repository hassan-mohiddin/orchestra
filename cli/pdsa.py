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

from dataclasses import dataclass, field
from pathlib import Path


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

    return report
