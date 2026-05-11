---
Doc ID: refs-line-rules
Date: 2026-05-11
Skill-Status: Current
Skill version: 1.7.0-pre
---

# Refs:-Line Rules

Extracted from commit-strategy prose (LLD-008 r7 A2).

## Format

```
Refs: docs/<type>/<doc>.md
```

Where `<type>` ∈ `{features, bugs, adr, design, postmortems, runbooks}`.

Multiple `Refs:` lines allowed; one per referenced doc.

## When required

- Every `fix:` commit → `Refs: docs/bugs/BUG-NNN-name.md`
- Every `feat:` commit → `Refs: docs/features/NNN-name.md` (or `docs/adr/ADR-NNN-name.md`)

## When optional but recommended

- `refactor:`, `test:`, `chore:`, `docs:` — `Refs:` recommended when commit relates to a tracked doc.

## Orphan-commit prohibition

A `fix:` or `feat:` commit with no `Refs:` line pointing to a real file in `docs/` is an **orphan commit** and is NOT allowed.

If no doc exists yet: STOP, create the doc first (per Documentation Gate § Gate 2), then commit.

## Mechanical enforcement

- `cli.lint --commit` runs L1 (Refs:-line presence + path-resolvable) on staged code commits.
- commit-msg hook runs same check at message-author time (fail-closed; rejects empty/missing Refs:).
- pre-commit hook runs `cli.lint --pre-commit` covering L1+L2+L3+L4.

## Edge cases

- Supersession: after archive + -rN.md created, Refs: points to **new** path, NOT archived original.
- Multi-doc commits (rare): one `Refs:` line per doc referenced.
- WIP commits (`wip:` prefix): NOT subject to Refs: rule — used during bug iteration loops only.

## Why

Refs:-line creates audit trail: every code change traces back to a design doc capturing the why. Lost refs = lost provenance = canonical-doc decay over time.
