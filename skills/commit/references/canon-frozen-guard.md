---
Doc ID: canon-frozen-guard
Date: 2026-05-11
Skill-Status: Current
Skill version: 1.7.0-pre
---

# Canon-Frozen Guard

Canonical source for the canon-frozen narrow-change rule. Migrated from SCALE-side `.claude/rules/canon-frozen-guard.md` (deleted per LLD-008 r7 A8).

Agent-side companion to LLD-006-r4 § narrow change. Mechanical lint check L2 (`cli.lint --pre-commit` / `--commit-msg-finalize`) catches violations; this reference prevents the agent from triggering them.

## When this fires

ANY of these → STOP, surface to user with options:

1. About to `git add` or `git commit` a `.md` file under refs-eligible prefix (`docs/{features,bugs,adr,design,postmortems,runbooks}/`)
2. AND the prior committed state of that file (i.e., `git show HEAD:<path>`) has Status field ∈ canon-frozen-statuses `{Approved, Implemented, Verified, Fix Applied, Current}`
3. AND the diff includes ANY change outside whitelist `{Status, Iteration, Superseded by}` frontmatter fields and append-only Changelog rows

If all three true → fire interview-gate. Show user:
- Summary of what changed
- Status field at HEAD (canon-frozen value)
- Two paths: narrow-change (only if change is whitelist-eligible) OR supersession (archive + new -rN.md per LLD-006-r4)
- Recommend supersession with one-line reason

## What is canon-frozen

Per LLD-006-r4 Glossary § canon-frozen statuses: `{Approved, Implemented, Verified, Fix Applied, Current}`.

These statuses indicate the doc represents a committed contract. Body edits to canon-frozen docs silently rewrite contracts that other commits' `Refs:` lines point at.

## What's permitted (narrow-change whitelist)

1. **Frontmatter field flip** — `Status`, `Iteration`, `Superseded by` only.
2. **Changelog append** — adding NEW rows. Existing rows must remain byte-identical.
3. **Both 1 and 2 in one commit** — common for status transitions.

ANYTHING else — section heading edited, paragraph rewritten, code snippet updated, Acceptance item changed, table row modified — is non-narrow. Supersession required.

## Tiered exception (BUG-011 — orchestra v1.7+)

Per BUG-011 (closes via LLD-009 r6 Phase 2), the strict-binary rule is relaxed for non-Critical findings:

| Finding severity driving change | Permitted edit |
|---|---|
| **Critical** | Supersession REQUIRED (no exception) |
| **Important** | Author judgment: ≤3 findings = narrow-change with `Addresses:` commit-msg lines + Changelog row per finding; 4+ = supersession |
| **Minor** | Narrow-change body edit + `Addresses:` commit-msg lines + Changelog row per finding |

`Addresses:` line format (required when using tiered narrow-change):

```
Addresses: docs/reviews/<doc-id>-rN.review.yaml gate <gate> finding <N> (Minor|Important)
```

Where `<gate>` ∈ `{completeness, evidence, clarity, consistency}`. Mechanical enforcement: `cli.lint --commit-msg-finalize`.

## Supersession workflow (non-narrow change)

1. `git mv docs/<type>/<doc>.md docs/archive/<type>/<doc>.md`
2. Edit archived file: Status: Rejected; Reason; Superseded by.
3. `cp docs/archive/<type>/<doc>.md docs/<type>/<doc>-r<N+1>.md`
4. Edit new file: Status: Draft (full edit allowed); Iteration: N+1; Supersedes: archive path.
5. Run spec-review on new file → fresh attestation.
6. After re-attestation passes, flip Status: Draft → Implemented (or appropriate canon status).
7. `python -m cli.lifecycle update-attestation-paths --reviews <prior-attestation-paths>` to rewrite old attestation `doc_subject.path` → archive path.
8. Single `feat:` commit with `Refs: docs/<type>/<doc>-r<N+1>.md`.

Procedural reference: `docs/runbooks/RUNBOOK-canon-inplace-violation-recovery.md`.

## What is NOT a trigger (proceed silently)

- Editing a Status: Draft doc (Draft permits full edit; supersession only on Rejected).
- Adding new file under `docs/<type>/` (no prior — no canon to violate).
- Editing `docs/plans/` files (plans are not canon-frozen).
- Editing `docs/reviews/*.review.yaml` (attestations are immutable; never edit committed attestations).
- Editing files outside `docs/` (code, tests, configs, READMEs).
- Whitelist-only edit (Status/Iteration/Superseded by + Changelog append).

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| "Just one wording fix" on canon-frozen → body edit | Supersession or batch with next iteration |
| Bumping Iteration to "make the diff fit" body change | Iteration bump alone OK; body change requires supersession |
| Adding Changelog entry "explaining" the body change | Changelog is whitelist; body change still violates |
| Skipping spec-review on canon-frozen because "it's already Implemented" | Run spec-review on supersession-iteration before flipping Status |
| Renaming file to bypass L2 | L4 doc-id-burn catches this; use `-rN` supersession path |

## Why this reference exists

Direct lineage: POSTMORTEM-2026-05-10-canon-inplace-violation. Agent body-edited canon-frozen LLD-007 in commits `653db4e` + `bc359e7` instead of routing through supersession. Three-layer defense:

1. `cli.lint --commit` (L1+L2+L3+L4 — BUG-009 closed)
2. Pre-commit hook installed (BUG-010 closed)
3. Agent self-check via this skill (current)
