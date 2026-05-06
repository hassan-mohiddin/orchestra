# Orchestra Documentation Standards

> **Canonical source of truth for all agents (Claude, Gemini) and humans working on orchestra.**
> When any agent's internal doc-standards file conflicts with this file, this file wins.
> Last Updated: 2026-05-06
>
> **Note:** This is the orchestra-development workspace STANDARDS. It mirrors `orchestra/docs/STANDARDS.md`
> in the orchestra plugin repo. Edit either path; sync via `bash orchestra-dev/sync-orchestra-dev.sh`.

---

## Doc Types

| Type | Location | Naming | Auto-numbered |
|---|---|---|---|
| Feature LLD | `docs/features/` | `NNN-kebab-name.md` | Yes (001, 002…) |
| Bug Report | `docs/bugs/` | `BUG-NNN-kebab-name.md` | Yes (BUG-001…) |
| ADR | `docs/adr/` | `ADR-NNN-kebab-name.md` | Yes (ADR-001…) |
| Design Doc (living) | `docs/design/` | `kebab-name.md` | No |
| Postmortem | `docs/postmortems/` | `POSTMORTEM-YYYY-MM-DD-kebab-name.md` | No (date-prefixed) |
| Runbook | `docs/runbooks/` | `RUNBOOK-kebab-name.md` | No |
| Policies | `docs/policies/` | `kebab-name.md` | No |
| Implementation Plan | `docs/plans/` | `YYYY-MM-DD-kebab-name.md` | No (date-prefixed) |
| Research | `docs/research/` | `NNN-kebab-name.md` | Yes (001, 002…) |
| Investigation | `docs/investigations/` | `kebab-name.md` | No (scratch) |

**Vocabulary notes:**
- **Design Doc** is the canonical term for living component-level architecture — replaces
  the deprecated "HLD" wording. Path stays `docs/design/`.
- **ADR** records an architectural decision that has been MADE. RFC vocabulary is not used
  — SCALE has a single decision-maker. Re-evaluate if 2+ senior engineers join.
- The previous `docs/rfcs/` directory was migrated to `docs/adr/` on 2026-05-05.

**`docs/archive/`** holds superseded or outdated docs. Move docs here instead of deleting them.
No naming convention enforced — keep the original filename.

**Postmortem + Runbook templates ship with the skill** but the directories are created on first use. Until SCALE has a user-facing incident, Bug Reports continue to cover incident-shaped events.

---

## Required Metadata Block

Every doc must open with a metadata block immediately after the title:

```markdown
> **Doc ID:** NNN-kebab-name
> **Date:** YYYY-MM-DD
> **Status:** [see lifecycle below]
> **DRI:** [Name — Directly Responsible Individual]
```

Additional fields by doc type:

| Type | Extra fields |
|---|---|
| Feature LLD | `Type: Feature LLD` |
| Bug Report | `Severity: Critical \| High \| Medium \| Low` |
| ADR | `OKR Alignment: [which objective this serves]` |
| Design Doc | `Last Updated: YYYY-MM-DD`, `Version: 1.x` |
| Postmortem | `Severity: SEV1 \| SEV2 \| SEV3 \| SEV4` |
| Runbook | `Severity: P1 \| P2 \| P3` (page priority handled) |
| Implementation Plan | `LLD: [path to Feature LLD or Bug Report this implements]` |
| Research | `Scope: [what was researched]`, `Researchers: [who/what conducted the research]` |

---

## Status Lifecycle

### Feature LLD

`Draft` → `Proposed` → `Approved` → `In Progress` → `Implemented` → `Verified`

### Bug Report

`Investigating` → `Root Cause Found` → `In Progress` → `Fix Applied` → `Verified`

