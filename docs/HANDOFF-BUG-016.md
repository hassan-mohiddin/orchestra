# Handoff — BUG-016 Controlled Vocabulary Canon (parallel agent session)

> **Created:** 2026-05-11
> **Author:** Claude Opus 4.7 (during LLD-011 spec-review v2 grilling)
> **For:** parallel agent session led by Hassan
> **Status:** ready to start

---

## What this session needs to design

A **single controlled-vocabulary canon** for orchestra, plus a migration plan from current scattered state to canon. See `docs/bugs/BUG-016-scattered-vocabulary-no-canon.md` for the full defect catalog.

Output of the session: a Design Doc (likely `docs/design/controlled-vocabulary.md`) plus an implementation plan that retires the scattered copies.

This is **a Design Doc effort, not a Bug Fix.** BUG-016 catalogues the defect; this session designs the canon and the migration. The canon itself is a LIVING component-level artifact.

---

## Why this session was spun off

This issue surfaced during the LLD-011 spec-review v2 grill (2026-05-11). PDSA (Pre-Dispatch Self-Audit) Phase 2 of spec-review v2 wants strict enum validation against a canonical vocabulary — but no canon exists. Folding the canon design into LLD-011 would balloon its scope. Spinning it out keeps both LLDs coherent.

PDSA Phase 2 ships with heuristic enum checks against current scattered sources. When this session's canon lands, PDSA tightens to strict match — one-line code change per check.

---

## Scope (what to decide)

1. **Canon location and format.** Options:
   - Single Design Doc with embedded canonical tables: `docs/design/controlled-vocabulary.md` (human-first)
   - Machine-readable YAML: `docs/vocabulary/canon.yaml` (code-first; doc cross-references it)
   - Upgrade `docs/STANDARDS.md` to be the canon itself (no new file)
   - Hybrid: `docs/design/controlled-vocabulary.md` *is* the canon, but `cli/lint.py` parses canonical sections from it at import time
2. **Enums to canonicalize.** At minimum:
   - `status_enum_per_doc_type` (currently `cli/lint.py § STATUS_ENUMS`)
   - `canon_frozen_statuses` (currently `cli/lint.py § CANON_FROZEN_STATUSES`)
   - `refs_eligible_prefixes`
   - `allowed_attestation_path_prefixes`
   - `severity_enums` per consumer (Bug / Postmortem / Runbook / spec-review-finding)
   - `verdict_enum`
   - `doc_type_enum`
   - `required_sections_per_doc_type`
3. **Filename and naming conventions to canonicalize.**
   - Doc filename grammar per doc-type (already partly in `LLD-006-r4`; promote to canon)
   - Review-doc filename convention per peer-judge format — orchestra writes `<doc-id>-rN.review.yaml`; codex writes `<doc-id>-rN.codex.md`; no enforced canon. Decide: every peer-judge appends `.<judge>.review.<ext>`? Or stick with native?
   - Terminal-state suffix conventions (`Rejected`, `Superseded`, `Archived`)
4. **Severity-term reconciliation.** Currently three different families:
   - Bug Reports use `Critical | High | Medium | Low`
   - spec-review findings use `Critical | Important | Minor`
   - Postmortems use `SEV1-4`; Runbooks use `P1-P3`
   - Decide: unify? Document why they're different axes? Re-bind some of them?
5. **Migration plan.** How to retire the scattered copies:
   - `cli/lint.py § STATUS_ENUMS` → load from canon at import
   - `cli/templates/standards-default-7.md` → generated from canon, or canon-referencing
   - `docs/STANDARDS.md` → reconcile with canon (or become canon)
   - `skills/spec-review/attestation-schema-v1.0.json` → load enums from canon
6. **L5 lint check** (new) — strict enum match for every doc's metadata.
7. **Backward compatibility.** Existing docs already use scattered enum values. Migration must not break L1/L2/L3/L4 lint on the existing corpus. Either canonize current values exactly, or add a grace period.

