# BUG-012: v1.7.1 minor followups (deferred Minors from LLD-008/009/010 + plan iterations)

> **Doc ID:** BUG-012-v17-1-minor-followups
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** Low
> **Status:** Fix Applied
> **Iteration:** 6

**Severity note:** `Low` matches canon §4.2 `bug_severity = {Critical, High, Medium, Low}`. This is a paperwork-grade tracker (no behavioral defect); Low is correct.

**Doc ID note:** Filename `BUG-012-v17-1-minor-followups.md` encodes the version segment `v17-1` (= "v1.7.1") with an internal hyphen. This is canon §4.10 bug grammar `BUG-NNN-name(-rN)?.md` compliant (`v17-1-minor-followups` is the `name` segment; iteration-suffix `-rN` is reserved for filename revisions and never used here since BUG-012 is a single first-iteration filename — iterations are tracked via Iteration Log entries, not by `-rN` filename revisions). No L4 grammar collision possible.

## Observed Behavior

v1.7.0 shipped LLD-008 r7 + LLD-009 r6 + LLD-010 r4 + Plan r4 with Minor findings explicitly deferred to v1.7.1 per user interview-gate direction ("ship without 4th review"). This BUG aggregates the deferred items into a single tracker so they are not lost between releases.

## Expected Behavior

All Minor findings closed in v1.7.1 (or explicitly re-deferred to v1.8+ with rationale).

## Steps to Reproduce

Read the cited attestation paths in `docs/reviews/` for each LLD/plan iteration; cross-reference against current frontmatter of LLD-008/009/010 + plan body for unresolved Minors.

## Environment

- orchestra v1.7.0 tag at `6a4ea94`; this BUG filed in commit `20132da` (one commit after the tag, post-cleanup batch)
- Pytest baseline at v1.7.0 ship: 259. Current (post-BUG-016 + post-T2 + post-BUG-001-WIP): 521 (verified `2026-05-11` against HEAD `a35a0f7`; +1 from T2 commit `8af4b45`, +2 from BUG-001 parallel-session WIP per HANDOFF — exact provenance via `git log --since=2026-05-09 --oneline tests/`).

## Root Cause Analysis

User-delegated interview-gate decision per `feedback_spec_review_aggregation.md` memory: ship v1.7.0 with Critical/HIGH closed; defer Minor paperwork. Trade-off accepted to land tiered narrow-change + framework detection + SCALE migration in one window.

The aggregate-tracker pattern itself is the systemic root cause: each multi-LLD release window produces Minor findings that don't gate the tag but do accumulate. Without an explicit cross-release tracker BUG, Minor findings vanish into per-attestation-YAML silos and never get a closure pass. BUG-012 is the first instance of the tracker discipline; future v1.x.y+ releases inherit the pattern (each release's deferred-Minor sweep gets its own BUG-NNN tracker, filed before tag).

## Fix Description

Iterate through the items below; close per LLD-006-r4 narrow-change whitelist (Changelog append + Status flip — see [LLD-006-r4 § Narrow change](../features/006-archive-and-supersession-conventions-r4.md)) OR tiered narrow-change (Minor body edits with `Addresses:` commit-msg lines per [LLD-009 r6 § Tiered narrow-change](../features/009-commit-msg-l2-finalize.md)). Most items here qualify as Minor → tiered narrow-change path eligible.

### LLD-008 r7 deferred Minors

