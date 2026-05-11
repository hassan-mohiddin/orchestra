# Skills Registry — situation → skill mapping (orchestra)

> **Purpose:** Single source of truth for which skill handles which situation. The workflow
> file (`.claude/workflow.md`) and rules use SITUATION LANGUAGE only — no skill names. When a
> plugin changes or a skill is added/removed, only this file needs updating.

**Last updated:** 2026-05-11
**Active plugins (7):** caveman, codex, impeccable, mattpocock-skills, orchestra (self-host), skill-creator, superpowers

**Note on self-host:** This is the orchestra plugin repo itself. We dogfood our own skills. `orchestra:*` skills come from the locally-developed plugin source (`skills/` in repo root), reloaded via `/reload-plugins`.

---

## Always-on situational bindings

| Situation | Skill | Plugin | Notes |
|---|---|---|---|
| Discovery / investigation defect-found | (no skill — Discovery Gate rule fires) | — | See `rules/documentation-gate.md` Gate 1 |
| Pre-design interview / brainstorm (project-aware) | `mattpocock-skills:grill-with-docs` | mattpocock | Reads docs/design/ + ADRs |
| Pre-design interview (no project context yet) | `mattpocock-skills:grill-me` | mattpocock | Fallback |
| Design doc creation (LLD / Bug / ADR / Postmortem / Runbook) | `orchestra:design-docs` | orchestra (self) | Dogfood our own skill. Saves to `docs/{features,bugs,adr,postmortems,runbooks}/`. |
| Spec review on docs | `orchestra:spec-review` | orchestra (self) | Judge-1. User invokes additional judges (codex, caveman) manually for multi-judge consensus. |
| Commit discipline (any commit, status flip, supersession) | `orchestra:commit` | orchestra (self) | Wraps Gates 4 + 5 (canon-frozen guard + commit strategy). |
| Init new orchestra-using repo | `orchestra:init` | orchestra (self) | Used when bringing orchestra into another project. |
| Plan writing (multi-step) | `superpowers:writing-plans` | superpowers | **Override save path:** `docs/plans/YYYY-MM-DD-name.md` |
| Plan execution (subagents) | `superpowers:executing-plans` or `superpowers:subagent-driven-development` | superpowers | |
| TDD execution (vertical slicing) | `mattpocock-skills:tdd` | mattpocock | Vertical-slice red-green-refactor |
| TDD principle (iron law: no code without failing test) | `superpowers:test-driven-development` (rule-only) | superpowers | Treat as principle. Execute via mattpocock-skills:tdd. |
| Bug debugging loop | `mattpocock-skills:diagnose` | mattpocock | Reproduce→minimize→hypothesize→instrument→fix→regression-test |
| Self code review (pre-commit) | `caveman:caveman-review` | caveman | Terse, line-by-line |
| Adversarial review (optional second opinion) | `codex:adversarial-review` (slash cmd) | codex | Different model = different blind spots |
| Adversarial / stuck-investigation rescue | `codex:rescue` (subagent) | codex | When investigation hits wall |
| Verification before complete | `superpowers:verification-before-completion` | superpowers | **Bug override:** also requires explicit user confirmation |
| Architecture refactor / deepening | `mattpocock-skills:improve-codebase-architecture` | mattpocock | Reads design docs + ADRs |
| Issue triage | `mattpocock-skills:triage` | mattpocock | Five-role state machine |
| Plan → issues breakdown | `mattpocock-skills:to-issues` | mattpocock | Tracer-bullet vertical slices |
| Skill creation / iteration / eval | `skill-creator:skill-creator` | skill-creator | Eval framework + variance analysis. **Use when modifying orchestra's own skills.** |
| Compression / brief mode | `caveman:caveman` | caveman | Auto-active via SessionStart hook |
| Commit messages | `caveman:caveman-commit` | caveman | Conventional commits, terse |
| Branch finishing / PR creation | `superpowers:finishing-a-development-branch` | superpowers | |
| Receiving code review (verifying feedback) | `superpowers:receiving-code-review` | superpowers | |
| Parallel independent tasks | `superpowers:dispatching-parallel-agents` | superpowers | |
| Worktree isolation | `superpowers:using-git-worktrees` | superpowers | |
| Compress memory file | `caveman:compress` | caveman | Compress CLAUDE.md / MEMORY.md to caveman format |
| PR / diff review (anthropic native) | `review` | anthropic builtin | Alternative to caveman:caveman-review for full PRs |
| Security review | `security-review` | anthropic builtin | Dedicated security lens |

