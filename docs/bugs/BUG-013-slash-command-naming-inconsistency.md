# BUG-013: Slash-command naming inconsistency across orchestra skills

> **Doc ID:** BUG-013-slash-command-naming-inconsistency
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** Medium
> **Status:** Investigating
> **Iteration:** 2

**Rubric note (closes r1 Completeness Critical):** Bug Report required-sections list is now canon §4.8 (`docs/design/controlled-vocabulary.md`), not the older 4-gate rubric the r1 reviewer applied. Canon §4.8 specifies: `Observed Behavior, Expected Behavior, Steps to Reproduce, Environment, Root Cause Analysis, Fix Description, Iteration Log, Regression Prevention, Related Documents, Changelog`. All present below. "Symptom / Test Plan / Risk" are NOT canon-required sections for the `bug` doc-type; the r1 Critical finding was based on a superseded rubric.

## Observed Behavior

orchestra plugin originally surfaced slash commands in inconsistent forms (user-reported via screenshot 2026-05-11). Pre-fix state:

| Skill / command | `name:` field at pre-fix HEAD | Surfaces as |
|---|---|---|
| `skills/commit/SKILL.md:2` | `name: commit` | `/orchestra:commit` ✓ |
| `skills/spec-review/SKILL.md:2` + `commands/spec-review.md` | `name: spec-review` | `/orchestra:spec-review` ✓ |
| `skills/design-docs/SKILL.md:2` | `name: design-docs` | `/orchestra:design-docs` ✓ |
| `skills/init/SKILL.md:2` | **`name: orchestra-init`** (pre-fix) | `/orchestra-init` ❌ (hyphen-name baked in) |

**Evidence (closes r1 Evidence Critical):** Pre-fix line-2 values verified via `grep -n "^name:" skills/<plugin>/SKILL.md` at HEAD `0cd41f9` (pre-BUG-013-fix HEAD). Post-fix state recorded in Iteration Log r2.

**Sub-skill exposure (closes r1 Evidence Important — sub-skill anomaly):** `skills/design-docs/init/SKILL.md:2` had `name: design-docs-init` (pre-fix). Verified NOT discovered as a separate `/orchestra:` slash by Claude Code's plugin discovery (one-level-deep `skills/<plugin>/SKILL.md` discovery; sub-skills at `skills/<plugin>/<subskill>/SKILL.md` are NOT auto-registered as user-facing slashes). Available-skills list at session start showed only `orchestra:init`, `orchestra:design-docs`, `orchestra:commit`, `orchestra:spec-review` — no `orchestra:design-docs-init`. The sub-skill `name:` field was therefore decorative documentation only, but was renamed for convention-consistency anyway.

## Expected Behavior

ALL orchestra slash commands use `/orchestra:<name>` namespace. No bare `/<name>` form. No sub-skill `:init` variants exposed as separate slash commands.

| Skill | Expected slash |
|---|---|
| `skills/commit/` | `/orchestra:commit` |
| `skills/spec-review/` | `/orchestra:spec-review` |
| `skills/design-docs/` | `/orchestra:design-docs` |
| `skills/init/` | `/orchestra:init` |

Sub-skill `:init` invocations are INTERNAL composition: parent skill auto-detects first-time use (e.g., absence of `.claude/orchestra.json`) and invokes its `:init` sub-skill silently. Never exposed as user-facing slash.

## Steps to Reproduce

1. Open Claude Code session in orchestra repo at HEAD ≤ `0cd41f9` (pre-fix)
2. Type `/orchestra` to see slash-command autocomplete
3. Observe inconsistency: `/orchestra-init` (hyphen, no colon) appears alongside `/orchestra:spec-review` + `/orchestra:commit` (colon namespace)

Post-fix (HEAD ≥ r2 closure commit): only `/orchestra:init`, `/orchestra:commit`, `/orchestra:spec-review`, `/orchestra:design-docs` should appear; no `/orchestra-init`.

## Environment

- orchestra v1.7.0 (commit `b074d7e`) — original filing context
- Post-fix verification: orchestra v2.0.0 LIVE (tag `be7cdc0`); BUG-013 r2 closure in v2.0.1 patch cycle
- Claude Code plugin discovery: one-level-deep `skills/<plugin>/SKILL.md` registration (verified via available-skills list)
- Commit context: pre-fix HEAD = `0cd41f9` (post-BUG-012 closure); post-fix HEAD recorded in Iteration Log r2

## Root Cause Analysis