1. ~~**`input_fn=input` pseudocode clarification**~~ — CLOSED 2026-05-11 (commit dogfood batch 1). Inline comment added to install_one_hook pseudocode.
2. ~~**Prompt UX preservation note**~~ — CLOSED 2026-05-11 (LLD-008 batch 3). A5 inline note documenting v1.5+ prompt UX preservation added.
3. ~~**T2 11-file enumeration assertion**~~ — CLOSED 2026-05-11 (BUG-012 r5 batch; commit `8af4b45`). Full canonical-set enumeration test added to `tests/test_install_hooks_skill_dir.py::test_cli_templates_dir_full_enumeration` asserting exactly the 11 files in cli/templates/ post-BUG-016 slice 8 (vocabulary-default-1.md). Detects drift in either direction. **Test/A3-prose disagreement note:** As of r5, the test asserts 11 (matches reality) while LLD-008 r8 A3 prose still says 10 — A3 sync is tracked separately as §Post-ship cleanup #5 below. The test is the authoritative canon; A3 prose is stale and will be synced in the next commit slice (r6 body sync first, A3 sync second, since LLD-008 r8 is canon-frozen and requires tiered narrow-change with an attestation finding to address).
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
5. **LLD-008 r8 A3 enumeration drift (10 → 11)** — BUG-016 slice 8 (commit `937a5f0`) added `cli/templates/vocabulary-default-1.md` (generated from `docs/design/controlled-vocabulary.md` canon §4.x) without syncing LLD-008 r8 A3 prose. Reality: 11 files; A3 prose says 10. Detected by T2 enumeration test (this iteration). **Status: BLOCKED on `BUG-018` (`docs/bugs/BUG-018-lint-addresses-validator-v2-schema-gap.md`, iter-2, Status: Investigating, High).** The A3 sync requires tiered narrow-change `Addresses:` line per LLD-009 r6 §A6 citing a v2.0 attestation — `cli.lint § _verify_finding_in_attestation` rejects v2.0 attestation paths (looks for v1.0 `gates.<gate>.findings` path; v2.0 has flat `findings_aggregated[]` + `sub_judges[].findings[]`). Repro captured in BUG-018 §Observed Behavior. **Reclassification (r6, 2026-05-12):** Post-ship #5 is now **tracking-only**, not blocking — BUG-012 closes once r6 v2 review passes; A3 prose sync lands in v2.0.1 patch cycle after BUG-018 ships the validator fix. Discipline-layer documentation in §Regression Prevention covers the gap: T2 test (mechanical) is the canonical source of truth for cli/templates/ membership; A3 prose at 10 is a stale prose artifact that does not affect runtime behavior or any code path. **Owner:** BUG-018 closure unblocks; **then** Hassan owns the A3 sync commit slice.

## Iteration Log

