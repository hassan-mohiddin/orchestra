# Orchestra Handoff — Session Continuity Pointer

> **Last updated:** 2026-05-11 PM (twice in one day — LLD-011 Phase 1 close AM, LLD-012 ship PM)
> **Last session ended:** LLD-012 (rule durability + learning layer) shipped as Draft + spec-review trail committed; pre-compact handoff.

This file is the single pointer for picking up orchestra work between sessions. Read this BEFORE acting.

**Two active workstreams** running in parallel sessions:
1. **LLD-011 Phase 2** — spec-review v2 (PDSA + delta-review + rubric-freeze). Owner: other session. State: 11 slices shipped post-Phase-1.
2. **LLD-012 v1.8 plan** — rule durability + learning layer. Owner: this session. State: Draft doc committed; implementation deferred.

---

## ✅ NEWLY SHIPPED — LLD-012 Rule Durability + Learning Layer (this session)

**Commits:**
- `2d3e452` docs: file LLD-012 (rule durability + learning layer) + spec-review trail (453 lines)
- `8eebe00` docs: add LLD-012 spec-review trail + W1-W7 investigation refresh note (4 files, 704 lines)

**Doc state:** `docs/features/012-rule-durability-and-learning-layer.md` Status: Draft, Iteration: 2.

**Scope:**
- v1.8.0 ship target
- W6 (rule durability): TLDR compression on `.claude/CLAUDE.md` + 4 rule files; SessionStart + PreCompact + UserPromptSubmit hooks via `cli.install_claude_hooks`; `cli.compaction_probe` CI gate; `<system-reminder>` injection mechanism with 500-token budget
- W7 (learning loop): `/orchestra:teach` (free-text, audit-only) + `/orchestra:violation` (structured, injected) + `docs/lessons/<YYYY-MM>-lessons.md` storage + `cli.lessons_lint` (proxy artifact emit only) + `cli.lessons_apply` (user-invoked schema-layer mutation; gated by passed spec-review on proxy)
- 14 success criteria (SC-1..SC-14)

