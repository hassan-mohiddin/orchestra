# Investigation: orchestra:workflow Skill Refresh

> **Status:** Scratch (`docs/investigations/` — never canon, no spec-review required)
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Trigger:** User wants to "work on workflow skill." `orchestra:workflow` is on roadmap for v2.0 (per `skills/init/SKILL.md:18` + `docs/design/orchestra-philosophy-r2.md:260`). Existing design input lives in `2026-05-07-workflow-spec-review-brainstorm.md` (393 lines, 6 research rounds), but most of that scratch's scope already shipped through v1.5/v1.6/v1.7. This note isolates what's genuinely still open for v2.0.

---

## Origin pointers

| Source | Role |
|---|---|
| `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` | Original 6-round research; seeded LLD-005 (rejected) → LLD-006-r4 + LLD-007 |
| `.claude/workflow.md` (221 lines) | Current project-local 8-step pipeline; situation-language only |
| `.claude/skills-registry.md` | Situation → skill bindings (skill names live ONLY here) |
| `.claude/rules/interview-gate.md` | "Cheap half" of backward-flow workflow (shipped v1.5.1) |
| `skills/init/SKILL.md:18` | "Workflow init (v2.0) — sets up `orchestra:workflow` skill scaffolding" |
| `docs/design/orchestra-philosophy-r2.md:260` | Roadmap gantt: `orchestra:workflow skill :v20, after v15, 63d` |
| `docs/HANDOFF.md` | Current ship state: v1.7.0 canon, v1.7.1 in flight (paperwork+code), v1.8 = BUG-015 |

---

## Q-status audit: 2026-05-07 scratch vs current canon

| Q | Topic | Scratch verdict | Current state | Status |
|---|---|---|---|---|
| Q1 | Reviewer separation (fresh subagent vs different model) | Fresh subagent mandatory | `orchestra:spec-review` shipped (LLD-007 → v1.6) | ✅ Closed |
| Q2 | Attestation file format | YAML sidecar at `docs/reviews/<doc-id>-rN.review.yaml` | Shipped + in use; schema validated | ✅ Closed |
| Q3 | Supersession scope | All reviewed types; plans+investigations mutable | LLD-006-r4 canon; bare-name design supersession added (BUG-014 fix pending v1.7.1) | ✅ Closed |
| Q4 | Phase model formalization | Informal — no Petri net | `.claude/workflow.md` 8-step informal | ✅ Closed |
| Q5 | Re-entry naming (`revise`/`supersede`/`re-enter`) | Deferred to LLD-005 | LLD-005 rejected/decomposed; **no primitive landed** | 🔴 OPEN |
| Q6 | Hard block vs warn | Hard block | L1-L4 lint + pre-commit hook + canon-frozen guard | ✅ Closed |
| Q7 | Backcompat for pre-v1.5 docs | Grandfather (no retro-attest) | Pre-v1.5 docs grandfathered; v1.5+ attestation-required | ✅ Closed |
| Q8 | 4-placement adoption (system / UserPromptSubmit / subagent / PreToolUse JIT) | All four wholesale | (a) ✅ trim shipped (b) ✅ caveman hook (c) ✅ spec-review subagent (d) 🔴 **PreToolUse gate enforcement NOT shipped** | 🟡 Partial |
| Q9 | CLAUDE.md trim (identity + index only) | Yes | `.claude/rules/` JIT pattern shipped | ✅ Closed |
| Q10 | Subagent skill API | Wrap reviewer in `orchestra:spec-review` | Shipped | ✅ Closed |

**Score:** 8/10 closed, 1 partial (Q8d), 1 fully open (Q5). Most of the 2026-05-07 scope landed through LLD-006/007 + v1.5.1 Interview Gate.

---

## Genuine open scope for v2.0 workflow skill

SIX concerns survive the audit (W6 added 2026-05-11 from rule-decay research). These are what the workflow-skill LLD (next available doc-id — LLD-011 is taken by spec-review v2 in drafting; this work likely lands as LLD-012+) must cover:

### W1 — Backward-flow state machine — DECIDED 2026-05-11

**Problem:** Workflow is forward-only (Phase 0 → Step 7). When execute surfaces a design gap, current pattern degrades to "patch with BUG-NNN" instead of "rewind to design, fix, re-flow."

**Key reframe (user, 2026-05-11):** Brainstorm = universal rescue path. Interview Gate = brainstorm-on-demand (inline trigger). Picking a rewind destination (Document vs Plan vs new BUG) is itself a silent decision the agent shouldn't make alone. Brainstorm output IS the destination decision.