- r1 (2026-05-11) — initial aggregate; pre-shipping fix. Closes/tracks deferred Minors across LLDs + plan + post-ship cleanup observations. Reviewed: `docs/reviews/BUG-012-v17-1-minor-followups-r1.orchestra.review.yaml` (overall_verdict: fail, 12 findings: 4 Important + 8 Minor).
- r2 (2026-05-11) — dogfood batch landed via tiered narrow-change (LLD-009 r6 first real-world use). Closed: LLD-008 r7 Minors #1 (input_fn comment) + #4 (A8 section-header anchor); LLD-009 r6 Minors #3 (3a/3b legend) + #4 (A13 pre-commit.sh ownership). Plan Minors #1 (cross-doc lineage verification) + #2 (test-quality audit) closed via Plan Phase D/J. Remaining open: LLD-008 #2/#3/#5 + LLD-009 #1/#2/#5 + Post-ship cleanup #1-#4 (under original #3-#6 numbering) = 11 items.
- r3 (2026-05-11) — second narrow-change batch landed. Closed: LLD-008 r7 Minors #2 (prompt UX preservation note) + #5 (Skill-Status value-collision example); LLD-009 r6 Minors #1 (D1-D3 verifiability classification) + #2 (mixed anchors → function-anchors) + #5 (A16 CHANGELOG cite verification). Remaining open: LLD-008 #3 (T2 test enumeration — test code, not narrow-change) + Post-ship cleanup #1-#4 (under original #3-#6) = 5 items.
- r4 (2026-05-11) — supersession batch landed (philosophy r1→r2 + LLD-008 r7→r8). Closed: Post-ship #3 (attestation-template move via LLD-008 r8; now renumbered #3 in r5) + #4 (philosophy.md lint blockers via r2; now renumbered #4 in r5). Surfaced new BUG-014 (L4 doc-id-burn rejects bare-name design supersession; --no-verify bypass used; v1.7.1 fix). Remaining open: LLD-008 #3 (T2 test enumeration) + Post-ship #1 (lint.py split — deferred) + Post-ship #2 (scale_migration_helper move — actually already done at commit `7f581e9`, body stale) = 3 items.
- r5 (2026-05-11) — closure batch post-BUG-016. Closed: LLD-008 r7 Minor #3 (T2 full enumeration test — `tests/test_install_hooks_skill_dir.py::test_cli_templates_dir_full_enumeration`, commit `8af4b45`) + Post-ship #2 (scale_migration_helper move verified at commit `7f581e9`; body corrected). Surfaced new Post-ship #5 (LLD-008 r8 A3 enumeration drift 10→11 via BUG-016 slice 8; tracked for separate commit slice). Applied 12 r1 attestation findings inline (free edit, Status: Investigating; commits `c1259d0` + `3b80fb9`). Renumbered Post-ship cleanup observations #1-#5 (was #3-#6 + new). r5 v2 spec-review attestation: `docs/reviews/BUG-012-v17-1-minor-followups-r5.orchestra.review.yaml` (overall_verdict: fail; 32 deduped findings: 3 Critical [all adversarial], 15 Important, 14 Minor; repo-context pass). Remaining open: Post-ship #1 (lint.py split, deferred v1.8+) + Post-ship #5 (LLD-008 r8 A3 sync, separate commit slice).

  **r1 finding closure table (12 r1 findings → r5 body edits):**

  | r1 Gate | r1 Finding | Severity | Closure in r5 body | Commit |
  |---|---|---|---|---|
  | Completeness | Iteration field missing in frontmatter | Minor | Added `Iteration: 5` | `c1259d0` |
  | Completeness | Regression Prevention thin | Minor | Expanded with 3 new prevention rules | `c1259d0` |
  | Evidence | Related Docs path `008-commit-skill.md` should be `-r8.md` | Important | Path corrected | `c1259d0` |
  | Evidence | Post-ship #4 `scale_migration_helper.py` non-reproducible | Important | Renumbered as #2 + struck-through with commit `7f581e9` cite | `c1259d0` |
  | Evidence | Environment commit-lineage relationship unclear | Minor | Reworded `6a4ea94` tag + `20132da` one-after relationship | `c1259d0` |
  | Evidence | r2 Phase J commit SHA missing | Minor | Added cite `dac0195`-era cleanup batch | `c1259d0` |
  | Clarity | Post-ship numbering starts at #3 with no #1/#2 | Important | Renumbered #1-#5 | `c1259d0` |
  | Clarity | Regression Prevention bullet-2 wrong BUG cross-ref | Minor | Corrected to `docs/plans/2026-05-11-test-quality-audit.md` | `c1259d0` |
  | Clarity | LLD-006-r4 + tiered narrow-change anchor missing | Minor | Inline anchors added in Fix Description | `c1259d0` |
  | Consistency | Related Docs bare-name supersession-stale (same as Evidence #3) | Important | Same closure as Evidence #3 | `c1259d0` |
  | Consistency | r4 iteration count 4 vs list-derived 3 | Minor | Renumbering exposed root cause; reconciled | `c1259d0` |
  | Consistency | Review-yaml iteration paths stale | Minor | Related Docs paths updated to latest on-disk + Convention note added | `c1259d0` |

  Plus §Root Cause Analysis canon spelling fix (Root Cause → Root Cause Analysis per canon §4.8) in commit `3b80fb9`. Total: 12/12 r1 findings closed.
- r6 (2026-05-11, refined 2026-05-12) — r5 attestation closure batch. Closed (via this iteration's body edits): all 3 r5 Critical findings (Regression Prevention rewritten to discipline-not-gate framing — mechanical-vs-discipline boundary made explicit) + 15 r5 Important findings (Changelog rows added for r2/r3/r4, per-finding closure table added to r5 entry above, BUG-014 cross-referenced in Related Documents, Convention note narrowed to BUG-012-local, Post-ship #5 fix-path made implementable, aggregate-tracker recursion termination criterion added, frontmatter Severity + Doc ID notes added, Environment pytest delta explained, test/A3-prose disagreement noted explicitly in LLD-008 #3 closure entry). **r6 refinement (2026-05-12):** Surfaced BUG-018 (`cli.lint` Addresses: validator rejects v2.0 schema) which blocks the originally-planned A3 sync commit slice. §Post-ship #5 reclassified from *blocking* to *tracking-only* — BUG-012 can now close at r6 review pass without waiting for the A3 prose sync (which itself awaits BUG-018 closure). Status: Investigating. Reviewed: pending r6 v2 spec-review. Remaining open: Post-ship #1 (lint.py split, deferred v1.8+) + Post-ship #5 (tracking-only; A3 sync target v2.0.1 patch cycle after BUG-018 lands).

## Regression Prevention

**Scope of this section:** What follows is *agent discipline + manual convention*, not mechanically-enforced gates. Where a mechanical layer exists (pre-commit hook, cli.lint, CI), it is cited explicitly. Where no mechanical layer exists, the claim is labeled as **discipline** to make the enforcement boundary unambiguous (closes BUG-012 r5 adversarial Critical findings 1-3 — "enforcement claimed without mechanism").

### Mechanical layer (enforced by code)

- **L1+L2+L3+L4+L5 lint checks** at `cli/lint.py` enforce metadata + required-sections + Refs-line + doc-id-burn + strict-enum-match. Wired into pre-commit hook (BUG-010, LLD-008). Bypass: `--no-verify`.
- **T2 enumeration test** at `tests/test_install_hooks_skill_dir.py::test_cli_templates_dir_full_enumeration` fails CI if cli/templates/ membership drifts. The brittleness is *by design* (canon-frozen-guard intent): test failure forces simultaneous A3-prose sync, preventing silent additions that drift A3 contract. There is intentionally no env-var grace path — the coupling IS the protection.

### Discipline layer (agent / human convention; no mechanical enforcement)

- **`--no-verify` discipline:** When `--no-verify` is required to bypass an L4 gap (e.g., BUG-014 bare-name design supersession case), it SHOULD be tracked as a new BUG immediately. **No mechanical enforcement exists** — `--no-verify` by definition disables the hook, and git history does not expose post-hoc which commits used `--no-verify`. This is agent self-discipline. Future v1.8+ work could explore signed commits + `--no-verify` audit trail; out of scope here.
- **Deferred-Minor leakage discipline:** Each ship SHOULD file an aggregate BUG-NNN tracker before tag if spec-review attestation Minor findings were deferred. **No mechanical enforcement** — currently relies on author memory. Hardening path: add a `cli.lint --pre-tag` check that fails if any open spec-review attestation has open Minor findings and no corresponding BUG-NNN tracker exists; deferred to v1.8+ (BUG-012 itself surfaces the need but does not fix the mechanism).
- **A3-prose ↔ test lockstep discipline:** Future additions to `cli/templates/` MUST update both LLD-008 r8 A3 prose AND `CLI_TEMPLATES_CANONICAL_SET` frozenset in the test, in a single tiered narrow-change commit with `Addresses:` line. Test failure (mechanical, above) prevents merging the partial update; the closing of the test failure requires the prose sync as a discipline (no code enforces that A3 prose is updated, only that the test passes — author can in principle "fix" the test by reverting the addition).
- **Aggregate-tracker recursion termination:** BUG-012 itself is a tracker for v1.7.x deferred Minors. To prevent unbounded recursion (tracker-of-tracker-of-tracker), the convention is: **trackers terminate at version-boundary closure**. BUG-012 closes at v2.0.1 ship; any Minor findings from BUG-012 r5+ get either (a) absorbed inline before close, OR (b) filed as named follow-up BUGs with concrete fix scope (not aggregate paperwork). Aggregate trackers do not generate aggregate trackers.

### Cross-references

- Test-quality audit handled independently via `docs/plans/2026-05-11-test-quality-audit.md` (commit `a1932bd`; closed Plan r2/r3 Minor #2). Independent of BUG-013 (slash-command naming inconsistency).
- BUG-014 (L4 bare-name design supersession) surfaced via r4 batch; see `docs/bugs/BUG-014-l4-bare-name-design-supersession.md`. Cross-listed in §Related Documents below.

## Related Documents

- `docs/features/008-commit-skill-r8.md` — LLD-008 r8 (Implemented; supersedes r7)
- `docs/features/009-commit-msg-l2-finalize.md` — LLD-009 r6 (Implemented)
- `docs/features/010-framework-detection-determinism.md` — LLD-010 r4 (Implemented)
- `docs/plans/2026-05-11-v17-implementation.md` — Plan r4 (Implemented)
- `docs/plans/2026-05-11-test-quality-audit.md` — test-quality audit (commit `a1932bd`)
- `docs/bugs/BUG-014-l4-bare-name-design-supersession.md` — surfaced by r4 batch (L4 doc-id-burn rejects bare-name design supersession); cross-referenced for bidirectional supersession-integrity intent per LLD-006-r4.
- `docs/bugs/BUG-018-lint-addresses-validator-v2-schema-gap.md` — surfaced by r6 batch (cli.lint Addresses: validator rejects v2.0 schema attestations); blocks BUG-012 §Post-ship #5 (A3 sync). Closure of BUG-018 unblocks the A3 sync commit slice (target: v2.0.1).
- `docs/reviews/BUG-012-v17-1-minor-followups-r1.orchestra.review.yaml` — r1 spec-review (schema v1.0; overall_verdict: fail; 12 findings: 4 Important + 8 Minor)
- `docs/reviews/BUG-012-v17-1-minor-followups-r5.orchestra.review.yaml` — r5 spec-review (schema v2.0, 6-sub-judge ensemble under --override-cap; overall_verdict: fail; 32 deduped findings: 3 Critical + 15 Important + 14 Minor; repo-context pass)
- `docs/reviews/008-commit-skill-r4.orchestra.review.yaml` + `.codex.review.md` — LLD-008 last full-stack reviewed iteration. LLD-008 sits at r8 (Implemented); r5-r6-r7 shipped under interview-gate "ship without 4th review"; r7→r8 supersession added r8-only orchestra attestation at `docs/reviews/008-commit-skill-r8.orchestra.review.yaml`.
- `docs/reviews/009-commit-msg-l2-finalize-r2.orchestra.review.yaml` + `.codex.review.md` — LLD-009 last reviewed iteration. LLD-009 sits at r6 (Implemented); r3-r6 shipped under interview-gate; r1 sonnet also present.
- `docs/reviews/010-framework-detection-determinism-r2.orchestra.review.yaml` + `.codex.review.md` — LLD-010 last reviewed iteration. LLD-010 sits at r4 (Implemented); r3-r4 shipped under interview-gate; r1 sonnet also present.
- `docs/reviews/2026-05-11-v17-implementation-r3.orchestra.review.yaml` + `.codex.review.md` — Plan last reviewed iteration. Plan sits at r4 (Implemented); r4 shipped under interview-gate.

**Convention note (BUG-012-local; do NOT generalize without ADR):** Related Documents for BUG-012 tracks the latest on-disk attestation paths and notes where doc-iteration has advanced beyond attestation-iteration (the "ship without 4th review" pattern shipped r5-r8 for LLD-008, r3-r6 for LLD-009, r3-r4 for LLD-010, r4 for the plan without fresh attestations). This is a paperwork-disclosure convention for the aggregate-tracker BUG itself — BUG-012's whole purpose is to track those deferred iterations. **This convention is NOT a generally-applicable Gate 3 bypass rule for orchestra docs.** Any doc that wishes to invoke "doc-iteration ≥ attestation-iteration" must (a) cite an explicit interview-gate consent for that ship, OR (b) be explicitly classified as paperwork-grade. Generalizing the convention to other docs requires an ADR. r6 body sync done in commit batch immediately following the r5 attestation write.

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | r1 — BUG filed post-v1.7.0 ship to aggregate deferred Minors across 3 LLDs + plan + post-ship cleanup observations. Severity: Low (paperwork-grade; no behavioral defects). Status: Investigating. Target: v1.7.1. |
| 2026-05-11 | r2 — dogfood batch (LLD-009 r6 first real-world tiered narrow-change use). Closed 4 Minors via tiered path + 2 Plan Minors via Phase D/J. Remaining open: 11 items. |
| 2026-05-11 | r3 — second narrow-change batch. Closed 5 more Minors. Remaining open: LLD-008 #3 (test code) + Post-ship cleanup. |
| 2026-05-11 | r4 — supersession batch (philosophy r1→r2 + LLD-008 r7→r8). Closed 2 Post-ship items. Surfaced BUG-014 (L4 doc-id-burn gap; `--no-verify` bypass used). Remaining open: 3 items. |
| 2026-05-11 | r5 closure batch: applied 12 r1 attestation findings inline (Iteration field added; Related Documents paths corrected to current iterations + per-judge suffix; Post-ship cleanup renumbered #1-#5; BUG-013 cross-ref corrected; Regression Prevention expanded). Closed LLD-008 #3 (T2 enumeration test, commit `8af4b45`) + Post-ship #2 (scale_migration_helper already moved at `7f581e9`). Surfaced Post-ship #5 (LLD-008 r8 A3 enumeration drift). r5 v2 attestation written: overall_verdict: fail (32 findings: 3 Crit + 15 Imp + 14 Min). Remaining open: Post-ship #1 (lint.py split, deferred v1.8+) + Post-ship #5 (A3 sync slice). Commits: `c1259d0` + `3b80fb9`. |
| 2026-05-11 | r6 — r5 attestation closure batch. Reworded Regression Prevention to discipline-not-gate framing (closes 3 r5 Criticals by making mechanical-vs-discipline boundary explicit); added per-finding closure table for r1 findings; added BUG-014 to Related Documents; narrowed Convention note to BUG-012-local; made Post-ship #5 fix-path implementable (cites r5 attestation); added aggregate-tracker recursion termination criterion; added frontmatter Severity + Doc ID notes; explained Environment pytest delta; flagged test/A3-prose disagreement in LLD-008 #3 closure. Status: Investigating. Reviewed: pending r6 v2 spec-review. |
| 2026-05-12 | r6 refinement — A3 sync blocked on BUG-018 (cli.lint Addresses: validator gap, v2.0 schema rejection). Post-ship #5 reclassified from blocking to tracking-only. BUG-018 cross-referenced in Related Documents. Iteration Log r6 entry updated. BUG-012 unblocked for closure at r6 review pass. |
| 2026-05-12 | Status: Investigating → **Fix Applied** (user-confirmed; user-authorized skip-r6-review per closure path interview-gate). r5 attestation (v2.0 schema; 32 findings) is canonical closure attestation; r6 body addressed all 3 Critical + 15 Important inline. Open trackers remain: Post-ship #1 (lint.py split, deferred v1.8+) + Post-ship #5 (tracking-only; A3 prose sync awaits BUG-018 closure, target v2.0.1 patch). BUG-012 is now canon-frozen — any further edits require narrow-change (whitelist: Status/Iteration/Superseded by + Changelog append) or tiered narrow-change (post-BUG-018) or supersession. |
| 2026-05-12 | Post-ship cleanup observation #5 CLOSED via LLD-008 r8 A3 prose sync (commit `b481f72`). BUG-018 v2.0.1 fix unblocked tiered narrow-change against v2.0 attestations; A3 sync used `Addresses: docs/reviews/BUG-012-...-r5.orchestra.review.yaml gate adversarial finding 4 (Important)`. cli/templates/ A3 prose now reads 11 init-related artifacts in lockstep with T2 enumeration test. Remaining open tracker: Post-ship #1 (lint.py split deferred v1.8+ — YAGNI verdict reconfirmed). |
