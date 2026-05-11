---
Doc ID: doc-vs-code-commit
Date: 2026-05-11
Skill-Status: Current
Skill version: 1.7.0-pre
---

# Doc vs. Code Commit Separation

Extracted from commit-strategy prose (LLD-008 r7 A2).

## Rule

Doc commits and code commits are **separate atomic units**. Never combine.

| Doc commit | Code commit |
|---|---|
| `docs:` (any doc-only change) | `feat:`, `fix:`, `refactor:`, `test:`, `chore:` (any code change) |
| Touches files under `docs/` ONLY | Touches code (any file outside `docs/`) |
| No `Refs:` requirement (recommended) | `Refs:` MANDATORY for `fix:`/`feat:` |

## Why separate

1. **Atomic revert** — bad code revertable without losing doc; bad doc revertable without losing code.
2. **Bisect clarity** — `git bisect` lands on offending change-class, not mixed-bag commit.
3. **Review focus** — reviewers can evaluate doc rationale separately from impl correctness.
4. **Refs:-line semantics** — `Refs:` on code commit means "this code implements/fixes this doc"; only meaningful when doc commit precedes.

## Ordering

Standard sequence:

1. Create/update doc → `docs:` commit (no code touched).
2. Implement → `feat:` or `fix:` commit (code only; Refs: points to doc from step 1).
3. (Optional) Update doc Status: Implemented → Verified after verification → second `docs:` commit (Changelog append + Status flip; whitelist-eligible).

## Exceptions

**None.** Even tiny "fix typo in code + add line to doc Changelog" splits into 2 commits.

## Mechanical enforcement

- pre-commit hook runs `cli.lint --pre-commit` which detects mixed code + doc staging in single commit and rejects.
- `cli.lint --pre-stage-check` author-time helper warns before staging mixed change.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `feat: add X + update LLD` (mixed) | Split into `docs:` (LLD update) then `feat:` (impl) |
| Squashing doc + code commits into one before push | Preserve atomic units; refactor squash strategy if needed |
| Commit message mixed prefix like `feat: + docs:` | Pick the prefix matching the change-class; the other lives in separate commit |
