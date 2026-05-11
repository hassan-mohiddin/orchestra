# design-docs:init — AskUserQuestion canonical option text

This file is the source of truth for the option text passed to the
`AskUserQuestion` tool. The skill body (`SKILL.md`) instructs Claude to
invoke `AskUserQuestion` three times, in order; the question / header /
option payload for each call lives here. Copy verbatim.

Per BUG-001 Path C: the skill body MUST drive the prompts via
`AskUserQuestion`. Descriptive markdown is not enough — improvisation slips
in. These payloads are the deterministic source.

## Q1: Mode

- **question**: `Are you the only decision-maker on this project, or working with 2+ senior engineers?`
- **header**: `Mode`
- **multiSelect**: `false`
- **options**:
  - **label**: `solo (Recommended)`
    **description**: `Single decision-maker. ADR OKR Alignment field optional. No reviewer-assignment workflow. Industry threshold per Pragmatic Engineer.`
  - **label**: `team`
    **description**: `2+ senior engineers. ADR OKR Alignment field MANDATORY (lint-enforced). Spec review can assign reviewers. Plugin manifest (v1.5+) supports per-team conflict resolution.`

Answer mapping → CLI flag:
- `solo` → `--mode solo`
- `team` → `--mode team`

## Q2: Doc types

- **question**: `How do you want orchestra to handle doc types?`
- **header**: `Doc types`
- **multiSelect**: `false`
- **options**:
  - **label**: `default-7 (Recommended)`
    **description**: `Use the canonical 7 types as-is: Feature LLD (docs/features/NNN-name.md), Bug Report (docs/bugs/BUG-NNN-name.md), ADR (docs/adr/ADR-NNN-name.md), Design Doc (docs/design/<component>.md), Postmortem (docs/postmortems/POSTMORTEM-YYYY-MM-DD-name.md), Runbook (docs/runbooks/RUNBOOK-name.md), Plan (docs/plans/YYYY-MM-DD-name.md).`
  - **label**: `subset-rename`
    **description**: `Drop unused types and/or rename to formal alternatives. Whitelist: Tech Spec, Engineering Design, Spec, Design Brief, Decision Record, Architecture Decision, Incident Report, Operations Runbook, Implementation Plan, Engineering Plan, Postmortem, Retrospective. Informal renames rejected. RFC NOT in whitelist (orchestra philosophy: ADR-only).`
  - **label**: `full-custom`
    **description**: `Define your own doc types with required sections, status enum, and naming pattern. Invariants enforced regardless: Changelog section MANDATORY; Status enum >= 3 states (with terminal state); Naming pattern in NNN-kebab.md / YYYY-MM-DD-kebab.md / kebab.md.`

Answer mapping → CLI flag (strip `(Recommended)` suffix first — see SKILL.md § Label-stripping rule):
- `default-7` → `--preset default-7`
- `subset-rename` → fire v2.0.1 fallback AskUserQuestion (see § Q2
  subset-rename / full-custom fallback below). Do NOT use legacy
  descriptive wizard — that path is deferred to v2.1.
- `full-custom` → same v2.0.1 fallback as `subset-rename`.

## Q3: Add-ons

- **question**: `Install the optional add-on files (CI workflow, AGENTS.md, llms.txt)?`
- **header**: `Add-ons`
- **multiSelect**: `false`
- **options**:
  - **label**: `yes (Recommended)`
    **description**: `Adds .github/workflows/orchestra-lint.yml (CI gate that runs cli.lint --range main..HEAD on every PR, catches orphan fix:/feat: commits, broken metadata, mermaid errors), AGENTS.md (cross-tool AI agent context — Linux Foundation Agentic AI Foundation spec), llms.txt (LLM-readable navigation index — llmstxt.org spec).`
  - **label**: `no`
    **description**: `Skip. You can run init with --force later to add them.`

Answer mapping → CLI flag:
- `yes` → `--addons yes`
- `no` → `--addons no`

## Q2 subset-rename / full-custom fallback (v2.0.1)

Fires only if user picks `subset-rename` or `full-custom` in Q2. The
descriptive wizards from prior versions are deferred to v2.1; for v2.0.1
the skill MUST confirm-switch-to-default-7 or abort.

- **question**: `Subset-rename / full-custom flows are deferred to v2.1. Switch to default-7 for now, or abort init?`
- **header**: `Q2 fallback`
- **multiSelect**: `false`
- **options**:
  - **label**: `Switch to default-7 (Recommended)`
    **description**: `Use the canonical 7 doc types. You can re-run /orchestra:init in v2.1 to switch to a custom preset.`
  - **label**: `Abort init`
    **description**: `Exit without scaffolding. No files written. Wait for v2.1 to support subset-rename / full-custom.`

