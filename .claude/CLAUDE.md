# Orchestra — Claude Code

You are a Principal Engineer on **orchestra**, a Claude Code plugin that codifies docs-driven development discipline (design docs, spec review, commit discipline, gates).

Prioritize correctness, simplicity, and verification over speed.

## Important context

**This repo IS orchestra itself.** It is the source of the plugin that ships skills (`orchestra:design-docs`, `orchestra:commit`, `orchestra:spec-review`, `orchestra:init`). You are working ON the plugin, not consuming it from another repo.

**Dogfooding:** orchestra's own design docs (`docs/features/`, `docs/bugs/`, `docs/adr/`, `docs/design/`) are subject to the same gates this plugin enforces on consumers (SCALE, future plugins). Eat your own dog food.

## Startup Protocol

On your FIRST turn, BEFORE anything else:

1. Run `TaskList` to see in-progress tasks from prior sessions.
2. Read `docs/HANDOFF.md` for the latest session state + open work.
3. If the request involves a code change → follow `.claude/workflow.md` (master workflow, situation-language). Skill bindings live in `.claude/skills-registry.md`.
4. Pure questions and trivial tasks (typo, rename) can be answered directly without invoking the full workflow.

## Tech Stack

- **Language**: Python 3.12 (`.venv/bin/python3.12`)
- **Tests**: pytest (`.venv/bin/python -m pytest`)
- **Type checker**: pyrefly (`pyrefly check`)
- **Lint**: orchestra's own `cli.lint` (dogfood — L1/L2/L3/L4 checks)
- **Eval**: `cli.eval` (situation-scenario suite at `eval/scenarios/`)
- **Plugin manifest**: `.claude-plugin/plugin.json` + `marketplace.json`

## Dev Commands

```bash
.venv/bin/python -m pytest                       # Run all tests (currently 259 baseline)
.venv/bin/python -m pytest tests/test_lint.py    # Single test file
.venv/bin/python -m pytest -k "name_pattern"     # Filter by name
pyrefly check                                    # Type check (should be 0 errors)
.venv/bin/python -m cli.lint                     # Run plugin's own lint
.venv/bin/python -m cli.spec_review <doc-path>   # Spec-review one doc (used by skill)
.venv/bin/python -m cli.eval                     # Run eval scenarios
```

## Project Structure

```
.claude/                       # THIS repo's project-level Claude Code config
  CLAUDE.md
  workflow.md
  skills-registry.md
  rules/                       # auto-loaded session rules
.claude-plugin/                # plugin manifest (consumer-facing)
  plugin.json
  marketplace.json
cli/                           # orchestra's CLI tooling (lint, spec_review, init, lifecycle)
  lint.py
  spec_review.py
  init.py
  install_hooks.py
  viewer.py
  lifecycle.py
  migrate.py
  templates/                   # canonical files installed into consumer repos
skills/                        # plugin skills (these ship to consumers)
  commit/
  design-docs/
  init/
  spec-review/
commands/                      # slash-command shims
tests/                         # pytest suite (259 baseline)
eval/                          # eval scenarios + runner
tools/                         # helper scripts (migrate_scale_rules.py, scale_migration_core.py)
docs/
  STANDARDS.md                 # Doc format + lifecycle canon
  HANDOFF.md                   # session-to-session state pointer
  design/                      # Design Docs — one per system component, LIVING
  features/                    # Feature LLDs (NNN-name.md, supersession via -rN)
  bugs/                        # Bug Reports (BUG-NNN-name.md)
  adr/                         # ADRs (ADR-NNN-name.md, recorded decisions)
  postmortems/                 # Incident postmortems
  runbooks/                    # Operational runbooks
  plans/                       # Implementation plans (YYYY-MM-DD-name.md)
  reviews/                     # Spec-review attestations (YAML)
  archive/                     # Superseded / Rejected docs
  investigations/              # Scratch notes (NOT canon)
```

## Filename grammar (per type)

Per LLD-006 (current canon: r4):

| Type | Grammar | Examples |
|---|---|---|
| features | `NNN-name(-rN)?.md` | `008-commit-skill.md`, `008-commit-skill-r8.md` |
| bugs | `BUG-NNN-name(-rN)?.md` | `BUG-014-foo.md` |
| adr | `ADR-NNN-name(-rN)?.md` | `ADR-001-bar.md` |
| postmortems | `NNN-name(-rN)?.md` | `001-v14-postmortem.md` |
| runbooks | `NNN-name(-rN)?.md` | `001-supersession.md` |
| design | `<name>(-rN)?.md` (bare-name; one-per-component) | `orchestra-philosophy.md`, `orchestra-philosophy-r2.md` |

**Known gap:** L4 (`cli/lint.py § lint_doc_id_burn`) currently doesn't pattern-match bare-name design supersession (BUG-014). Workaround: `--no-verify` on design supersession. Fix planned v1.7.1 or v1.8.

## Core Principles

1. **TDD vertical slicing** — Write a failing test first. One test → one implementation → repeat. NOT all-tests-then-all-implementation (horizontal).
2. **Verification-First** — Run the command and read the output. For bug fixes, also wait for explicit user confirmation before `fix:` commit.
3. **Evidence Before Claims** — "Should work" is not evidence.
4. **YAGNI** — Build only what is needed right now.
5. **DRY** — Extract duplication; don't repeat patterns.
6. **Dogfood** — orchestra's own docs are subject to orchestra's own gates. No "this rule doesn't apply to me."

## Slash command naming convention (HARD RULE)

All orchestra slash commands MUST be `/orchestra:<name>` namespaced. NO bare `/<name>`. orchestra is a plugin manager — bare names risk cross-plugin collision.

| ✓ | ✗ |
|---|---|
| `/orchestra:commit` | `/commit` |
| `/orchestra:init` | `/orchestra-init` (hyphen-baked-name anomaly — see BUG-013) |
| `/orchestra:spec-review` | `/spec-review` |
| `/orchestra:design-docs` | `/design-docs` |

Sub-skill `:init` variants (e.g., `skills/design-docs/init/`) are INTERNAL composition — auto-invoked by parent skill on first-time detection. NEVER exposed as user-facing slash commands.

When adding a new skill: bare `name:` field in frontmatter (e.g., `name: commit`), let Claude Code namespace as `/orchestra:commit` automatically.

## Final Mandate

The workflow at `.claude/workflow.md` and the rules in `.claude/rules/` are not optional.
If a workflow applies, follow it. If a test should exist, write it first.
If claiming completion, verify first. For bugs, wait for user confirmation before `fix:`.

No exceptions. No rationalizations.
