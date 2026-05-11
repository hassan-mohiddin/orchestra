---
Doc ID: supersession-decision
Date: 2026-05-11
Skill-Status: Current
Skill version: 1.7.0-pre
---

# Supersession Decision Tree

Extracted from canon-frozen-guard prose (LLD-008 r7 A2). Decision tree for choosing between narrow-change and supersession on canon-frozen docs.

## Pre-conditions

Doc is canon-frozen (`Status` ∈ `{Approved, Implemented, Verified, Fix Applied, Current}`).

If Draft: full edit permitted — no decision needed.

## Step 1 — Is the change whitelist-only?

YES — change is exclusively:
- Frontmatter `Status`, `Iteration`, or `Superseded by` field flip
- Append-only Changelog row (no edits to existing rows)
- Both of above in one commit

→ **Proceed with narrow-change commit.** No interview-gate. No supersession.

NO — change touches body (section, paragraph, code block, table-row, acceptance item, etc.)

→ continue to Step 2.

## Step 2 — Is the change driven by a spec-review finding?

NO — change is unprompted edit (typo fix without review backing, prose clarification, etc.)

→ **Supersession REQUIRED.** Archive + create -rN.md. No exception.

YES — change closes one or more spec-review findings on this doc.

→ continue to Step 3.

## Step 3 — What is the highest-severity finding driving the change?

| Severity | Verdict |
|---|---|
| **Critical** | Supersession REQUIRED (no exception). Critical = architectural defect; warrants fresh attestation. |
| **Important** (≤3 findings) | Narrow-change permitted with `Addresses:` commit-msg lines + Changelog row per finding. |
| **Important** (4+ findings) | Supersession REQUIRED. Too many fixes = architectural drift; warrants re-attestation. |
| **Minor** (any count) | Narrow-change permitted with `Addresses:` commit-msg lines + Changelog row per finding. |

## `Addresses:` line format

Required in commit message body when using tiered narrow-change (Step 3 Important/Minor paths):

```
Addresses: docs/reviews/<doc-id>-rN.review.yaml gate <gate> finding <N> (Minor|Important)
```

Where:
- `<doc-id>-rN` matches the doc + iteration the change addresses.
- `<gate>` ∈ `{completeness, evidence, clarity, consistency}`.
- `<N>` is 1-indexed finding index within the gate's findings array.
- `Minor|Important` matches the attestation's `severity` field.

One `Addresses:` line per finding. Multiple findings → multiple lines.

## Mechanical enforcement

- pre-commit hook L2-detect (`cli.lint --pre-commit`) flags canon-inplace candidates → writes pending entry.
- commit-msg hook L2-finalize (`cli.lint --commit-msg-finalize <msg-file>`) reads pending + verifies each entry's `Addresses:` lines match attestation findings + Changelog rows.
- Author-time pre-flight: `cli.lint --pre-stage-check <doc-path> --commit-msg-draft "<msg>"` runs the same check against working-tree before staging.

## Decision examples

### A. Status flip after impl

> Change: BUG-005 `Status: Investigating → Fix Applied`, plus Changelog row noting transition.
> Step 1: whitelist-only? YES.
> Verdict: narrow-change. `chore: BUG-005 → Fix Applied`. No interview.

### B. Typo fix without review

> Change: fix one typo in LLD-007 Acceptance section.
> Step 1: whitelist-only? NO (body edit).
> Step 2: driven by review finding? NO.
> Verdict: supersession REQUIRED. Either archive + -r2 OR defer to next supersession event.

### C. Closing 2 Minor findings via narrow-change

> Change: fix wording per 2 Minor findings in `008-commit-skill-r4.orchestra.review.yaml`.
> Step 1: whitelist-only? NO (body edit).
> Step 2: driven by review finding? YES.
> Step 3: highest severity? Minor.
> Verdict: narrow-change permitted. Commit body includes 2 `Addresses:` lines + Changelog row per finding.

### D. Architectural rewrite

> Change: replace LLD-005 Design section because architecture changed.
> Step 1: whitelist-only? NO.
> Step 2: driven by review finding? Likely YES (Critical).
> Step 3: severity? Critical.
> Verdict: supersession REQUIRED. No tiered exception for Critical.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Skipping spec-review when "Minor change is obvious" | Run spec-review before narrow-change commit — Minor still requires attestation backing |
| Bundling Critical fix with Minor fixes in narrow-change | Critical drives the tier → supersession; Minors fold in after re-iteration |
| Forging `Addresses:` line pointing at non-existent attestation | L2-finalize verifies path resolves + finding-N within gate's findings array; forgery rejected |
| Using narrow-change to bypass attestation re-run | Re-attestation is mandatory on supersession; narrow-change is for already-reviewed findings only |
