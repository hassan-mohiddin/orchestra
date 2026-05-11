---
name: design-docs-init
description: Use when setting up design docs scaffolding in a new repo, or when migrating from orchestra v1.0 to v1.1 config schema. Triggers on phrases like "set up design docs", "initialize design docs", "scaffold docs directory", "create STANDARDS.md". Runs 3-prompt flow (mode / doc-types / add-ons) via the AskUserQuestion tool, then writes .claude/orchestra.json + docs/ subdirs + STANDARDS.md + optional CI/AGENTS.md/llms.txt.
---

# Design Docs Init

Sub-skill of `orchestra:init`. Sets up design docs scaffolding via a 3-prompt
interactive flow that MUST be driven by the `AskUserQuestion` tool — never by
descriptive markdown, never by silent defaults.

## When to invoke

- User explicitly asks to "set up design docs" or "initialize orchestra design docs"
- `orchestra:init` master skill delegates here
- The `orchestra:design-docs` skill auto-detects missing `.claude/orchestra.json`
  and routes here (after user confirms `[y]` to the auto-prompt)

## STEP 0 — v1.0 config detection (fires BEFORE Q1)

Before issuing Q1, you MUST detect a v1.0 config:

1. Read `.claude/settings.local.json` via the `Read` tool. If the file does
   not exist OR does not contain a top-level `orchestra` key, skip the
   rest of STEP 0 and go directly to Q1.
2. If `.claude/settings.local.json` contains an `orchestra` key, invoke
   the `AskUserQuestion` tool ONCE with the v1.0 migration payload
   defined in `prompts.md § v1.0 migration prompt`. Do NOT auto-migrate;
   do NOT skip; do NOT collapse this prompt into Q1.
3. If user picks `Migrate`: proceed to Q1/Q2/Q3, surfacing the detected
   v1.0 values in each AskUserQuestion description but still requiring
   the user to answer each question. Never auto-fill. After Q3 collect
   the three answers and invoke the CLI with the `--migrate-v10` flag:
   `python -m cli.init --migrate-v10 --mode <a1> --preset <a2>
   --addons <a3>`. The `--migrate-v10` flag tells the CLI to use
   `migrate_v10_to_v11` as the base config, preserving the v1.0
   `spec_review_skill` + `doc_paths` while overriding mode/preset/addons
   from the user's fresh answers. Do NOT omit `--migrate-v10` on the
   Migrate path — without it the CLI builds a fresh v1.1 default and
   the v1.0 fields are silently lost.
4. If user picks `Keep v1.0`: emit a chat message stating no changes
   were made + exit the skill. Do NOT proceed to Q1.

This STEP 0 is imperative: skipping it means a v1.0 user silently
double-initialises into a v1.1 schema with default answers.

## The 3-prompt flow — HARD RULE

You MUST invoke the `AskUserQuestion` tool **once per question**, in order
(Q1 → Q2 → Q3), waiting for the user's selection before issuing the next call.
Do NOT shortcut. Do NOT auto-fill defaults. Do NOT collapse multiple questions
into a single AskUserQuestion call — each step has its own header, and users
will treat them as distinct decisions.

Each call below shows the exact options to pass to `AskUserQuestion`. The
option text in `prompts.md` is the canonical wording — copy it verbatim.

### Label-stripping rule (applies to ALL questions)

`AskUserQuestion` option labels carry a `(Recommended)` suffix on the
default option. When mapping an answer to a CLI flag, **strip the
`(Recommended)` suffix first** (case-insensitive). Treat
`solo (Recommended)` and `solo` as the same value. Same rule for Q2's
`default-7 (Recommended)` and Q3's `yes (Recommended)`. Do NOT pass the
`(Recommended)` suffix through to the CLI.

### Q1: Mode

Invoke AskUserQuestion with:

