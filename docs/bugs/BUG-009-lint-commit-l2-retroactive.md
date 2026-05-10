# BUG-009: cli.lint --commit does not include L2 (canon-inplace) retroactive check

> **Doc ID:** BUG-009-lint-commit-l2-retroactive
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** High
> **Status:** Implemented

## Observed Behavior

`python -m cli.lint --commit <SHA>` runs only L1 (`lint_commit_refs_eligible`) — checks Refs:-eligibility on commit subject + body. It does NOT run L2 (`lint_commit_no_canon_inplace_edit`) — the canon-frozen narrow-change diff check.

Code path:

- `cli/lint.py:668-682` — `lint_commit(commit_sha, repo_root)` returns `lint_commit_refs_eligible(subject, body, repo_root)` only
- `cli/lint.py:705-728` — `lint_staged(repo_root)` calls `lint_commit_no_canon_inplace_edit(repo_root, staged)` at line 728
- L2 fires only via the `--pre-commit` / staged-files path. Never via `--commit <SHA>`.

Confirmed by retroactive lint check on 2026-05-10:

```bash
$ git log --oneline -3
bc359e7 docs: LLD-007 r5 dogfood verification + v1.6.1 doc-snippet sync
653db4e fix: ship v1.6.1 — dogfood patches
6ca0ea7 feat: ship LLD-007 — orchestra:spec-review skill

$ python -m cli.lint --commit bc359e7
PASS — all design-docs checks green

$ python -m cli.lint --commit 653db4e
PASS — all design-docs checks green
```

Both commits made body edits to canon-frozen LLD-007 (Status: Implemented at HEAD~1). L2 would have rejected. `--commit` mode silently passed.

## Expected Behavior

`cli.lint --commit <SHA>` runs L1 AND L2. L2 retroactive check:

- Get list of .md files modified in commit (`git diff --name-only HEAD~1 <SHA>`)
- For each file under `REFS_ELIGIBLE_PREFIXES`:
  - `git show HEAD~1:{path}` → prior text (skip if missing — new file)
  - `git show <SHA>:{path}` → new text
  - parse_status(prior_text) ∈ CANON_FROZEN_STATUSES?
  - if yes: `is_narrow_change(prior_text, new_text)` → if False → emit Finding

Same logic as `lint_commit_no_canon_inplace_edit` but reading both states from git rather than HEAD vs working tree.

## Reproduction

```bash
cd /tmp && git init && mkdir -p docs/features && \
  printf '# F\n\n> **Status:** Implemented\n> **Iteration:** 1\n\n## Body\n\nOriginal.\n' > docs/features/001-x.md && \
  git add . && git -c user.email=t@t -c user.name=t commit -q -m 'docs: seed' && \
  printf '# F\n\n> **Status:** Implemented\n> **Iteration:** 1\n\n## Body\n\nMUTATED canon-frozen body.\n' > docs/features/001-x.md && \
  git -c user.email=t@t -c user.name=t commit -q -am 'fix: violate' && \
  PYTHONPATH=/Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra python -m cli.lint --commit HEAD
# Expected: FAIL (canon-inplace violation)
# Actual:   PASS
```

## Fix Design

Extend `lint_commit()` in `cli/lint.py:668-682`:

```python
def lint_commit(commit_sha: str, repo_root: Path) -> list[Finding]:
    """Lint a single commit: subject + body Refs:-eligibility (L1) + canon-inplace (L2)."""
    try:
        subject = subprocess.check_output(...).strip()
        body = subprocess.check_output(...)
        files = subprocess.check_output(
            ["git", "diff", "--name-only", f"{commit_sha}~1", commit_sha],
            cwd=repo_root, text=True,
        ).strip().splitlines()
    except subprocess.CalledProcessError as e:
        return [Finding("error", commit_sha, f"git log/diff failed: {e}")]

    findings = lint_commit_refs_eligible(subject, body, repo_root)
    findings.extend(_lint_commit_canon_inplace(commit_sha, files, repo_root))
    return findings


def _lint_commit_canon_inplace(commit_sha: str, files: list[str],
                                repo_root: Path) -> list[Finding]:
    """L2 retroactive — reject canon-frozen body edits in a committed SHA."""
    findings: list[Finding] = []
    for path in files:
        if not path.endswith(".md") or not path.startswith(REFS_ELIGIBLE_PREFIXES):
            continue
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"{commit_sha}~1:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue  # New file at this commit
        prior_status = parse_status(prior_text)
        if prior_status not in CANON_FROZEN_STATUSES:
            continue
        try:
            new_text = subprocess.check_output(
                ["git", "show", f"{commit_sha}:{path}"],
                cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue  # File deleted at this commit (handled separately by archive flow)
        ok, why = is_narrow_change(prior_text, new_text)
        if not ok:
            findings.append(Finding(
                "error", path,
                f"Doc Status was {prior_status!r} (canon-frozen) at {commit_sha}~1. "
                f"Non-narrow change in commit {commit_sha}: {why}. "
                "Use supersession (new file with -rN suffix and Supersedes:) instead.",
            ))
    return findings
```

