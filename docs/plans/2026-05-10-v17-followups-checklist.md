# orchestra v1.7+ Followups Checklist

> **Doc ID:** 2026-05-10-v17-followups-checklist
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Plan
> **Status:** Active
> **LLD:** N/A (cross-cutting tracker; references multiple LLDs + BUGs + POSTMORTEMs)
> **Origin:** End-of-session 2026-05-10 (after v1.6.2 ship); consolidates all open followups so nothing falls through

## Header

**Goal:** Single durable checklist for every open work item identified through end of v1.6.2 ship (2026-05-10). Tick items as completed. Update Iteration Log row when completing. Consolidate or supersede when stale.

**Scope:** Cross-cutting. Each item links to the originating BUG / POSTMORTEM / LLD / Action-Item. Not a substitute for the originating doc — pointer-only tracker.

**Out of scope:** Features not yet conceived; speculative roadmap. Only items with concrete origin in shipped docs.

## File Structure

This is a tracker doc. No file structure produced; references existing files only.

## Tasks

Grouped by priority + temporal locality. Tick `[x]` when complete; add Iteration Log row noting commit + outcome.

### § A. Immediate / housekeeping (next session)

- [ ] **A1. Push 18 orchestra + 1 SCALE commit to origin** — not authorized in 2026-05-10 session per safety convention. Authorize before push.
  - orchestra commits: `6ca0ea7` → `f5e9dcc` (range)
  - SCALE commit: `94b32d8` (canon-frozen-guard rule)
  - Pre-push: confirm no secrets / credentials in any commit; `git log --diff-filter=A --name-only` review

- [ ] **A2. Test BUG-003 + BUG-007 fixes end-to-end on fresh repo**
  - `mkdir /tmp/bug-test && cd /tmp/bug-test && git init && python -m cli.viewer install-mkdocs`
  - Verify 5 files written + post-install warning fires when `.pre-commit-config.yaml` present
  - `pip install -r requirements-docs.txt && mkdocs build`
  - Verify `site/tags/` directory generated with status filter pages
  - Eval: extend `mkdocs-build` scenario in `eval/scenarios/` with `site/tags/` assertion

- [ ] **A3. Memory cleanup** — older handoff memory entries superseded by `project_v162_state.md`. Audit:
  - `project_phase_5_handoff.md` (orchestra v1.0→v1.3) — archive or trim
  - `project_v15_lld006_handoff.md` — archive or trim (LLD-006-r4 shipped)
  - `project_v16_lld007_handoff.md` — archive or trim (LLD-007 shipped + r5 supersession)
  - Decide: full archive vs surgical trim. Memory size budget per turn matters.

### § B. POSTMORTEM-session-process-drift Action Items

Source: `docs/postmortems/POSTMORTEM-2026-05-10-session-process-drift.md` § Action Items.

- [x] **B1. Close lint_commit L2 gap** — BUG-009 — Fix Applied (`6c13610`)
- [x] **B2. Auto-install pre-commit hook in orchestra repo** — BUG-010 — Fix Applied (`6c13610`)
- [ ] **B3. Tiered supersession rule (Critical/Important/Minor)** — BUG-011 — design captured (Status: Investigating); code impl pending v1.7+
- [x] **B4. SCALE-side `.claude/rules/canon-frozen-guard.md`** — Done (`94b32d8` SCALE commit)
- [ ] **B5. Mechanical Interview-Gate triggers** — replace markdown rule with hook-style check (e.g., commit-msg-write hook checking modified-file Status field). Deferred to workflow skill v2.0+ (LLD-011+)
- [ ] **B6. Mutation testing — file BUG-012-mutation-testing-coverage.md** — currently TBD-allocate placeholder. File the BUG; track as low-priority measurement work.
- [ ] **B7. Different-model process-judge** — separate from spec-review; dedicated to process-pattern detection (cargo-cult markers, canon-inplace, gate-skips). v1.7+ design phase needed.

### § C. v1.7 BUG implementations (deferred from v1.6.2)

5 BUGs Status: Investigating with v1.7+ deferral notes in their Iteration Log.

- [ ] **C1. BUG-001 init-flow-not-interactive (Critical)**
  - Verify current `orchestra:init` skill behavior on fresh repo first — may be already-resolved by AskUserQuestion-based init
  - If still broken: implement genuine 3-prompt flow with AskUserQuestion at each step
  - Reference: `docs/bugs/BUG-001-init-flow-not-interactive.md` § Iteration Log 2026-05-10

