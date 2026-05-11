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

## The 3-prompt flow — HARD RULE

You MUST invoke the `AskUserQuestion` tool **once per question**, in order
(Q1 → Q2 → Q3), waiting for the user's selection before issuing the next call.
Do NOT shortcut. Do NOT auto-fill defaults. Do NOT collapse multiple questions
into a single AskUserQuestion call — each step has its own header, and users
will treat them as distinct decisions.

Each call below shows the exact options to pass to `AskUserQuestion`. The
option text in `prompts.md` is the canonical wording — copy it verbatim.

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

Map the answer:
- `default-7` → `--preset default-7`
- `subset-rename` → `--preset subset-rename` then run the subset-rename wizard
  (toggle/rename per default type — currently out of scope for v2.0.1 hot path;
  surface "use default-7 for now" if user picks this)
- `full-custom` → `--preset full-custom` then run the full-custom wizard
  (same out-of-scope note)

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

If `.claude/settings.local.json` has an `orchestra` key (v1.0 config
location), this skill detects it during init. Before running the 3-prompt
flow, invoke AskUserQuestion ONE EXTRA TIME:

- **question**: `"v1.0 orchestra config detected at .claude/settings.local.json. Migrate to v1.1 schema (.claude/orchestra.json)?"`
- **header**: `"v1.0 migration"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "Migrate (Recommended)", description: "Copy fields (mode + doc_paths + spec_review_skill) to v1.1 schema. v1.0 block left in place (non-destructive)." }`
  - `{ label: "Keep v1.0", description: "Continue reading from settings.local.json — works but no v1.1 features." }`

On Migrate: proceed to Q1/Q2/Q3 with detected defaults pre-suggested in
the AskUserQuestion descriptions (still ask — never auto-fill).

## Related skills

- `orchestra:init` — master init that delegates here
- `orchestra:design-docs` — main design-docs skill (use after init)
- `superpowers:requesting-code-review` — default `spec_review_skill` per ADR-001
