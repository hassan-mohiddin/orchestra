# Codex Adversarial Review

Target: branch diff against main
Verdict: needs-attention

No-ship: there is no branch diff to validate against `main`, and the plan still specifies fail-open and non-transactional execution paths that can silently disable enforcement or leave cross-repo state inconsistent.

Findings:
- [critical] SCALE migration is destructive but lacks transactional rollback guarantees (docs/plans/2026-05-11-v17-implementation.md:197-203)
  Phase 4 calls for a one-shot manual script that deletes files and edits rules in a separate repository. The plan does not define preflight backup, idempotency constraints, or automatic rollback on partial failure/interruption. A mid-run error can leave policy documents in inconsistent state with irreversible deletions.
  Recommendation: Require transactional migration semantics before ship: snapshot/backup + restore path, dry-run mode, explicit pre/post invariant checks, and idempotent rerun behavior covered by tests.
- [high] Release plan is marked active without any corresponding branch implementation diff (docs/plans/2026-05-11-v17-implementation.md:7-19)
  The plan declares an active v1.7.0 ship scope with major behavior changes and a 90-test expansion, but repository context/local git state show no branch diff against `main`. That means none of the implementation, safety, or test claims in this plan are currently verifiable from the change under review. Shipping on this basis risks a false-ready release decision.
  Recommendation: Block release until the branch contains the referenced code/test changes and this plan links concrete implementation SHAs and test evidence for each phase milestone.
- [high] `cli.init` bootstrap is explicitly designed to fail open on hook install failure (docs/plans/2026-05-11-v17-implementation.md:90-91)
  The plan specifies `cli.init` should invoke hook installation, emit only a warning on non-zero return, and still return 0 unconditionally. This makes installation failures (permission issues, security checks, framework errors) non-blocking and can leave repos without active commit/pre-commit enforcement while automation still sees success.
  Recommendation: Fail closed by default: propagate non-zero bootstrap failures, or require an explicit best-effort flag to allow non-blocking behavior; add machine-readable failure output and remediation guidance.
- [high] `ORCHESTRA_BYPASS` is introduced with logging but no trust-boundary control (docs/plans/2026-05-11-v17-implementation.md:134)
  The finalize path includes `ORCHESTRA_BYPASS` handling with audit logging, but no control boundary is specified. Any actor/process able to set env vars can bypass enforcement, and inherited CI environment can unintentionally disable checks broadly. Logging detects abuse after the fact; it does not prevent it.
  Recommendation: Constrain bypass to explicit guarded flows (for example: disallow in CI, require reason+ticket, and enforce short-lived/allowlisted bypass tokens) and add tests for accidental env inheritance.

Next steps:
- Add implementation commits and test artifacts to the branch, then rerun review on actual diff vs `main`.
- Revise the plan to make init/bootstrap and finalize paths fail closed unless an explicit override is provided.
- Redesign Phase 4 migration as idempotent and rollback-safe before execution in SCALE.
