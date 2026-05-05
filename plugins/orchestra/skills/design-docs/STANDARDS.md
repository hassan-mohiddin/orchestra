# Documentation Standards

> Canonical reference for all doc types this skill produces. Templates implement these standards.
> Last updated: 2026-05-06

## Doc Types

| Type | Default location | Naming | Auto-numbered |
|------|-----------------|--------|---------------|
| Feature LLD | `docs/features/` | `NNN-kebab-name.md` | Yes |
| Bug Report | `docs/bugs/` | `BUG-NNN-kebab-name.md` | Yes |
| ADR | `docs/adr/` | `ADR-NNN-kebab-name.md` | Yes |
| Design Doc (living) | `docs/design/` | `kebab-name.md` | No |
| Postmortem | `docs/postmortems/` | `POSTMORTEM-YYYY-MM-DD-kebab.md` | Date-prefixed |
| Runbook | `docs/runbooks/` | `RUNBOOK-kebab.md` | No |
| Plan | `docs/plans/` | `YYYY-MM-DD-kebab.md` | Date-prefixed |
| Research | `docs/research/` | `NNN-kebab.md` | Yes |
| Investigation | `docs/investigations/` | `kebab.md` | Scratch — promote to Bug Report when confirmed |
| Policy | `docs/policies/` | `kebab.md` | No |

Override locations via plugin config `doc_paths`.

## Required Metadata Block

Every doc opens with:

```markdown
> **Doc ID:** NNN-kebab-name
> **Date:** YYYY-MM-DD
> **Status:** [from lifecycle below]
> **DRI:** [Name — Directly Responsible Individual]
```

Additional fields by doc type:

| Type | Extra fields |
|------|--------------|
| Feature LLD | `Type: Feature LLD` |
| Bug Report | `Severity: Critical \| High \| Medium \| Low` |
| ADR | `OKR Alignment: [objective]` (mandatory in **team mode**) |
| Design Doc | `Last Updated: YYYY-MM-DD`, `Version: 1.x` |
| Postmortem | `Severity: SEV1 \| SEV2 \| SEV3 \| SEV4` |
| Runbook | `Severity: P1 \| P2 \| P3` |
| Plan | `LLD: [path to Feature LLD or Bug Report this implements]` |

## Status Lifecycles

### Feature LLD
`Draft` → `Proposed` → `Approved` → `In Progress` → `Implemented` → `Verified`

### Bug Report
`Investigating` → `Root Cause Found` → `In Progress` → `Fix Applied` → `Verified`

Bug iteration loop: `In Progress` ↔ `Fix Applied` may iterate. One BUG-NNN doc spans all attempts. `fix:` commit only after user confirms `Verified`.

### ADR
`Draft` → `Proposed` → `Approved` → `Implemented` | `Superseded` | `Rejected`

ADRs are RECORDED. If the decision changes, write a new ADR with `Supersedes: ADR-NNN`.

### Postmortem
`Draft` → `Reviewed` → `Action Items Tracked` → `Closed`

`Closed` only when all P0/P1 action items have shipped.

### Runbook & Design Doc
`Current` | `Outdated` | `Deprecated`

## Required Sections per Doc Type

### Feature LLD (all required)

1. Problem Statement
2. Success Criteria (measurable, checkboxes)
3. Scope — In Scope / Out of Scope
4. Design (architecture/data flow + ≥1 Mermaid diagram)
5. API Changes (if any)
6. Database Changes (if any)
7. Edge Cases & Error Handling
8. Security Considerations
9. Testing Strategy
10. Related Documents
11. Changelog

### Bug Report (all required)

1. Observed Behavior
2. Expected Behavior
3. Steps to Reproduce
4. Environment
5. Root Cause Analysis (with Mermaid diagram)
6. Fix Description
7. **Iteration Log** (one entry per attempt — hypothesis, change, observed, user verification)
8. Regression Prevention
9. Related Documents
10. Changelog

### ADR (all required)