---

## Out of scope

- Designing or building LLD-011 (spec-review v2). That LLD owns its own scope; this session feeds it the canon to reference (eventually). They run in parallel.
- Adding new vocabularies that don't exist today. Goal is consolidation, not expansion.
- Changing the doc taxonomy itself (Feature LLD vs Bug Report vs ADR etc.) — that's `LLD-006-r4` territory.

---

## Investigation starting points (file:line)

- `cli/lint.py:62-94` — every scattered enum lives here in code form.
- `docs/STANDARDS.md:13-104, 115-222, 250-261` — human-readable copies.
- `cli/templates/standards-default-7.md:30-186` — template-mirror copy.
- `cli/templates/mkdocs_hooks.py:15-23` — yet another consumer.
- `skills/spec-review/attestation-schema-v1.0.json` — spec-review-finding severity / verdict.
- `skills/spec-review/prompt-template.md:64-67` — prompt-side severity copy.
- `docs/bugs/BUG-014-l4-bare-name-design-supersession.md` — adjacent issue: filename grammar inconsistency at L4 lint.
- `docs/HANDOFF.md` — orchestra overall handoff (read this first for repo state).
- `docs/features/006-...-r4.md` (LLD-006-r4) — current filename grammar canon (will likely fold into the new canon).

---

## Recommended workflow for this session

1. **Read** the files above + BUG-016 in full.
2. **Decide** canon location and format (option 1-4 above) — interview Hassan first, blast radius is high.
3. **Draft Design Doc** `docs/design/controlled-vocabulary.md` with embedded canonical tables. Status: Draft.
4. **Spec-review the Design Doc.** (When LLD-011 v2 ships, run the multi-judge version; until then, use v1 spec-review.)
5. **Write migration plan** in `docs/plans/YYYY-MM-DD-vocab-canon-migration.md` — tasks, sequencing, test strategy. Should NOT re-state Design Doc decisions; describes order of operations.
6. **Surface** to Hassan for approval before implementing.
7. **Implement** in vertical slices per the plan. TDD: each lint enum migration starts with a failing test that demonstrates current behavior, then refactors to load from canon.
8. **Update BUG-016 Iteration Log** as work progresses. Close when canon ships + all scattered copies retired.

---

## Constraints (read these first)

- **Orchestra workflow rules apply.** All work must follow `.claude/workflow.md` + `.claude/rules/documentation-gate.md`. Design Doc before code, spec-review before commit, etc.
- **Dogfood.** Orchestra's own canon is subject to orchestra's own gates. No exceptions.
- **No breaking changes to existing docs.** Migration must preserve current valid metadata values; if reconciliation requires renaming a value, write a migration that updates all existing docs in lockstep.
- **Parallel session.** LLD-011 (spec-review v2) is being designed in another session. Coordinate on shared touchpoints (PDSA strict-enum-match upgrade, review-doc filename convention) but do not block on each other.

---

## Open questions Hassan flagged

- "all the vocabulary and glossary for the docs should be fixed (like all the options for 'status' should be saved in a vocabular file or something similar)"
- "each file's naming should be fixed, rejected or superseeded or anything else naming should be fixed"
- "review docs naming and conventions should be fixed"
- "status's or anything that is a variable and is not constant that changes needs to have a pre set option (or vocabulary) that it will be one of this"
- Goal: zero scope for ambiguity in any doc field that has a discrete set of valid values.

These should be addressed in the Design Doc.

---

## When to surface to Hassan

- Before locking in canon location/format (blast radius > 10 min undo).
- Before reconciling severity term families (semantic choice with downstream impact).
- Before deciding review-doc filename convention (coordinates with LLD-011).
- When migration plan is drafted (sign-off before implementation).
- Anytime a silent design decision would normally be made (per `.claude/rules/interview-gate.md`).

Otherwise: proceed with reasonable defaults and report back.
