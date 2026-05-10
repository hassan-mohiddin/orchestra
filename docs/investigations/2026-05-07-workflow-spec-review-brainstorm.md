# Brainstorm: Workflow Iteration + Spec-Review Architecture

> **Status:** In progress (brainstorm scratch — not committed to docs/ taxonomy yet)
> **Date:** 2026-05-07
> **DRI:** Hassan Mohiddin
> **Trigger:** v1.4 rolled back after spec-review markers added without real review (3 commits + plan dropped). Two interlocking defects identified.

## The Two Defects

**Defect A — Workflow is forward-only.**
Phases: brainstorm → design → plan → execute → verify. No formal way to return when execution surfaces a design gap. Pattern degrades to "patch with BUG-NNN doc" instead of "rewind to design, fix, re-flow."

**Defect B — Spec review is self-attested by string presence.**
Marker `Iteration N spec review — X/4 gates pass` is the only evidence. Lint checks regex, not substance. Author = reviewer = same agent context. Result: cargo-cult markers.

## Research Summary (subagent, 2026-05-07)

### Key citations

| Source | Insight |
|---|---|
| van der Aalst, Petri Nets for Workflow | Petri nets are the only formalism with first-class concurrent re-entry tokens. |
| Camunda BPMN compensation events | Boundary-event compensation = forward-running corrective step, not state rewind. |
| Temporal saga / Argo / Airflow | Production engines do NOT support "rewind to phase N." Clear-and-rerun-forward or compensation-forward only. |
| ADR supersession pattern | Accepted ADRs are immutable; revision = new doc linked as Supersedes:. |
| RFC 2026 | Internet-Drafts auto-expire after 6 months unless promoted (timeout-bounded iteration). |
| Atlassian Kanban WIP limits | Structural brake on infinite iteration. |
| Cursor builder/validator | Production pattern: separate agents, separate context windows, optionally different models. |
| Joshtronic / Bluesock solo-dev | Delay self-review by ≥1 day to break confirmation bias. |
| arXiv 2510.12367 (LLM-REVal) | Single LLM judge inflates scores for LLM-authored content; same-context same-model is worst config. |
| arXiv 2512.01786 (LLM Jury) | Multi-judge ensembles outperform single judges; dynamic juries beat static. |
| SLSA + in-toto attestations | Evidence is a signed Statement keyed to a content hash, NOT a flag inside the doc. |
| Linford / Maruti SOC2 | Auditors discount checkboxes. Real evidence: timestamped, system-generated, signed by identity distinct from artifact author. |
| Redgate / Atlas roll-forward | Mature systems uniformly prefer roll-forward (corrective new state) over rewind (data loss + audit gap). |

### Synthesis: "Attested Supersession with Out-of-Context Review"

Three primitives the literature unanimously endorses:

1. **Immutable artifacts + supersession links** (ADR + DB roll-forward + in-toto). A doc never moves backward. New revision = new file with `Supersedes:` chain. Backward iteration implemented as forward supersession.

2. **Out-of-context adversarial review** (Cursor builder/validator + LLM-REVal). Reviewer = fresh agent context (subagent / separate session / different model). Receives doc + diff only. Prompted adversarially ("find problems"), no access to author reasoning trace.

3. **Signed external attestation** (SLSA / in-toto). Review record = separate hash-bound file (e.g. `docs/reviews/<doc-id>-r<N>.review.yaml`). Lint checks: file exists + hash matches + reviewer identity ≠ author + 4-gate findings present.

### Implementation risk
If attestation requires manual ceremony (spawn subagent → copy output → write file), it degrades to cargo-cult within weeks. SLSA's lesson. Must be ONE skill invocation that auto-writes the attestation.

## Open Questions for Grill (in order of dependency)

