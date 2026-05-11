# Codex Adversarial Review

Target: branch diff against main
Verdict: needs-attention

No-ship. The LLD still contains contract mismatches and unhandled failure/security paths that can leave commit enforcement broken or bypassed in real workflows.

Findings:
- [high] Bootstrap invocation uses a CLI flag that is not defined by the spec’s own parser contract (docs/features/008-commit-skill.md:55)
  A6 requires `cli.install_hooks.main(["--pre-commit", "--commit-msg", "--on-conflict=skip"])`, but the parser section only specifies `--on-conflict` and does not define `--pre-commit`. This is not theoretical: current `cli/install_hooks.py` also lacks `--pre-commit` (only default pre-commit behavior, `--commit-msg`, `--all`). If implemented/documented this way, argparse can exit 2 and bootstrap/manual recovery fail before hooks are installed.
  Recommendation: Make the CLI contract consistent end-to-end: either switch calls/docs to `--all --on-conflict=skip` or formally add/test a `--pre-commit` flag. Update A6, Edge Case 1, and parser snippets together.
- [high] Security claim overstates symlink protection and misses a writable path escape (docs/features/008-commit-skill.md:269-270)
  The Security section says symlink traversal is protected via `repo_root.resolve()`, but resolving repo root does not prevent `.git/hooks/<hook>` itself from being a symlink. Replace/append/write paths can still follow that symlink and modify files outside the repo boundary. This is a trust-boundary break for tampered/untrusted local repos.
  Recommendation: Require explicit destination-path symlink checks (`lstat`/`is_symlink`, fail-closed) before any hook write, and add a test that verifies symlinked hook destinations are rejected.
- [medium] Init bootstrap path leaves hook-install failures weakly observable (docs/features/008-commit-skill.md:219-223)
  The doc defines a fail-closed missing-template condition, but the init pseudocode only assigns `result = cli.install_hooks.main(...)` and does not require propagation/reporting semantics. Combined with `--on-conflict=skip`, init can complete while hooks are absent/unchanged, reducing enforcement with poor operator visibility under partial install/version-skew scenarios.
  Recommendation: Specify mandatory bootstrap result handling in `cli.init`: surface non-zero return codes and emit explicit warnings when hooks are skipped/not installed; add tests for missing-template and skipped-conflict outcomes.

Next steps:
- Fix the install-hooks CLI contract mismatch before implementation starts.
- Add explicit symlink-safe hook-write guards and tests.
- Define and test observable error handling for hook bootstrap failures/skips in `cli.init`.