**Bug iteration loop:** A Bug Report's lifecycle may iterate inside `In Progress` → `Fix
Applied`. If the user reports the bug still persists, the doc remains the same — append a
new iteration entry to the changelog and loop. Only advance to `Verified` after the user
explicitly confirms resolution.

### ADR

`Draft` → `Proposed` → `Approved` → `Implemented` | `Superseded` | `Rejected`

ADRs are RECORDED decisions. If your draft has a long "Options Considered" section weighing
alternatives without a chosen direction, you wrote an RFC, not an ADR. Decide first (using
brainstorm/grilling skills), then record as ADR.

### Design Doc

`Current` | `Outdated` | `Deprecated`

### Postmortem

`Draft` → `Reviewed` → `Action Items Tracked` → `Closed`

Closed only when all P0/P1 action items have shipped. P2 items can extend beyond closure if tracked elsewhere.

### Runbook

`Current` | `Outdated` | `Deprecated`

Runbooks rot fastest of all doc types. Update after every incident the runbook was used in (working or not). Mark `Outdated` if the system it describes has changed materially without runbook update.

**Status update rule:** Update the doc status **before or alongside** the final implementation commit — never after.

| Code state | Doc status to set |
|---|---|
| Implementation committed | `Implemented` |
| Verification passed (tests green, evidence confirmed, user confirmed for bugs) | `Verified` |

---

## Required Sections Per Doc Type

### Feature LLD (all required)

1. Problem Statement
2. Success Criteria (measurable, checkboxes)
3. Scope — In Scope / Out of Scope
4. Design (architecture/data flow + at least 1 Mermaid diagram)
5. API Changes (if any)
6. Database Changes (if any)
7. Edge Cases & Error Handling
8. Security Considerations
9. Testing Strategy
10. Related Documents (Design Doc links, ADR links)
11. Changelog (append-only — add an entry when the doc is created and whenever reality diverges from the original design)

### Bug Report (all required)

1. Observed Behavior (exact error messages / logs)
2. Expected Behavior
3. Steps to Reproduce
4. Environment (branch, component, trigger)
5. Root Cause Analysis (with Mermaid diagram showing bug path)
6. Fix Description (files changed + why it works)
7. Iteration Log (one entry per attempt — hypothesis, change, observed result, user verification result)
8. Regression Prevention (test added, guard added)
9. Related Documents
10. Changelog (append-only — add an entry at creation; add entries as status transitions)

The Iteration Log is what prevents the multi-doc-spam bug pattern: one BUG-NNN doc covers all attempts.

### ADR (all required)

1. Context (the situation that forced a decision — forces and constraints, not options)
2. Decision (what was chosen — direct, declarative, no hedging)
3. Consequences (positive / negative / neutral commitments)
4. Alternatives Briefly Rejected (two-sentence dismissals — if alternatives need more, this is an RFC, not an ADR)
5. Related Documents (Supersedes / Superseded by / Related)
6. Changelog (append-only — add entries on each status transition)

Status lives in the metadata block, not a separate section. ADRs record decisions and are immutable in spirit — if the decision changes, write a new ADR with `Supersedes: ADR-NNN` and set the prior ADR's status to `Superseded`.

### Design Doc — Living Document (all required)

1. Overview
2. Architecture/ER/Deployment Diagrams (≥3)
3. Domain/Module/Endpoint Details
4. Key Decisions (links to ADRs)
5. Changelog (append-only, newest at top)

### Postmortem (all required)

1. Summary (2-3 sentences)
2. Impact (users affected, duration, SLO/revenue impact, data integrity)
3. Timeline (UTC timestamps from logs/pagers)
4. Root Cause (with Mermaid diagram, trigger + underlying cause)
5. What Went Well
6. What Went Wrong
7. Where We Got Lucky (near-miss surfacing — highest signal section)
8. Action Items (priority, owner, due date, tracking link — trackable, not aspirational)
9. Lessons Learned (pattern + rule change)
10. Related Documents
11. Changelog

Postmortems are blameless. Refer to roles, not names ("the on-call engineer", not "Jane").

### Runbook (all required)

1. When This Fires (alert name, symptom, page priority)
2. Quick Reference (one-line 3am-friendly TL;DR)
3. Diagnosis (numbered steps, each with command + expected output)
4. Mitigation (ordered by safety — least risky first)
5. Verification (checkboxes for confirming recovery)
6. Escalation (who to page when mitigation fails)
7. Background (optional — context for non-paging reading)
8. Related Documents
9. Changelog (update after every incident the runbook was used in)

### Policy (all required)

1. Policy Statement (what this policy governs)
2. Rules / Checklist
3. Examples or templates (where applicable)
4. Changelog (append-only — add entries when policy is created or updated)

### Implementation Plan (all required)

1. Header (goal, architecture, tech stack, LLD reference)
2. File Structure (which files will be created or modified)
3. Tasks (bite-sized, TDD vertical slicing: one failing test → one implementation → repeat)
4. Each task must have: Files list, sequencing/dependencies, commit message

**Pitfall — LLD vs Plan no-overlap:** Plans describe HOW and IN WHAT ORDER. LLDs describe
WHAT to build. A plan that re-states the LLD's design content is doing the wrong thing.

### Research (all required)

1. Metadata (date, researchers, scope, decision reference)
2. Table of Contents
3. Findings organized by topic (with subsections per model/technique/paper)
4. Recommendations Summary (with rationale)
5. Sources (all URLs, paper references, benchmark links)

### Investigation (lightweight — no formal sections required)

Scratch notes for unconfirmed observations. Once confirmed, graduate to a formal Bug Report or
Feature LLD per `documentation-gate.md` Gate 1 promotion rule. Keep brief — these are working
notes, not published docs.

---

## Mermaid Diagram Requirements

| Doc Type | Minimum | Preferred type |
|---|---|---|
| Feature LLD | 1 | Sequence (API flows) or Activity (business logic) |
| Bug Report | 1 | Sequence showing the bug's data path |
| ADR | 0–1 | Optional — current → proposed if architecture change |
| Design Doc | 3+ | Architecture + data flow + deployment |
| Postmortem | 1 | Sequence showing failure path (trigger → system → users) |
| Runbook | 0 | Optional |
| Implementation Plan | 0 | Optional (code blocks serve as the primary visual) |
| Research | 0 | Optional (tables and comparison matrices serve as the primary visual) |
| Investigation | 0 | Optional |

**All diagrams must:**

- Use Unicode symbols (🔐 🌐 ⚙️ 💾 📬 👤)
- Use descriptive labels — `"Auth Service (JWT)"` not `"Service A"`
- Use high-contrast, accessible colors

---

## Naming Conventions

| Type | Pattern | Example |
|---|---|---|
| Feature LLD | `NNN-kebab.md` (3-digit zero-padded) | `003-transaction-search.md` |
| Bug Report | `BUG-NNN-kebab.md` | `BUG-002-duplicate-ingestion.md` |
| ADR | `ADR-NNN-kebab.md` | `ADR-002-multi-currency.md` |
| Design Doc | `system-component.md` | `api-design.md` |
| Postmortem | `POSTMORTEM-YYYY-MM-DD-kebab.md` | `POSTMORTEM-2026-05-06-auth-token-leak.md` |
| Runbook | `RUNBOOK-kebab.md` | `RUNBOOK-celery-queue-backlog.md` |
| Policy | `topic-policy.md` | `migration-policy.md` |
| Implementation Plan | `YYYY-MM-DD-kebab.md` | `2026-04-06-prediction-engine.md` |
| Research | `NNN-kebab.md` (3-digit zero-padded) | `001-prediction-engine-model-selection.md` |
| Investigation | `kebab.md` | `stale-cache-hypothesis.md` |

---

## Writing Style

1. **Be specific** — "Increases latency by ~200ms" not "might be slower"
2. **Show data flow** — How data enters, transforms, and exits
3. **Name things** — Concrete function/table/endpoint names, not abstractions
4. **No TODOs** — Every section filled. If unknown, write "TBD by [date/person]"
5. **Use diagrams** — A picture is worth a thousand tokens
6. **Version awareness** — Reference specific versions, commits, or dates

---

## Design Doc Sync Rule

After writing any Feature LLD or Bug Report, always check if a Design Doc needs updating:

| Change type | Design Doc to update |
|---|---|
| New or modified API endpoints | `docs/design/api-design.md` |
| Schema / DB changes | `docs/design/database-design.md` |
| Architecture / service topology | `docs/design/system-architecture.md` |

Add a changelog entry at the bottom of any Design Doc you update.

---

## Spec Review Rule

After writing or updating ANY doc, run a spec review before committing. The skill bound to
the spec-review situation lives in `.claude/skills-registry.md` — workflow files do not name
the skill directly so plugin changes don't break this rule.

The review evaluates four named gates (see `.claude/skills/design-docs/references/spec-review-gates.md`):

1. **Completeness** — all required sections per this document are present and filled
2. **Evidence** — every claim has a backing artifact (file:line, benchmark, log, citation)
3. **Clarity** — a fresh reader can act on the doc without needing prior conversation context
4. **Consistency** — doc agrees with itself, peer docs, and code

Process:

1. Run spec review (registry: spec-review situation)
2. Fix all issues found, naming the failing gate
3. Re-run until clean (max 3 iterations; surface to user if still failing)
4. Commit only after spec review passes

This applies to all doc types: Feature LLDs, Bug Reports, ADRs, Postmortems, Runbooks, Design Docs, Policies.

---

## Deviation Log Rule

When implementation diverges from a design doc, record it in the Changelog:

```markdown
| YYYY-MM-DD | DEVIATION: [what changed from original design] — [why it changed] |
```

This is distinct from a status-change entry. Its purpose is to explain WHY reality
diverged from the documented intent. A doc without deviation entries that describes
something that no longer matches the code is a silent lie.

---

## Planned Automation (not yet implemented — tracked for future Feature LLDs)

| Item | Description | Status |
|---|---|---|
| Pre-commit Refs: check | Shell hook that blocks `fix:`/`feat:` commits without a `Refs:` line pointing to a real `docs/` file | **Implemented** (`.pre-commit-config.yaml` — `Check Refs line on fix/feat commits`) |
| CI doc-gate job | GitHub Action that requires every `fix:`/`feat:` PR to also modify a file in `docs/bugs/` or `docs/features/` | Planned |
| Stale doc detector | `make check-docs` script: finds docs with `Status: In Progress` and no recent commits referencing them | Planned |