| # | Question | Notes |
|---|---|---|
| Q1 | Solo-mode reviewer separation acceptable as fresh subagent (same Opus), or require different model (e.g. Sonnet judge for Opus author)? | Drives skill design + cost. |
| Q2 | Attestation file location + format. Separate file vs in-doc both? | Drives lint shape. |
| Q3 | Supersession scope — apply to ALL doc types, or only "reviewed" types (LLD/ADR/BUG)? Plans currently mutate. | Drives lint + STANDARDS rewrite. |
| Q4 | Phase model — keep informal (brainstorm/design/plan/execute/verify) or formalize (Petri places + transitions)? | Drives complexity. |
| Q5 | Re-entry mechanic name — `revise`, `supersede`, `re-enter`? Single primitive or two? | Naming + skill. |
| Q6 | Hard block (commit-msg hook reject) vs soft warning (lint exit 1)? | Failure mode. |
| Q7 | Backward compatibility for existing v1.0-1.3 docs that don't have attestations. Grandfather-in or retro-attest? | Migration. |

## Proposed Grill Order

Q1 → Q2 → Q3 → Q5 → Q4 → Q6 → Q7

Rationale: Q1 is most consequential (sets reviewer cost model). Q2 + Q3 are downstream. Q5 is naming and depends on Q3 scope. Q4 is least urgent — can be informal phases for v1.5, formalize later. Q6/Q7 are policy.

## Round 2 Research (Context Rot + Rule Drift)

### Key citations

| Source | Insight |
|---|---|
| Liu et al. "Lost in the Middle" (TACL 2024) | U-shaped attention; ~30% accuracy drop on middle-positioned info. |
| Chroma "Context Rot" study (18 frontier models incl. Claude 4) | Non-uniform degradation at EVERY length increment, not just near limit. Distractor density matters as much as length. |
| Anthropic "Effective context engineering for AI agents" | Anthropic's own framing: attention is limited budget; context rot is real; recommend progressive disclosure + JIT retrieval over prompt-stuffing. |
| Cursor forum "Always Rules Intermittently Fail" | Cursor's `alwaysApply: true` rules drift in long sessions. Cursor's documented workaround: ask user to manually re-prompt. |
| Cline context-window doc | Per-turn rule injection + `new_task` handoff at threshold. Best-in-class but still falls through under tool-output recency pressure. |
| Mu et al. "Can LLMs Follow Simple Rules?" + arXiv 2407.08440 | LLMs frequently restate a rule and violate it within same response. "Acknowledge and ignore" is documented. |
| Anthropic "Agent Skills" engineering blog | Progressive disclosure: skill name+description in initial context; full SKILL.md loads on selection. CLAUDE.md acknowledged as fallback, not primary discipline. |
| Claude API prompt-caching docs | 5-min default TTL, 4 breakpoints. Stable content first; volatile hook content after breakpoint preserves prefix cache. |
| acdigest "Most of your Claude Code tokens are overhead" | Empirical: hook stacks inject 200-800 tokens each; ~2400 baseline per turn. Need cooldowns to prevent compounding. |

### Synthesis: Four-Placement Architecture

| Placement | Holds | Tradeoff |
|---|---|---|
| (a) System prompt (cache prefix) | Identity + gate-name index ≤500 tokens | Cache stability vs attention share |
| (b) UserPromptSubmit hook ≤80 tokens, conditional | Short imperative reminders keyed on prompt surface form | Recency-bias gain vs compounding bloat |
| (c) Fresh-context subagent | Discipline-critical actions (spec review, verify, doc-write) | Fidelity vs latency / coordination cost |
| (d) PreToolUse JIT disk read | Rule body injected JUST before action | Attention-at-action vs retrieval-failure-risk (mitigate with tool-level guard) |

### Deepest principle

**Place rule next to action, not remind model to remember it.**

Self-reminders ("re-read CLAUDE.md") are placebo. Position dominates introspection. The work is in moving rules to placements (a/b/c/d) — not in reminding the agent to honor them.

## Updated Open Questions

