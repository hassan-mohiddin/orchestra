# Postmortem: LLD-007 Canon-Inplace Violation (v1.6.1 Initial Ship)

> **Doc ID:** POSTMORTEM-2026-05-10-canon-inplace-violation
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Postmortem
> **Severity:** SEV4 production / MEDIUM process (process incident — no production user impact; revertable; remediated within same session — but second canon-discipline failure in same session per Impact §)
> **Status:** Action Items Tracked

> Blameless. Roles only ("the agent", "the user"), no names.

## Summary

After shipping orchestra v1.6.0 (LLD-007 spec-review skill) the agent ran r4 dogfood, received 13 substantive findings, and applied them as **in-place body edits** to the canon-frozen LLD-007 (Status: Implemented) across two commits (`653db4e` v1.6.1 + `bc359e7` r5). LLD-006-r4 § narrow change forbids canon-frozen body edits — supersession workflow is required. Three layers of enforcement (cli.lint --commit L2, pre-commit hook, agent self-check) all failed. The user observed the violation and asked "what happened to the rejection/archive thing?" Remediation: revert both commits (`68fd538`), redo via proper supersession (`2ce394a` — archive prior LLD as Rejected, create `-r5.md` supersession file with patches, re-attest, run cli.lifecycle update-attestation-paths on r1-r4 attestations).

## Impact

- **Users affected:** zero (orchestra plugin not yet in user production; SCALE-only consumer with the developer in the loop)
- **Duration:** ~25 min (between first canon-inplace commit at ~13:10 IST and user observation at ~13:35 IST per Timeline)
- **SLO/revenue:** N/A (pre-revenue)
- **Data integrity:** zero (no data loss; revert clean; r1-r4 attestations preserved with rewritten doc_subject.path)
- **Process integrity:** MEDIUM — same canon-discipline failure mode as v1.4 cargo-cult, four commits later. Demonstrates discipline-by-markdown insufficient even with shipped enforcement primitives.

## Timeline (IST = UTC+5:30, 2026-05-10)

Sourced from `git log --date=iso` and `git reflog --date=iso`:

| Time | Event | Commit |
|---|---|---|
| ~13:00 | r4 dogfood ran on LLD-007 | (no commit; `/orchestra:spec-review` invocation) |
| ~13:05 | r4 attestation written, verdict=fail (13 findings) | `41721e1 docs: LLD-007 r4 dogfood attestation + iteration bump (3→4)` |
| ~13:10 | Agent applied 13 findings as in-place body edits to canon-frozen LLD-007 | `653db4e fix: ship v1.6.1 — dogfood patches` ⚠ violation |
| ~13:15 | r5 dogfood ran; found 4 Important + 3 Minor doc-vs-code drift findings | (no commit) |
| ~13:20 | Agent applied r5 fixes as further in-place body edits | `bc359e7 docs: LLD-007 r5 dogfood verification + v1.6.1 doc-snippet sync` ⚠ violation |
| ~13:35 | User observation: "what happened to the whole rejected doc and throwing it in archive thing?" | (none — chat) |
| ~13:40 | Agent confirmed both commits violated LLD-006-r4 § narrow change. cli.lint --commit retroactively returned PASS — gap discovered: `lint_commit()` runs only L1, not L2 | (none — diagnosis) |
| ~13:45 | User chose supersession redo (Recommended option) | (none — chat) |
| ~13:50 | Reverted both commits in single revert | `68fd538 revert: undo canon-inplace violations` |
| ~14:00 | Archive + supersession redo executed | `2ce394a feat: ship v1.6.1 via LLD-006-r4 supersession workflow` |
| ~14:15 | r5-supersession attestation: verdict=conditional_pass (all 13 r4 findings VERIFIED RESOLVED; 5 new findings tracked as v1.6.2 followups) | (in 2ce394a) |

## Root Cause

```
            ┌──────────────────────────────────────────┐
            │  Agent action momentum during dogfood   │
            │  iteration loop (no Interview Gate fire) │
            └────────────────────┬─────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │ Body edit applied to canon-frozen doc   │
            │ instead of supersession workflow         │
            └────────────────────┬─────────────────────┘
                                 │ (would have been caught by L2)
                                 ▼
            ┌──────────────────────────────────────────┐
            │ Three enforcement layers all fail:       │
            │ 1. cli.lint --commit runs L1 only        │
            │ 2. Pre-commit hook not installed         │
            │ 3. Agent self-check missed Interview-Gate│
            │    trigger (silent design decision)      │
            └────────────────────┬─────────────────────┘
                                 │
                                 ▼
                    Violation lands as committed state
```

