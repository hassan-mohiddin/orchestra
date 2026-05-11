---
description: Run orchestra:spec-review v2 (6-parallel-sub-judge ensemble) on a doc — produces schema-v2.0 attestation
arguments:
  - name: doc_path
    description: Repo-relative path to the doc (e.g., docs/features/011-spec-review-v2.md)
    required: true
  - name: override_cap
    description: Bypass the 2-iter post-commit cap (fires interview-gate; logged in attestation notes as degraded mode)
    required: false
    flag: --override-cap
  - name: force
    description: Overwrite an existing same-iteration attestation (refused for v1.0 historical attestations)
    required: false
    flag: --force
---

Invoke skill `orchestra:spec-review` with arg `${doc_path}`.

The skill follows the v2 (LLD-011) dispatch protocol:

1. **PDSA** — `cli.spec_review --pdsa ${doc_path}` mechanical pre-flight (lint, sections, citations, placeholders, Refs:, filename grammar, class-audit-attestation). Fails block dispatch.
2. **Iteration check** — iter-1 = fresh full-doc; iter-2 = delta-review against iter-1 attestation; iter-3+ = HARD BLOCK unless `--override-cap` passed.
3. **Render 6 sub-judge prompts** — `structure`, `semantic` (mandatory), `gate-compliance`, `adversarial` (mandatory), `repo-context`, `architectural-fit`. Each prompt inlines the target doc.
4. **Parallel dispatch** — single message, 6 Task tool calls. No per-call max_tokens cap (length-bias mitigation moved to prompt level).
5. **Persist provenance** — `git rev-parse HEAD` → iter_commit_sha; `git hash-object -w ${doc_path}` → iter_blob_sha (PERSISTED to .git/objects/ for iter-2 retrieval).
6. **Aggregate + write** — pipe sub-judge YAMLs through `python -m cli.spec_review --aggregate-and-write ${doc_path} [--override-cap] [--force]` for schema-v2.0 validation, mechanical aggregator dedup, self-referential integrity hash, atomic write to `docs/reviews/<doc-id>-rN.orchestra.review.yaml` (canon §4.11 filename convention).
7. **Read codex peer-judge file** (if present at `docs/reviews/<doc-id>-rN.codex.review.md`) for cross-judge comparison.
8. **Cross-judge report** — markdown table to chat (NOT a persistent file). Counts per judge + top-5 findings by severity.
9. **Interview-gate** — `AskUserQuestion` fires when aggregate findings contain any Critical or Important. Skipped when only Minor / no findings.

**Failure-attestation invariant**: even all-fail / mandatory-fail / doc-disappeared cases persist an attestation file with `overall_verdict: fail` + `reason: ...`. Audit trail never has a gap.

**Mandatory tier**: failure of `semantic` or `adversarial` forces `overall_verdict: fail` with `reason: mandatory_subjudge_failed`. Optional sub-judges soft-fail (excluded from aggregation, do not block the verdict).

Exit codes:
- 0 — pass / conditional_pass attestation written
- 1 — fail attestation written OR validation/identity/verdict mismatch OR PDSA halted dispatch OR 2-iter cap exceeded without --override-cap
- 2 — path traversal blocked

See `skills/spec-review/SKILL.md` for the full dispatch protocol and `docs/features/011-spec-review-v2.md` for the v2 LLD.
