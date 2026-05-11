# BUG-012: v1.7.1 minor followups (deferred Minors from LLD-008/009/010 + plan iterations)

> **Doc ID:** BUG-012-v17-1-minor-followups
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** Low
> **Status:** Investigating

## Observed Behavior

v1.7.0 shipped LLD-008 r7 + LLD-009 r6 + LLD-010 r4 + Plan r4 with Minor findings explicitly deferred to v1.7.1 per user interview-gate direction ("ship without 4th review"). This BUG aggregates the deferred items into a single tracker so they are not lost between releases.

## Expected Behavior

All Minor findings closed in v1.7.1 (or explicitly re-deferred to v1.8 with rationale).

## Steps to Reproduce

Read the cited attestation paths in `docs/reviews/` for each LLD/plan iteration; cross-reference against current frontmatter of LLD-008/009/010 + plan body for unresolved Minors.

## Environment

- orchestra v1.7.0 (commit `20132da` post-cleanup; tag `v1.7.0` at `6a4ea94`)
- Pytest baseline 259

## Root Cause

User-delegated interview-gate decision per `feedback_spec_review_aggregation.md` memory: ship v1.7.0 with Critical/HIGH closed; defer Minor paperwork. Trade-off accepted to land tiered narrow-change + framework detection + SCALE migration in one window.

## Fix Description

Iterate through the items below; close per LLD-006-r4 narrow-change whitelist (Changelog append + Status flip) OR tiered narrow-change (Minor body edits with `Addresses:` commit-msg lines). Most items here qualify as Minor → tiered narrow-change path eligible.

### LLD-008 r7 deferred Minors

1. ~~**`input_fn=input` pseudocode clarification**~~ — CLOSED 2026-05-11 (commit dogfood batch 1). Inline comment added to install_one_hook pseudocode.
2. ~~**Prompt UX preservation note**~~ — CLOSED 2026-05-11 (LLD-008 batch 3). A5 inline note documenting v1.5+ prompt UX preservation added.
3. **T2 11-file enumeration assertion** — A3 lists 11 init-related artifacts retained in `cli/templates/`; test currently asserts presence of representative subset only. Add full enumeration assertion. (Test code change; non-narrow.)
4. ~~**A8 section-header citation**~~ — CLOSED 2026-05-11 (commit dogfood batch 1). Line range 109-128 replaced with `## Quick Reference` section-header anchor.
5. ~~**Skill-Status value-collision documentation**~~ — CLOSED 2026-05-11 (LLD-008 batch 3). Explicit value-collision example added to Skill-Status field-name divergence note.

### LLD-009 r6 deferred Minors

1. ~~**D1-D3 verifiability classification**~~ — CLOSED 2026-05-11 (LLD-009 batch 3). Verification mechanism marked per deliverable (manual / doc-deliverable).
2. ~~**Mixed line/function anchors**~~ — CLOSED 2026-05-11 (LLD-009 batch 3). Glossary + A6 + Related Documents converted to function-anchors (§ CANON_FROZEN_STATUSES, § CONVENTIONAL_PREFIX_RE).
3. ~~**3a/3b sub-numbering convention**~~ — CLOSED 2026-05-11 (commit dogfood batch 2). One-line legend added to Edge Cases § 3a/3b.
4. ~~**pre-commit.sh canonical content inline**~~ — CLOSED 2026-05-11 (commit dogfood batch 2). A13 reworded to clarify LLD-008 ships file / LLD-009 specifies content (mirrors A12 commit-msg.sh split).
5. ~~**A16 third-place CHANGELOG cite verification**~~ — CLOSED 2026-05-11 (LLD-009 batch 3). CHANGELOG.md v1.7.0 entry (150 → 259) verified matches A16 cite; post-ship actual numbers added inline.

### LLD-010 r4 deferred Minors

Per LLD-010 r4 Changelog entry, r4 was paperwork-only cascading edit; no internal Minors deferred. All r2/r3 Minors closed in r3/r4.

### Plan r2/r3 deferred Minors

1. ~~**Cross-doc number lineage Slice 5.2**~~ — CLOSED 2026-05-11 in Phase J: verified Plan §Goal (≥252), LLD-008 A9/A10 (150+17=167), LLD-009 A16 (167+53=220 → ≥252), CHANGELOG v1.7.0 entry (150→259) all consistent.
2. ~~**Test-count audit**~~ — CLOSED 2026-05-11 via `docs/plans/2026-05-11-test-quality-audit.md` (commit `a1932bd`). All 132 audited tests KEEP-disposition.