| # | Question | Status |
|---|---|---|
| Q1 reviewer separation | Settled: fresh-context subagent mandatory. Different model is bonus. | RESOLVED |
| Q2 attestation file | Settled: separate hash-bound file (SLSA/in-toto), not in-doc marker. | RESOLVED |
| Q3 supersession scope | Settled: all reviewed types (LLD/ADR/BUG/Design). Plans + investigations stay mutable. | RESOLVED |
| Q4 phase model | Stay informal phase names. | RESOLVED |
| Q5 re-entry naming | `revise` vs `supersede` vs `re-enter`? | OPEN |
| Q6 hard block vs warn | Settled: hard block via PreToolUse + tool-level guard. | RESOLVED |
| Q7 backwards compat | Grandfather v1.0-1.3 docs, or retro-attest? | OPEN |
| Q8 placement adoption | All four placements wholesale, or phase in? | OPEN |
| Q9 CLAUDE.md trim | Cut existing rules from auto-load to JIT-on-hook? | OPEN |
| Q10 subagent skill API | Calling convention for orchestra:reviewer subagent — must be one-line invoke. | OPEN |

## Round 3 Research (Memory Architectures)

### Three-layer scope decision

| Layer | Scope | Verdict |
|---|---|---|
| L0 | Claude Code primitives only — hooks, subagents, skills, file conventions | **COMMIT NOW (v1.5)** |
| L1 | Structured notes, scratchpad, attestation files, Karpathy-style agent-curated index | Future (v1.6-1.8) |
| L2 | Vector DB / RAG / agent-memory framework (Mem0, Letta, Zep, Cognee) | DEFER (v2.0+, signal-based upgrade) |

### Key citations

| Source | Insight |
|---|---|
| karpathy/llm-wiki gist | "Agent compiles, doesn't index" — markdown IS memory, structure = signal. |
| arXiv 2509.16780 | RAG wins page-level; GraphRAG wins relational. For ≤1000 structured docs with explicit refs, plain grep beats both. |
| FalkorDB / Meilisearch graph-vs-vector | Vector accuracy collapses past ~5 entities/query; graph stable past 10. Threshold not relevant for orchestra's ~50 docs. |
| Letta / Mem0 / Zep / Cognee comparisons | Self-curation failure mode: "write-without-manage" — agents add, never delete, stale gets retrieved as fresh. |
| TDS / DEV practical guides | Mitigation: separate SCRATCH from CANON; never retrieve scratch as canon. |
| Anthropic Effective Context Engineering | Smallest set of high-signal tokens. <10k stable rules → prompt; growing/conditional → retrieval; user-state → memory. |
| Cursor memories user reports | Closed/opaque memory fails — users can't audit. Visible file-based wins. |

### Critical insight

**Skipping straight to L2 makes drift INVISIBLE.** Today when agent skips a rule, transcript shows it. Vector store mediation hides that diagnostic signal. Orchestra's problem is **enforcement, not retrieval**. Build gates first.

### Concrete L0 commit (orchestra v1.5)

| Component | Mechanism |
|---|---|
| Gate 2 enforcement | PreToolUse hook on Edit/Write to apps/packages — block unless matching `docs/features/NNN-*.md` or `docs/bugs/BUG-NNN-*.md` exists + recently modified |
| Per-action attestation | PostToolUse hook for docs → append `(ts, doc, gate)` line to `.claude/state/session-attestations.log` |
| Anti-rot doc context | UserPromptSubmit hook injects 10-line "active doc context" via grep — NOT full rule body |
| Gate 3 spec review | Fresh-context subagent wrapping `superpowers:requesting-code-review`; verdict file = artifact at `docs/reviews/<doc-id>-r<N>.review.yaml` |
| File conventions | `docs/investigations/` (scratch, NEVER canon) / `docs/{features,bugs,adr,design,postmortems,runbooks}/NNN-*.md` (canon) / `docs/STANDARDS.md` (rules) |
| Skills read contracts | Every gate-skill reads rule body from `.claude/rules/<gate>.md` — workflow update = markdown edit |
| CLAUDE.md trim | Identity + gate-name index ≤500 tokens. Bodies live in `.claude/rules/` and JIT-inject. |

### L1-upgrade signal metrics

Trigger upgrade when ≥2 fire concurrently:
- Gate-violation rate >0.5 per 4-hour session (even with L0 hooks installed)
- docs/ corpus >200 files OR median retrieval requires >2 grep iterations
- Cross-session handoff failures >1/week

## All grill questions resolved