---

## Skills available but NOT bound to situations

These are fine to invoke when explicitly needed, but the workflow does not auto-route:

- `superpowers:brainstorming` — superseded by `mattpocock:grill-with-docs` (project-aware).
- `superpowers:writing-skills` — superseded by `skill-creator`.
- `mattpocock-skills:write-a-skill` — superseded by `skill-creator`.
- `mattpocock-skills:to-prd` — uses PRD vocabulary. orchestra uses Feature LLD instead.
- `mattpocock-skills:caveman` — duplicate of `caveman:caveman` (real plugin with hooks). Use real one.
- `impeccable:impeccable` — UI-design skill. orchestra is CLI/plugin, no frontend.
- `init` (anthropic builtin) — for new repos, not orchestra.
- `superpowers:requesting-code-review` — superseded by `orchestra:spec-review` for doc review. Still usable for code-diff review when not doc-related.

---

## Override rules (applied AFTER skill resolution)

| # | Override | Source skill | Override |
|---|---|---|---|
| A | Save plan path | superpowers:writing-plans | `docs/plans/YYYY-MM-DD-name.md` (not `docs/superpowers/specs/`) |
| B | Save design path | superpowers:brainstorming | `docs/features/`, `docs/bugs/`, `docs/adr/` per type. Use `orchestra:design-docs` instead. |
| C | Doc vocabulary | mattpocock-skills:to-prd | Don't use. Use `orchestra:design-docs` for LLDs instead. |
| D | TDD execution shape | superpowers:test-driven-development | Iron-law principle preserved as rule. Execute via mattpocock-skills:tdd vertical slicing. |
| E | Caveman duplicate | mattpocock-skills:caveman | Use `caveman:caveman` (real plugin). Mattpocock copy suppressed. |
| F | Doc review skill | superpowers:requesting-code-review | For doc review, use `orchestra:spec-review` (4-gate rubric). Use superpowers only for code-diff review. |
| G | Commit decisions | (any commit op) | All commits route through `orchestra:commit` (canon-frozen guard + commit strategy). |

---

## Lookup procedure

When a workflow rule says "spec review the doc" or "execute via TDD":

1. Find matching situation in the table above
2. Use the bound skill
3. If skill not in current session's available-skills list:
   a. Check plugin enabled (settings + `/reload-plugins`)
   b. If still missing → tell user, do NOT silently skip
4. Apply override rules (paths, formats)

The workflow file never names skills directly. This file is the only place where situation ↔ skill bindings live.

---

## Adding / removing skills

When a new plugin installed:
1. Run `/reload-plugins`
2. Read each skill description
3. For each skill, decide: new situation row OR overlap-update existing
4. Note path/format conflicts → add override rule
5. Update `MEMORY.md` with rationale

When a plugin removed:
1. Find rows bound to its skills
2. Re-bind to alternative OR mark "no candidate"
3. Update workflow rules if no-candidate situation is critical

---

## Self-host caveat

orchestra develops its own skills under `skills/` in this repo. Two paths to invoke them:

1. **Production (consumer) path:** install orchestra as plugin → `/orchestra:<skill>` available
2. **Dev (in-repo) path:** with orchestra installed locally, `/reload-plugins` after each skill edit picks up changes from `skills/*/SKILL.md` in this repo

If `orchestra:<skill>` is not in the available-skills list while editing this repo:
- Check that orchestra is installed in your Claude Code (`/plugin`)
- Run `/reload-plugins`
- Verify skill is loaded by checking session-start available-skills system reminder
