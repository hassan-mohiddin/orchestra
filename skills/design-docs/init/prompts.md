# design-docs:init — 3-prompt flow scripts

These are the canonical prompt texts the skill emits during init.

## Q1: Mode

```
=== Step 1 of 3: Mode ===

Are you the only decision-maker on this project, or working with 2+ senior
engineers?

  [1] solo (default)
      - Single decision-maker
      - ADR `OKR Alignment` field optional
      - No reviewer-assignment workflow
      - Faster paths: skip team-coordination steps

  [2] team
      - 2+ senior engineers (industry threshold per Pragmatic Engineer)
      - ADR `OKR Alignment` field MANDATORY (lint-enforced)
      - Spec review can assign reviewers
      - Plugin manifest (v1.5+) supports per-team conflict resolution

Choose [1/2] (default: 1):
```

Validation: input must be `1`, `2`, or empty (defaults to `1`).

## Q2: Doc types

```
=== Step 2 of 3: Doc types ===

How do you want orchestra to handle doc types?

  [1] default-7 (recommended)
      Use the canonical 7 types as-is:
        - Feature LLD     (docs/features/NNN-name.md)
        - Bug Report      (docs/bugs/BUG-NNN-name.md)
        - ADR             (docs/adr/ADR-NNN-name.md)
        - Design Doc      (docs/design/<component>.md, living)
        - Postmortem      (docs/postmortems/POSTMORTEM-YYYY-MM-DD-name.md)
        - Runbook         (docs/runbooks/RUNBOOK-name.md)
        - Plan            (docs/plans/YYYY-MM-DD-name.md)

  [2] subset-rename
      Drop unused types and/or rename to formal alternatives.
      Whitelist: Tech Spec, Engineering Design, Spec, Design Brief,
      Decision Record, Architecture Decision, Incident Report,
      Operations Runbook, Implementation Plan, Engineering Plan,
      Postmortem, Retrospective.
      Informal renames rejected (no "doc", "thing", "writeup", "note").
      RFC NOT in whitelist (orchestra philosophy: ADR-only across both modes).

  [3] full-custom
      Define your own doc types with required sections, status enum, and
      naming pattern. Invariants enforced regardless:
        - Changelog section MANDATORY
        - Status enum ≥3 states (must include terminal state)
        - Naming pattern in: NNN-kebab.md / YYYY-MM-DD-kebab.md / kebab.md
        - Path validated against ^[a-z][a-z0-9-]*$ (no traversal)

Choose [1/2/3] (default: 1):
```

If user picks [2]: enter subset-rename wizard (toggle/rename per default type).
If user picks [3]: enter full-custom wizard (one type at a time, 6 sub-questions).

## Q3: Add-ons

```
=== Step 3 of 3: Optional add-ons ===

Install these helpful files alongside the core scaffolding?

  - .github/workflows/orchestra-lint.yml
        CI gate that runs `python -m cli.lint --range main..HEAD` on every PR.
        Catches orphan fix:/feat: commits, broken metadata, mermaid errors.

  - AGENTS.md
        Cross-tool AI agent context (Linux Foundation Agentic AI Foundation spec).
        Tells Claude/Gemini/Cursor/Copilot etc. about your doc layout.

  - llms.txt
        LLM-readable navigation index (llmstxt.org spec from Jeremy Howard).
        Lists key docs for AI agents to consume.

Install? [y/n] (default: y):
```

Validation: input must be `y`, `n`, or empty (defaults to `y`).

## v1.0 migration prompt (only if v1.0 config detected)

```
v1.0 orchestra config detected at .claude/settings.local.json.

The orchestra block contains:
  mode: <value>
  doc_paths: <values>
  spec_review_skill: <value>

Migrate to v1.1 schema (.claude/orchestra.json)? [y/n]:

[y] Generate .claude/orchestra.json from v1.0 fields (preserves v1.0 block).
[n] Keep using v1.0 config (orchestra continues to read from
    settings.local.json — works but no v1.1 features available).
```

## Final summary

After all prompts complete:

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

Status: ready.
```
