---
name: spec-review
description: Use when reviewing any orchestra design doc (Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc, Plan) via the v2 multi-sub-judge ensemble. Dispatches 6 sub-judges in parallel (structure, semantic [mandatory], gate-compliance, adversarial [mandatory], repo-context, architectural-fit). Produces one schema-v2.0 attestation. User invokes additional peer judges (codex, etc.) separately for cross-judge consensus. Triggers when user runs `/orchestra:spec-review <doc-path>` or asks "spec review this doc."
---

# orchestra Spec Review v2 (LLD-011)

## Overview

Multi-sub-judge ensemble spec review. Produces one schema-v2.0 YAML attestation per invocation at `docs/reviews/<doc-id>-rN.orchestra.review.yaml`. The 6 sub-judges run in parallel (single-message Task tool fanout), are aggregated mechanically (no LLM merge), and emit a cross-judge comparison report + interview-gate.

**Sub-judge ensemble:**

| ID | Model | Tool set | Mandatory? | Rubric slice |
|---|---|---|---|---|
| structure | Sonnet 4.6 | Read | optional | format, sections, filename grammar, Mermaid |
| semantic | Opus 4.7 | Read | **mandatory** | 4-gate continuity (inherits v1) |
| gate-compliance | Sonnet 4.6 | Read | optional | orchestra Gates 1-3 + canon-frozen + lifecycle |
| adversarial | Opus 4.7 | Read | **mandatory** | red-team, blast-radius, invariants, edge cases |
| repo-context | Opus 4.7 | Read + Grep + Glob | optional | citation validity, impl-doc match, test coverage |
| architectural-fit | Opus 4.7 | Read + Grep | optional | Design Doc + ADR consistency |

**Mandatory tier**: failure of `semantic` or `adversarial` forces `overall_verdict: fail` with `reason: mandatory_subjudge_failed`. Optional sub-judges soft-fail (recorded as `status: error|timeout`, excluded from aggregation).

## Invocation

User runs:

```
/orchestra:spec-review <doc-path>
```

Where `<doc-path>` is repo-relative (e.g., `docs/features/011-spec-review-v2.md`).

Flags:
- `--force` — overwrite existing same-iteration attestation (still refused for v1.0 historical attestations per LLD-011 §slice 1.7)
- `--override-cap` — bypass 2-iter post-commit cap (fires interview-gate before dispatch)

## Dispatch flow

When invoked, the main agent (Claude) MUST follow these steps in order:

### Step 1 — PDSA (Pre-Dispatch Self-Audit)

Invoke `cli.spec_review --pdsa <doc-path>`. If PDSA fails, report mechanical findings to the author and halt — sub-judges DO NOT dispatch. (PDSA scope: lint, required sections, citation validity, placeholder detection, cross-doc Refs: resolution, filename grammar. Glossary check is non-gating warn-only until BUG-016 vocab canon ships.)

### Step 2 — Iteration check

Read `> **Iteration:** N` from doc metadata.

- **iter 1**: fresh full-doc dispatch (Step 3 below)
- **iter 2**: delta-review dispatch (read iter-1 attestation, verify integrity hash, retrieve iter-1 bytes via `git cat-file -p <iter_blob_sha>`, diff, pass changed sections + iter-1 findings to sub-judges)
- **iter ≥ 3**: HARD BLOCK. Refuse unless `--override-cap` was passed; override fires `AskUserQuestion` interview-gate before proceeding.

### Step 3 — Render sub-judge prompts

For each of the 6 sub-judges, read `skills/spec-review/judges/<id>/prompt.md` and inline the target doc text where the template marker `<doc text inlined here at dispatch time>` appears. For iter-2 delta-review, also inline the diff + iter-1 findings list.

### Step 4 — Parallel dispatch via Task tool

**Dispatch ALL 6 sub-judges in a single message with 6 parallel Task tool invocations.** This is the critical parallelism step — sequential dispatch would multiply latency. Per-Task kwargs:

