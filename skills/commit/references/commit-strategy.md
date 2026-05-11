---
Doc ID: commit-strategy
Date: 2026-05-11
Skill-Status: Current
Skill version: 1.7.0-pre
---

# Commit Strategy

Canonical source for orchestra commit-discipline. Migrated from SCALE-side `.claude/rules/commit-strategy.md` (deleted per LLD-008 r7 A8).

## Conventional Commit Prefixes

| Prefix | When |
|---|---|
| `docs:` | Documentation only (LLD, Design Doc, ADR, Bug Report) |
| `feat:` | New feature implementation |
| `fix:` | Bug fix |
| `test:` | Adding or updating tests |
| `refactor:` | Code restructuring, no behavior change |
| `chore:` | Maintenance (deps, config, Design Doc sync) |

## When to Commit

- After design docs are written — before any code
- After each logical unit of implementation
- After Design Doc sync at the end of a feature
- Mid-feature commits are fine if a sub-task is independently useful

## Mandatory Doc Reference (enforced for fix: and feat:)

Every `fix:` commit MUST reference a Bug Report:

```
fix: write user_model_metadata after adapter training

Upserts user_model_metadata on training completion so the classifier
can discover the adapter URL on next request.
Refs: docs/bugs/BUG-002-linear-adapter-broken-pipeline.md
```

Every `feat:` commit MUST reference a Feature LLD or ADR.

**No Refs: = orphan commit.** A `fix:` or `feat:` commit with no `Refs:` line pointing to a real file in `docs/` is NOT ALLOWED. If no doc exists yet, create it first.

`refactor:`, `test:`, `chore:`, `docs:` commits: `Refs:` is optional but recommended.

## Pre-Commit: Update Doc Status

Before the final feature/bug/ADR commit, update the design doc's `Status` field:

| Code state | Doc status to set |
|---|---|
| Implementation complete, about to commit | `Implemented` |
| Verification passed (tests green, evidence confirmed) | `Verified` |

Commit the status update **before or alongside** the code commit — never after.

## Bug iteration commits (no `fix:` until user confirms)

For bug-iteration loops where multiple attempts may be needed:
- During iteration: WIP commits OK on a feature branch (`wip:` prefix), do NOT use `fix:`
- Append iteration entries to the BUG-NNN doc changelog, not separate `fix:` commits
- Only after the user explicitly confirms the bug is resolved → consolidate into a single `fix:` commit with `Refs: docs/bugs/BUG-NNN-name.md`

Hook (`make check` / pytest) passing is necessary but NOT sufficient for `fix:`. User confirmation is the gate.

## After Verification Passes

Commit automatically — do not ask for permission after verification confirms everything works.
