# BUG-013: Slash-command naming inconsistency across orchestra skills

> **Doc ID:** BUG-013-slash-command-naming-inconsistency
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** Medium
> **Status:** Investigating

## Observed Behavior

orchestra plugin currently surfaces slash commands in 3 different forms (user-reported via screenshot 2026-05-11):

| Skill / command | `name:` field | Surfaces as |
|---|---|---|
| `skills/commit/SKILL.md` | `name: commit` | `/orchestra:commit` ✓ |
| `skills/spec-review/SKILL.md` + `commands/spec-review.md` | `name: spec-review` | `/orchestra:spec-review` ✓ |
| `skills/design-docs/SKILL.md` | `name: design-docs` | `/orchestra:design-docs` ✓ |
| `skills/init/SKILL.md` | **`name: orchestra-init`** | `/orchestra-init` ❌ (anomaly: hyphen-name baked in) |

Sub-skill anomaly: `skills/design-docs/init/` exists as an internal sub-skill but is referenced in `skills/init/SKILL.md` body as `design-docs:init`. If exposed as a slash command (`/orchestra:design-docs:init`), it leaks internal composition to users. Currently NOT exposed (per user observation: "I don't see that at all") but the naming convention is ambiguous.

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

1. Open Claude Code session in orchestra repo
2. Type `/orchestra` to see slash-command autocomplete
3. Observe inconsistency: `/orchestra-init` (hyphen, no colon) appears alongside `/orchestra:spec-review` + `/orchestra:commit` (colon namespace)

## Environment

- orchestra v1.7.0 (commit `b074d7e`)
- Claude Code (current; namespacing varies across versions)

## Root Cause

1. `skills/init/SKILL.md` frontmatter declares `name: orchestra-init` — the hyphen is baked into the name. Other skills declare bare names (`commit`, `spec-review`, `design-docs`) and Claude Code auto-namespaces under plugin.
2. No project-wide naming convention documented. Each skill author picked their own form.
3. Sub-skill exposure semantics undocumented. `skills/design-docs/init/SKILL.md` exists but its slash-command visibility is implicit, not specified.

## Fix Description

**Phase 1: rename + convention doc**
- Edit `skills/init/SKILL.md` frontmatter: `name: orchestra-init` → `name: init`.
- Add naming convention to `docs/design/orchestra-philosophy.md` § Skill artifact layout (or new section): "All skill `name:` fields are bare names; Claude Code namespaces as `/orchestra:<name>` automatically."
- Update `CONTRIBUTING.md` § Adding a new Orchestra skill: enforce bare-name convention.

**Phase 2: sub-skill composition contract**
- Document in design philosophy: "Sub-skill `:init` variants are internal composition. Parent skill auto-detects first-time use and invokes them silently. Never expose as user-facing slash."
- Update `skills/init/SKILL.md` body to reflect rename (any internal references to `orchestra-init` → `init`).
- Verify `skills/design-docs/SKILL.md` auto-invokes `design-docs/init/` on first-time detection (currently delegates per skill body — confirm behavior).

**Phase 3: README + CHANGELOG sync**
- README slash-command listings + CONTRIBUTING examples reflect `/orchestra:init` instead of `/orchestra-init`.
- CHANGELOG v1.7.1 entry documents the rename.

## Iteration Log

- r1 (2026-05-11) — filed post-user-report. Severity: Medium (UX confusion + cross-plugin collision risk via bare `/commit` namespace). Status: Investigating.

## Regression Prevention

- `CONTRIBUTING.md` § Adding new skill: assertion that `name:` MUST be bare (no `orchestra-` prefix).
- Spec review of new skill SKILL.md frontmatter against convention.
- Consider lint check (BUG-013 v1.7.1+ follow-up): `cli.lint --skill-names` validates all `skills/*/SKILL.md` `name:` fields are bare (no plugin-prefix).

## Related Documents

- `skills/commit/SKILL.md` — bare-name reference
- `skills/init/SKILL.md` — anomaly source
- `skills/design-docs/init/SKILL.md` — internal sub-skill (slash-exposure unclear)
- `commands/spec-review.md` — slash-shim pattern (when arg-passing needed)
- `docs/design/orchestra-philosophy.md` — § Skill artifact layout (target for convention doc)
- `docs/bugs/BUG-012-v17-1-minor-followups.md` — v1.7.1 minor-fix aggregate (NOT this BUG's home; BUG-013 is a standalone Medium issue)

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | BUG filed after user-reported inconsistency via screenshot. orchestra slash commands appear in 3 forms: `/orchestra:<name>` (colon-namespace, 3 skills) + `/orchestra-<name>` (hyphen-name, 1 skill) + sub-skill `:init` exposure semantics undocumented. Severity: Medium. Target fix: v1.7.1 or v1.8. Status: Investigating. |
