# orchestra Workflow

> **Purpose:** Master workflow for ALL code changes in orchestra. Pure situation language — no
> skill names. Skill bindings live in `.claude/skills-registry.md`.

This file is auto-loaded on every session and routes all code-change work.

---

## When to use

For ANY of: new feature, bug fix, architectural decision, or any work that changes code.
Also fires when investigation reveals a defect (Phase 0 below).

---

## The 8-step pipeline

```
Phase 0: Investigate     → Discovery Gate fires when defect found
Step 1: Brainstorm        → interview-style grilling, project-aware
Step 2: Document          → design doc + spec review
Step 3: Plan              → multi-step sequencing (saved to docs/plans/)
Step 4: Execute           → TDD vertical slicing
Step 4.5: Doc sync        → record deviations
Step 5: Self review       → terse, line-by-line
Step 5.5: Adversarial     → optional second opinion (different model)
Step 6: Verify            → tests pass + pyrefly clean + (for bugs) user confirmation
Step 7: Commit            → conventional commit + Refs: line + Design Doc sync
```

---

## Phase 0 — Investigation reveals a defect

If you are investigating, researching, or analyzing code and find a defect (broken
pipeline, missing data, dead code, constraint violation, wrong path, unreachable state):

1. **STOP** — do not continue analysis, do not propose solutions
2. Create the Bug Report immediately (`docs/bugs/BUG-NNN-name.md`) using the design-doc situation
3. Run spec review on it
4. Commit: `git commit -m "docs: add BUG-NNN — <name>"`
5. Only THEN proceed to Step 1 (brainstorm the fix)

Promotion: investigation scratch notes that confirm a defect graduate to BUG-NNN. Delete or archive the scratch.

See `rules/documentation-gate.md` Gate 1 for full rule.

---

## Step 1 — Brainstorm

Interview-style grilling, project-aware. The session reads existing project docs (orchestra-philosophy, ADRs) so questions are grounded in actual decisions, not generic.

- Run for as many rounds as user needs — no fixed limit
- Exit criteria: user explicitly says they're satisfied with the direction
- Do NOT shortcut

Brainstorming IS this step. Do not brainstorm separately and then start the workflow — same thing.

---

## Step 2 — Document

Create the design doc per work type:

| Work type | Path |
|---|---|
| New feature | `docs/features/NNN-name.md` (Feature LLD) |
| Bug fix | `docs/bugs/BUG-NNN-name.md` (Bug Report) |
| Architectural decision | `docs/adr/ADR-NNN-name.md` (ADR — recorded decision) |
| System component update | `docs/design/<component>.md` (Design Doc — living, bare-name) |
| Postmortem | `docs/postmortems/NNN-name.md` |
| Runbook | `docs/runbooks/NNN-name.md` |

Required: Mermaid diagram for non-trivial designs, all required sections per `docs/STANDARDS.md`.

**Run spec review before committing.** Fix all issues. No commit until spec review passes.

```bash
git add docs/
git commit -m "docs: add LLD for <name>"
```

Exit criteria: user approves doc AND spec review passes.

**Spec-review v2 (LLD-011, shipped v2.0.0)**: `/orchestra:spec-review <doc>` dispatches 6 parallel sub-judges (`structure`, `semantic` [mandatory], `gate-compliance`, `adversarial` [mandatory], `repo-context`, `architectural-fit`) via single-message Task fanout. `semantic` preserves the v1 4-gate rubric (Completeness / Evidence / Clarity / Consistency); the other 5 expand depth (red-team, citation validity, architectural-fit). Mandatory-tier failure forces `overall_verdict: fail`. Mechanical aggregator (no LLM merge) dedupes by location+fuzzy-hash, takes max severity, unions raised_by. Provenance recorded via `git hash-object -w` (iter_blob_sha) + git HEAD (iter_commit_sha). Iter-2 delta-review uses the stored blob for diff. 2-iter post-commit hard cap (`--override-cap` for iter-3+ with interview-gate confirmation). Attestation lands at `docs/reviews/<doc-id>-rN.orchestra.review.yaml` (schema v2.0). Full LLD: `docs/features/011-spec-review-v2.md`.

---

## Step 3 — Plan (multi-step only)

For multi-step features, write an implementation plan.

- Save to `docs/plans/YYYY-MM-DD-name.md` (NOT to any plugin-specific path)
- TaskCreate entries also created from the plan
- Skip this step entirely for trivially-scoped or single-step changes
- Exit criteria: user approves the plan