| # | Resolution |
|---|---|
| Q1 reviewer separation | Fresh subagent mandatory; different model is bonus. Use `superpowers:requesting-code-review`. |
| Q2 attestation file | Separate hash-bound YAML at `docs/reviews/<doc-id>-r<N>.review.yaml`. |
| Q3 supersession scope | All reviewed types (LLD/ADR/BUG/Design). Plans + investigations stay mutable. |
| Q4 phase model | Informal phase names — no Petri net formalism. |
| Q5 re-entry naming | Defer to LLD-005 (small surface). |
| Q6 hard block vs warn | Hard block via PreToolUse + tool-level guard. |
| Q7 backwards compat | Grandfather v1.0-1.3 docs. NO retroactive attestation (would be cargo cult). New convention from v1.5 forward; mark old docs legacy. |
| Q8 placement adoption | All four placements wholesale at L0. Phasing-in defeats the point. |
| Q9 CLAUDE.md trim | Yes. Identity + gate-name index only. Bodies move to `.claude/rules/` for JIT. |
| Q10 subagent skill API | Wrap `superpowers:requesting-code-review`. orchestra:spec-review skill = thin wrapper passing 4 gates. |

## Round 4 — Gates + Philosophy Audit (RETURNED)

### Key citations

| Source | Insight |
|---|---|
| OPA Policy as Code in CI/CD | Declarative executable rules replace prose policy. |
| Rally Health Conftest Policy Packs | Markdown lives INSIDE executable Rego, not as standalone "rule docs". |
| Ken Muse — Security Theater | Documented controls pass audit; effective undocumented ones fail. Named pattern: compliance theater. |
| PactFlow — Schemas Can Be Contracts | Drift between spec + code is detected by EXECUTING the spec, not re-reading it. 70% API failures = silent contract drift that passed self-checks. |
| Pragmatic Engineer — Bug Management | Defer ticket creation until reproduction confirmed. "STOP" on every observation imports interrupt cost. |
| Yegor256 — Bug Tracking Principles | One ticket per cause; iteration history as comments — VALIDATES orchestra's one-BUG-NNN rule. |
| Pragmatic Engineer — RFC + Design Doc Examples | Stripe/Uber/Microsoft/Google all separate design (what/why) from rollout (how/when). VALIDATES LLD vs Plan no-overlap. |
| Naz Hamid — Opinionated vs Flexible | Opinionation accelerates onboarding, raises exit cost. VALIDATED for solo dev with fork capability. |
| Jacksonbates / Hillel Wayne — Solo Dev Code Quality | Self-review pathology predates LLMs. Workarounds: time-delay, written PR-to-self, automated linter. |
| Pair Programming Meta-Analysis (ScienceDirect) | Quality gain from forced verbalization, NOT from second person. |

### Gates verdict

| Gate | Status | Rebuild as |
|---|---|---|
| 1 Discovery | KEEP | Tighten "STOP" to confirmed defect not suspected. |
| 2 Design | KEEP | Validated. |
| 3 Spec Review | **REBUILD** | Separate-context reviewer + executable attestation lint. Current = compliance theater. |
| 4 Commit Refs | KEEP | Already non-self-attestation, hook-enforced. |
| 5 Impl Sync | **REBUILD** | Mechanical drift checks (Refs target exists, file paths resolve, signatures match AST), not author re-read. |

### Philosophy verdict

| Stance | Status |
|---|---|
| Discipline is the product | VALIDATED — keep |
| ADR-only, no RFC | VALIDATED solo |
| Formal-vocab whitelist | UNTESTED — keep, enforce via lint |
| LLD vs Plan no-overlap | VALIDATED |
| One BUG-NNN spans iterations | VALIDATED |
| Opinionated not configurable | VALIDATED for current user; document opinions as ADRs |
| **"Markdown discipline > code"** | **CONTRADICTED — REMOVE** |
| Solo-mode default | UNTESTED, defensible |

### Replacement philosophy stance

> **Executable discipline > markdown discipline. Markdown is the human-readable face of code-enforced rules.**

Policy-as-code lineage (OPA / Conftest / Rego). Rule IS the executor (cli.lint, hooks, subagent verdict file). Markdown describes for humans; never substitutes for executor.

### NEW Philosophy stance — Interview Gate / Question Stance