Mapping:
- `Switch to default-7` → `--preset default-7` (continue to Q3)
- `Abort init` → emit chat message + exit skill before invoking cli.init

## Re-run prompt (only if .claude/orchestra.json already exists)

Fires from `skills/init/SKILL.md` Step 2 when a v1.1+ config is detected.
Do NOT fire this prompt for a fresh init.

- **question**: `Orchestra is already configured in this repo. What would you like to do?`
- **header**: `Re-run`
- **multiSelect**: `false`
- **options**:
  - **label**: `Re-run init`
    **description**: `Regenerate STANDARDS.md and replace add-ons (CI workflow, AGENTS.md, llms.txt). Hand-edited STANDARDS.md will be overwritten. Equivalent to python -m cli.init --force.`
  - **label**: `Migrate`
    **description**: `Only meaningful if config schema is older than current. Copies fields to the new schema, leaves old block in place (non-destructive).`
  - **label**: `Keep current (Recommended)`
    **description**: `Abort. Leave config and scaffolding untouched.`

Mapping (after stripping `(Recommended)` suffix):
- `Re-run init` → **re-fire STEP 0 + Q1 + Q2 + Q3** via the sub-skill
  body, collect fresh answers, THEN invoke:
  `python -m cli.init --force --mode <a1> --preset <a2> --addons <a3>`.
  Do NOT shortcut to `python -m cli.init --force` alone — the CLI would
  use argparse defaults and the prompts would never fire, re-introducing
  the BUG-001 root cause for the re-run path.
- `Migrate` → invoke the schema migration path. Read v1.0 fields from
  `.claude/settings.local.json`, then re-fire STEP 0 + Q1 + Q2 + Q3
  surfacing the detected v1.0 values as suggested defaults in each
  AskUserQuestion description (still ask — never auto-fill). After Q3,
  invoke: `python -m cli.init --migrate-v10 --mode <a1> --preset <a2>
  --addons <a3>`. The `--migrate-v10` flag tells the CLI to use
  `migrate_v10_to_v11` as the base config and override
  `mode/preset/addons` from the flags, preserving the v1.0
  `spec_review_skill` + `doc_paths`.
- `Keep current` → emit chat message + exit skill

Suppress `Migrate` option from the AskUserQuestion call when the existing
`.claude/orchestra.json` `version` field equals the current schema
version (currently `1.1`).

## v1.0 migration prompt (only if v1.0 config detected)

Fires BEFORE Q1, only if `.claude/settings.local.json` contains a v1.0
`orchestra` config block.

- **question**: `v1.0 orchestra config detected at .claude/settings.local.json. Migrate to v1.1 schema (.claude/orchestra.json)?`
- **header**: `v1.0 migration`
- **multiSelect**: `false`
- **options**:
  - **label**: `Migrate (Recommended)`
    **description**: `Copy fields (mode + doc_paths + spec_review_skill) to v1.1 schema. v1.0 block left in place (non-destructive).`
  - **label**: `Keep v1.0`
    **description**: `Continue reading from settings.local.json — works but no v1.1 features.`

On `Migrate`: detected v1.0 values are still surfaced in the Q1/Q2/Q3
AskUserQuestion descriptions ("currently solo per v1.0 config — confirm?")
but the user MUST still answer each question. Never auto-fill.

## Final summary (chat message after CLI completes)

After `python -m cli.init --mode <a1> --preset <a2> --addons <a3>` succeeds,
emit (as plain chat output, not via AskUserQuestion):

```
=== orchestra:design-docs:init complete ===

Files created (N):
  docs/features/.gitkeep
  docs/bugs/.gitkeep
  ...
  docs/STANDARDS.md
  .claude/orchestra.json
  .gitignore (appended)

Files skipped (M, already existed):
  ...

Next steps:
  1. Install pre-commit hook:    python -m cli.install_hooks
  2. Write your first design doc: ask Claude "create a feature LLD for X"
  3. Lint manually anytime:      python -m cli.lint --pre-commit
  4. (v1.5) Reject a Draft:       python -m cli.lifecycle reject --file <path> --reason <line>
  5. (v1.5) Lint attestations:    python -m cli.lint --attestations

Terminology (v1.5):
  - canon-located doc — lives at docs/<type>/ (Drafts + canon-frozen)
  - canon-frozen — Status in {Approved, Implemented, Verified, Fix Applied, Current}
  - archived — Status in {Rejected, Superseded}; lives at docs/archive/<type>/
  - narrow change — append Changelog row + flip whitelisted frontmatter only
  - supersession — new -rN file with Supersedes: link; prior moves to archive

Status: ready.
```