**Pitfall — LLD vs Plan no-overlap:** LLD describes WHAT to build. Plan describes HOW and IN WHAT ORDER. A plan re-stating LLD design content is wrong. A plan introducing design decisions not in the LLD means the LLD is incomplete — fix the LLD first.

---

## Step 4 — Execute (TDD vertical slicing)

**Vertical slicing:** one test → one implementation → repeat. NOT all-tests-then-all-implementation (horizontal). Horizontal slicing produces tests of imagined behavior, not actual.

- RED → GREEN → REFACTOR per slice
- **Iron rule:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
- TaskCreate entry per slice, update status as you go
- Commit after each logical unit

| Prefix | When |
|---|---|
| `feat:` | New feature implementation (with `Refs: docs/features/...`) |
| `fix:` | Bug fix (with `Refs: docs/bugs/BUG-NNN-...`) — **only after user confirms** |
| `test:` | Adding/updating tests |
| `refactor:` | Code restructuring, no behavior change |
| `chore:` | Maintenance, config, Design Doc sync |
| `docs:` | Documentation-only changes |
| `wip:` | Work-in-progress during bug iteration loops |

---

## Step 4.5 — Implementation Doc Sync

Before running verification, re-read the design doc and reconcile against what you built.

If reality diverged → add a `DEVIATION:` changelog entry explaining what changed and why.
If matches → add a confirmation entry: `Implementation matches design. Status → Implemented`.

Commit doc update before verification. Never verify against a stale doc.

---

## Step 5 — Self review

Run a fast, comment-style review on your own diff. Fix nits, naming, dead code, missed edge cases. Discipline is the point — first reviewer is yourself.

---

## Step 5.5 — Adversarial review (optional)

Use when:
- Change touches lint enforcement, commit gates, or canon-frozen-doc handling
- Change is large enough that a different model's perspective would catch blind spots
- You suspect the design has issues you can't see

Skip for trivially-scoped changes.

---

## Step 6 — Verify

Definition of Done — ALL must pass:

| Check | Command |
|---|---|
| Tests | `.venv/bin/python -m pytest` |
| Type check | `pyrefly check` |
| Lint (dogfood) | `.venv/bin/python -m cli.lint` |
| Eval (when relevant) | `.venv/bin/python -m cli.eval` |

Run each command. Read actual output. Don't assume.

If ANY fail → back to Step 4.
If ALL pass → update doc status to `Verified`.

### Bug iteration — user confirmation gate

For bug fixes, tests passing is necessary but **NOT sufficient**. The user must confirm the bug is actually resolved.

If user says "still broken":
1. **Same BUG-NNN doc** — never create a new one. One BUG-NNN per defect, lifetime spans iterations.
2. Append iteration entry to BUG-NNN Iteration Log: hypothesis tried, what changed, observed result.
3. Loop back to Step 4 (Execute) with new vertical slice.
4. NO `fix:` commit. Use `wip:` prefix during iteration.
5. Repeat until user explicitly confirms.

When user confirms:
- Update BUG-NNN status to `Verified`
- Consolidate WIP into one `fix:` commit (or squash) with `Refs: docs/bugs/BUG-NNN-name.md`

---

## Step 7 — Final commit

1. Update doc status to `Implemented` (if not already `Verified`)
2. Re-check Design Doc sync: did implementation deviate from `docs/design/<component>.md`?
3. Update affected Design Doc(s) + add changelog entries (narrow-change for canon-frozen Design Docs)
4. Final commit: `chore: update Design Doc and finalize <feature-name>`

---

## Transition rules

| From | To | Trigger |
|---|---|---|
| Brainstorm | Document | User satisfied |
| Document | Plan | User approves docs |
| Plan | Execute | User approves plan |
| Execute | Self review | Slice complete |
| Self review | Adversarial review | Optional, user choice |
| Self/Adversarial review | Verify | Reviews clean |
| Verify PASS | Final Commit | Evidence + (for bugs) user confirmation |
| Verify FAIL | Execute | Fix issues, re-verify, same doc |
| Any step | Brainstorm | Fundamental flaw discovered |

---

## Skill bindings

This file uses situation language. The skill bound to each situation lives in
`.claude/skills-registry.md`. When you need to "run spec review", look up the
spec-review situation in the registry and use that skill.

If the registry's bound skill is not in the current session's available-skills list:
1. Check whether the plugin is enabled (settings + `/reload-plugins`)
2. If still missing → tell user, do NOT silently skip the step

Override rules (alternate paths, suppression, etc.) live in `.claude/skills-registry.md` under "Override rules."
