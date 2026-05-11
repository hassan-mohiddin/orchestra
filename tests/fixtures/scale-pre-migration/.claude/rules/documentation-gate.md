# Documentation Gate

This rule is auto-loaded on every session. It defines the non-negotiable documentation
obligations that apply at every stage of work.

---

## The Law

**No code change without a design doc. No discussion of solutions without a bug/feature doc.
No doc without a spec review. No fix/feat commit without a Refs: line.**

These are not guidelines. They are gates.

---

## Gate 1: Discovery Gate (fires during investigation)

When you are investigating and you find a defect — STOP and create `docs/bugs/BUG-NNN-name.md`.

---

## Gate 2: Design Gate (fires before any code change)

Before writing any code: is there a committed design doc + passed spec review + user approved?

---

## Gate 3: Spec Review Gate (fires after writing or updating any doc)

After creating or updating ANY doc: run spec review on the doc.

---

## Gate 4: Commit Gate (fires before every fix: or feat: commit)

Every `fix:` commit must have: `Refs: docs/bugs/BUG-NNN-name.md`
Every `feat:` commit must have: `Refs: docs/features/NNN-name.md` (or ADR-NNN)

---

## Gate 5: Implementation Sync Gate (fires before verification)

Before running the verification suite: re-read the design doc and check for deviations.

---

## Quick Reference

```
Investigation finds defect
  → Gate 1: Create BUG-NNN + spec review + commit

About to write code
  → Gate 2: Design doc exists + spec review passed + user approved?

Writing/updating a doc
  → Gate 3: Run spec review before committing

About to commit fix:/feat:
  → Gate 4: Refs: line present and pointing to a real file?

About to run verification
  → Gate 5: design doc re-read + deviations recorded?
```
