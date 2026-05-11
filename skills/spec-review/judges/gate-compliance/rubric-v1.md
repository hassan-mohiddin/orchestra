# Rubric — gate-compliance sub-judge — v1

**Rubric version**: `gate-compliance-v1`
**Model**: claude-sonnet-4-6
**Tools allowed**: Read (target doc only)
**Mandatory**: false

---

## Domain

orchestra-specific governance rules: Gates 1–3 from `.claude/rules/documentation-gate.md`, canon-frozen narrow-change rule, lifecycle transitions per `docs/STANDARDS.md`. This is policy-compliance pattern-matching, not semantic content review.

## Gate 1 (Discovery Gate)

A defect found during investigation must be filed as `BUG-NNN-name.md` before any fix is brainstormed. If this doc is a `feat:` or `fix:` design doc, has the discovery trail been documented? If this doc is a BUG, was it filed when the defect was discovered (Discovery date traceable to git log)?

## Gate 2 (Design Gate)

Code changes require a committed design doc. If this doc IS the design doc, does it include design sufficient to gate code? Specifically: Scope (in/out), Design (architecture/data flow), Edge Cases, Testing Strategy.

## Gate 3 (Spec Review Gate)

This doc is in the process of being spec-reviewed. The Gate 3 check is:
- Iteration field present?
- Status appropriate for the review cycle (Draft for pre-commit, Approved for post-approval)?
- If iter > 1, is the prior iter's attestation still on disk?

## Canon-frozen narrow-change rule

If `Status: ∈ {Approved, Implemented, Verified, Fix Applied, Current}`, the doc is canon-frozen. Edits permitted:
- **Whitelist edit** — Status / Iteration / Superseded by + Changelog append → no Addresses: needed
- **Tiered narrow-change** (BUG-011) — Addresses: lines per finding + NEW Changelog row per finding
- **Supersession** — archive + `-rN.md` path

A canon-frozen doc with edits that don't fit these patterns is a Critical finding.

## Status lifecycle (per STANDARDS § Status Lifecycle)

| Doc type | Lifecycle |
|---|---|
| Feature LLD | Draft → Proposed → Approved → In Progress → Implemented → Verified |
| Bug Report | Investigating → Root Cause Found → In Progress → Fix Applied → Verified |
| ADR | Draft → Proposed → Approved → Implemented \| Superseded \| Rejected |
| Postmortem | Draft → Reviewed → Action Items Tracked → Closed |
| Design Doc | Current \| Outdated \| Deprecated |
| Runbook | Current \| Outdated \| Deprecated |

Status skips (e.g., Draft → Implemented without passing through Approved) are an Important finding unless the doc Changelog explicitly justifies the skip.

## Severity guidance

- **Critical**: canon-frozen doc with non-narrow-change edit; doc claims to close a BUG without spec-review pass attestation; Gate 1 (BUG was needed but not filed) skipped.
- **Important**: Iteration field missing on canon-frozen doc; Status lifecycle skip without Changelog justification; Changelog entry missing for a status transition.
- **Minor**: Changelog entry format imprecise; metadata field formatting quirks; cross-ref to gates rule file not present (but enforcement is correct).

## Anti-pedantry

Don't flag the bare existence of a `feat:` doc that hasn't been spec-reviewed YET — Gate 3 is in-progress at the moment of this review. Flag only the missing prerequisite gates.

## Output discipline

YAML in `sub_judges[]` entry shape. Locations match `^(.+\s+§\s+.+|line\s+\d+)$`.
