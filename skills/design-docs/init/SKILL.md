---
name: design-docs-init
description: Use when setting up design docs scaffolding in a new repo, or when migrating from orchestra v1.0 to v1.1 config schema. Triggers on phrases like "set up design docs", "initialize design docs", "scaffold docs directory", "create STANDARDS.md". Runs 3-prompt flow (mode / doc-types / add-ons) and writes .claude/orchestra.json + docs/ subdirs + STANDARDS.md + optional CI/AGENTS.md/llms.txt.
---

# Design Docs Init

Sub-skill of `orchestra:init`. Sets up design docs scaffolding via 3-prompt interactive flow.

## When to invoke

- User explicitly asks to "set up design docs" or "initialize orchestra design docs"
- `orchestra:init` master skill delegates here
- The `orchestra:design-docs` skill auto-detects missing `.claude/orchestra.json` and routes here (after user confirms `[y]` to the auto-prompt)

## The 3-prompt flow

See `prompts.md` for full prompt scripts. Summary:

### Q1: Mode (solo/team)

```
Are you the only decision-maker on this project, or working with 2+ senior engineers?

[1] solo (default) — Single decision-maker. ADR `OKR Alignment` field optional.
[2] team — 2+ senior engineers. ADR `OKR Alignment` field MANDATORY (lint-enforced).

Industry threshold per Pragmatic Engineer: 2+ senior engineers = team mode.
```

### Q2: Doc types

```
How do you want orchestra to handle doc types?

[1] default-7 (recommended) — Use the canonical 7 types as-is:
    Feature LLD, Bug Report, ADR, Design Doc, Postmortem, Runbook, Plan

[2] subset-rename — Drop unused types and/or rename to formal alternatives
    (Tech Spec, Engineering Design, Decision Record, etc.).
    Informal renames rejected (no "doc", "thing", "writeup").
    RFC explicitly NOT in whitelist (orchestra philosophy: ADR-only).

[3] full-custom — Define your own doc types with required sections,
    status enum, and naming pattern. Invariants enforced:
    - Changelog section MANDATORY
    - ≥3 status states (with terminal state)
    - Naming pattern in {NNN-kebab.md, YYYY-MM-DD-kebab.md, kebab.md}
```

### Q3: Optional add-ons

```
Install these helpful add-ons?

[y] (recommended) — Adds:
    - .github/workflows/orchestra-lint.yml (CI gate for orphan commits)
    - AGENTS.md (cross-tool AI agent context — Linux Foundation spec)
    - llms.txt (LLM-readable nav — llmstxt.org spec)

[n] — Skip. You can run init with --force later to add them.

Always installed regardless of choice:
    - docs/ subdirs (features, bugs, adr, design, postmortems, runbooks, plans)
    - docs/STANDARDS.md (canonical doc rules)
    - .claude/orchestra.json (config)
    - docs/adr/DECISIONS.md (auto-index, regenerates on each commit)
    - .gitignore append (excludes orchestra.local.json + investigations/)
```

## Implementation

The skill invokes `python -m cli.init` programmatically with the user's answers. CLI handles:

- Bucket 1 scaffolding (`scaffold_bucket_1`)
- STANDARDS.md generation per preset (`generate_standards_md`)
- Bucket 2 add-ons (`scaffold_bucket_2`)
- DECISIONS.md seeding (`seed_decisions_index` — always-run)
- Config write to `.claude/orchestra.json`

## Idempotency

- Re-run = skip-existing (no overwrites)
- `--force` = regenerate STANDARDS.md, replace add-ons
- Bug-iteration-safe: re-running init never destroys hand-edited STANDARDS.md unless `--force`

## v1.0 → v1.1 migration

If `.claude/settings.local.json` has an `orchestra` key (v1.0 config location), this skill detects it during init prompt:

```
v1.0 orchestra config detected at .claude/settings.local.json.
Migrate to v1.1 schema (.claude/orchestra.json)? [y/n]
```

On `y`: copies fields (mode + doc_paths + spec_review_skill) to v1.1 schema with v1.1-only fields filled with defaults. v1.0 block left in place (non-destructive).

## Related skills

- `orchestra:init` — master init that delegates here
- `orchestra:design-docs` — main design-docs skill (use after init)
- `superpowers:requesting-code-review` — default `spec_review_skill` per ADR-001