**Decision: single primitive — `re-enter brainstorm`.**

| Sub-Q | Lock |
|---|---|
| W1a primitive | First-class skill action. Single primitive `re-enter brainstorm`. Not a state machine. Not 6 destinations. |
| W1b audit trail | `.claude/state/workflow-transitions.log` append-only `(ts, source_phase, brainstorm_doc_ref, exit_decision)`. Mechanical, no agent self-reporting. |
| W1c canon-frozen | Brainstorm OUTPUT decides supersession (not skill side-effect). When brainstorm output = "supersede design doc," skill invokes `orchestra:design-docs` supersession flow. |
| W1d granularity | Single backward edge: `Any → Brainstorm`. Existing rule, now mechanically enforced. Closes silent-destination-pick loophole. |

**Brainstorm primitive shape:**
1. **Trigger sources:** (a) agent self-detect — low context / silent decision / ambiguity / iteration plateau, (b) user invoke, (c) LLD-011 plateau signal, (d) PreToolUse hook block
2. **Action:** load project context (existing docs, current state, registry) → grill user via Interview Gate mechanic
3. **Exit criteria:** user explicit satisfaction — no ambiguity left
4. **Output (structured):** routes to forward phase OR triggers supersession OR opens new BUG-NNN
5. **Audit:** log line + (optional) scratch note in `docs/investigations/`

### W2 — Re-entry naming (Q5 from original scratch) — RESOLVED 2026-05-11

**Decision: `brainstorm` (or `re-enter brainstorm`).**

Auto-resolved by W1 collapse. Single primitive → no taxonomy needed. Supersession is downstream consequence of brainstorm output, not a workflow-level verb. `revise` dropped (ambiguous, never used). `supersede` reserved for LLD-006-r4 file-level mechanic only.

Slash command surface: `/orchestra:brainstorm` (or `/orchestra:workflow brainstorm` — TBD in skill packaging).

### W3 — PreToolUse gate enforcement (Q8d) — DECIDED 2026-05-11

**Problem:** Gate 2 (Design Gate) currently relies on agent self-discipline. No hook blocks Edit/Write on code paths unless matching `docs/{features,bugs}/...` exists.

**Decisions:**

| Sub-Q | Lock |
|---|---|
| W3a block scope | **Strict — all code dirs.** `skills/`, `cli/`, `packages/`, `apps/`, `tools/`, `commands/`. Skip `docs/`, `tests/`, `eval/`, `.claude/`. |
| W3b matching doc heuristic | (a) BUG-NNN / feat-NNN match in current branch name OR HEAD commit OR (b) explicit `Refs:` line in HEAD commit |
| W3c recency threshold | 7 days OR current-branch-touched; either qualifies |
| W3d bypass | `ORCHESTRA_BYPASS=trivial` env var for typo/rename/comment ops. Logged + audited. NO `--no-verify` semantics |
| W3e cross-plugin compat | Hook no-ops if `.claude/orchestra.json` absent (consumer hasn't init'd orchestra) |
| W3f brainstorm-on-block UX | Hook exits 2 with stderr: `"BLOCKED: no design doc for this code path. Invoke /orchestra:brainstorm"`. Agent reads stderr, decides. |

**Phase:** v2.0 with workflow skill (LLD-013+). NOT in v1.8 (LLD-012) since W3 is workflow-skill scope, not rule-durability.

### W4 — Iteration plateau guard

**Problem:** Spec-review currently averages 2-3 iterations per doc. Same findings re-surface. No mechanism breaks the loop.

**Current state:**
- `interview-gate.md§Iteration plateau heuristic` — "If review failing iter N+1 with overlapping findings from N, interview the user."
- **LLD-011 spec-review v2 in drafting** (per MEMORY:33) — 6 sub-judges + PDSA + class/instance + delta-review + rubric-freeze + 2-iter cap; v2.0.0 big-bang ship target. BUG-016 spun off for vocab canon.

**Implication:** Most of the original 5-layer plan is now absorbed into LLD-011 spec-review v2 — not deferred to v1.8 anymore. The workflow-skill LLD inherits a much-reduced W4 footprint.