```
subagent_type: general-purpose
model: claude-opus-4-7 | claude-sonnet-4-6   # per cast table above
prompt: <rendered sub-judge prompt>
# NO max_tokens cap — length-bias mitigation lives in prompt instruction, not output cap
```

Tool set per sub-judge is enforced via prompt-level instruction (Claude Code's Task tool does not natively filter tools per subagent). Sub-judges with broader tool access (`repo-context`, `architectural-fit`) declare their scope in their prompt; the `cli.spec_review` output-quarantine step rejects tool-trace violations per LLD-011 §Security S1 + §E21.

### Step 5 — Collect sub-judge YAML outputs + persist provenance

Once all 6 Task tool calls return, collect the 6 YAML chunks into a list. Before any aggregation:

- Compute `iter_commit_sha` via `git rev-parse HEAD` (recorded for audit; '<uncommitted>' if no HEAD)
- Compute `iter_blob_sha` via `git hash-object -w <doc-path>` (PERSISTS blob to `.git/objects/`; required for iter-2 retrieval)

### Step 6 — Aggregate + validate + write

Pipe sub-judge YAMLs to `cli.spec_review --aggregate-and-write <doc-path>` via stdin. CLI performs:

- Schema validation of each sub-judge entry (v2.0 schema fragment per LLD-011)
- Mechanical aggregator (`cli/aggregator.py`) — dedup by (location, problem_hash), max severity, union raised_by
- Path canonicalization (F1+F5 inherited from v1)
- Authoritative field write (`content_hash`, `iter_commit_sha`, `iter_blob_sha`, `attestation_integrity_hash`, `overall_verdict`, `overall_verdict_basis`)
- Stale-state byte-compare (F6+F8 inherited)
- Atomic write of `docs/reviews/<doc-id>-rN.orchestra.review.yaml`

**Failure-attestation invariant**: even when sub-judges fail (all-fail, mandatory-fail, doc-disappeared E18, prompt-missing E11), an attestation file is ALWAYS persisted with `overall_verdict: fail` + `reason:` + sub-judge statuses. The audit trail never has a gap.

### Step 7 — Read codex peer-judge file if present

If `docs/reviews/<doc-id>-rN.codex.md` exists, read it. Used for cross-judge comparison in Step 8. Native format — no normalization to v2 YAML (rejected per LLD-011 §Out-of-scope due to misinterpretation risk).

### Step 8 — Cross-judge comparison report

Emit a markdown table to chat (NOT a persistent file):

```markdown
## Spec-Review v2 Report — <doc-id>-rN

| Judge | Critical | Important | Minor | File |
|---|---|---|---|---|
| orchestra | C1 | I1 | M1 | docs/reviews/<doc-id>-rN.orchestra.review.yaml |
| codex     | C2 | I2 | M2 | docs/reviews/<doc-id>-rN.codex.md |

**Cross-judge overlap:** ...
**Unique to orchestra:** ...
**Unique to codex:** ...

**Top 5 by severity (cross-judge, deduped):**
1. ...
```

### Step 9 — Interview-gate

If aggregate `findings_aggregated[*].severity` contains any `Critical` or `Important`, fire `AskUserQuestion`:

```
Findings need direction. Options:
  - Address all findings now
  - Defer some to BUG-NNN (which?)
  - Mark won't-fix (which?)
  - Re-review after author response
```

Skip gate when only Minor findings present.

## Schema

v2.0 schema at `skills/spec-review/attestation-schema-v2.0.json` (JSON Schema draft-07). v1.0 schema at `attestation-schema-v1.0.json` remains frozen for historical read-only support.

## References

- `judges/<id>/prompt.md` — per-sub-judge prompt template (6 files)
- `judges/<id>/rubric-v1.md` — per-sub-judge rubric body (6 files)
- `attestation-schema-v2.0.json` — JSON Schema for v2.0 attestations
- `attestation-schema-v1.0.json` — frozen v1.0 schema (read-only)
- `references/4-gate-rubric.md` — semantic sub-judge inherits this
- `docs/features/011-spec-review-v2.md` — full v2 LLD
- `docs/features/007-spec-review-architecture-r5.md` — v1 LLD (superseded by 011)
