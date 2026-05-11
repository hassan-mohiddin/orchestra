# BUG-010: orchestra repo does not install its own pre-commit hook

> **Doc ID:** BUG-010-orchestra-self-install-precommit-hook
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** High
> **Status:** Fix Applied

## Observed Behavior

orchestra repo `.git/hooks/` contains only `pre-commit.sample`. No active hook fires on commit. Verified 2026-05-10:

```bash
$ ls -la /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra/.git/hooks/ | grep -E 'pre-commit|commit-msg'
-rwxr-xr-x  1 user staff  896 May  6 commit-msg.sample
-rwxr-xr-x  1 user staff 1649 May  6 pre-commit.sample
-rwxr-xr-x  1 user staff 1492 May  6 prepare-commit-msg.sample
```

orchestra ships `python -m cli.install_hooks --pre-commit` (cli/install_hooks.py) for downstream consumers but never invokes it on its own repo. Pre-commit gate (which runs `python -m cli.lint --pre-commit` — invoking `lint_staged()` with all of L1/L2/L3/L4) is therefore inactive on the repo where orchestra itself is developed.

Direct consequence: 2026-05-10 session canon-inplace violations (commits `653db4e` + `bc359e7`) landed locally because no hook fired. Same enforcement layer that protects downstream consumers does not protect orchestra-the-product itself.

## Expected Behavior

orchestra repo `.git/hooks/pre-commit` is installed and active. On any commit attempt, pre-commit hook runs `python -m cli.lint --pre-commit` against staged files. Canon-inplace violations rejected before commit lands.

Two installation paths:

1. **Manual one-time** — developer runs `python -m cli.install_hooks --pre-commit --repo .` once after clone. Documented in CONTRIBUTING.md.
2. **Auto on first `make` / first `python -m cli.<anything>` invocation** — sidecar idempotent install that ensures hook present. Optional; safer than manual-only.

Choosing path 1 (manual + documented) for v1.6.x patch; auto-install considered for future polish.

## Steps to Reproduce

```bash
cd /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra && \
  ls .git/hooks/pre-commit 2>/dev/null && echo "PASS — hook installed" || echo "FAIL — hook missing"
# Current output: FAIL — hook missing
# Post-fix expected: -rwxr-xr-x ... .git/hooks/pre-commit + "PASS — hook installed"
```

Cross-reference: BUG-006 already filed on the broader pre-commit framework choice (heredoc-shell vs framework). BUG-010 is narrower: just install the hook in the orchestra repo using the existing `cli.install_hooks` shipped in v1.5.

## Fix Description

Two-part fix:

### Part 1 — install hook in this repo

```bash
cd /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra
python -m cli.install_hooks --pre-commit --repo .
ls -la .git/hooks/pre-commit  # confirm symlink/script present
```

`cli.install_hooks` already implements idempotent install (safe to re-run). Verifies via `cli/install_hooks.py` source.

### Part 2 — document in CONTRIBUTING.md

Append to `CONTRIBUTING.md` § Setup section:

```markdown
### Pre-commit hook (required for contributors)

orchestra dogfoods its own canon-inplace enforcement. After cloning,
install the pre-commit hook:

    python -m cli.install_hooks --pre-commit --repo .

This runs `python -m cli.lint --pre-commit` (calls `lint_staged()`
which invokes L1 Refs-eligibility + L2 canon-inplace narrow-change
+ L3 attestation-path-resolution + L4 doc-id-burn) before each commit.
Canon-inplace violations on Status: Implemented/Verified/Current/...
docs are rejected; supersession workflow required (see LLD-006-r4).
```

### Part 3 (deferred to v1.6.x followup) — auto-install on bootstrap

Add hook-install check to `cli/init.py` or `Makefile`. If `.git/hooks/pre-commit` missing → run `cli.install_hooks --pre-commit --repo .` as side effect. Mark as v1.6.x followup (not blocking for BUG-010 close).

## Test Plan

- Manual verification post-fix: `ls .git/hooks/pre-commit` shows symlink/script
- Behavioral test: stage a canon-inplace violation, attempt commit, confirm hook rejects (without --no-verify)
- No new automated test (hook install is filesystem state, exercised by existing `tests/test_install_hooks.py` which tests the install logic itself)

## Risk

- Low. Hook install is idempotent. Existing contributors who already installed it manually unaffected.
- Caveat: contributors using `--no-verify` to skip will still bypass. Hook is a backstop, not a hard gate. BUG-009 (lint_commit retroactive) covers post-hoc detection for that case.
- CI mirror: ensure CI also runs `cli.lint --pre-commit` so hook-skipped commits caught upstream. Out of scope for BUG-010; track as v1.6.x followup if CI added later.

## Acceptance

- [ ] `.git/hooks/pre-commit` present in orchestra repo
- [ ] Hook content: invokes `python -m cli.lint --pre-commit` (or equivalent)
- [ ] `CONTRIBUTING.md` documents the install step
- [ ] Reproduction `ls .git/hooks/pre-commit` returns success exit
- [ ] Behavioral check: attempt canon-inplace commit on test branch → hook rejects

## Environment