1. Context (forces and constraints, not options)
2. Decision (declarative — "We will X")
3. Consequences (positive / negative / commitments)
4. Alternatives Briefly Rejected (≤2-sentence dismissals — if longer, this is an RFC, not an ADR)
5. Related Documents (Supersedes / Superseded by / Related)
6. Changelog

Status lives in metadata, not a separate section.

### Postmortem (all required)

1. Summary (2-3 sentences)
2. Impact (users, duration, SLO/revenue, data integrity)
3. Timeline (UTC timestamps from logs/pagers)
4. Root Cause (with Mermaid + trigger + underlying cause)
5. What Went Well
6. What Went Wrong
7. **Where We Got Lucky** (near-miss surfacing — highest-signal section)
8. Action Items (priority, owner, due, tracking link)
9. Lessons Learned
10. Related Documents
11. Changelog

Blameless. Roles, never names.

### Runbook (all required)

1. When This Fires (alert name, symptom, page priority)
2. Quick Reference (one-line 3am-friendly TL;DR)
3. Diagnosis (numbered steps + commands + expected output)
4. Mitigation (ordered by safety)
5. Verification (checkboxes for confirming recovery)
6. Escalation (who, when, channel)
7. Background (optional)
8. Related Documents
9. Changelog (update after every incident the runbook was used in)

### Design Doc (living component) (all required)

1. Overview
2. Architecture/ER/Deployment Diagrams (≥3)
3. Domain/Module/Endpoint Details
4. Key Decisions (links to ADRs)
5. Changelog (newest at top)

## Mermaid Requirements

| Doc | Min | Preferred |
|-----|-----|-----------|
| Feature LLD | 1 | Sequence (API) or Activity (workflow) |
| Bug Report | 1 | Sequence showing bug data path |
| Postmortem | 1 | Sequence: trigger → system → users |
| ADR | 0–1 | Optional — current → proposed |
| Design Doc | 3+ | Architecture + data flow + deployment |

All diagrams must use Unicode symbols, descriptive labels, accessible colors.

## Spec Review Rule (4 gates)

After writing or updating any doc destined for `docs/` and a commit:

1. **Completeness** — required sections present + filled
2. **Evidence** — claims have file:line / benchmark / citation
3. **Clarity** — fresh reader can act on the doc
4. **Consistency** — doc agrees with itself, peer docs, code

Failures named by gate. Max 3 review iterations. See `references/spec-review-gates.md`.

## Commit Gate

Every `fix:` and `feat:` commit MUST have a `Refs:` line pointing to a real doc:

```
fix: validate token expiry boundary

Refs: docs/bugs/BUG-014-auth-token-leak.md
```

Validated by `cli/lint.py`. Orphan commits fail CI.

For bug iteration: `wip:` prefix during iteration; single `fix:` commit only after user confirms `Verified`.

## Writing Style

1. Be specific — "increases latency by ~200ms" not "might be slower"
2. Show data flow — how data enters, transforms, exits
3. Name things — concrete function/table/endpoint names
4. No TODOs — every section filled or marked `TBD by [date/person]`
5. Use diagrams — picture worth 1000 tokens
6. Version-aware — reference specific versions, commits, dates

## Solo vs Team Mode

| Aspect | Solo | Team |
|--------|------|------|
| RFC vocabulary | Suppressed | Enabled (ADR with status `Proposed` during deliberation) |
| Reviewer assignment in spec review | Skipped | Mandatory |
| ADR `OKR Alignment` field | Optional | Mandatory |
| Bug iteration `fix:` gate | User confirmation | User OR designated approver confirmation |

Industry threshold for switching: 2+ senior engineers. Re-evaluate when team grows.

## References

- Nygard, *Documenting Architecture Decisions* (2011)
- Google SRE Book, *Postmortem Culture*
- *RFCs and Design Docs* — Pragmatic Engineer
- AGENTS.md spec — agents.md
- llms.txt spec — llmstxt.org
- 4-gate review — `rvdbreemen/adr-kit`
- Conventional Commits 1.0.0
