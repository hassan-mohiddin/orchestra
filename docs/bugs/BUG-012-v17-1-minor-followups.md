# BUG-012: v1.7.1 minor followups (deferred Minors from LLD-008/009/010 + plan iterations)

> **Doc ID:** BUG-012-v17-1-minor-followups
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** Low
> **Status:** Investigating
> **Iteration:** 5

## Observed Behavior

v1.7.0 shipped LLD-008 r7 + LLD-009 r6 + LLD-010 r4 + Plan r4 with Minor findings explicitly deferred to v1.7.1 per user interview-gate direction ("ship without 4th review"). This BUG aggregates the deferred items into a single tracker so they are not lost between releases.

## Expected Behavior

All Minor findings closed in v1.7.1 (or explicitly re-deferred to v1.8+ with rationale).

## Steps to Reproduce

Read the cited attestation paths in `docs/reviews/` for each LLD/plan iteration; cross-reference against current frontmatter of LLD-008/009/010 + plan body for unresolved Minors.

## Environment

- orchestra v1.7.0 tag at `6a4ea94`; this BUG filed in commit `20132da` (one commit after the tag, post-cleanup batch)
- Pytest baseline at v1.7.0 ship: 259. Current (post-BUG-016 + post-T2): 521.

## Root Cause Analysis

User-delegated interview-gate decision per `feedback_spec_review_aggregation.md` memory: ship v1.7.0 with Critical/HIGH closed; defer Minor paperwork. Trade-off accepted to land tiered narrow-change + framework detection + SCALE migration in one window.

The aggregate-tracker pattern itself is the systemic root cause: each multi-LLD release window produces Minor findings that don't gate the tag but do accumulate. Without an explicit cross-release tracker BUG, Minor findings vanish into per-attestation-YAML silos and never get a closure pass. BUG-012 is the first instance of the tracker discipline; future v1.x.y+ releases inherit the pattern (each release's deferred-Minor sweep gets its own BUG-NNN tracker, filed before tag).

## Fix Description

Iterate through the items below; close per LLD-006-r4 narrow-change whitelist (Changelog append + Status flip — see [LLD-006-r4 § Narrow change](../features/006-archive-and-supersession-conventions-r4.md)) OR tiered narrow-change (Minor body edits with `Addresses:` commit-msg lines per [LLD-009 r6 § Tiered narrow-change](../features/009-commit-msg-l2-finalize.md)). Most items here qualify as Minor → tiered narrow-change path eligible.

### LLD-008 r7 deferred Minors

1. ~~**`input_fn=input` pseudocode clarification**~~ — CLOSED 2026-05-11 (commit dogfood batch 1). Inline comment added to install_one_hook pseudocode.
2. ~~**Prompt UX preservation note**~~ — CLOSED 2026-05-11 (LLD-008 batch 3). A5 inline note documenting v1.5+ prompt UX preservation added.
3. ~~**T2 11-file enumeration assertion**~~ — CLOSED 2026-05-11 (BUG-012 r5 batch). Full canonical-set enumeration test added to `tests/test_install_hooks_skill_dir.py::test_cli_templates_dir_full_enumeration` asserting exactly the 11 files in cli/templates/ post-BUG-016 slice 8 (vocabulary-default-1.md). Detects drift in either direction.
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

1. ~~**Cross-doc number lineage Slice 5.2**~~ — CLOSED 2026-05-11 in Plan Phase J (commit `dac0195`-era cleanup batch; lineage verification performed during Phase J post-ship cleanup): verified Plan §Goal (≥252), LLD-008 A9/A10 (150+17=167), LLD-009 A16 (167+53=220 → ≥252), CHANGELOG v1.7.0 entry (150→259) all consistent.
2. ~~**Test-count audit**~~ — CLOSED 2026-05-11 via `docs/plans/2026-05-11-test-quality-audit.md` (commit `a1932bd`). All 132 audited tests KEEP-disposition.

### Post-ship cleanup observations (2026-05-11; numbered #1-#5)

