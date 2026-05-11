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

Before `git add` on a canon-frozen-eligible doc:

1. Check prior Status: `git show HEAD:<path> | head -20 | grep "Status:"`.
2. If Status ∈ {Approved, Implemented, Verified, Fix Applied, Current} → canon-frozen. Body changes require one of:
   - **Whitelist edit** (Status / Iteration / Superseded by + Changelog append) → no `Addresses:` needed
   - **Tiered narrow-change** (BUG-011) → `Addresses:` lines per finding + NEW Changelog row per finding
   - **Supersession** → archive + `-rN.md` path (see `references/supersession-decision.md`)
3. For tiered narrow-change:
   - Read attestation YAML at `docs/reviews/<doc-id>-rN.review.yaml`.
   - Note gate name (`completeness | evidence | clarity | consistency`) + 1-indexed finding-N within that gate.
   - **Commit attestation YAML FIRST** (separate `docs:` commit) — uncommitted attestation fails `--pre-stage-check`.
   - Add NEW Changelog row per finding to doc body:
     ```
     | <YYYY-MM-DD> | Addresses: docs/reviews/<doc-id>-rN.review.yaml gate <gate> finding <N> (Minor|Important) — <fix description> |
     ```
   - Draft commit message with `Addresses:` line per finding:
     ```
     Addresses: docs/reviews/<doc-id>-rN.review.yaml gate <gate> finding <N> (Minor|Important)
     ```
   - Early feedback: `python -m cli.lint --pre-stage-check <doc-path> --commit-msg-draft "$(cat msg.txt)"`.
   - On PASS: stage doc + commit with prepared message.
4. If Status: Draft / Investigating / Proposed → full edit permitted; standard discipline only.
5. Doc and code commits MUST stay separate (see `references/doc-vs-code-commit.md`).

## References

- `references/commit-strategy.md` — conventional prefix table, Refs:-line rules, when to commit.
- `references/canon-frozen-guard.md` — narrow-change rule, supersession workflow, tiered exception.
- `references/refs-line-rules.md` — Refs:-line format, orphan-commit prohibition.
- `references/doc-vs-code-commit.md` — separation rule, atomic ship invariants.
- `references/supersession-decision.md` — when to archive + re-iterate vs. narrow-change edit.

## Mechanical backstop

Git hooks (pre-commit + commit-msg) installed by `python -m cli.install_hooks --all`. Hooks fire automatically and catch violations the skill missed. `--no-verify` is the only bypass.
