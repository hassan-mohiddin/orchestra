# BUG-010: orchestra repo does not install its own pre-commit hook

> **Doc ID:** BUG-010-orchestra-self-install-precommit-hook
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** High
> **Status:** Implemented

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

## Reproduction

```bash
cd /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra && \
  ls .git/hooks/pre-commit 2>/dev/null && echo "PASS — hook installed" || echo "FAIL — hook missing"
# Current output: FAIL — hook missing
# Post-fix expected: -rwxr-xr-x ... .git/hooks/pre-commit + "PASS — hook installed"
```

Cross-reference: BUG-006 already filed on the broader pre-commit framework choice (heredoc-shell vs framework). BUG-010 is narrower: just install the hook in the orchestra repo using the existing `cli.install_hooks` shipped in v1.5.

## Fix Design

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