Helper `_lint_commit_canon_inplace` is module-private (separate from public `lint_commit_no_canon_inplace_edit` which reads HEAD vs working tree). Same `is_narrow_change` + `parse_status` reused.

## Test Plan

New test file `tests/test_lint_commit_l2.py` with:

1. `test_canon_inplace_violation_in_committed_sha_caught` — seed repo with prior canon-frozen doc; mutate body; commit; `lint_commit(HEAD)` returns 1 finding with "Non-narrow change"
2. `test_canon_inplace_narrow_change_committed_passes` — same but only Status field flipped; `lint_commit(HEAD)` returns 0 findings
3. `test_canon_inplace_new_file_in_commit_passes` — file added at commit (no prior); 0 findings
4. `test_canon_inplace_non_canon_status_committed_passes` — prior Status: Draft; body edit; 0 findings (Draft permits full edit)
5. `test_lint_commit_still_runs_l1` — regression — Refs:-eligibility check still fires

Pytest target: 144 → 149.

## Risk

- Low. Adds checks; does not weaken existing. False-positive risk: commits that legitimately rename + body-edit in same commit could trip L2 if path stays same. Mitigation: rename-then-body-edit goes through supersession workflow (different file path). Same-path body edit on canon-frozen IS the violation L2 catches.
- Subprocess invocations grow O(N) in modified files per commit. For typical commits (1-10 .md files) negligible.

## Acceptance

- [ ] `lint_commit(SHA)` includes L2 check on .md files under REFS_ELIGIBLE_PREFIXES
- [ ] All 5 new tests pass
- [ ] `cli.lint --commit 653db4e` (the historical violation commit) FAILS with canon-inplace finding
- [ ] `cli.lint --commit 68fd538` (the revert commit) PASSES (revert restores canon state; not a violation)
- [ ] Existing pytest 144 + 5 new = 149 (no regressions; 144 baseline preserved + 5 new tests)

## Related Documents

- `docs/postmortems/POSTMORTEM-2026-05-10-canon-inplace-violation.md` — root incident
- `docs/runbooks/RUNBOOK-canon-inplace-violation-recovery.md` — operator procedure for already-landed violations
- `docs/features/006-archive-and-supersession-conventions-r4.md` — LLD-006-r4 § narrow change (the rule this BUG enforces)
- `cli/lint.py:490-521` — L2 implementation `lint_commit_no_canon_inplace_edit` (existing — used by `lint_staged`)
- `cli/lint.py:668-682` — `lint_commit` (the gap)
- `cli/lint.py:705-728` — `lint_staged` (line 728 is current L2 call site)

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | BUG filed post-supersession redo of LLD-007 r5. Identifies enforcement gap that allowed canon-inplace commits 653db4e + bc359e7 to land. High severity (closes hole that produced this session's incident). |
| 2026-05-10 | r1 spec-review verdict: conditional_pass. 4 findings (2 Minor wording + 2 false-positive on severity-enum — false positives because spec-review prompt-template's `Critical/Important/Minor` enum applies to attestation findings, NOT to doc-header severity which uses orchestra convention `Critical/High/Medium/Low` for BUGs). Acceptance pytest target tightened from `≥145` to exact `=149`. False-positive enum-vocabulary drift tracked as v1.6.x followup (spec-review prompt should distinguish finding-severity vs doc-header-severity). Status: Draft → Implemented. |