**Primary cause**: agent applied dogfood findings as in-place body edits to canon-frozen LLD instead of routing through supersession. Same root pattern as v1.4 cargo-cult: discipline-by-markdown insufficient when checker = checked.

**Contributing causes**:
1. **Tooling gap (L2 retroactive)** — `cli.lint --commit SHA` (`cli/lint.py:668-682` — `lint_commit()`) runs only L1 (Refs eligibility via `lint_commit_refs_eligible`). L2 (canon-inplace narrow-change via `lint_commit_no_canon_inplace_edit` defined `cli/lint.py:490-521`) is invoked only inside `lint_staged()` (`cli/lint.py:705-728` — line 728 is the L2 call site). No code path connects `lint_commit()` to L2
2. **Hook not installed** — orchestra repo `.git/hooks/` has only `pre-commit.sample`. No active hook fires. cli.install_hooks would set this up but was never invoked on the orchestra repo itself
3. **Interview Gate dormant** — agent shipped `interview-gate.md` rule (v1.5.1) with explicit trigger "silent design decision: about to commit to architecture/approach not stated in the user's instruction or design doc." Body-editing canon-frozen IS a silent design decision. Trigger never fired in agent's own check
4. **Action momentum** — sequential dogfood→fix→commit→dogfood→fix loop suppresses meta-checks. Agent in execution mode, not gate mode
5. **Recency illusion** — agent shipped LLD-006-r4 four commits prior. Memory of rule was "fresh." Fresh memory ≠ active enforcement

## What Went Well

- (Moved to Where We Got Lucky — user observation was the only safety net, no automated gate caught it; per blameless convention this is luck not process strength)
- Revert was clean (no merge conflicts, no data loss)
- Supersession redo applied same content via correct workflow in single commit
- `cli.lifecycle update-attestation-paths` worked as designed (rewrote 4 attestations from canon-path → archive-path)
- All 13 r4 findings VERIFIED RESOLVED by r5-supersession attestation (verdict: conditional_pass)
- Pytest 144, evals 12/12, lint clean throughout remediation

## What Went Wrong

- **L2 not in --commit mode** — retroactive linting cannot catch canon-inplace post-hoc. Only pre-commit (lint_staged) catches it, and only if hook installed
- **No pre-commit hook installed in orchestra repo** — the repo that ships `cli.install_hooks` does not run its own hook
- **Interview Gate did not fire** — "silent design decision" trigger is in the rule but agent did not apply it to its own actions
- **Repeated process drift** — second canon-discipline failure in same session (after v1.4 cargo-cult was already postmortemed). Pattern is durable
- **Chat-only observation** — no automated check between the two violation commits would have surfaced this; user's recall was the only safety net

## Where We Got Lucky

- User asked "what happened to the rejection thing?" within 25 minutes of first violation commit. Sole safety net — no automated gate fired (L2 not in `lint_commit()`; pre-commit hook not installed). Could have been after a third violation, after push to origin, or after another agent dispatched on stale state — all caught by chance, not process
- Both violation commits were unpushed (no upstream contamination)
- Supersession was clean (LLD-006-r4 had cli.lifecycle helper already shipped; no new code needed for remediation)
- r4 attestation preserved through revert (commit `41721e1` with iteration-bump-only narrow change is intact and points at the now-archived doc via `update-attestation-paths`)

## Action Items

| Item | Owner | Tracking | Severity |
|---|---|---|---|
| Extend `lint_commit()` to include L2 retroactive check (canon-inplace narrow-change diff between current SHA and HEAD~1 for the same file path) | Hassan | v1.6.x patch — `docs/bugs/BUG-009-lint-commit-l2-retroactive.md` (TBD-allocate by 2026-05-15) | High |
| Auto-install pre-commit hook in orchestra repo via `cli.install_hooks --pre-commit --repo .` from bootstrap or release-engineering procedure | Hassan | v1.6.x — `docs/bugs/BUG-010-orchestra-self-install-hook.md` (TBD-allocate by 2026-05-15) | High |
| Write POSTMORTEM-session-process-drift consolidating v1.4 cargo-cult + this canon-inplace + repeated interview-gate skips into one durable record | Hassan | `docs/postmortems/POSTMORTEM-2026-05-10-session-process-drift.md` (TBD-allocate by 2026-05-15; consolidates this postmortem + POSTMORTEM-2026-05-07-v1.4-cargo-cult-rollback) | Medium |
| Refine LLD-006-r4 supersession rule — tiered Minor (Changelog append narrow-extension) / Important (author judgment) / Critical (mandatory supersession). Current strict-binary rule is over-correction for wording-only fixes | Hassan | v1.7+ — `docs/features/008-supersession-tier-refinement.md` (TBD-allocate by 2026-05-20) | Medium |
| Explicit Interview-Gate self-check before any commit modifying a canon-frozen doc — extend agent rules with "before commit on .md under refs-eligible prefix, check Status field; if canon-frozen, ASK before body edit" | Hassan | v1.6.x rule update to `.claude/rules/` (SCALE-side) + orchestra template | Medium |