- orchestra repo: `/Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra` (main branch)
- Python: 3.10+ (interpreter resolved via `$PYTHON` env override → `python3` → `python` fallback chain in pre-commit.sh template post-fix)
- Git: any version with `.git/hooks/` standard support
- OS: tested Darwin 25.4.0 (macOS); template uses POSIX shell so portable across Linux/macOS

## Root Cause

orchestra ships `cli.install_hooks` for downstream consumers but never invokes it on its own repo at clone or release time. `.git/hooks/` contained only `*.sample` files; pre-commit gate was inactive. Compounded by an env-portability bug in `cli/templates/pre-commit.sh` using bare `python` (fails on systems where only `python3` exists or where venv-bin paths vary) — only discovered when the hook fired for the first time in this session.

## Iteration Log

- **r1 (2026-05-10)** — Bug filed; spec-review verdict conditional_pass; lint-entrypoint and reproduction wording reconciled. Status: Draft → In Progress.
- **r1 implementation (2026-05-10)** — `python -m cli.install_hooks --repo .` invoked; `.git/hooks/pre-commit` installed (193 bytes, 0o755). CONTRIBUTING.md § Pre-commit hook section appended. Hook fired on next commit attempt → caught template env-portability bug → patched `cli/templates/pre-commit.sh` with `$PYTHON`/`python3`/`python` fallback chain → reinstalled via `--force`. Hook now operational. Status: In Progress → Fix Applied.

## Regression Prevention

- Pre-commit hook now active on orchestra repo. First-line defense against canon-inplace + Refs:-eligibility violations.
- `cli/templates/pre-commit.sh` env-portability fix: PR-tested on system without bare `python` on PATH. Future contributors unaffected.
- CONTRIBUTING.md install instruction explicit; new contributors run `python -m cli.install_hooks --repo .` after clone.
- BUG-009 ships post-hoc backstop for any commit that bypassed the hook (via `--no-verify`).
- Auto-install on bootstrap (Part 3 in Fix Description) tracked as v1.6.x followup; would prevent contributors forgetting the manual install.

## Related Documents

- `docs/postmortems/POSTMORTEM-2026-05-10-canon-inplace-violation.md` — root incident (this gap is contributing-cause-2)
- `docs/bugs/BUG-009-lint-commit-l2-retroactive.md` — sibling fix (lint_commit retroactive); BUG-009 + BUG-010 close enforcement together
- `docs/bugs/BUG-006-install-hooks-precommit-framework.md` — older BUG on hook framework choice; BUG-010 is narrower scope (just install what already exists)
- `cli/install_hooks.py` — existing install machinery (v1.5)
- `CONTRIBUTING.md` — append target

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | BUG filed post-supersession redo of LLD-007 r5. Self-install gap was contributing-cause-2 of canon-inplace violation. Fix is one-shot install + CONTRIBUTING.md doc. High severity. |
| 2026-05-10 | r1 spec-review verdict: conditional_pass. 4 findings (2 Important on lint-entrypoint naming + severity-enum drift; 2 Minor). Lint-entrypoint reconciled to `python -m cli.lint --pre-commit` calling `lint_staged()` with L1+L2+L3+L4 in both Observed Behavior and Fix Design Part 2. Reproduction got post-fix expected output. Severity-enum finding is false-positive (reviewer applied finding-enum to doc-header field — orchestra BUG vocab is Critical/High/Medium/Low; tracked as v1.6.x prompt-template followup). Status: Draft → Implemented. |
| 2026-05-10 | Implementation: Part 1 ran `python -m cli.install_hooks --repo .` — installed `.git/hooks/pre-commit` (193 bytes, 0o755). Hook script invokes `python -m cli.lint --pre-commit` with `set -euo pipefail`. Part 2: appended Pre-commit hook section to `CONTRIBUTING.md` § Quick path with rationale (BUG-010 + BUG-009 reference) and bypass discouragement. Acceptance items 1-3 met. Acceptance item 4 (`ls .git/hooks/pre-commit` exit 0) verified. Acceptance item 5 (behavioral check on test branch) deferred — relies on BUG-009 L2 retroactive (just-shipped) for failure-mode confirmation; hook content matches expected entry-point. Part 3 (auto-install on bootstrap) remains as v1.6.x followup. |
| 2026-05-10 | Env-portability fix on `cli/templates/pre-commit.sh` discovered when first hook invocation failed with `python: command not found` (modern systems may have python3 only; venv-bin paths vary). Template now resolves Python interpreter via `$PYTHON` env override → `python3` → `python` fallback chain; fails loudly if none. Hook reinstalled via `--force`; behavioral check now confirms hook fires correctly on this commit (the bootstrap commit). |
| 2026-05-11 | Part 3 (auto-install on bootstrap) closed via LLD-008 r7 A6 in orchestra v1.7.0 (commit `eb50924`). `cli.init` now invokes `install_hooks.main(["--all", "--on-conflict=skip"])` post-init with TTY-aware fail-open/closed default + `ORCHESTRA_INIT_STRICT=1` opt-in (A14). 7 bootstrap tests added (T5a-g). Refs: docs/features/008-commit-skill.md |