- [ ] **C2. BUG-002 gitignore-affects-tracked-files (High)**
  - Fix: `cli.init` must `git ls-files --error-unmatch <path>` before appending to .gitignore
  - If tracked: warn user + skip the .gitignore append for that path
  - Add test: tracked file + init → no .gitignore mutation
  - Reference: `docs/bugs/BUG-002-gitignore-affects-tracked-files.md`

- [ ] **C3. BUG-004 templates-not-project-aware (Medium)**
  - Fix: introduce `{project_name}`, `{tech_stack}`, `{repo_url}` template-variable substitution in `cli.init`
  - Read from `.claude/orchestra.json` config
  - Apply to `cli/templates/AGENTS.md.template` + `cli/templates/llms.txt.template`
  - Reference: `docs/bugs/BUG-004-templates-not-project-aware.md`

- [ ] **C4. BUG-005 mkdocs-nav-no-auto-detect (Medium)**
  - Fix option A: extend `mkdocs_hooks.py` with `on_files` event auto-discovering `docs/` subdirs and emitting nav warnings for unlisted dirs
  - Fix option B: migrate template to use `mkdocs-awesome-pages-plugin` (auto-discovery built-in)
  - Author judgment: pick A (less dependency) or B (less code)
  - Reference: `docs/bugs/BUG-005-mkdocs-nav-no-auto-detect.md`

- [ ] **C5. BUG-006 install-hooks-precommit-framework (Low)**
  - Fix: `cli.install_hooks` must detect `.pre-commit-config.yaml` presence
  - If found: emit warning + offer to add orchestra hook as `local` repo entry instead of overwriting `.git/hooks/pre-commit`
  - Unifies framework-detection with BUG-010 Part 3 (auto-install on bootstrap)
  - Reference: `docs/bugs/BUG-006-install-hooks-precommit-framework.md`

### § D. v1.7 design + impl items

- [ ] **D1. BUG-011 tiered supersession code impl**
  - Design captured in `docs/bugs/BUG-011-supersession-tier-refinement.md`
  - Phase 1: extend `is_narrow_change(prior_text, new_text, commit_msg=None)` with `Addresses: <attestation> finding N (severity)` parsing
  - Phase 2: STANDARDS template update — tiered table
  - Phase 3: update `.claude/rules/canon-frozen-guard.md` (SCALE) to encode tier logic
  - Phase 4: backfill — prior supersessions stay as-is (no rollback)
  - 5 new tests in `tests/test_lint_narrow_change_tiered.py`
  - Anti-gaming: severity comes from signed attestation YAML, not author claim

- [ ] **D2. Mermaid parse error fixes in BUG-006/007/008**
  - Pre-existing parse errors filed 2026-05-06 with broken diagrams
  - Blocks pre-commit hook full lint when those files staged
  - Choice: supersession (each becomes -r2.md with mermaid fixed) OR direct edit if Status flipped to non-canon-frozen
  - Currently BUG-007/008 are Fix Applied (canon-frozen) → supersession required; BUG-006 is Investigating → direct edit allowed
  - Run `npx -y @mermaid-js/mermaid-cli -i <doc>` per doc to find specific syntax errors

- [ ] **D3. Auto-install hook on `cli.init` bootstrap (BUG-010 Part 3)**
  - Extend `cli/init.py` to invoke `cli.install_hooks --pre-commit --repo .` if `.git/hooks/pre-commit` missing
  - Idempotent (already-installed → skip)
  - Removes manual install requirement for new contributors

- [ ] **D4. Spec-review prompt-template enum clarification**
  - Current: `skills/spec-review/prompt-template.md` says `Severity enum: Critical / Important / Minor`. Reviewers conflate this with doc-header severity.
  - Fix: prompt template explicitly distinguishes:
    - **Finding severity** (in attestation findings): `Critical / Important / Minor` — schema enforced
    - **Doc-header severity** (in BUG / postmortem header): per orchestra convention. BUG = `Critical / High / Medium / Low`. Postmortem = `SEV1-5`. NOT subject to finding-severity enum check.
  - Reduces false-positives observed across 4 spec-reviews this session
  - Reference: false-positive findings flagged in BUG-009/010/011 + POSTMORTEM-drift attestations

### § E. Plugin roadmap (later orchestra versions)

Source: `README.md` Roadmap table. Each = future LLD + skill ship.