> **When agent feels lost, low on context, making silent decisions, or skipping a step — HALT and ASK. Confusion is signal, not noise. Silent decisions are the cargo-cult precursor.**

User-proposed 2026-05-07. Encodes meta-rule that failed in this session: agent jumped from research to "approve LLD-005" without grilling open design decisions. Same pattern as marker-without-review. Mechanism: PreToolUse hook on Edit/Write asks "is there a silent decision happening here?" before allowing the action. OR: skill-level instruction at every phase transition that lists known-unknowns and forces ask-or-document.

Interview Gate is candidate **Gate 0** — fires before any forward motion. To-be-designed in LLD-005.

### Single biggest architectural change before v1.5

Move Gate 3 (spec review) + Gate 5 (impl sync) from author-attested markdown to executable checks + separate-context reviewer. Until that exists, every other gate's reliability is bounded by integrity of agent grading own homework.

## v1.5 Scope (FINAL after all 4 rounds)

**LLD-005 covers FIVE concerns — all derive from one principle: rule enforced where it acts, not described where it sits.**

| Pillar | What |
|---|---|
| 1. Memory architecture | 4-placement (system prompt / UserPromptSubmit / fresh subagent / PreToolUse JIT) + attestation files + file conventions (scratch vs canon) |
| 2. Skills registry auto-population | orchestra scans installed plugins; builds situation → skill registry; surfaces conflicts. Delivers v1.5 positioning promise. |
| 3. Backward-flow / supersession primitive | Never edit reviewed canon docs in place. `LLD-NNN-r2.md` with `Supersedes: LLD-NNN-r1.md`. Forward-only with re-entry as supersession. |
| 4. Gate redesign (policy-as-code) | Gate 1: tighten trigger language. Gate 3: REBUILD — separate-context reviewer + executable attestation lint. Gate 5: REBUILD — mechanical drift checks. Gates 2 + 4 keep as-is. |
| 5. Philosophy update | REMOVE "markdown discipline > code". REPLACE with "executable discipline > markdown; markdown is the human-readable face of code-enforced rules." Document each kept opinion as ADR. |

All five share primitives: file conventions + attestation contract + hook system + skills registry + lint engine. Atomic LLD.

## Orchestra positioning re-confirmed

orchestra is **orchestrator**, not wrapper:
- Defines workflow + philosophy + memory architecture
- Provides hook / skill / situation primitives
- Skills registry maps situation → user-installed skill (NOT hardcoded)
- Lint checks artifacts (attestations) are conformant — agnostic to which skill produced them
- Spec review = situation; user's registered reviewer (could be superpowers, mattpocock, custom) fulfills it
- DOES NOT wrap any specific plugin

## v1.6+ Roadmap

| Version | Scope |
|---|---|
| v1.6 | Backfill 8 v1.4 BUGs (BUG-001..007) under v1.5 process — each with subagent review + attestation file + supersession-style status updates |
| v1.7+ | Future per emerging needs |
| v2.0 | L2 memory upgrade (vector/graph) IF L1-upgrade signals fire (gate-violation rate >0.5/session post-L0, corpus >200 docs, handoff failures >1/week) |

## Next step (post-Round-4 research)

Once gates+philosophy audit returns: write LLD-005 covering all three pillars.

Ship under bootstrap-mode review (manual 4-gate walkthrough + author flags own concerns explicitly + user confirms). Use the LLD as canonical example of v1.5 process for all subsequent work.

## Round 5 — File Format Choice (post-r1 review)

Triggered by user question: why YAML for attestations, markdown for design docs? Should we re-evaluate format per file type?

### Key citations

| Source | Insight |
|---|---|
| llms.txt spec (Answer.AI) | "Markdown is most widely understood format for language models" — empirical not formal argument |
| AGENTS.md (Linux Foundation Dec 2025) | 60k+ projects adopted; markdown picked for cross-runtime portability |
| Karpathy llm-wiki gist | Markdown choice IMPLICIT, not argued. "Just a directory of LLM-generated markdown files." |
| Agent Skills open spec | Markdown body + YAML frontmatter — production convergence |
| Cursor MDC reference | `.mdc` = markdown + YAML frontmatter (description, globs, alwaysApply) |
| improvingagents.com benchmark | Format causes 10-40% performance variance. YAML 62.1% > Markdown 54.3% > JSON 50.3% > XML 44.4% on nested retrieval (GPT-5 Nano). |
| TOON format launch (Nov 2025) | NARROW critique — only for tabular agent-to-agent data exchange. Not for prose. |
| Cloudflare "Markdown for Agents" | Markdown for prose surfaces; structured sidecars for data. Same as orchestra pattern. |
| Agent KG production reports (Cognee, FalkorDB) | KGs used for memory substrate; NOT for canonical instruction files in any major coding agent. |

