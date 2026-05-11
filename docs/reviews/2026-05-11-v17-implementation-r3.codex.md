# Codex Adversarial Review

Target: branch diff against main
Verdict: needs-attention

No-ship: the plan still contains high-risk failure modes around state consumption and destructive-target validation, plus a release-gate inconsistency that can undercut test rigor at ship time.

Findings:
- [high] Finalize flow can lose pending state and allow retry-time policy bypass (docs/plans/2026-05-11-v17-implementation.md:162)
  Slice 2.6 says finalize reads pending entries and cleans up via `unlink(missing_ok=True)` but does not require cleanup to occur only after successful validation and exit. Inference: if cleanup occurs before a late failure/crash, a retried commit can run without pending entries and skip intended L2-finalize enforcement for already-detected canon-frozen candidates.
  Recommendation: Make pending-file handling transactional: move to a temp lock, validate all entries, delete only on success, and restore on failure/interruption; add explicit retry/crash idempotency tests.
- [high] Repo identity check is too weak for a destructive migration path (docs/plans/2026-05-11-v17-implementation.md:243)
  The migration guard treats a directory as the target repo if `.claude/CLAUDE.md` exists and contains `SCALE — Claude Code` in the first 100 lines. That single-content sentinel is forgeable and can match non-target trees, while the script performs rewrites and deletions immediately after this check.
  Recommendation: Require stronger identity proof before mutation (e.g., verified git toplevel + expected remote/repo match + multiple immutable sentinels) and fail closed if any identity signal is missing or mismatched.
- [medium] Conflicting pytest baselines create release-gate ambiguity (docs/plans/2026-05-11-v17-implementation.md:266)
  Slice 5.2 states `Pytest baseline: 150 → 240`, while the acceptance gate later requires `≥248`. This mismatch makes it plausible to publish release artifacts or sign-off evidence against an outdated threshold, masking missing test coverage.
  Recommendation: Normalize all baseline references to a single source of truth (`≥248` per acceptance gate) and add a pre-ship checklist item that verifies docs/changelog baseline consistency.

Next steps:
- Harden Slice 2.6 with success-only pending cleanup + retry-safe semantics.
- Upgrade Slice 4.1 identity checks to multi-factor repo verification before any file mutation.
- Fix baseline inconsistency in Slice 5.2 and re-run release-gate review against the corrected plan.