- **question**: `"Are you the only decision-maker on this project, or working with 2+ senior engineers?"`
- **header**: `"Mode"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "solo (Recommended)", description: "Single decision-maker. ADR OKR Alignment field optional. No reviewer-assignment workflow." }`
  - `{ label: "team", description: "2+ senior engineers. ADR OKR Alignment field MANDATORY (lint-enforced). Spec review can assign reviewers." }`

Map the answer:
- `solo` (or label starting with `solo`) → `--mode solo`
- `team` → `--mode team`

### Q2: Doc types

Invoke AskUserQuestion with:

- **question**: `"How do you want orchestra to handle doc types?"`
- **header**: `"Doc types"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "default-7 (Recommended)", description: "Use the canonical 7 types as-is: Feature LLD, Bug Report, ADR, Design Doc, Postmortem, Runbook, Plan." }`
  - `{ label: "subset-rename", description: "Drop unused types and/or rename to formal alternatives (Tech Spec, Engineering Design, Decision Record, etc.). Informal renames rejected." }`
  - `{ label: "full-custom", description: "Define your own doc types with required sections, status enum, and naming pattern. Invariants enforced." }`

Map the answer (strip `(Recommended)` suffix first — see Label-stripping rule):
- `default-7` → `--preset default-7`
- `subset-rename` → **v2.0.1 fallback**: fire a confirm AskUserQuestion
  with the payload defined in `prompts.md § Q2 subset-rename / full-custom
  fallback (v2.0.1)`. Two options: `Switch to default-7` (Recommended)
  vs `Abort init`. On `Switch to default-7` → map to `--preset default-7`.
  On `Abort init` → emit chat message explaining subset-rename wizard
  is deferred to v2.1 + exit skill without running cli.init. Do NOT
  run the legacy descriptive wizard.
- `full-custom` → same v2.0.1 fallback as `subset-rename` (fire confirm
  AskUserQuestion → `Switch to default-7` or `Abort init`).

### Q3: Add-ons

Invoke AskUserQuestion with:

- **question**: `"Install the optional add-on files (CI workflow, AGENTS.md, llms.txt)?"`
- **header**: `"Add-ons"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "yes (Recommended)", description: "Adds .github/workflows/orchestra-lint.yml (CI gate), AGENTS.md (cross-tool AI agent context), llms.txt (LLM-readable nav)." }`
  - `{ label: "no", description: "Skip. You can run init with --force later to add them." }`

Map the answer:
- `yes` → `--addons yes`
- `no` → `--addons no`

### Then invoke the CLI

After all three answers are collected, run:

```bash
python -m cli.init --mode <a1> --preset <a2> --addons <a3>
```

Substituting the user's three answers into the flags. The CLI handles the
scaffolding (Bucket 1 + STANDARDS.md + Bucket 2 + DECISIONS.md + config
write). No further prompts should fire from the CLI side.

## Why this contract is HARD

BUG-001 root cause: skill markdown that *described* prompts (without
instructing the AskUserQuestion tool) left the 3-prompt flow up to
improvisation. Claude sometimes shortcut to `cli.init` with hardcoded
defaults. Path C fix: the skill body now MUST drive the prompts through
AskUserQuestion so the UI fires deterministically and the user's choices
flow into the CLI flags.

Programmatic invocation (CI, automation) bypasses the skill and calls
`python -m cli.init --mode X --preset Y --addons Z` directly.

## Idempotency

- Re-run = skip-existing (no overwrites)
- `--force` = regenerate STANDARDS.md, replace add-ons
- Bug-iteration-safe: re-running init never destroys hand-edited STANDARDS.md
  unless `--force`

## v1.0 → v1.1 migration

See STEP 0 above (imperative detection block). Canonical AskUserQuestion
payload for the migration prompt lives in `prompts.md § v1.0 migration
prompt`.

## Related skills

- `orchestra:init` — master init that delegates here
- `orchestra:design-docs` — main design-docs skill (use after init)
- `superpowers:requesting-code-review` — default `spec_review_skill` per ADR-001
