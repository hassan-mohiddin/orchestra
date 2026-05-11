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

1. **`input_fn=input` pseudocode clarification** — design § install_one_hook pseudocode uses `input_fn=input` as default arg; not all readers will recognize this as the test-injection seam. Add one-line comment.
2. **Prompt UX preservation note** — A5 covers `--on-conflict={skip,replace,append}` flag; existing interactive prompt path retained for TTY users. Document explicitly that prompt-string wording was preserved verbatim.
3. **T2 11-file enumeration assertion** — A3 lists 11 init-related artifacts retained in `cli/templates/`; test currently asserts presence of representative subset only. Add full enumeration assertion.
4. **A8 section-header citation** — A8 cites line ranges (109-128) for documentation-gate.md Quick Reference block; line ranges drift. Replace with section-header anchor.
5. **Skill-Status value-collision documentation** — `Skill-Status` field is intentionally distinct from doc-lifecycle `Status` to prevent future value-collision if `skills/` is ever added to `REFS_ELIGIBLE_PREFIXES`. Documented in design § references/ governance; lacks an explicit value-collision example in glossary.

### LLD-009 r6 deferred Minors

1. **D1-D3 verifiability classification** — Deliverables D1-D3 listed without explicit verification mechanism (lint-checkable vs. manual). Mark each.
2. **Mixed line/function anchors** — Related Documents section mixes `cli/lint.py:128-130` (line range) with `cli/lint.py § extract_changelog_and_strip` (function anchor). Pick one convention.
3. **3a/3b sub-numbering convention** — Edge Cases § uses 3a/3b/3 for `--amend` variants; convention not documented. Add legend.
4. **pre-commit.sh canonical content inline** — A13 references pre-commit.sh template; currently file is shipped via LLD-008 path; inlining content in LLD-009 A13 would mirror LLD-009 A12 for commit-msg.sh (single-source).
5. **A16 third-place CHANGELOG cite verification** — A16 cites pytest target lineage; cite includes "third-place" reference that should be verified post-impl matches actual CHANGELOG row.

### LLD-010 r4 deferred Minors

Per LLD-010 r4 Changelog entry, r4 was paperwork-only cascading edit; no internal Minors deferred. All r2/r3 Minors closed in r3/r4.

### Plan r2/r3 deferred Minors

1. **Cross-doc number lineage Slice 5.2** — Originally Plan r3 orchestra Minor; fixed in r4. Verify CHANGELOG entry baseline number cross-references match all 3 LLDs.
2. **Test-count audit** — Phase 0 deferred per plan §Phase 0 30-min time-box. File `docs/plans/2026-05-11-test-quality-audit.md` per output contract.

### Post-ship cleanup observations (2026-05-11)

3. **`cli/lint.py` 1367 lines → module split** — Natural seam: `cli/lint/` package with `core.py` (regex constants + Finding dataclass + parsers) / `canon.py` (L2-detect + L2-finalize + tiered + helpers) / `commit.py` (Refs-eligibility + retroactive L2 + commit-range). Deferred until seam pressure increases.
4. **`tests/scale_migration_helper.py` → `tools/`** — `tools/migrate_scale_rules.py` imports from `tests/` (wrong dependency direction). Promote helper out of tests/.
5. **`attestation-template.yaml` → `skills/spec-review/templates/`** — currently in `cli/templates/`; spec-review skill owns it conceptually; move under skill dir for consistency with LLD-008 r7 placement rule.
6. **`docs/design/orchestra-philosophy.md` lint issues** — pre-existing to-be-determined placeholders in Key Decisions table + mermaid parse error on line 240. Blocks whitelist Changelog appends. Either fix (supersession, since Status: Current) or relax lint to permit whitelist appends despite body warnings.

## Iteration Log

- r1 (2026-05-11) — initial aggregate; pre-shipping fix. Closes/tracks deferred Minors across LLDs + plan + post-ship cleanup observations.

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