### Verdict

orchestra's current three-format split is **empirically validated**. No 2025-2026 high-visibility critique argues markdown is broadly wrong. The contrarian "markdown isn't for agents" position is not supported by literature. Production AI coding tools have CONVERGED, not diverged, on markdown + YAML frontmatter for rules/skills/instructions.

### Per-file-type choice (validates current + 2 minor updates)

| File type | Format | Status |
|---|---|---|
| Design docs (LLD/ADR/BUG/Design/Postmortem/Runbook) | Markdown + optional YAML frontmatter | KEEP (current) |
| Rules (`.claude/orchestra/rules/*.md`) | Markdown + YAML frontmatter | UPDATE — add frontmatter for activation conditions per Cursor MDC convention |
| Attestations | YAML sidecar | KEEP (current) |
| Metrics | JSONL | KEEP (current) |
| Lessons | Markdown + YAML frontmatter | NEW — was unspecified; adopt design-doc shape |
| STANDARDS.md, philosophy, README | Markdown | KEEP |

### Biggest risk

Unifying everything onto a single format breaks the system. Markdown destroys machine-validatable contracts (attestations, metrics). Pure structured destroys prose nuance (design docs, lessons). Resist unification urge. Three-format split is correct per content-shape rule (prose vs schema-fixed vs append-event).

## Round 6 — Spec-Review Skill Architecture (for LLD-007)

Research dispatched after r2 FAIL + Path B decision (drop atomic LLD, decompose). Findings inform LLD-007 architecture.

### Key citations

| Source | Insight |
|---|---|
| OpenAI Codex CLI + cookbook + codex-plugin-cc | Schema-forced JSON output, "flag only actionable issues introduced by patch" scope-anchor, three-stage pipeline, `gpt-5-codex` recommended for review specifically |
| caveman:cavecrew-reviewer | One-line/severity-emoji format engineered against LLM rambling; "no praise, no scope creep, skip formatting nits" |
| superpowers:requesting-code-review | Placeholder-templated prompt + `general-purpose` subagent + after-each-task cadence |
| Greptile / CodeRabbit benchmarks 2025 | Async dispatch + bounded context + structured findings; FP rate is dominant production complaint |
| arXiv 2410.21819 (Self-Preference Bias) | Same-model judging biased toward familiar text via perplexity correlation. **Opus-judging-Opus systematically under-flags.** |
| arXiv 2506.13639 (Empirical LLM-as-Judge) | Rubric quality + structured output dominate reliability; CoT only helps when rubric weak |
| Anthropic Skill Best Practices | "Low freedom" (script/CLI) for fragile + consistency-critical; "high freedom" (prose) for context-dependent |
| Diffray + arXiv 2411.03079 | Hallucinated findings biggest production complaint; mitigation = file:line citation + auto-verify |
| Jesse Vincent adversarial-review prompt | Competitive two-reviewer scoring; minimum-issue quota framing |

### orchestra:spec-review architecture (informs LLD-007)

**Skill body shape:** hybrid — frontmatter + prose body (reviewer prompt) + sidecar `cli.spec_review` for dispatch + schema validation + YAML serialization.

**7-element adversarial prompt anatomy:**
1. Role anchor — "adversarial reviewer; find problems"
2. Scope fence — "this doc only, not broader system"
3. 4-gate rubric — concrete pass/fail per gate (Completeness / Evidence / Clarity / Consistency)
4. Anti-sycophancy — "if zero findings, justify in rationale field"
5. Anti-pedantry — "skip taste-level issues unless they change meaning"
6. Forced YAML schema v1.0 — Critical/Important/Minor enum, NO Info level
7. Minimum-issue framing — "typical reviews find 2-5 issues; zero requires justification"

