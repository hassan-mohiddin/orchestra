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


_CITATION_RE = re.compile(
    r"`([^\s`]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`"
)

_PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|FIXME)\b(.*)$", re.MULTILINE)
_OWNER_SUFFIX_RE = re.compile(r"^\s*(?::|by)\s+\S+", re.IGNORECASE)


def _strip_code_spans(text: str) -> str:
    """Remove inline `code` spans and fenced ```code blocks``` for placeholder scanning.

    Backtick-quoted tokens are meta-references (e.g., the literal text `TBD`),
    not bare placeholders. Stripping them eliminates false positives in docs
    that document the placeholder canon itself.
    """
    # Remove fenced code blocks first (greedy across lines)
    out = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Then inline `code` spans on a single line
    out = re.sub(r"`[^`\n]+`", "", out)
    return out

_REFS_LINE_RE = re.compile(r"^Refs:\s+(\S+)", re.MULTILINE)

_FILENAME_GRAMMAR: dict[str, re.Pattern[str]] = {
    "feature": re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*(-r\d+)?\.md$"),
    "bug": re.compile(r"^BUG-\d{3}-[a-z0-9][a-z0-9-]*(-r\d+)?\.md$"),
    "adr": re.compile(r"^ADR-\d{3}-[a-z0-9][a-z0-9-]*(-r\d+)?\.md$"),
    "postmortem": re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*(-r\d+)?\.md$"),
    "runbook": re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*(-r\d+)?\.md$"),
    "design": re.compile(r"^[a-z0-9][a-z0-9-]*(-r\d+)?\.md$"),
    "plan": re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\.md$"),
}


_ITERATION_RE = re.compile(r"^>\s*\*\*Iteration:\*\*\s*(\d+)", re.MULTILINE)
_DOC_ID_RE = re.compile(r"^(?:BUG-\d+|ADR-\d+|\d+)-[a-z0-9-]+|^[a-z0-9-]+", re.IGNORECASE)


def _check_class_audit_attestation(doc_path: Path) -> CheckResult:
    """Per LLD-011 §Design class-vs-instance — iter-2+ docs must sweep class findings.

    Reads the prior-iteration attestation (if any) at
    `docs/reviews/<doc-stem>-r<N-1>.review.yaml`. When any iter-1 finding has
    scope=class, this iter-2 doc must contain an `## Audit Attestation` section
    documenting the systemic sweep. Missing audit → check fails.

    No prior attestation, iter=1, or zero class findings → check passes.
    """
    import yaml

    body = doc_path.read_text()
    m = _ITERATION_RE.search(body)
    if not m:
        return CheckResult(passed=True, detail="no Iteration: marker — no audit required")
    iteration = int(m.group(1))
    if iteration <= 1:
        return CheckResult(passed=True, detail="iter-1: no prior attestation to audit")

    prior_iter = iteration - 1
    stem = doc_path.stem
    # Strip any existing -rN suffix to get base id
    base = re.sub(r"-r\d+$", "", stem)
    reviews_dir = Path.cwd() / "docs" / "reviews"
    prior_path = reviews_dir / f"{base}-r{prior_iter}.review.yaml"
    if not prior_path.exists():
        return CheckResult(
            passed=True,
            detail=f"no prior attestation at {prior_path} — no audit required",
        )

    try:
        prior = yaml.safe_load(prior_path.read_text()) or {}
    except yaml.YAMLError as exc:
        return CheckResult(passed=False, detail=f"cannot parse prior attestation: {exc}")

    findings = prior.get("findings_aggregated") or []
    class_findings = [f for f in findings if f.get("scope") == "class"]
    if not class_findings:
        return CheckResult(passed=True, detail="no class findings in iter-1 — no sweep required")

    if re.search(r"^#{2,4}\s+Audit Attestation\b", body, re.MULTILINE | re.IGNORECASE):
        return CheckResult(
            passed=True,
            detail=f"audit_attestation section present ({len(class_findings)} class finding(s) swept)",
        )
    return CheckResult(
        passed=False,
        detail=(
            f"{len(class_findings)} class finding(s) in iter-{prior_iter} attestation but no "
            "`## Audit Attestation` section in iter-2 doc body"
        ),
    )


def _check_glossary(doc_path: Path) -> CheckResult:
    """Glossary completeness — NON-GATING per LLD-011 §PDSA item 4.

    Placeholder until BUG-016 controlled-vocabulary canon ships. When canon is
    available, this check will compare doc terms against the canon and warn on
    drift; for now it always reports pass with informational detail.
    """
    return CheckResult(
        passed=True,
        detail="glossary check deferred to BUG-016 canon",
        gating=False,
    )


def _check_filename_grammar(doc_path: Path) -> CheckResult:
    """Per LLD-006-r4 — filename grammar per doc type."""
    doc_type = _detect_doc_type(doc_path)
    if doc_type is None or doc_type not in _FILENAME_GRAMMAR:
        return CheckResult(passed=True, detail="unknown doc type — grammar check skipped")

    name = doc_path.name
    pattern = _FILENAME_GRAMMAR[doc_type]
    if not pattern.match(name):
        return CheckResult(
            passed=False,
            detail=f"{name} does not match {doc_type} grammar {pattern.pattern}",
        )
    return CheckResult(passed=True, detail=f"{doc_type} grammar OK")