**Remaining W4 footprint for workflow skill:**
- Plateau detection mechanism is LLD-011 internal (iter cap of 2 enforced inside spec-review).
- Workflow skill role = WIRE the plateau signal into phase-return primitive (W1). When LLD-011's 2-iter cap fires, workflow skill receives signal and routes to "re-enter Document" with interview-gate.
- Open Q: signal contract between `orchestra:spec-review` (cap-hit emitter) and `orchestra:workflow` (cap-hit consumer)? Side-effect file at `.claude/state/`? Exit-code? Skill-return?

### W5 — Skill packaging (project-local → consumer-installable) — DECIDED 2026-05-11

**Problem:** `.claude/workflow.md` is project-local to orchestra repo. Consumer repos installing orchestra get no workflow primitive.

**v2.0 deliverable:** Package as `skills/workflow/SKILL.md` + `commands/orchestra-workflow.md` + `skills/init/` v2.0 branch wires it into `orchestra:init`.

**Decision: Option D — Fixed skill body + registry-driven customization.**

Workflow steps are INVARIANT (8-step pipeline is the product). Consumer customization is on tool/skill bindings only, via `.claude/skills-registry.md`. Each situation in workflow (spec review, TDD execution, adversarial review, etc.) routes to consumer's registered skill. Default recommendations ship with orchestra; user can swap.