1. **`cli/lint.py` 1367 lines → module split** — Natural seam: `cli/lint/` package with `core.py` (regex constants + Finding dataclass + parsers) / `canon.py` (L2-detect + L2-finalize + tiered + helpers) / `commit.py` (Refs-eligibility + retroactive L2 + commit-range). **DEFERRED to v1.8+** — evaluated 2026-05-11 Phase K and concluded split was YAGNI: file is large but cohesive, well-sectioned, searchable; split would touch 9+ test file imports for marginal benefit. Re-evaluate when a third major v1.8+ addition needs a new home. Re-confirmed defer in r5 (2026-05-11 post-BUG-016: lint.py grew to support canon parser imports; cohesion preserved; YAGNI verdict holds).
2. ~~**`tests/scale_migration_helper.py` → `tools/`**~~ — CLOSED 2026-05-11 via commit `7f581e9` (`refactor: move scale_migration_helper.py from tests/ to tools/scale_migration_core.py`). `tools/migrate_scale_rules.py` now imports cleanly from `tools.scale_migration_core` (correct dependency direction). Verified on-disk: `tests/scale_migration_helper.py` does NOT exist; `tools/scale_migration_core.py` + `tools/migrate_scale_rules.py` both present.
3. ~~**`attestation-template.yaml` → `skills/spec-review/templates/`**~~ — CLOSED 2026-05-11 via LLD-008 r7 → r8 supersession. File moved (git mv preserves history); A3 adjusted to 10 cli/templates artifacts + new skills/spec-review/templates/ dir. Zero code refs; tests untouched.
4. ~~**`docs/design/orchestra-philosophy.md` lint issues**~~ — CLOSED 2026-05-11 via philosophy r1 → r2 supersession. 4 placeholder rows + mermaid gantt colon parse error fixed inline; v1.7.0 Changelog row added.
5. **LLD-008 r8 A3 enumeration drift (10 → 11)** — BUG-016 slice 8 (commit `937a5f0`) added `cli/templates/vocabulary-default-1.md` (generated from `docs/design/controlled-vocabulary.md` canon §4.x) without syncing LLD-008 r8 A3 prose. Reality: 11 files; A3 prose says 10. Detected by T2 enumeration test (this iteration). **Fix path:** tiered narrow-change to LLD-008 r8 A3 in-place + Changelog row (canon-frozen edit, requires `Addresses:` commit-msg line citing BUG-012 r2 attestation finding). Tracked separately as a r5 commit slice.

## Iteration Log

- r1 (2026-05-11) — initial aggregate; pre-shipping fix. Closes/tracks deferred Minors across LLDs + plan + post-ship cleanup observations. Reviewed: `docs/reviews/BUG-012-v17-1-minor-followups-r1.orchestra.review.yaml` (overall_verdict: fail, 12 findings: 4 Important + 8 Minor).
- r2 (2026-05-11) — dogfood batch landed via tiered narrow-change (LLD-009 r6 first real-world use). Closed: LLD-008 r7 Minors #1 (input_fn comment) + #4 (A8 section-header anchor); LLD-009 r6 Minors #3 (3a/3b legend) + #4 (A13 pre-commit.sh ownership). Plan Minors #1 (cross-doc lineage verification) + #2 (test-quality audit) closed via Plan Phase D/J. Remaining open: LLD-008 #2/#3/#5 + LLD-009 #1/#2/#5 + Post-ship cleanup #1-#4 (under original #3-#6 numbering) = 11 items.
- r3 (2026-05-11) — second narrow-change batch landed. Closed: LLD-008 r7 Minors #2 (prompt UX preservation note) + #5 (Skill-Status value-collision example); LLD-009 r6 Minors #1 (D1-D3 verifiability classification) + #2 (mixed anchors → function-anchors) + #5 (A16 CHANGELOG cite verification). Remaining open: LLD-008 #3 (T2 test enumeration — test code, not narrow-change) + Post-ship cleanup #1-#4 (under original #3-#6) = 5 items.
- r4 (2026-05-11) — supersession batch landed (philosophy r1→r2 + LLD-008 r7→r8). Closed: Post-ship #3 (attestation-template move via LLD-008 r8; now renumbered #3 in r5) + #4 (philosophy.md lint blockers via r2; now renumbered #4 in r5). Surfaced new BUG-014 (L4 doc-id-burn rejects bare-name design supersession; --no-verify bypass used; v1.7.1 fix). Remaining open: LLD-008 #3 (T2 test enumeration) + Post-ship #1 (lint.py split — deferred) + Post-ship #2 (scale_migration_helper move — actually already done at commit `7f581e9`, body stale) = 3 items.
- r5 (2026-05-11) — closure batch post-BUG-016. Closed: LLD-008 r7 Minor #3 (T2 full enumeration test — `tests/test_install_hooks_skill_dir.py::test_cli_templates_dir_full_enumeration`) + Post-ship #2 (scale_migration_helper move verified at commit `7f581e9`; body corrected). Surfaced new Post-ship #5 (LLD-008 r8 A3 enumeration drift 10→11 via BUG-016 slice 8; tracked for separate commit slice). Applied 12 r1 attestation findings inline (free edit; Status: Investigating). Renumbered Post-ship cleanup observations #1-#5 (was #3-#6 + new). Reviewed: pending r2 v2 spec-review. Remaining open: Post-ship #1 (lint.py split, deferred v1.8+) + Post-ship #5 (LLD-008 r8 A3 sync, separate commit slice). Target: close A3 sync slice → r2 review pass → user-confirm → Fix Applied.

