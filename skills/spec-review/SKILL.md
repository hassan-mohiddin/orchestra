---
name: spec-review
description: Use when reviewing any orchestra design doc (Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc, Plan) against the 4-gate rubric (Completeness / Evidence / Clarity / Consistency). Judge-1 default — orchestra ships exactly one judge; user manually invokes additional judges (codex, cavecrew, superpowers) for multi-judge consensus. Triggers when user runs `/orchestra:spec-review <doc-path>` or asks "spec review this doc."
---

# orchestra Spec Review (Judge-1)

## Overview

Adversarial spec review using a fresh-context subagent. Produces one schema-validated YAML attestation per invocation at `docs/reviews/<doc-id>-rN.review.yaml`. Multi-judge with **manual chair** — user invokes other judges separately and decides verdict.

**Bias mitigations:** position-bias (ordering instruction), self-preference (`--force` required for same-iteration overwrite), length-bias (output token cap 4000), same-model bias (documented; user runs `/codex:adversarial-review` as judge-2 manually).

## Invocation

User runs:

```
/orchestra:spec-review <doc-path>
```

Where `<doc-path>` is repo-relative (e.g., `docs/features/007-spec-review-architecture.md`). Skill resolves via `commands/spec-review.md` slash-command shim.

## Dispatch flow

When invoked, the main agent (Claude) MUST follow these exact steps:

### Step 1 — render prompt

Read `skills/spec-review/prompt-template.md`. Inline the target doc text where the template marker `<doc text inlined here at dispatch time>` appears.

### Step 2 — dispatch subagent via Task tool

Invoke the Claude Code `Task` tool with the following kwargs (verbatim):

```
subagent_type: general-purpose
max_tokens: 4000
prompt: <rendered prompt from step 1>
```

The `general-purpose` subagent runs in fresh context (no main-thread history). The 4000 token cap is the length-bias mitigation per LLD-007 § Bias mitigations and bounds output to one schema-conformant YAML document.

### Step 3 — capture YAML output

Take the subagent's response (one YAML document, schema v1.0 — see `attestation-schema-v1.0.json`). Subagent is instructed to output YAML only, no preamble.

### Step 4 — pipe to cli.spec_review for validation + write

Invoke (Bash):

```bash
echo "<yaml-output>" | python -m cli.spec_review <doc-path>
```

`cli.spec_review` performs schema validation, path canonicalization, hash binding, verdict authoritative-compute, stale-state check, and atomic-write of attestation YAML to `docs/reviews/<doc-id>-rN.review.yaml`. Exit codes:

- `0` — pass / conditional_pass attestation written
- `1` — fail attestation written OR validation/identity/verdict mismatch
- `2` — path traversal blocked

### Step 5 — surface result to user

Read the attestation file. Report `overall_verdict` and any findings to the user. User decides next step (commit, iterate, invoke additional judges).

## Multi-judge protocol (manual chair)

orchestra ships ONLY judge-1. User manually invokes additional judges as needed:

```
/codex:adversarial-review <doc-path>     # different model — bypasses Opus self-preference
/caveman:cavecrew-reviewer <doc-path>    # one-line/severity-emoji format
/superpowers:requesting-code-review <doc-path>
```

Each judge produces independent output. orchestra does NOT auto-aggregate verdicts. User reads all outputs and decides:

- All pass → commit + advance Status
- Any fail → revise + bump `Iteration:` field → re-review
- Disagreement → user policy (default: any fail = doc fails)

Max 3 iterations per doc per LLD-006-r4 convention. Iteration 4+ → interview-gate fires (suspect context drift; surface to user).

## Iteration handling

Skill reads `> **Iteration:** N` from doc metadata block. Emits matching `iteration: N` in attestation. Mismatch → exit 1. **Author bumps Iteration before re-invoking** — skill does not auto-increment.

## Existing attestation handling

If `docs/reviews/<doc-id>-rN.review.yaml` already exists for the same iteration:

- Default: skill exits 1 with explicit error
- Override: pass `--force` to overwrite (use only for testing / replay)

## Bias mitigations summary

| # | Mitigation | Where enforced |
|---|---|---|
| 1 | Position bias | Prompt template instructs ordering by location, not severity |
| 2 | Self-preference | `--force` required for same-iteration overwrite (cli.spec_review) |
| 3 | Length bias | `max_tokens: 4000` Task kwarg (this skill body, step 2) |
| 4 | Same-model bias | Documented — STANDARDS recommends user runs codex as judge-2 |

## Schema

Attestation schema v1.0 lives at `skills/spec-review/attestation-schema-v1.0.json`. Validated by `cli.spec_review` before write. Schema bumps require new skill version + migration.

## References

- `prompt-template.md` — 7-element adversarial prompt
- `attestation-schema-v1.0.json` — JSON-schema for YAML attestations
- `references/4-gate-rubric.md` — pass/fail criteria per gate
- `docs/features/007-spec-review-architecture.md` — full LLD
