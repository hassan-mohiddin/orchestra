---
description: orchestra commit-discipline skill — Refs: line rules, canon-frozen narrow-change rule, doc/code separation, supersession decision tree, tiered narrow-change Addresses: line construction.
---

Invoke skill `orchestra:commit`.

The skill enforces orchestra commit discipline. Invoke before:

- Any code commit (`fix:`, `feat:`, `refactor:`, `test:`)
- Any doc commit on a canon-frozen-eligible file under `docs/{features,bugs,adr,design,postmortems,runbooks}/`
- Status-flip operations (Draft → Implemented; Investigating → Fix Applied; etc.)
- Supersession decisions

The skill walks through:

1. **Pre-stage checklist** — read prior `git show HEAD:<path>` Status field; if canon-frozen, decide whitelist narrow-change vs tiered narrow-change vs supersession.
2. **Tiered narrow-change construction** — read attestation YAML, identify gate name (`completeness | evidence | clarity | consistency`) + 1-indexed finding-N, append Changelog row per finding, draft commit message with `Addresses:` lines.
3. **Doc/code separation** — doc and code commits MUST stay separate per `skills/commit/references/doc-vs-code-commit.md`.
4. **Mechanical backstop** — git hooks (pre-commit + commit-msg) fire automatically; `--no-verify` is the only bypass and triggers a follow-up BUG-NNN per agent discipline.

See `skills/commit/SKILL.md` for the full skill body + references.
