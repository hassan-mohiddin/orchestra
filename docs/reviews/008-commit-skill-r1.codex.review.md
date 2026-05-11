# Codex Adversarial Review — LLD-008 r1 (Judge-2)

> **Doc subject:** docs/features/008-commit-skill.md
> **Iteration:** 1
> **Reviewer:** codex (via /codex:adversarial-review)
> **Reviewer model:** different-from-author (Opus author; codex non-Opus → bypasses self-preference)
> **Invoked at:** 2026-05-10
> **Verdict:** needs-attention (no-ship)

## Findings

### [high] Pre-commit framework path can silently disable orchestra enforcement

**Location:** docs/features/008-commit-skill.md:48-220 (A5 + Design § cli.install_hooks framework-detection)

A5 and the framework-detection design skip raw hook install when `.pre-commit-config.yaml` exists and instead print `precommit-yaml-patch.txt`. That snippet (validated against current repo content) is for BUG-007 YAML-checker `--unsafe` patch, NOT for wiring orchestra lint/commit-discipline checks. Result: pre-commit-framework consumers receive success output but still do not run orchestra's commit-discipline gates, recreating the exact silent-failure class this LLD is trying to eliminate.

**Recommendation:** Define a dedicated framework snippet that actually registers orchestra checks (`local` repo entry invoking `python -m cli.lint --pre-commit`). Keep commit-msg enforcement installed (or provide equivalent framework hook). Add integration test proving a violating commit is rejected in a repo with `.pre-commit-config.yaml`.

### [high] Tiered narrow-change exception incompatible with hook ordering

**Location:** docs/features/008-commit-skill.md:50-257 (A7 + Design § cli.lint.is_narrow_change tiered extension)

A7 requires `is_narrow_change()` to parse `Addresses:` lines from `commit_msg`. But L2 runs at pre-commit (before commit message exists); commit-msg runs LATER. Under normal git flow:

```
git commit invoked
  ↓
.git/hooks/pre-commit  ← L2 runs here; commit_msg NOT yet available
  ↓
.git/hooks/prepare-commit-msg
  ↓
editor opens (or -m message used)
  ↓
.git/hooks/commit-msg  ← commit_msg only available HERE
  ↓
commit lands
```

Data required for tiered exception is unavailable when L2 decides pass/fail. Impact: either false-rejection of valid Minor/Important fixes (L2 doesn't know commit message has `Addresses:`) OR weakening L2 to avoid blocking — both user-visible and high-cost.

**Recommendation:** Move tiered exception evaluation to a stage with commit message access (commit-msg hook invoking lint with message path), OR redesign the exception to avoid commit-message dependency at pre-commit time (e.g., side-file `.commit-msg-draft` written by author before staging, parsed at pre-commit).

### [medium] cli.init bootstrap plan is not safely non-interactive

**Location:** docs/features/008-commit-skill.md:49-267 (A6 + Design § cli.init bootstrap)

A6/Design says `cli.init` should auto-run hook bootstrap and remain idempotent. Edge-case notes preserve interactive conflict handling for differing hook content (per current installer behavior at `cli/install_hooks.py:48-75`: prompts `[a]ppend / [r]eplace / [s]kip`). Calling that path from `cli.init` in automation/CI can block on `input()` or fail after partial init work, leaving inconsistent state and unclear recovery.

**Recommendation:** Specify bootstrap as explicitly non-interactive: `--on-conflict={skip,replace,append}` flag (default: `skip`). Deterministic exit behavior. Add tests for non-TTY execution with pre-existing divergent hooks.

## Notes

- All 3 findings are architectural / contract issues that affect whether the impl ships functional or non-functional. Differs from orchestra judge-1 verdict (conditional_pass, 18 findings mostly textual ambiguity / cross-ref consistency).
- Multi-judge value: codex (different-model, full-codebase context) caught defects orchestra (same-model author + judge) missed via cross-checking actual code paths (`cli/install_hooks.py`, `cli/lint.py`, hook ordering).
- Combined verdict (manual chair): **fail** — codex `[high]` findings #1 + #2 make impl non-functional as written.

## Next steps (per LLD-007 multi-judge protocol)

1. Author applies all 3 codex findings + 12 orchestra Important findings inline (Status: Draft permits full edit).
2. Bump Iteration: 1 → 2.
3. Re-dispatch both judges for r2.
4. Repeat until both pass.