## Lessons Learned

1. **Discipline-by-markdown is a tripwire, not a gate.** Same lesson as v1.4. Markdown rules tell agent what to do; only mechanical enforcement guarantees behavior. Pre-commit hook + retroactive lint + Interview Gate fresh-subagent dispatch are the actual gates.
2. **Shipping enforcement is not the same as enabling enforcement.** v1.5 shipped L1-L4 lint. orchestra repo never installed its own hook. Self-application of new tooling is a separate step from ship.
3. **Different-model judge keeps catching what same-model judge misses.** r4 + r5 attestations (codex-style adversarial review on Opus output) caught both the substantive findings AND the doc-vs-code drift. User observation caught the rule-level violation. Three independent observers; only the third caught the rule.
4. **Rules expire faster than memory of rules.** Agent recalled rule existence; did not apply rule to action. Rule recall ≠ rule application. Mechanical gates close that gap.
5. **Strict-binary rules over-correct for minor changes.** LLD-006-r4 supersession-or-narrow rule made sense as v1.4 backlash. For Minor wording fixes, it is overhead. Tiered rule (Minor=narrow, Important+=supersession) preserves audit value with less friction.
6. **Action momentum is the meta-failure mode.** v1.4 cargo-cult AND this canon-inplace both happened during execution loops where meta-checks felt like context-switch overhead. Interview Gate is the discipline-against-momentum primitive; agent must internalize that trigger fires DURING action loops, not just before them.

## Related Documents

- `docs/postmortems/POSTMORTEM-2026-05-07-v1.4-cargo-cult-rollback.md` — prior canon-discipline incident; same session
- `docs/archive/features/007-spec-review-architecture.md` — the rejected canon LLD (Status: Rejected, Reason, Superseded by)
- `docs/features/007-spec-review-architecture-r5.md` — the supersession file (Status: Implemented, Iteration: 5)
- `docs/reviews/007-spec-review-architecture-r4.review.yaml` — r4 dogfood attestation (verdict: fail; doc_subject.path rewritten to archive)
- `docs/reviews/007-spec-review-architecture-r5.review.yaml` — r5 supersession attestation (verdict: conditional_pass)
- LLD-006-r4 § narrow change — `docs/features/006-archive-and-supersession-conventions-r4.md`
- `cli/lint.py:486` — L2 implementation in lint_staged (NOT in lint_commit — the gap)
- Commits: `653db4e` (violation 1), `bc359e7` (violation 2), `68fd538` (revert), `2ce394a` (supersession redo)

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Postmortem written immediately post-supersession-redo. Captures canon-inplace violation, root cause, action items, lessons. Status: Draft → spec-review pending. SEV4 process incident; no production impact; remediated within session. |
| 2026-05-10 | r1 spec-review (verdict: conditional_pass; 6 findings: 3 Important / 3 Minor). All addressed inline (Status: Draft, full edit allowed): Severity tag clarified to "SEV4 production / MEDIUM process"; Duration 30→25 min reconciled with Timeline; Timeline header gained UTC offset note; Root Cause § contributing-cause-1 gained line-citations to lint.py:668-682 (lint_commit) + lint.py:705-728 (lint_staged) + lint.py:490-521 (L2 fn def); user-observation event moved from What-Went-Well → Where-We-Got-Lucky (per blameless convention, sole-safety-net = luck); Action Items table allocated BUG-009 (lint_commit l2 retroactive), BUG-010 (orchestra self-install hook), POSTMORTEM-session-process-drift, LLD-008 (supersession tier refinement) with TBD-allocate deadlines. Status: Draft → Implemented. |
| 2026-05-11 | Status narrow-change: Implemented → Action Items Tracked. Canon §4.1 postmortem enum does not include "Implemented" (it has Draft/Reviewed/Action Items Tracked/Closed/Rejected/Superseded). Surfaced by BUG-016 slice 5 L5 strict-enum-match sweep. Action items remain open (BUG-008/009/010/011) so canon-matching value is Action Items Tracked. |