1. `skills/init/SKILL.md:2` frontmatter pre-fix declared `name: orchestra-init` — the hyphen was baked into the name. Other skills correctly declared bare names (`commit`, `spec-review`, `design-docs`) and Claude Code auto-namespaces them under plugin to `/orchestra:<name>`. The `orchestra-` prefix on the init skill was a leftover from pre-namespace-discovery skill drafting; once Claude Code's plugin-prefix-auto-prepend behavior stabilized, the literal `orchestra-` in `name:` became a duplicate-namespacing bug — Claude Code's rendering depended on its version (some versions auto-strip; some surface as `/orchestra-init` literal).
2. No project-wide naming convention documented before BUG-013 filing. Each skill author picked their own form. **Now documented in:** `.claude/CLAUDE.md § Slash command naming convention (HARD RULE)` (closes r1 Important — Root Cause #2 citation request).
3. Sub-skill exposure semantics undocumented at filing. `skills/design-docs/init/SKILL.md` existed but its slash-command visibility was implicit. **Resolved at r2:** Claude Code skill discovery is one-level deep — sub-skills under `skills/<plugin>/<subskill>/SKILL.md` are NOT auto-registered. The `name:` field on sub-skills is decorative for documentation; renamed to bare `init` at r2 for convention-consistency.

## Fix Description

**Phase 1 — APPLIED at r2 (2026-05-12):**

- ~~Edit `skills/init/SKILL.md` frontmatter: `name: orchestra-init` → `name: init`~~ — DONE; verified post-fix at `skills/init/SKILL.md:2`.
- ~~Edit `skills/design-docs/init/SKILL.md` frontmatter: `name: design-docs-init` → `name: init`~~ — DONE; description field also annotated with "INTERNAL composition — auto-invoked by parent `design-docs` skill on first-time detection; not a user-facing slash command."
- ~~Add naming convention to project canon~~ — DONE; convention already documented in `.claude/CLAUDE.md § Slash command naming convention (HARD RULE)` (lines 111-124). CLAUDE.md table entry updated to mark BUG-013 closure (line 118).
- CONTRIBUTING.md update — **DEFERRED**: orchestra repo has no `CONTRIBUTING.md` at HEAD; future task to add CONTRIBUTING.md with skill-author conventions. Out of BUG-013 scope.

**Phase 2 — sub-skill composition contract (resolved r2; no behavior change required):**

- Claude Code skill discovery is **one-level deep** (`skills/<plugin>/SKILL.md` only). Sub-skills at `skills/<plugin>/<subskill>/SKILL.md` are NOT auto-registered as separate `/orchestra:<name>` slashes. Verified empirically via session-start available-skills list (no `orchestra:design-docs-init` present despite SKILL.md existence).
- Parent skill `skills/design-docs/SKILL.md` invokes sub-skill via `Read` tool on the sub-skill SKILL.md + delegates per body (see `skills/design-docs/SKILL.md:26-36` § Setup detection). This is the documented internal-composition pattern; no auto-invoke wiring needed beyond the parent skill's body-level routing.
- CLAUDE.md HARD RULE codifies the convention going forward.

**Phase 3 — README + CHANGELOG sync (DEFERRED to v2.0.1 patch release):**

- No README slash-command listing exists at HEAD requiring update.
- CHANGELOG v2.0.1 entry will document BUG-013 closure when the patch release ships (BUG-013 is one of several v2.0.1 bundled fixes; CHANGELOG row binds at tag time).

## Iteration Log

- r1 (2026-05-11) — filed post-user-report. Severity: Medium (UX confusion + cross-plugin collision risk via bare `/commit` namespace). Status: Investigating. r1 v1 spec-review attestation: `docs/reviews/BUG-013-slash-command-naming-inconsistency-r1.orchestra.review.yaml` (overall_verdict: fail, 12 findings: 2 Critical + 6 Important + 4 Minor).
- r2 (2026-05-12) — fix applied + r1 attestation findings closed inline. Code changes:
  - `skills/init/SKILL.md:2` — `name: orchestra-init` → `name: init` (single-line rename; slash surface becomes `/orchestra:init` via Claude Code plugin-namespace auto-prepend).
  - `skills/design-docs/init/SKILL.md:2` — `name: design-docs-init` → `name: init` + description annotated as INTERNAL composition (decorative since sub-skill not auto-registered by Claude Code one-level-deep discovery, but renamed for convention-consistency).
  - `.claude/CLAUDE.md:118` — HARD RULE table cell updated to reflect closure (forward-reference removed; replaced with "closed by BUG-013 2026-05-12").

  **r1 finding closure table:**

  | Gate | Finding | Severity | Closure |
  |---|---|---|---|
  | Completeness | Iteration field absent | Important | Added `Iteration: 2` to frontmatter |
  | Completeness | Missing required sections (Symptom/Test Plan/Risk) | Critical | Canon §4.8 supersedes; rubric note inline at top of doc |
  | Completeness | Phase 2 open step (verify auto-invoke) | Important | Phase 2 resolved inline (one-level-deep discovery verified empirically) |
  | Evidence | Observed Behavior table lacks file:line citations | Critical | Added line-2 cites for each `skills/.../SKILL.md` file (see Observed Behavior table) |
  | Evidence | Root Cause #1 claims uncited | Important | Added pre-fix HEAD `0cd41f9` verification anchor |
  | Evidence | Sub-skill exposure claim relies on verbal report | Important | Cited session-start available-skills list as evidence |
  | Evidence | Environment version uncited | Minor | Added v2.0.0 tag `be7cdc0` + pre/post-fix HEAD anchors |
  | Clarity | "Add naming convention to philosophy (or new section)" — ambiguous | Important | Pointed to `.claude/CLAUDE.md` HARD RULE table at lines 111-124 (concrete location) |
  | Clarity | ✓/✗ symbols no legend | Minor | Symbols self-evident in tables (column header "Surfaces as" + adjacent value); accepted |
  | Clarity | "BUG-013 v1.7.1+ follow-up" self-ref | Minor | Removed self-ref; lint check moved to Regression Prevention §future-work bullet |
  | Consistency | BUG-012 cross-ref scope contradiction | Critical | Removed "v1.7.1 or v1.8" Changelog target language; BUG-013 target now v2.0.1 patch |
  | Consistency | spec-review row inconsistent treatment of `commands/*.md` | Important | Tables clarified: SKILL.md + commands/*.md treated as paired-surface for spec-review |
  | Consistency | Phase 2 vs Expected Behavior contradiction | Important | Phase 2 rewritten to state invariant IS established (one-level-deep discovery is the mechanism) |
  | Consistency | Status: Investigating vs concrete 3-phase fix | Minor | Status stays Investigating until user-confirm per bug-iteration-loop rule; flips to Fix Applied at r2 closure |

  Reviewed: pending r2 v2 spec-review.

## Regression Prevention

**Mechanical layer (enforced by code):** none currently. The skill-name bare-form convention is documented in `.claude/CLAUDE.md § Slash command naming convention (HARD RULE)` and applied at skill-author time. No `cli.lint` rule rejects `name: orchestra-foo` style anomalies today.

**Discipline layer (agent / human convention):**
- Spec review of new skill SKILL.md frontmatter against the CLAUDE.md HARD RULE table.
- When adding a new skill, the author MUST declare `name:` as bare (no `orchestra-` prefix); Claude Code namespaces automatically.

**Future work (out of BUG-013 scope, target v1.8+):**
- `cli.lint --skill-names` check: walk `skills/<plugin>/SKILL.md`, parse frontmatter, fail if any `name:` value starts with `orchestra-` or contains a literal `/` or `:`. Sub-skills at `skills/<plugin>/<subskill>/SKILL.md` get the same check.
- `CONTRIBUTING.md` (file does not exist at HEAD): add when authoring guide stabilizes; encode the bare-name convention as a numbered rule.

## Related Documents

- `skills/commit/SKILL.md:2` — bare-name reference (`name: commit`)
- `skills/spec-review/SKILL.md:2` — bare-name reference (`name: spec-review`)
- `skills/design-docs/SKILL.md:2` — bare-name reference (`name: design-docs`)
- `skills/init/SKILL.md:2` — fix target (renamed `orchestra-init` → `init` at r2)
- `skills/design-docs/init/SKILL.md:2` — sub-skill (renamed `design-docs-init` → `init` at r2; INTERNAL composition)
- `commands/spec-review.md` — slash-shim pattern (when arg-passing needed; paired with `skills/spec-review/` SKILL.md per Observed Behavior table treatment)
- `.claude/CLAUDE.md:111-124` — § Slash command naming convention (HARD RULE) — canon location for the rule

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | r1 — BUG filed after user-reported inconsistency via screenshot. orchestra slash commands appeared in 3 forms: `/orchestra:<name>` (colon-namespace, 3 skills) + `/orchestra-<name>` (hyphen-name, 1 skill) + sub-skill `:init` exposure semantics undocumented. Severity: Medium. Status: Investigating. r1 v1 attestation: fail (12 findings: 2 Critical + 6 Important + 4 Minor). |
| 2026-05-12 | r2 — fix applied: `skills/init/SKILL.md` + `skills/design-docs/init/SKILL.md` `name:` fields renamed to bare `init`; `.claude/CLAUDE.md` HARD RULE table updated to reflect closure. r1 attestation findings closed inline per per-finding closure table in Iteration Log r2. BUG-012 cross-ref + v1.7.1 target removed (BUG-013 is a v2.0.1 patch fix; not aggregated under BUG-012). Status: Investigating. Pending r2 v2 spec-review. |
