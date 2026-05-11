# Rubric — structure sub-judge — v1

**Rubric version**: `structure-v1`
**Model**: claude-sonnet-4-6
**Tools allowed**: Read (target doc only)
**Mandatory**: false

---

## Domain

Mechanical structure of the doc: required sections, metadata block, filename grammar, Mermaid presence, format consistency. Pattern-match heavy; no deep reasoning required. Surface-level findings only.

## Required-sections matrix (per doc type)

Source of truth: `docs/STANDARDS.md § Required Sections Per Doc Type`. Authoritative list reproduced here for sub-judge convenience (re-check STANDARDS for latest):

| Doc type | Required sections (must all be present) |
|---|---|
| Feature LLD | Problem Statement, Success Criteria, Scope, Design (with ≥ 1 Mermaid), API Changes, Database Changes, Edge Cases, Security Considerations, Testing Strategy, Related Documents, Changelog |
| Bug Report | Observed Behavior, Expected Behavior, Steps to Reproduce, Environment, Root Cause Analysis (Mermaid), Fix Description, Iteration Log, Regression Prevention, Related Documents, Changelog |
| ADR | Context, Decision, Consequences, Alternatives Briefly Rejected, Related Documents, Changelog |
| Design Doc | Overview, Architecture diagrams (≥ 3), Domain/Module/Endpoint Details, Key Decisions (links to ADRs), Changelog |
| Postmortem | Summary, Impact, Timeline, Root Cause (Mermaid), What Went Well, What Went Wrong, Where We Got Lucky, Action Items, Lessons Learned, Related Documents, Changelog |
| Runbook | When This Fires, Quick Reference, Diagnosis, Mitigation, Verification, Escalation, Background, Related Documents, Changelog |
| Implementation Plan | Header (goal/architecture/tech stack/LLD ref), File Structure, Tasks (TDD vertical slicing), per-task Files/sequencing/commit |
| Research | Metadata, TOC, Findings, Recommendations Summary, Sources |

## Metadata-block check

Required at top of every doc:
```
> **Doc ID:** ...
> **Date:** YYYY-MM-DD
> **Status:** ...
> **DRI:** ...
```
Additional fields per doc type (Type, Severity, OKR Alignment, etc. per STANDARDS).

## Filename-grammar (per LLD-006-r4)

| Type | Grammar |
|---|---|
| features | `NNN-name(-rN)?.md` |
| bugs | `BUG-NNN-name(-rN)?.md` |
| adr | `ADR-NNN-name(-rN)?.md` |
| postmortems | `NNN-name(-rN)?.md` |
| runbooks | `NNN-name(-rN)?.md` |
| design | `<name>(-rN)?.md` (bare-name) |
| plans | `YYYY-MM-DD-name.md` |

## Mermaid presence

Per `STANDARDS.md § Mermaid Diagram Requirements`:
- Feature LLD: ≥ 1
- Bug Report: ≥ 1 (sequence showing bug data path)
- ADR: optional
- Design Doc: ≥ 3
- Postmortem: ≥ 1 (sequence)
- Runbook: optional
- Plan: optional

## Severity guidance

- **Critical**: required section absent entirely; filename violates grammar; metadata block missing.
- **Important**: a metadata field missing; required Mermaid absent; sections in wrong order.
- **Minor**: heading hierarchy quirks (h3 before h2); list nesting inconsistent; trailing whitespace.

## Anti-pedantry

This is the surface-level sub-judge. Don't flag:
- Stylistic table formatting (compact vs spread)
- Choice of bullet character (`-` vs `*`)
- Markdown extension variants
- Capitalization of section headers (unless STANDARDS specifies)

## Output discipline

YAML in `sub_judges[]` entry shape (see prompt). Locations must match `^(.+\s+§\s+.+|line\s+\d+)$`.