- [ ] **E0. `orchestra:commit` skill (NEW — narrower-scope predecessor to E4 workflow skill)** — proposed end-of-v1.6.2 session. Packages all commit-time discipline into single skill: 4 lint levels (L1-L4) + 2 hook templates (pre-commit + commit-msg) + 6 SCALE-side rules consolidated (canon-frozen-guard, interview-gate, documentation-gate, commit-strategy, skills-routing, task-tracking) + BUG-006/010/011 unified framework-detection + tiered supersession + Refs:-line + doc-vs-code commit conventions. **Higher priority than E4** because narrower scope = faster ship; closes B5-partial + F1 + F2 + D3 + BUG-006 + BUG-010-Part-3 + BUG-011 unified ship. Status: **needs grilling session** before LLD draft. Brainstorm inputs: SCALE `.claude/rules/*` (6 files) + orchestra `cli/templates/*.sh` (2 hooks) + `cli/lint.py` (L1-L4) + `cli/install_hooks.py` + 11 BUGs + POSTMORTEM-canon-inplace + POSTMORTEM-session-process-drift. Grilling needed because: cli/templates/ messy (~13 files); test suite needs audit for skill coverage; scope-creep risk into E4 workflow skill territory.
- [ ] **E1. LLD-008 memory architecture** — referenced in older handoff; orthogonal to v1.6. Capture how memory entries grow / consolidate / archive over multi-session work
- [ ] **E2. LLD-009 lessons-capture** — separate skill for distilled-learning extraction (postmortems → reusable rules)
- [ ] **E3. LLD-010 skills-registry auto-population** — auto-discover plugins in `~/.claude/plugins/` → emit `.claude/skills-registry.md` with situation→skill bindings
- [ ] **E4. LLD-011+ workflow skill (v2.0+)** — backward-flow state-machine primitives (return-to-phase, feedback-loop persistence, mechanical Interview-Gate hook). Heavy. Workflow skill template-generates SCALE-side rules → unifies cross-repo strategy. **Closes B5, F1, F2, D3 partial AFTER E0 commit-skill ships its narrower scope first.** E4 picks up state-machine + multi-step-workflow primitives that E0 explicitly defers.
- [ ] **E5. `orchestra:tasks` skill (v1.2 placeholder)** — task-tracking discipline + cross-agent state
- [ ] **E6. `orchestra:gates` skill (v1.2 placeholder)** — pre-commit / CI gate enforcement broader than docs. **May overlap heavily with E0 commit-skill — grilling session must clarify boundary; possible E6 absorbs into E0.**
- [ ] **E7. `orchestra:plans` skill (v1.3 placeholder)** — plan-as-source artifact with TDD vertical slicing

### § F. Cross-repo strategy migration

When LLD-011+ workflow skill ships, SCALE-side derivatives become orchestra-canonical via `cli.init` template generation.

- [ ] **F1. SCALE → orchestra-canonical migration of `.claude/rules/canon-frozen-guard.md`** — currently SCALE-only. Move to `cli/templates/canon-frozen-guard-rule.md`; SCALE consumes via `cli.init`. Removes TRANSITION STATE marker from cross-repo refs in attestations.
- [ ] **F2. SCALE → orchestra-canonical migration of `.claude/rules/interview-gate.md`** — same pattern. Currently SCALE-only.
- [ ] **F3. `docs/STANDARDS.md` consolidation** — both SCALE and orchestra carry standards docs. Workflow skill consolidates. Source-of-truth = orchestra `cli/templates/standards-default-7.md`.
- [ ] **F4. Update RUNBOOK-iteration-plateau-detection (LLD-007 r4 followup)** — soften "do NOT reference cross-repo paths" line to allow dual-citation in transition-state; correct "generated from orchestra template at cli.init time" from aspirational to actual once workflow skill lands

### § G. Stuck-but-tracked (small followups, no blocking)

- [ ] **G1. arXiv 2512.01786 citation re-add** — removed pending verification in LLD-007-r5 § Related Documents. Re-add when source ID confirmed.
- [ ] **G2. `cli.spec_review_overlap` helper** — referenced in iteration-plateau runbook for deterministic finding-overlap signature `<gate>::<normalized-location>::<normalized-issue-key>`. Not yet implemented. Automates plateau detection.
- [ ] **G3. Stdin-bound size limit on `cli.spec_review`** — DoS bound. Set max stdin bytes before yaml.load. v1.6.x followup.
- [ ] **G4. Runtime token-cap enforcement** — currently SKILL.md prose only (`max_tokens: 4000`). Claude Code SDK doesn't expose `max_tokens` Task kwarg. Two paths: (a) move dispatch into Python with Anthropic SDK, (b) wait for SDK to expose. Track in r4/r5 attestations as v1.6.x followup #2.
- [ ] **G5. Iteration field vs `-rN` filename suffix semantic** — strict reading vs in-draft pragmatic. LLD-006-r4 followup. May need clarifying note in canon Glossary.

### § H. Older session memory items (still valid)