## Regression Prevention

- Each v1.7.x and v2.0.x ship verifies BUG-012 checklist before tag.
- Test-quality audit handled independently via `docs/plans/2026-05-11-test-quality-audit.md` (commit `a1932bd`; closed Plan r2/r3 Minor #2). Independent of BUG-013 (slash-command naming inconsistency).
- **Canon-frozen-guard discipline that surfaced BUG-014:** When --no-verify is required to bypass an L4 gap (BUG-014 bare-name design supersession case), it MUST be tracked as a new BUG immediately. Pre-commit hook (BUG-010) catches most violations mechanically; the residual gaps are owned by BUG-NNN trackers, not silent precedent.
- **Deferred-Minor leakage prevention between releases:** Each ship's spec-review attestation Minor findings get an aggregate BUG-NNN tracker filed BEFORE the tag commit. Tag commit blocked until tracker exists. Prevents Minors from being forgotten across version boundaries (BUG-012 itself was this discipline's first instance).
- **A3 enumeration drift prevention:** T2 full-enumeration test (closed r5) detects cli/templates/ membership drift programmatically. Future additions to cli/templates/ MUST update both LLD-008 r8 A3 prose + CLI_TEMPLATES_CANONICAL_SET frozenset in the test, in a single tiered narrow-change commit with `Addresses:` line.

## Related Documents

- `docs/features/008-commit-skill-r8.md` — LLD-008 r8 (Implemented; supersedes r7)
- `docs/features/009-commit-msg-l2-finalize.md` — LLD-009 r6 (Implemented)
- `docs/features/010-framework-detection-determinism.md` — LLD-010 r4 (Implemented)
- `docs/plans/2026-05-11-v17-implementation.md` — Plan r4 (Implemented)
- `docs/plans/2026-05-11-test-quality-audit.md` — test-quality audit (commit `a1932bd`)
- `docs/reviews/BUG-012-v17-1-minor-followups-r1.orchestra.review.yaml` — r1 spec-review (overall_verdict: fail; 12 findings)
- `docs/reviews/008-commit-skill-r4.orchestra.review.yaml` + `.codex.review.md` — LLD-008 last reviewed iteration (r5-r6-r7-r8 shipped under interview-gate "ship without 4th review" + r7→r8 supersession; latest on-disk attestation is r8 orchestra-only at `docs/reviews/008-commit-skill-r8.orchestra.review.yaml`)
- `docs/reviews/009-commit-msg-l2-finalize-r2.orchestra.review.yaml` + `.codex.review.md` — LLD-009 last reviewed iteration (r3-r4-r5-r6 shipped under interview-gate; r1 sonnet also present)
- `docs/reviews/010-framework-detection-determinism-r2.orchestra.review.yaml` + `.codex.review.md` — LLD-010 last reviewed iteration (r3-r4 shipped under interview-gate; r1 sonnet also present)
- `docs/reviews/2026-05-11-v17-implementation-r3.orchestra.review.yaml` + `.codex.review.md` — Plan last reviewed iteration (r4 shipped under interview-gate)

**Convention note:** Related Documents tracks the LATEST attestation on-disk and notes when the doc-iteration has advanced beyond the attestation-iteration (interview-gate "ship without 4th review" pattern shipped r5-r8 for LLD-008 + r3-r6 for LLD-009 + r3-r4 for LLD-010 + r4 for the plan without fresh attestations). This BUG itself is the deferred-Minor tracker for those un-attested iterations. r5 sync done in this commit batch.

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | BUG filed post-v1.7.0 ship to aggregate deferred Minors across 3 LLDs + plan + post-ship cleanup observations. Severity: Low (paperwork-grade; no behavioral defects). Status: Investigating. Target: v1.7.1. |
| 2026-05-11 | r5 closure batch: applied 12 r1 attestation findings inline (Iteration field added; Related Documents paths corrected to current iterations + per-judge suffix; Post-ship cleanup renumbered #1-#5; BUG-013 cross-ref corrected; Regression Prevention expanded). Closed LLD-008 #3 (T2 enumeration test) + Post-ship #2 (scale_migration_helper already moved at `7f581e9`). Surfaced Post-ship #5 (LLD-008 r8 A3 enumeration drift). Remaining open: Post-ship #1 (lint.py split, deferred v1.8+) + Post-ship #5 (A3 sync slice). |