**Out of scope (deferred):**
- PreToolUse blocking → LLD-013 workflow skill v2.0
- TLDR on `workflow.md` + `skills-registry.md` → LLD-013 (those files restructure under workflow skill anyway)
- Anthropic Memory tool integration (research confirmed not callable from plugins; Claude Code's MEMORY.md is complementary)
- Cross-machine lesson sync (use git)
- Rush-mode detection → v1.9

**Spec-review trail:**
| Run | Verdict | Findings | Artifact |
|---|---|---|---|
| r1 orchestra judge-1 | fail | 2C+14I+4M | `docs/reviews/012-...r1.review.yaml` |
| r2 orchestra judge-1 | fail | 2C+5I+3M | `docs/reviews/012-...r2.review.yaml` |
| r1 codex judge-2 | needs-attention | 1C+2H+1M | `docs/reviews/012-...r1.codex.md` |

All r1 codex findings + all r1+r2 orchestra findings APPLIED inline before commit (per user "Apply r2 findings + commit r2-final" decision). r2 attestation preserves fail-with-applied-followups audit trail rather than re-running iter-3.

**Implementation NOT started.** v1.8 implementation plan to be written next (see "Open work" below).

---

## 🎯 ACTIVE WORK — LLD-011 spec-review v2 implementation (parallel session; do not touch)

**LLD**: `docs/features/011-spec-review-v2.md` (Status: Approved, canon-frozen)
**Plan**: `docs/plans/2026-05-11-spec-review-v2-implementation.md` (Status: Approved, canon-frozen)
**BUG spinoff**: `docs/bugs/BUG-016-scattered-vocabulary-no-canon.md` (Status: Investigating; parallel session via `docs/HANDOFF-BUG-016.md`)

**Parallel-session artifacts (uncommitted as of this session, owned by other session):**
- `docs/design/controlled-vocabulary.md` — vocab canon Design Doc drafted by parallel agent (BUG-016 effort)
- `docs/reviews/controlled-vocabulary-r1.review.yaml` + `r2` + `r3` — spec-review attestations for vocab canon
- `docs/reviews/2026-05-11-vocab-canon-migration-r1.review.yaml`
- `docs/plans/2026-05-11-vocab-canon-migration.md`
- `cli/spec_review.py` + `tests/test_spec_review_v2.py` may have ongoing modifications from Phase 2 slice work — verify before touching.

**On resume**: do NOT overwrite or modify these without checking parallel-session state first. LLD-011 Phase 2 work is independent of LLD-012 v1.8 plan.

### Phase 1 (Depth Fix) — ✅ COMPLETE (33/33 slices)

Main HEAD: `25f4cd7`. Pytest 321 (was 259 → +62 new). Pyrefly 0. `cli.lint --pre-commit` PASS.

Phase 1 shipped:
- Schema v2.0 (`skills/spec-review/attestation-schema-v2.0.json`)
- v1.0 backward-read + frozen-historical overwrite refusal
- `MANDATORY_SUBJUDGES = frozenset({"semantic", "adversarial"})`
- 6 sub-judge prompt.md + rubric-v1.md (`skills/spec-review/judges/<id>/*.md`)
- Mechanical aggregator (`cli/aggregator.py` — dedup + severity union + raised_by union + location ordering)
- Provenance helpers (`_get_iter_commit_sha`, `_persist_doc_blob` via `git hash-object -w`, `_retrieve_doc_bytes_by_blob_sha` via `git cat-file -p`)
- Attestation integrity hash (`_compute_attestation_integrity_hash` + `_verify_attestation_integrity_hash`, canonical-YAML with field-zero-out)
- SKILL.md rewritten for v2 9-step dispatch protocol
- Tiered partial-failure policy (`compute_overall_verdict_v2` — mandatory hard fail + optional soft fail + always-persist invariant)
- Cross-judge report renderer (`render_cross_judge_report`) + codex .md tolerant parser (`parse_codex_findings`)
- Interview-gate auto-fire decision (`should_fire_interview_gate`)
- Removed obsolete v1 `test_skill_md_specifies_max_tokens_4000`

### Phase 2 (Loop Fix Part A) — NEXT (29 slices)

Slice 2.1 — first slice to execute on resume:
> PDSA: invokes `cli.lint --doc <path>` — new module `cli/pdsa.py::run_pdsa`.

Phase 2 scope (from plan §Phase 2):
- 2.1-2.12 PDSA module (lint + sections + citation validity via splitlines bounds-check + placeholder detection + Refs: resolution + filename grammar + glossary non-gating + main flow integration)
- 2.13-2.16 Class-vs-instance scope tag + audit_attestation in schema + aggregator
- 2.17-2.27 Delta-review module (`cli/delta_review.py` — iter-1 attestation read + integrity verify + blob retrieval + diff extraction + sub-judge prompt augmentation)
- 2.28-2.29 E13 iteration-missing fail-closed when prior attestations exist

Sequencing Rule 7: full pytest + pyrefly + cli.lint + cli.eval at Phase 2 boundary. Pytest baseline target ≥ 317 by Phase 2 end.

Plan slice details: `docs/plans/2026-05-11-spec-review-v2-implementation.md § Phase 2`.

### Phase 3 (Loop Fix Part B) — DEFERRED until Phase 2 complete

22 slices: rubric-freeze + 2-iter cap + --override-cap + E11/E17b/E18/E20/E21 failure attestations.

### Self-application + ship — DEFERRED

After Phase 3: dogfood v2 on LLD-011 itself, depth-metric validation on 5-doc sample vs codex (≥80% overlap), tag v2.0.0.

---

## Open task #4 (pre-compact pending)

**Bootstrap commit** — these files are uncommitted in working tree but tightly coupled to the v2 work + general orchestra-cwd setup:
- `.claude/CLAUDE.md`
- `.claude/workflow.md` (already has LLD-011 ref edit)
- `.claude/skills-registry.md`
- `.claude/rules/*.md` (5 rule files)
- `docs/HANDOFF.md` (this file — has LLD-011 ref edits)
- `docs/reviews/008-commit-skill-r8.review.yaml`
- `docs/reviews/BUG-012-v17-1-minor-followups-r1.review.yaml`
- `docs/reviews/BUG-013-slash-command-naming-inconsistency-r1.review.yaml`
- `docs/reviews/BUG-014-l4-bare-name-design-supersession-r1.review.yaml`
- `docs/reviews/orchestra-philosophy-r2.review.yaml`
- `docs/investigations/2026-05-11-workflow-skill-refresh.md`

Decision deferred. Either commit en bloc ("docs: bootstrap orchestra-cwd + v1.7.1 paperwork yamls") or split by concern. Not blocking Phase 2.

---

## W1-W7 brainstorm decisions (this session — feeds LLD-012 v1.8 + LLD-013 v2.0)

Full investigation note: `docs/investigations/2026-05-11-workflow-skill-refresh.md` (committed in 8eebe00).

| W | Topic | Decision | Ships in |
|---|---|---|---|
| W1 | Backward-flow state machine | Single primitive `re-enter brainstorm`; brainstorm decides destination | LLD-013 v2.0 |
| W2 | Re-entry naming | `brainstorm` (resolved by W1 collapse) | LLD-013 v2.0 |
| W3 | PreToolUse gates | Strict scope (all code dirs); `ORCHESTRA_BYPASS=trivial` env var for typos; brainstorm-on-block | LLD-013 v2.0 |
| W4 | Plateau signal contract | `.claude/state/spec-review-plateau.json` from LLD-011 2-iter cap; UserPromptSubmit injects on file present; soft override (iter 3 after brainstorm, hard cap iter 5) | LLD-013 v2.0 |
| W5 | Skill packaging | Option D — fixed body + registry-driven; skill-manager skill (NOT YET BUILT) handles registry generation | LLD-013 v2.0 |
| W6 | Rule durability layer | TLDR + hooks + compaction probe | **LLD-012 v1.8 ✅** |
| W7 | Feedback loop | `/teach` + `/violation` + auto-promote pipeline | **LLD-012 v1.8 ✅** |

**Skill-manager skill dependency:** Workflow skill v2.0 ASSUMES a skill-manager skill exists (scans `~/.claude/plugins/`, generates registry, resolves situation→skill). Not yet built. Build order: skill-manager → workflow skill. Slot it as LLD-013 prerequisite.

---

## BUG candidates surfaced this session (file when ready)

From rule-decay research + LLD-012 r2 review patterns:

| BUG | Title | Severity | Source |
|---|---|---|---|
| BUG-NEW-A | Compaction silently drops process-standards (no test verifies rules survive) | HIGH | Yajin Zhou + Claude self-report |
| BUG-NEW-B | SessionStart hook does NOT match `compact\|clear\|resume` — only `startup` | HIGH | Audit cli/install_hooks.py |
| BUG-NEW-C | Concurrent plugin SessionStart text may blend silently — no isolation | MED | Industry observation |
| BUG-NEW-D | Rules files 100+ lines each — lower per-rule attention vs 5-line nonnegotiables | MED | Yajin + "300 lines" post |
| BUG-NEW-E | Rush mode under rapid user-message cadence — no detection or pause | LOW | Yajin post |
| BUG-NEW-F | Anthropic Memory tool integration unknown — does Claude Code expose it to plugins? | INFO | Exploration (research found: NOT exposed) |
| BUG-NEW-G | Edit-regression-validator gap — batch-fix introduces SC↔Design↔mermaid↔test contradictions; no sync-validator | MED | LLD-012 r2 review pattern |

Most are absorbed BY LLD-012 (A/B/D/F → LLD-012 design closes them; C requires plugin-protocol work; E deferred; G is process improvement for v1.9 spec-review feedback loop). File formally if/when they need standalone tracking.

---

## Session-survival memory pointers

- All session-end state persisted to this file
- Cwd memory dir: `/Users/mohammedhassanmohiddin/.claude/projects/-Users-mohammedhassanmohiddin-Documents-Antigravity-orchestra/memory/`
- New rules added in 2026-05-11 sessions:
  - `feedback_spec_review_per_invocation_authorization.md` — every spec-review run needs fresh permission
  - `feedback_spec_review_fix_grill.md` (added by user this PM session) — after findings reported, grill EACH fix-route before applying; "act on findings" ≠ silently pick approach

---

## Pre-LLD-011 ship state (v1.7.0, historical)

| Item | Value |
|---|---|
| Plugin version (canon) | 1.7.0 |
| Tag | `v1.7.0` at `6a4ea94` |
| Pre-LLD-011 HEAD | `dea9f1e` |
| Pre-LLD-011 pytest baseline | 259 |
| Working tree post-Phase-1 | LLD-011 + plan + BUG-016 + Phase 1 slices all committed; bootstrap files (above) untracked |

---

## Open work — v1.7.1 release

v1.7.1 = paperwork-cleanup + 2 small bug fixes. Decided NOT to do full doc supersession sweep (scope blowup discovered when LLD-006-r5 supersession draft failed spec-review with 2 Critical findings requiring deep rework).

### Code fixes (v1.7.1 scope)

| Task | What | Where |
|---|---|---|
| BUG-013 fix | Rename `name: orchestra-init` → `name: init` in skill frontmatter | `skills/init/SKILL.md` |
| BUG-014 fix | Add bare-name design supersession patterns to L4 lint | `cli/lint.py § lint_doc_id_burn` + tests |
| LLD-008 #3 fix | Update test enumeration 11 → 10 files | `tests/test_commit_skill_structure.py` |

### Doc paperwork (decision-pending)

5 docs have Gate 3 violations (committed without spec-review) — attestations now written this session (verdict: 4 fail + 1 conditional_pass):

| Doc | Attestation | Verdict | Critical findings |
|---|---|---|---|
| BUG-013 | `docs/reviews/BUG-013-...-r1.review.yaml` | fail | 2 |
| BUG-014 | `docs/reviews/BUG-014-...-r1.review.yaml` | fail | 2 |
| philosophy-r2 | `docs/reviews/orchestra-philosophy-r2.review.yaml` | conditional_pass | 1 |
| LLD-008-r8 | `docs/reviews/008-commit-skill-r8.review.yaml` | conditional_pass | 0 |
| BUG-012 | `docs/reviews/BUG-012-...-r1.review.yaml` | fail | 0 |

**Decision needed next session:** how to address findings without 5-8 hr supersession spiral. See §Spec-review feedback loop below.

### Open BUGs (deferred)

- **BUG-001 / BUG-002 / BUG-004 / BUG-005** — pre-v1.7 backlog, never triaged. Could be already fixed by LLD-008/009/010. Triage when v1.7.1 closes.
- **BUG-012** — v1.7.1 minor-followups aggregate (open items: LLD-008 #3 + cli/lint.py split deferred v1.8)
- **BUG-013** — slash command naming inconsistency (Investigating; fix planned v1.7.1)
- **BUG-014** — L4 doc-id-burn rejects bare-name design supersession (Investigating; fix planned v1.7.1)

---

## Spec-review feedback loop — biggest open issue

User flagged this session: every doc spec-review hits 2-3 iterations with new findings each time. Never one-shot clean-pass. Systemic problem.

**Root cause** (debugged in this session):

| Cause | % findings | Preventable? |
|---|---|---|
| Anti-sycophancy + min-issue-framing in judge prompt | ~30% | Yes (prompt tighten) |
| Citation drift (line numbers stale post-code-change) | ~25% | Yes (pre-dispatch self-check) |
| Missing rubric sections (Test Plan, Risk, etc.) | ~15% | Yes (author template) |
| Cross-doc inconsistency (Glossary, peer-doc refs) | ~20% | Yes (pre-dispatch self-check) |
| Genuine judgment-call findings | ~10% | No |

**5-layer fix plan** (proposed for v1.8):

1. **Pre-Dispatch Self-Audit (PDSA)** — new skill / CLI command runs mechanical checks (citations, sections, Glossary, forward-refs, cross-refs, placeholders) BEFORE judge dispatch. ~60% findings prevented.
2. **Judge prompt tightening** — remove false-positive Minor incentives. Clean-pass becomes normal expected outcome. ~30% noise drop.
3. **Differential judge for supersessions** — review only the diff vs predecessor, not full doc. ~70% supersession judge-load drop.
4. **Iteration plateau guard** — block dispatch on overlapping-findings → interview-gate fires.
5. **Supersession authoring template** — checklist filled BEFORE writing rN body.

Combined L1+L2 alone = max-iter ~1-2. Estimated: 1-2 days impl for L1+L2.

**Filed as LLD-011 (`docs/features/011-spec-review-v2.md`) — Feature LLD covers full v2 architecture: 6 sub-judges + PDSA + class/instance + delta-review + rubric-freeze + 2-iter cap. v2.0.0 big-bang ship target. BUG-016 spun off for vocab canon (separate parallel session).**

---

## Pre-v1.7 backlog (4 BUGs to triage)

After v1.7.1 ships:

| BUG | Title | Likely state |
|---|---|---|
| BUG-001 | (read doc) | Possibly stale |
| BUG-002 | (read doc) | Possibly stale |
| BUG-004 | (read doc) | Possibly closed by LLD-008/009/010 |
| BUG-005 | (read doc) | Possibly closed by LLD-008/009/010 |

Triage classifications: still-real / stale-close / v1.8-defer.

---

## Where things live

- **Memory:** `~/.claude/projects/-Users-mohammedhassanmohiddin-Documents-Antigravity-SCALE-APP/memory/` (note: still uses SCALE path because this is the project memory that survived the cwd switch — fresh session from orchestra cwd will get a NEW memory dir; preserve continuity via this HANDOFF.md)
- **Plan:** `docs/plans/2026-05-11-v17-implementation.md` (v1.7.0 plan; v1.7.1 ship checklist seeded at bottom)
- **SCALE-side migration backup:** `~/Documents/Antigravity/SCALE\ APP/.scale-migration-backup/<timestamp>/` — cleanup ~2026-05-18 (1-week observation window)

---

## Important behavioral rules (carry over from SCALE session)

- **Question vs action discipline (HARD RULE):** When user asks a question, answer it. Do NOT pre-emptively start fixing/executing. If question unclear → interview-gate. Only execute on explicit authorization. (See `feedback_question_vs_action.md` memory.)
- **Slash command naming (HARD RULE):** All orchestra slash commands = `/orchestra:<name>` namespaced. No bare `/<name>`. Sub-skill `:init` variants are internal composition, never user-facing slash. (See `feedback_slash_command_naming.md` memory.)
- **Spec-review aggregation (HARD RULE):** When multi-judge spec-review runs, WAIT for all judges → aggregate findings cross-judge → report to user → fire interview-gate when Critical/HIGH present → THEN apply fixes. No partial-fix off single judge. (See `feedback_spec_review_aggregation.md` memory.)
- **Ship whole skill override:** v1.7 commit-skill effort was shipped as v1.7.0 with all 3 LLDs (008+009+010) together; do not defer pieces to later versions when user explicitly says ship-whole. (See `feedback_user_wants_whole_skill.md` memory.)

---

## What was reverted in handoff prep

- `docs/features/006-archive-and-supersession-conventions-r5.md` — draft (scope-out)
- `docs/reviews/006-archive-and-supersession-conventions-r5.review.yaml` — attestation for above
- Both removed from working tree before handoff. LLD-006-r4 remains canon.

Attestations for the 5 paperwork-debt docs (BUG-013, BUG-014, philosophy-r2, LLD-008-r8, BUG-012) are RETAINED — they close Gate 3 violations (review run, fail noted, findings catalogued).

---

## Recommended fresh-session start (post-LLD-012 ship)

```
1. Read this HANDOFF.md (you're doing it)
2. Run `TaskList` to see open tasks
3. Verify ship state:
   - git log -3 → expect `8eebe00` (LLD-012 attestation trail) on top of `2d3e452` (LLD-012 doc)
   - For LLD-011 parallel work: git log --oneline | head -20 → check Phase 2 slice progression
4. Decide next move (LLD-012 v1.8 plan resume):
   a) Draft implementation plan `docs/plans/2026-05-11-lld-012-v18-implementation.md` — vertical slices for hook install + TLDR compression + lessons skill + lessons_lint + lessons_apply + compaction_probe. ~2-3 hrs.
   b) Apply 5 workflow.md gap fixes (G1, G3, G4, G7, G8) — small project-local edits from refresh note. ~1-2 hrs. (Tasks #3)
   c) File the 7 BUG-NEW candidates formally (A-G) — each needs Gate 3 spec-review. ~2-3 hrs. (Task #6)
   d) Triage pre-v1.7 backlog (BUG-001/002/004/005) — likely closed by LLD-008/009/010. ~30 min.
   e) Defer LLD-013 (workflow skill v2.0) until LLD-011 + LLD-012 implementations land.
5. OR pivot back to LLD-011 Phase 2 if owning that workstream.
```

**Open behavioral memory file added this session (HARD RULE):**
- `feedback_spec_review_fix_grill.md` — after spec-review findings, present 2-3 candidate fix-routes per finding (or per finding-class for batch mode) + recommend one + ask user; never silently pick approach.