**Dispatch:** Claude Code Task tool, `subagent_type: general-purpose`. Context = doc path + schema path + rubric only — never session history.

**Failure-mode mitigations (top 3):**
- Schema-validate YAML output, retry once on failure, hard-fail on second (kills 42% pipeline-attributed hallucinations)
- Scope fence + "justify zero findings" clause (kills sycophantic-pass + scope-creep)
- File:line/section citation required per finding + auto-verify cite exists (kills hallucinated findings, #1 production complaint)

**Borrow from cavecrew:** one-line, severity-emoji, no-praise/no-scope-creep finding format inside YAML rows.

**Biggest risk:** same-model self-preference bias. Opus-judging-Opus systematically under-flags Opus-authored docs. v1.5 mitigation: configurable `--judge-model` flag; document limitation prominently.

### Multi-judge architecture (user constraint, 2026-05-07)

orchestra reviewer = **Judge 1 (always default + always present)**. User adds Judge 2, 3, 4 as optional extras via skills registry (LLD-008+). If no extras registered, orchestra alone performs review. Matches LLM-Jury production pattern (arXiv 2512.01786) at smallest scale. Consensus algorithm deferred — for v1.5, attestation is union of all judges' findings; failing if any judge fails. Smarter consensus (weighted vote, conflict resolution) lands when jury_mode flag activates in v1.6+.

## Pre-Dispatch Pattern Checklist (added 2026-05-07 after 4 review fails)

Before dispatching subagent review on any LLD, verify draft against patterns observed in prior reviews:

| # | Pattern | Catch by |
|---|---|---|
| P1 | Citations without URLs | Every external ref must include URL or be removed |
| P2 | Hand-wavy helper functions ("details in implementation") | Every helper either fully specified OR named with cited parser library |
| P3 | OR / "alternatively" in design decisions | Every design decision commits to ONE; if undecided → open question, don't OR |
| P4 | Multiple definitions of same term | Single source of truth (Glossary); other sections reference Glossary |
| P5 | Acceptance items without tests | Every acceptance item maps 1:1 to a test in Testing § |
| P6 | Self-conflict (rule applied to its own LLD breaks) | Apply each new rule to the LLD itself as sanity check before dispatch |
| P7 | Temporal ambiguity (current vs post-merge) | Explicit "BEFORE merge" / "AFTER merge" labels on every dual-state mention |
| P8 | Silent decisions / "improvise it" | Interview Gate — surface to user before deciding silently |
| P9 | New machinery without interaction-check vs existing rules | Run mental test: does new rule break any existing rule on dogfood case? |

This checklist applied to LLD-006-r3 before dispatch.

## Status (2026-05-08 final)

All 6 research rounds complete. Path B decided. 5-iteration LLD chain converged.

**Final state of LLD-006:**
- LLD-006-r1 → FAIL (12 findings) → Rejected
- LLD-006-r2 → FAIL (10 findings, Evidence pass) → Rejected
- LLD-006-r3 → FAIL (11 findings, Evidence pass) → Rejected
- LLD-006-r4 → FAIL fresh subagent (9 findings) → author-applied 7 mechanical fixes inline → **conditional_pass** with 4 v1.6 followups tracked → CANON

**Migration dogfood (executed 2026-05-08):**
- LLD-005 r1 + r2 → `docs/archive/features/` (Status: Rejected)
- LLD-006 r1 + r2 + r3 → `docs/archive/features/` (Status: Rejected per promotion rule branch 2)
- LLD-006-r4 → stays at `docs/features/` (canon-frozen pending implementation)
- Attestations stay at `docs/reviews/` with updated `doc_subject.path` fields

**v1.5 architecture validated end-to-end on its own design docs.**

LLD-007 (orchestra:spec-review subagent + attestation creation skill) — Round 6 architecture mapped, NOT yet written. To be written after LLD-006-r4 implementation ships.

## Handoff

See `docs/plans/2026-05-08-state-of-orchestra-lld-006-handoff.md` for fresh-session resume guidance.