### Post-ship cleanup observations (2026-05-11)

3. **`cli/lint.py` 1367 lines → module split** — Natural seam: `cli/lint/` package with `core.py` (regex constants + Finding dataclass + parsers) / `canon.py` (L2-detect + L2-finalize + tiered + helpers) / `commit.py` (Refs-eligibility + retroactive L2 + commit-range). **Defer to v1.8+** — evaluated 2026-05-11 Phase K and concluded split was YAGNI: file is large but cohesive, well-sectioned, searchable; split would touch 9+ test file imports for marginal benefit. Re-evaluate when a third major v1.8+ addition needs a new home.
4. **`tests/scale_migration_helper.py` → `tools/`** — `tools/migrate_scale_rules.py` imports from `tests/` (wrong dependency direction). Promote helper out of tests/.
5. ~~**`attestation-template.yaml` → `skills/spec-review/templates/`**~~ — CLOSED 2026-05-11 via LLD-008 r7 → r8 supersession. File moved (git mv preserves history); A3 adjusted to 10 cli/templates artifacts + new skills/spec-review/templates/ dir. Zero code refs; tests untouched.
6. ~~**`docs/design/orchestra-philosophy.md` lint issues**~~ — CLOSED 2026-05-11 via philosophy r1 → r2 supersession. 4 placeholder rows + mermaid gantt colon parse error fixed inline; v1.7.0 Changelog row added.

## Iteration Log

- r1 (2026-05-11) — initial aggregate; pre-shipping fix. Closes/tracks deferred Minors across LLDs + plan + post-ship cleanup observations.
- r2 (2026-05-11) — dogfood batch landed via tiered narrow-change (LLD-009 r6 first real-world use). Closed: LLD-008 r7 Minors #1 (input_fn comment) + #4 (A8 section-header anchor); LLD-009 r6 Minors #3 (3a/3b legend) + #4 (A13 pre-commit.sh ownership). Plan Minors #1 (cross-doc lineage verification) + #2 (test-quality audit) closed via Phase D/J. Remaining open: LLD-008 #2/#3/#5 + LLD-009 #1/#2/#5 + Post-ship cleanup #1/#2/#3/#5/#6 = 11 items.
- r3 (2026-05-11) — second narrow-change batch landed. Closed: LLD-008 r7 Minors #2 (prompt UX preservation note) + #5 (Skill-Status value-collision example); LLD-009 r6 Minors #1 (D1-D3 verifiability classification) + #2 (mixed anchors → function-anchors) + #5 (A16 CHANGELOG cite verification). Remaining open: LLD-008 #3 (T2 test enumeration — test code, not narrow-change) + Post-ship cleanup #1/#2/#3/#5/#6 = 6 items.
- r4 (2026-05-11) — supersession batch landed (philosophy r1→r2 + LLD-008 r7→r8). Closed: §Post-ship cleanup #5 (attestation-template move via LLD-008 r8) + #6 (philosophy.md lint blockers via r2). Surfaced new BUG-014 (L4 doc-id-burn rejects bare-name design supersession; --no-verify bypass used; v1.7.1 fix). Remaining open: LLD-008 #3 (T2 test enumeration) + Post-ship cleanup #1/#2/#3 = 4 items.

## Regression Prevention

- Each v1.7.x ship verifies BUG-012 checklist before tag.
- BUG-013 (test-quality audit) handles item §Plan r2/r3 #2 independently if surfaced.

## Related Documents

- `docs/features/008-commit-skill.md` — LLD-008 r7 (Implemented)
- `docs/features/009-commit-msg-l2-finalize.md` — LLD-009 r6 (Implemented)
- `docs/features/010-framework-detection-determinism.md` — LLD-010 r4 (Implemented)
- `docs/plans/2026-05-11-v17-implementation.md` — Plan r4
- `docs/reviews/008-commit-skill-r4.review.yaml` + `.codex.md`
- `docs/reviews/009-commit-msg-l2-finalize-r2.review.yaml` + `.codex.md`
- `docs/reviews/010-framework-detection-determinism-r2.review.yaml` + `.codex.md`
- `docs/reviews/2026-05-11-v17-implementation-r3.review.yaml` + `.codex.md`

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | BUG filed post-v1.7.0 ship to aggregate deferred Minors across 3 LLDs + plan + post-ship cleanup observations. Severity: Low (paperwork-grade; no behavioral defects). Status: Investigating. Target: v1.7.1. |