- [x] **H1. Spec-review enforcement on every doc commit** — Substantively closed by BUG-008 Fix Applied (`6244ccc`). Auto-fire-on-commit deferred to workflow skill v2.0+ (E4).
- [ ] **H2. 8 v1.4 BUGs backfill** (older handoff item) — partially done. 5 BUGs (003/007/008/009/010) Fix Applied; 5 (001/002/004/005/006) deferred per § C; BUG-011 design-only per § D1.

## Dependencies

```
A1 (push) ────────────────────────────────────────┐
A2 (test BUG-003/007 e2e) ────────────────────────┤
                                                   │
B6 (file BUG-012) ────────────────────────────────┤
                                                   │
C2/C3/C4/C5 (BUG impls) ──┐                       │
                          │                        │
C1 (BUG-001 verify) ──────┤  ──► v1.7.0 ship       │
                          │                        │
D1 (BUG-011 code) ────────┤                        │
D2 (mermaid fixes) ───────┤                        │
D3 (auto-install hook) ───┤                        │
D4 (prompt enum clarify)  ┘                        │
                                                   │
E4 (workflow skill LLD-011) ──┐                    │
                              ├──► closes B5+F1+F2 │
F1 (canon-frozen-guard mig) ──┤    + D3 partial    │
F2 (interview-gate mig) ──────┤                    │
F3 (STANDARDS.md consolidate) ┘                    │
                                                   │
E1/E2/E3/E5/E6/E7 (other LLDs) ──► v2.0+ roadmap   │
                                                   │
G1-G5 (small fixes) ──► roll into adjacent ships ──┘
```

E4 (workflow skill v2.0+) is highest ROI — single ship closes B5 + F1 + F2 + D3-partial + multiple cross-repo migrations.

## Sequencing rule

Per LLD-006-r4 supersession discipline: every closed item gets Iteration Log row in originating doc. Plan-doc ticks are mirror-only. Plans are not canon-frozen; this checklist may be edited freely without supersession.

## Estimated time

| Group | Effort |
|---|---|
| § A immediate | 1-2h (A1 5min + A2 30min + A3 30-60min) |
| § B drift action items | B6 = 30min file BUG; B5 + B7 = workflow skill (large) |
| § C 5 BUG impls | 4-6h total (C1 verify-may-close 30min; C2/C3/C5 ~1h each; C4 1-2h) |
| § D 4 design+impl | D1 = 3h; D2 = 1-2h via supersession; D3 = 30min; D4 = 30min |
| § E plugin roadmap | LLD-008/009/010 each ~1 day design + impl; LLD-011 (workflow) is multi-week; E5/E6/E7 placeholder |
| § F cross-repo migration | dependent on E4 |
| § G small fixes | <1h total when batched |

**Realistic v1.7 milestone:** § A + § C (5 BUGs) + § D1-D4. ~10-15h total.

**v2.0 milestone:** § E4 (workflow skill) + § F migrations. Multi-week.

## v1.7+ followups (NOT this checklist; track post-ship)

This doc IS the followup tracker. Updates land here directly. When all items in a section close → strike-through the section header. When the doc is fully consumed → archive to `docs/archive/plans/`.

## Iteration Log

| Date | Hypothesis | Change | Result |
|---|---|---|---|
| 2026-05-10 | End-of-session capture; nothing should fall through. Consolidate v1.6.2 ship + canon-inplace incident + 11 BUG triage + roadmap items into single tracker | Plan doc filed at `docs/plans/2026-05-10-v17-followups-checklist.md`. 8 sections (A-H), 30+ checkbox items. References: 11 BUGs + 3 postmortems + 3 runbooks + LLD-006-r4 + LLD-007-r5 + 6 SKILL/LLD placeholders | Status: Active. Updates land directly on this doc (Plans not canon-frozen) |
| 2026-05-10 | User proposed `orchestra:commit` skill as narrower-scope predecessor to E4 workflow skill — packages commit-time discipline (4 lint levels + 2 hooks + 6 SCALE rules + BUG-006/010/011 unification). Higher ROI shorter ship than full workflow skill. | Added § E0 entry. E4 reframed as state-machine successor. E6 (gates skill) flagged for possible absorption into E0. Marked **needs grilling session** before LLD draft. | Pre-compact prep: memory entry filed at `project_v17_commit_skill_proposal.md`. Post-compact entry point: grilling session on E0 scope + scope-creep boundary vs E4/E6. |

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Filed at end of v1.6.2 ship session. Captures all open followups identified through 2026-05-10. Plan doc convention: not canon-frozen, edits land directly without supersession ceremony. Status: Active. |