- W5a (templated vs fixed) → **Fixed.** No per-repo workflow.md installed.
- W5b (sub-skill `:init`) → **No init flow.** Workflow skill activates the moment registry exists. Skill-manager skill (below) handles the init/scan.
- W5c (consumer's own workflow.md) → **Skill is canonical source.** Consumer cannot fork workflow content. If consumer wants different workflow, they don't use orchestra.
- W5d (slash command surface) → TBD in W1 (state machine).

**Hard dependency: skill-manager / plugin-scanner skill (NOT YET BUILT)**

For Option D to work, skills-registry must be populated. Currently `.claude/skills-registry.md` is hand-curated. Production-ready workflow skill needs:
- Scans `~/.claude/plugins/` for installed plugins
- Reads each plugin's skill descriptions
- Detects conflicts (e.g. two skills bind to "spec review" situation)
- Surfaces conflicts to user, asks for resolution
- Generates / updates `.claude/skills-registry.md`
- Assigns default per-situation skill with sensible recommendations
- Re-runs on `/reload-plugins`

This is the **v1.5 positioning shift** per `orchestra-philosophy-r2.md:255-257`:
> Plugin scan + registry generation       :v15, after v13, 42d
> Plugin manifest spec for authors        :v15b, after v13, 42d
> Conflict resolution UX                  :v15c, after v13, 42d

Status: planned, NOT shipped. Workflow skill v2.0 ASSUMES skill-manager exists (build order: skill-manager → workflow skill).

For this refresh + brainstorm, treat skill-manager as a black box that:
1. Exists in consumer's install
2. Has produced a valid `.claude/skills-registry.md`
3. Resolves situation → skill lookups for workflow skill

Skill-manager LLD is separate concern (likely LLD-013+ slot, or v1.5-positioning resurrection).

---

### W6 — Rule durability layer (NEW — added 2026-05-11)

**Problem (user-raised 2026-05-11):** Even with rules in CLAUDE.md + `.claude/rules/` auto-load + SessionStart hooks, agent EVENTUALLY violates rules in long sessions and especially POST-COMPACTION. Skips spec-review, executes without permission, etc. No matter how strong the workflow primitive, agent forgets the rules due to context rot.

**Research output (2026-05-11 deep dive — Karpathy + community + Anthropic):**

#### Root causes confirmed

| # | Cause | Source |
|---|---|---|
| RC1 | Compaction silently DROPS process-standards while preserving task-state | Yajin Zhou post + Claude self-report |
| RC2 | "Acknowledge and ignore" is documented LLM behavior — apologize after violation | Mu et al. + arXiv 2407.08440 + GH issue #15443 |
| RC3 | Rush mode under rapid user messages — agent deprioritizes process | Yajin post |
| RC4 | Probabilistic self-exemption — agent evaluates "is rule for this case?" rather than executing deterministically | Yajin post |
| RC5 | Long rule files have lower per-rule attention weight | "300 lines, ignored all" post + Jaroslawicz et al. 2025 [secondhand citation] |
| RC6 | Prompt cache invalidation cost discourages mid-session rule updates (5-min TTL or 1-hr extended) | Anthropic prompt-caching docs |
| RC7 | SessionStart hook may NOT delay first turn — async race | Disler hooks-mastery |
| RC8 | Concurrent plugin SessionStart text blends silently — namespace fix is naming-only | Industry observation; no clean fix |

#### Karpathy prescriptions (citation-backed)

| # | Move | Citation |
|---|---|---|
| K1 | Three-layer separation: raw / wiki / schema | [llm-wiki gist 2026-04-04](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) |
| K2 | Auto-maintained `index.md` + append-only `log.md` per wiki | llm-wiki gist |
| K3 | Periodic `lint` as session ritual, not just commit gate | llm-wiki gist |
| K4 | Schema (CLAUDE.md / workflow.md / rules) = ONLY place LLM behavior is configured | llm-wiki gist |
| K7 | Memory artifact must be EXPLICIT (disk-resident, user-inspectable) not implicit (chat-history-derived) | [Farzapedia tweet 2040572272944324650](https://x.com/karpathy/status/2040572272944324650) [paraphrase — full body not fetchable] |
| K8 | Wiki COMPILES knowledge once + keeps current — not RAG-style rediscovery per turn | llm-wiki gist |

#### Industry-converged solutions (top 11, ranked by impact/cost)

| # | Solution | Source | Impact | Cost |
|---|---|---|---|---|
| S5 | Hooks-as-law: PreToolUse + PreCompact + SessionStart → 60%→90%+ compliance | [codetodeploy](https://medium.com/codetodeploy/your-claude-md-is-a-suggestion-hooks-make-it-law-0124c5783b68) + [dev.to 200-lines post](https://dev.to/minatoplanb/i-wrote-200-lines-of-rules-for-claude-code-it-ignored-them-all-4639) | HIGH | ~2 days |
| S7 | Recursive rule re-injection via `<system-reminder>` in every recent message | [siddhantkcode DEV](https://dev.to/siddhantkcode/an-easy-way-to-stop-claude-code-from-forgetting-the-rules-h36) + [Anthropic prompt-caching lessons](https://claude.com/blog/lessons-from-building-claude-code-prompt-caching-is-everything) | HIGH | low |
| S8 | Compress 300-line rules → 5-line nonnegotiables + `references/` expansion | Yajin post | HIGH | ~1 day |
| S10 | SessionStart matcher = `startup\|resume\|clear\|compact` | [Superpowers v4.3.0 blog](https://blog.fsck.com/agent-blog/2026/02/12/superpowers-v4-3-0/) | HIGH | minimal |
| S1 | `cli.compaction_probe` test — assert critical rules survive | [Anthropic context-engineering cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools) | MED | ~1 day |
| S2 | Custom compaction instructions via `compact_20260112` API | Anthropic API docs | MED | low |
| S4 | Anthropic Memory tool (file-system mount, "always view memory first" auto-injected) | [Memory tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) | MED | exploration |
| S3 | `clear_tool_uses_20250919` with `exclude_tools` — clear noisy tool results, preserve memory reads | Anthropic API | MED | low |
| S6 | Three-cause failure taxonomy (rush mode / post-compact loss / self-exempt) → target hooks per cause | [Yajin post](https://yajin.org/blog/2026-03-22-why-ai-agents-break-rules/) | MED | analytical |
| S9 | Constitutional 7-layer validator (Authority + Dedup + escalate gates) — 65%/15%/20% production split | [zer0h1ro 7-layer post](https://dev.to/zer0h1ro/7-layer-constitutional-ai-guardrails-preventing-agent-mistakes-15i5) | MED-HIGH | HIGH (design work) |
| S11 | Letta-style memory paging — workflow skill as OS managing page-in/out of rule files via JIT | [Letta forum](https://forum.letta.com/t/agent-memory-letta-vs-mem0-vs-zep-vs-cognee/88) | LOW-MED | HIGH |

**W6 open Qs:**
- W6a — Compress rules now (pre-v2.0) or hold for skill packaging? Compression matches DRY + Karpathy K4 regardless of skill packaging.
- W6b — PreCompact + SessionStart-matcher hooks: ship in v1.7.1 / v1.8 / v2.0? Compliance-positive on day 1.
- W6c — `<system-reminder>` recursive re-injection: who emits? UserPromptSubmit hook? PreToolUse for high-risk actions?
- W6d — Compaction probes: live in `tests/` or `eval/`? CI gate or session-time?
- W6e — Anthropic Memory tool: does Claude Code expose it to plugins? Need exploration.
- W6f — Workflow skill needs `index.md` + `log.md` auto-maintenance (Karpathy K2) — who writes? Hooks?

---

## Gap audit of current `.claude/workflow.md`

Improvements available WITHOUT waiting for LLD-011. Some are now-edits, some are LLD-011-edits.

| # | Loc | Gap | Fix size | Depends on LLD-011? |
|---|---|---|---|---|
| G1 | §Step 2 "Known issue" | References "BUG-015 when filed" — not filed yet | 1 line | No |
| G2 | §Transition rules | "Any step → Brainstorm" too coarse; misses common `Execute → Document` / `Verify FAIL → Document` cases | 3-4 rows | Partial (W1) |
| G3 | §Step 4.5 Doc sync | No mention that canon-frozen edits require supersession, not in-place | 2 lines + ref | No |
| G4 | §Phase 0 | No Interview Gate reference (already-shipped cheap-half belongs here) | 1 line | No |
| G5 | §Step 5.5 Adversarial | Trigger vague — should spec when adversarial fires (canon-frozen + lint/gate touches + iteration plateau) | 3 bullets | Partial (W4) |
| G6 | Missing | Iteration plateau heuristic not surfaced as first-class transition trigger | New §; or ref interview-gate.md | Yes (W4) |
| G7 | Missing | No pointer to `skills-registry.md§Override rules` at bottom of file | 1 line | No |
| G8 | §Step 4 table | `wip:` prefix mentioned for bug iteration loops but not cross-ref'd to §Bug iteration | 1 line | No |

**Now-applicable (no LLD-011 block):** G1, G3, G4, G7, G8. Five small edits. Subject to Gate 3 spec-review.

**LLD-011-blocked:** G2 (depends on W1 phase-return primitives), G5 (depends on W4 plateau guard), G6 (depends on W4).

---

## Brainstorm queue — ALL CLOSED 2026-05-11

```
W5 ✅ Option D (fixed skill body + registry-driven)
W1 ✅ Single primitive (re-enter brainstorm; one rewind edge)
W2 ✅ Resolved by W1 collapse — just `brainstorm`
W6 ✅ Rule durability layer — TLDR compression + hooks + probes (v1.8 LLD-012)
W7 ✅ Feedback loop — /teach + /violation + auto-promote (v1.8 LLD-012)
W3 ✅ PreToolUse gates — strict scope, brainstorm-on-block (v2.0 LLD-013+)
W4 ✅ Plateau signal — soft override (iter 3 after brainstorm, hard cap iter 5; v2.0 LLD-013+)
```

**Ship plan:**
- **v1.7.1** — code-only paperwork (BUG-013 + BUG-014 + LLD-008 #3). Closes immediately. ~1 hr.
- **v1.8** — LLD-012 "Rule Reliability + Learning Layer" (W6 + W7). ~5-7 days. Hooks + TLDR + lessons + probes.
- **v1.9** — BUG-015 spec-review feedback loop (already planned). Becomes LLD-011 spec-review v2 ship if drafting finishes by then.
- **v2.0** — LLD-013 workflow skill (W1 brainstorm primitive + W3 PreToolUse blocking + W4 plateau wiring) + LLD-011 spec-review v2 big-bang.

---

## Ship-state context (for scoping decisions)

| Item | Current | Implication for v2.0 workflow skill |
|---|---|---|
| Plugin version (canon) | v1.7.0 | v2.0 is 2+ versions away |
| v1.7.1 scope | Code-only paperwork (BUG-013 + BUG-014 + LLD-008 #3) | Workflow-skill design work parallel; do NOT block v1.7.1 |
| LLD-011 status | In drafting — spec-review v2 (6 sub-judges + PDSA + class/instance + delta-review + rubric-freeze + 2-iter cap); v2.0.0 big-bang target | W4 mostly absorbed into LLD-011. Workflow skill consumes plateau signal but doesn't own detection. |
| BUG-016 | Spun off from LLD-011 for vocab canon | Out of workflow-skill scope; track separately |
| Philosophy:378 | "Not a workflow framework. Orchestra composes existing workflow plugins." | Reconciliation needed in workflow-skill LLD — composition layer ≠ inventing engine. Must clarify boundary. |
| Philosophy:268 | "v2.0 — orchestra delivers full workflow composition" | Workflow-skill LLD codifies what "composition" means at primitive level. v2.0.0 ships LLD-011 + workflow-skill together (big-bang). |

---

### W7 — Feedback loop from user-detected violations (NEW — added 2026-05-11)

**Problem (user-raised 2026-05-11):** When user detects a runtime violation (agent skipped step / executed without permission / made silent decision), there's currently no mechanism for the agent to learn. Same violation repeats.

**Decision (W7 — DECIDED 2026-05-11):** A+C hybrid feedback loop. Folded into LLD-012 v1.8 alongside W6.

| Sub-Q | Lock |
|---|---|
| W7a capture mechanism | Two slash commands: `/orchestra:teach <free-text>` (fast) + `/orchestra:violation --rule=<id> --observed=<X> --expected=<Y>` (structured) |
| W7b storage | `docs/lessons/<YYYY-MM>-lessons.md` — append-only, committed, durable across sessions/machines (NOT `~/.claude/projects/` which is machine-local) |
| W7c re-injection | SessionStart hook (shared with W6b) injects TLDR + last N lessons up to token budget. UserPromptSubmit re-injects on long sessions. |
| W7d auto-promotion | Lessons recurring ≥3× → `cli.lessons_lint` auto-edits corresponding rule file's TLDR section + triggers Gate 3 spec-review. SPEC-REVIEW is the user-authorization gate (matches "no execute/edit/commit without explicit user authorization" rule). |
| W7e auto-promotion mechanic | Scan + draft = automatic. Commit = user-gated (via spec-review pass). |
| W7f ship scope | Fold into LLD-012 v1.8 alongside W6. "Rule Reliability + Learning Layer" coherent ship. |

**Karpathy mapping:** W7 directly implements K2 (`log.md` append-only — `docs/lessons/`) + K3 (periodic `lint` as session ritual — `cli.lessons_lint`) + K8 (wiki compiles knowledge once — auto-promotion mutates the schema layer mechanically).

**Industry parallel:** Reinforcement-from-correction pattern. User correction = high-signal training data. Append-only log = audit-friendly. Auto-promotion to rule file = "the agent writes its own constitution from observed failures, but with user veto via spec-review."

**LLD-012 expanded scope (v1.8 ship):**
1. W6a TLDR compression (rule files + CLAUDE.md)
2. W6b SessionStart + PreCompact hooks
3. W6c `<system-reminder>` injection mechanism
4. W6d `cli.compaction_probe` CI test
5. W7a slash commands `/orchestra:teach` + `/orchestra:violation`
6. W7b `docs/lessons/<YYYY-MM>-lessons.md` structure
7. W7c `cli.lessons_lint` periodic session ritual
8. W7d Auto-promotion (≥3× → spec-review-gated commit)

Estimated: ~5-7 days. Biggest LLD orchestra has shipped. Coherent story = worth it.

---

## BUG candidates surfaced by rule-decay research

Adjacent problems uncovered. To file when v1.7.1 closes:

| BUG | Title | Source | Severity |
|---|---|---|---|
| BUG-NEW-A | Compaction silently drops process-standards (no test verifies rules survive) | Yajin + Claude self-report | HIGH |
| BUG-NEW-B | SessionStart hook does NOT match `compact\|clear\|resume` — only `startup` | Audit cli/install_hooks.py | HIGH |
| BUG-NEW-C | Concurrent plugin SessionStart text may blend silently — no isolation | Industry observation | MED |
| BUG-NEW-D | Rules files 100+ lines each — lower per-rule attention vs 5-line nonnegotiables | Yajin + "300 lines" post | MED |
| BUG-NEW-E | Rush mode under rapid user-message cadence — no detection or pause | Yajin post | LOW (rare) |
| BUG-NEW-F | Anthropic Memory tool integration unknown — does Claude Code expose it to plugins? | Exploration needed | INFO |

These join existing v1.8 backlog (BUG-015 spec-review feedback loop already planned).

---

## Handoff: what this seeds

1. **Brainstorm session** — work through W5 → W1 → W2 → W3 → W4 with user (Task #2). Output drives:
2. **workflow.md edits** — apply now-applicable G1, G3, G4, G7, G8 + any G2/G5/G6 unblocked by brainstorm (Task #3).
3. **Workflow-skill LLD (LLD-012 or next-available)** — file in parallel with LLD-011 spec-review v2 since both target v2.0.0 big-bang ship. Seeded by:
   - This refresh note (closed-Q + open W list)
   - Brainstorm output (W1-W5 decisions)
   - Final workflow.md state (reflects what's already shipped)
   - 2026-05-07 scratch (history/research substrate)
   - LLD-011 plateau-signal contract (once that draft firms up)

---

## Open question for user (post-refresh)

Ready to brainstorm W5 (skill packaging shape) first? Or want to re-sequence the queue?
