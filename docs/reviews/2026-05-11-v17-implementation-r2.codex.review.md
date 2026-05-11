# Codex Adversarial Review

Target: branch diff against main
Verdict: needs-attention

No-ship: the plan bakes in fail-open safety behavior and a bypass model that is too easy to evade in CI, plus a migration design that can mutate the wrong target without strong path/symlink hardening.

Findings:
- [high] `cli.init` bootstrap is explicitly fail-open on hook install failure (docs/plans/2026-05-11-v17-implementation.md:115-117)
  The plan states `cli.init` should always return 0 by default even when `cli.install_hooks` fails, only emitting a warning (strict mode is opt-in). This leaves a repository appearing successfully initialized while commit guards may be absent. Under real failure modes (missing deps, permission errors, hook conflicts), enforcement silently degrades to best-effort.
  Recommendation: Flip default to fail-closed for bootstrap failures (at least in non-interactive/CI contexts) and require an explicit override flag/env for local fail-open behavior, with a clear non-zero exit contract.
- [high] CI bypass denial depends on exact `CI=true`, creating an easy bypass gap (docs/plans/2026-05-11-v17-implementation.md:162-165)
  Bypass denial is specified only for `ORCHESTRA_BYPASS=1` when `CI=true` is detected. This is brittle: CI environments may expose other truthy forms (`1`, `TRUE`) or different provider signals, and environment values are mutable. The result is a trust-boundary hole where bypass logic can still execute in automation.
  Recommendation: Treat CI as deny-by-default for bypass using robust detection (`CI` non-empty plus provider-specific vars), and ignore/reject `ORCHESTRA_BYPASS` unconditionally in CI paths.
- [medium] SCALE migration plan lacks hard target identity and symlink-safe file mutation rules (docs/plans/2026-05-11-v17-implementation.md:236-243)
  The migration design performs rewrite/append/delete/rollback operations under user-provided `--scale-root`, but the plan does not require verifying repository identity or rejecting symlinks on all touched paths. Inference: accidental wrong-root execution or symlinked paths could mutate unintended files, and rollback-by-copy may not safely restore intended state boundaries.
  Recommendation: Add mandatory target validation (repo sentinel/expected remote), enforce `lstat` no-symlink + resolved-path containment for every read/write/delete/restore path, and use atomic replace semantics for rewrites.

Next steps:
- Revise Slice 1.4 to make hook bootstrap failure a blocking condition by default.
- Harden Slice 2.6 CI detection and set CI bypass policy to unconditional deny.
- Amend Slice 4.1 with explicit root-identity and symlink-containment invariants before any mutation.