def _check_refs(doc_path: Path) -> CheckResult:
    """Per LLD-011 §PDSA item 6 — each Refs: <path> line must resolve."""
    body = doc_path.read_text()
    failures: list[str] = []

    for m in _REFS_LINE_RE.finditer(body):
        ref_path_str = m.group(1)
        ref_path = Path(ref_path_str)
        if not ref_path.is_absolute():
            candidate = (doc_path.parent / ref_path).resolve()
            if not candidate.exists():
                candidate = Path.cwd() / ref_path
            ref_path = candidate
        if not ref_path.exists():
            failures.append(f"unresolved Refs: {ref_path_str}")

    if failures:
        return CheckResult(passed=False, detail="; ".join(failures))
    return CheckResult(passed=True, detail="all Refs: lines resolve")


def _check_placeholders(doc_path: Path) -> CheckResult:
    """Detect bare TBD/TODO/FIXME without owner-suffix.

    Per LLD-011 §PDSA item 5 + STANDARDS: `TBD by [date|person]` and
    `TODO by ...: ...` are owned placeholders (pass); bare tokens fail.
    Backtick-quoted tokens are stripped first — they are meta-references,
    not bare placeholders.
    """
    body = _strip_code_spans(doc_path.read_text())
    failures: list[str] = []

    for m in _PLACEHOLDER_RE.finditer(body):
        token = m.group(1)
        tail = m.group(2)
        if not _OWNER_SUFFIX_RE.match(tail):
            failures.append(f"bare {token} (line context: {m.group(0).strip()[:60]})")

    if failures:
        return CheckResult(
            passed=False,
            detail=f"{len(failures)} bare placeholder(s): " + "; ".join(failures[:3]),
        )
    return CheckResult(passed=True, detail="no bare placeholders")


def _check_citations(doc_path: Path) -> CheckResult:
    """Validate `<path>:<N>` and `<path>:<N>-<M>` citations in doc body.

    Per LLD-011 §PDSA item 3:
    - cited_path must exist (relative to repo root or absolute)
    - 1 <= N <= len(lines)
    - if M present: 1 <= M <= len(lines) AND M >= N
    """
    body = doc_path.read_text()
    failures: list[str] = []

    for m in _CITATION_RE.finditer(body):
        cited_path_str, n_str, m_str = m.group(1), m.group(2), m.group(3)
        cited_path = Path(cited_path_str)
        if not cited_path.is_absolute():
            # Try resolution in order: cwd (repo root), doc parent. Doc-relative
            # citations are uncommon; repo-root-relative is the canon (`cli/lint.py:42`).
            for candidate in (Path.cwd() / cited_path, doc_path.parent / cited_path):
                if candidate.exists():
                    cited_path = candidate
                    break
            else:
                cited_path = (doc_path.parent / cited_path).resolve()

        if not cited_path.exists():
            failures.append(f"nonexistent path: {cited_path_str}")
            continue

        try:
            lines = cited_path.read_text().splitlines()
        except OSError as exc:
            failures.append(f"cannot read {cited_path_str}: {exc}")
            continue

        n = int(n_str)
        total = len(lines)
        if not (1 <= n <= total):
            failures.append(f"{cited_path_str}:{n_str} out of range (file has {total} lines)")
            continue

        if m_str is not None:
            mm = int(m_str)
            if not (1 <= mm <= total and mm >= n):
                failures.append(f"{cited_path_str}:{n_str}-{m_str} invalid range")

    if failures:
        return CheckResult(passed=False, detail="; ".join(failures))
    return CheckResult(passed=True, detail="all citations valid")


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
    """One PDSA check outcome. `gating=False` checks emit info but never block dispatch."""

    passed: bool
    detail: str = ""
    gating: bool = True


@dataclass
class PdsaReport:
    """Aggregate of all PDSA checks for one doc."""

    doc_path: Path
    checks: dict[str, CheckResult] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """True only when every GATING check passed. Non-gating fails are warnings."""
        return all(c.passed for c in self.checks.values() if c.gating)

    def to_yaml(self) -> str:
        """Per LLD-011 §PDSA — emit a YAML report listing pass/fail per check."""
        import yaml

        data = {
            "doc_path": str(self.doc_path),
            "passed": self.passed,
            "checks": {
                cid: {
                    "passed": c.passed,
                    "gating": c.gating,
                    "detail": c.detail,
                }
                for cid, c in self.checks.items()
            },
        }
        return yaml.safe_dump(data, sort_keys=False)


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
    report.checks["citations"] = _check_citations(doc_path)
    report.checks["placeholders"] = _check_placeholders(doc_path)
    report.checks["refs"] = _check_refs(doc_path)
    report.checks["filename_grammar"] = _check_filename_grammar(doc_path)
    report.checks["glossary"] = _check_glossary(doc_path)
    report.checks["class_audit_attestation"] = _check_class_audit_attestation(doc_path)

    return report
