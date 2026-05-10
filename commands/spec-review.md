---
description: Run orchestra:spec-review (judge-1) on a doc — produces schema-validated YAML attestation
arguments:
  - name: doc_path
    description: Repo-relative path to the doc (e.g., docs/features/007-spec-review-architecture.md)
    required: true
---

Invoke skill `orchestra:spec-review` with arg `${doc_path}`.

The skill renders the 7-element adversarial prompt, dispatches a fresh `general-purpose` subagent via the `Task` tool (max_tokens: 4000), captures the YAML output, and pipes it through `python -m cli.spec_review ${doc_path}` for schema validation, hash binding, verdict authoritative-compute, and atomic-write to `docs/reviews/<doc-id>-rN.review.yaml`.

Exit codes:
- 0 — pass / conditional_pass attestation written
- 1 — fail attestation written OR validation/identity/verdict mismatch
- 2 — path traversal blocked

See `skills/spec-review/SKILL.md` for full dispatch flow and multi-judge protocol.
