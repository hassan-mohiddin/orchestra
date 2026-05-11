# Documentation Gate

This rule is auto-loaded on every session. It defines the non-negotiable documentation
obligations that apply at every stage of work.

---

## The Law

**No code change without a design doc. No discussion of solutions without a bug/feature doc.
No doc without a spec review. No fix/feat commit without a Refs: line.**

These are not guidelines. They are gates. Each one blocks the next step until satisfied.

---

## Gate 1: Discovery Gate (fires during investigation)

When you are investigating, researching, or analysing code and you find:
- A defect, broken pipeline, missing data, or dead code
- A constraint violation, wrong path, or unreachable state

**You must:**
1. STOP — do not discuss solutions, do not continue analysis, do not propose improvements
2. Create `docs/bugs/BUG-NNN-name.md` immediately (orchestra:design-docs skill)
3. Run spec review on it (situation: spec review — see `.claude/skills-registry.md`)
4. Commit the bug report: `git commit -m "docs: add BUG-NNN — <name>"`
5. Only then return to investigation or proceed to brainstorm the fix

**This gate fires even if no code is about to be written.**

### Investigation → BUG promotion path

Unconfirmed observations go to `docs/investigations/<scratch-note>.md` (lightweight, unreviewed,
never committed as formal docs).

**Promotion rule:** When an investigation note confirms a defect → graduate it to BUG-NNN
immediately. The investigation file is then either:
- Deleted (preferred — content moved into BUG-NNN doc), OR
- Archived to `docs/archive/investigations/` if it has historical value

Investigation notes that confirm a defect must NOT remain as scratch — they hide real defects
from the gate system. Discovery Gate fires the moment defect is confirmed, regardless of where
the observation started.

---

## Gate 2: Design Gate (fires before any code change)

Before writing any code for a feature or bug fix:

1. Is there a committed design doc (`docs/features/NNN`, `docs/bugs/BUG-NNN`, or `docs/adr/ADR-NNN`)?
2. Has spec review been run and passed on that doc?
3. Has the user approved the doc?

If any answer is NO → do not write code. Go back and satisfy the missing gate.

---

## Gate 3: Spec Review Gate (fires after writing or updating any doc)

After creating or updating ANY doc (Feature LLD, Bug Report, ADR, Design Doc, Policy):

1. Run spec review on the doc (situation: spec review — see `.claude/skills-registry.md`)
2. Fix all issues found
3. Re-review until no issues remain (max 3 iterations; surface to user if still failing)
4. Only commit the doc after spec review passes

**No exceptions for "small" updates.** Adding a changelog entry to a Design Doc still requires
a review pass. The review for a minor update is fast — the discipline is the point.

---

## Gate 4 / Gate 5 — moved to orchestra:commit

Gate 4 (Commit) and Gate 5 (Implementation Sync) → see orchestra:commit skill (skills/commit/references/canon-frozen-guard.md + skills/commit/references/commit-strategy.md).

---

## Quick Reference

```
Investigation finds defect
  → Gate 1: Create BUG-NNN + spec review + commit
  → THEN brainstorm the fix

Investigation note confirms defect
  → Gate 1 promotion: graduate scratch → BUG-NNN, delete or archive scratch

About to write code
  → Gate 2: Design doc exists + spec review passed + user approved?

Writing/updating a doc
  → Gate 3: Run spec review before committing

Gate 4 / Gate 5 → orchestra:commit skill (see references/canon-frozen-guard.md + references/commit-strategy.md)
```

---

## What "Trivially Scoped" Means (bypass for Gates 1–3)

Gates 1–3 may be bypassed ONLY for changes that are ALL of:
- Single misspelled word, string literal, or comment
- No logic change
- No behavioral impact
- Single file

If you are asking whether it qualifies, it does not.

---

## Pitfall rules (industry-research-derived)

### ADR is RECORDED, not deliberated

ADRs capture decisions already made. If your draft has a long "Options Considered" section
weighing alternatives without a chosen direction, you wrote an RFC, not an ADR. SCALE does not
use RFC vocabulary. Two paths:
- Decide first (use grill / brainstorm skills), then record as ADR
- If you genuinely cannot decide alone, surface to user — not to a doc

### LLD vs Plan no-overlap

Feature LLD describes WHAT to build (design, contracts, edge cases).
Plan describes HOW and IN WHAT ORDER to build it (steps, dependencies, sequencing).

A Plan that re-states the LLD's design content is doing the wrong thing. A Plan that
introduces design decisions not in the LLD means the LLD is incomplete — go back and fix it.

### Design Doc decay

Design Docs at `docs/design/<component>.md` are LIVING. After every feature that affects
that component, Gate 5 fires — either deviation entry or status confirmation. Stale Design
Docs lie to future-you and to AI agents. Sync them before the feature commit, never after.
