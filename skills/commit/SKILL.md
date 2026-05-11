---
name: commit
description: Commit-discipline skill — invoke before any code commit, any doc commit on canon-frozen-eligible file, status-flip operations, supersession decisions.
version: 1.7.0-pre
---

# orchestra:commit

Commit-discipline consolidation. Wraps Refs:-line rules, canon-frozen narrow-change rule, doc/code commit separation, supersession decision tree.

## When to invoke

- Any code commit (fix:/feat:/refactor:/test:)
- Any doc commit on canon-frozen-eligible file under `docs/{features,bugs,adr,design,postmortems,runbooks}/`
- Status-flip operations (Draft → Implemented; Investigating → Fix Applied; etc.)
- Supersession decisions

## Pre-stage checklist

1. Identify commit type — code vs. doc. Doc and code commits MUST stay separate.
2. For doc commit on canon-frozen-eligible file: route to canon-frozen-guard reference.
3. For fix:/feat: code commit: ensure `Refs: docs/<type>/<doc>.md` line in commit body.
4. Run `python -m cli.lint --pre-stage-check <doc-path> --commit-msg-draft "<msg>"` before `git add` — surfaces L2 narrow-change verdict early.
5. Stage attestation file first (separate commit) if commit will reference an attestation finding.

## References

- `references/commit-strategy.md` — conventional prefix table, Refs:-line rules, when to commit.
- `references/canon-frozen-guard.md` — narrow-change rule, supersession workflow, tiered exception.
- `references/refs-line-rules.md` — Refs:-line format, orphan-commit prohibition.
- `references/doc-vs-code-commit.md` — separation rule, atomic ship invariants.
- `references/supersession-decision.md` — when to archive + re-iterate vs. narrow-change edit.

## Mechanical backstop

Git hooks (pre-commit + commit-msg) installed by `python -m cli.install_hooks --all`. Hooks fire automatically and catch violations the skill missed. `--no-verify` is the only bypass.
