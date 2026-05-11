# Codex Adversarial Review — LLD-008 r2 (Judge-2)

> **Doc subject:** docs/features/008-commit-skill.md
> **Iteration:** 2
> **Reviewer:** codex (via /codex:adversarial-review)
> **Reviewer model:** different-from-author (Opus author; codex non-Opus → bypasses self-preference)
> **Invoked at:** 2026-05-11
> **Verdict:** needs-attention (no-ship)

## Findings

### [high] Commit-msg framework hook drops the message-file argument required by L2-finalize

**Location:** docs/features/008-commit-skill.md:272-281 (Design § cli.install_hooks framework-detection — YAML snippet) + lines 372-377 (`lint_commit_msg_finalize` pseudocode requiring `msg_file_path`)

`orchestra-commit-msg` snippet sets `pass_filenames: false` for the commit-msg hook stage. With pre-commit framework's documented handling of `pass_filenames: false` + empty `args: []`, no positional argument is supplied. But `--commit-msg-finalize` requires `<msg-file>` per A7 + the `lint_commit_msg_finalize(msg_file_path, repo_root)` signature. Result: framework users lose BUG-011 enforcement path. May fail-open or fail-closed depending on implementation.

**Recommendation:** For commit-msg hook stage, set `pass_filenames: true` (framework passes msg file as the filename). Require msg-filename argument contract explicitly. Add test asserting hook receives + uses commit message path under framework path (not just raw `.git/hooks/` path).

### [high] Framework-detection flow is advisory-only; can report success without installing enforceable hooks

**Location:** docs/features/008-commit-skill.md:252-257 (install_hooks early `return 0` after print) + line 392 (instruction to "run pre-commit install")

Detection is only `exists()` check + printed YAML instructions, then `return 0`. Consumer is told to paste snippet + run `pre-commit install`. But pre-commit framework's default `pre-commit install` only installs the pre-commit stage hook — it does NOT install commit-msg stage hook unless invoked as `pre-commit install --hook-type commit-msg` (or `default_install_hook_types` set in `.pre-commit-config.yaml`). Result: silent gap precisely in the path meant to close BUG-006 / BUG-010. Reports success; commit-msg L2-finalize never fires.

**Recommendation:** Framework mode must be deterministic. Two paths:
- (A) Auto-apply snippet to user's `.pre-commit-config.yaml` + run `pre-commit install --hook-type pre-commit --hook-type commit-msg` programmatically; verify both stages active before exit 0.
- (B) Print exact instruction set requiring `pre-commit install --hook-type commit-msg`, AND verify by checking `.git/hooks/commit-msg` exists post-instructions before exit 0; fail non-zero until verified.

Add integration test (T4d) proving BOTH stages fire after bootstrap with no manual hook-type guesswork.

### [high] L2-finalize pseudocode validates working-tree content instead of staged/index content

**Location:** docs/features/008-commit-skill.md:380-382 (`lint_commit_msg_finalize` pseudocode)

```
new_text = (repo_root / staged_path).read_text()
```

This reads working-tree content — what's currently in the file on disk — NOT what's in the staging index (what `git commit` will actually persist). Common workflow: developer stages a file, then continues editing; `git status` shows staged + unstaged changes. L2-finalize would validate the unstaged version, accept/reject based on text that won't be committed.

Conflicts with Edge Case 15's claim that `is_narrow_change` re-runs on "LIVE working-tree content + LIVE staged content" — the pseudocode ignores staged content entirely.

**Impact:** real canon-inplace violations can slip through (developer stages valid narrow-change, then makes additional canon-inplace edits in worktree before commit-msg fires). OR valid commits blocked (developer stages whitelist-only edit, edits in worktree creating non-narrow changes that won't be committed).

**Recommendation:** Use `git show :<path>` (index/staged content) or equivalent plumbing for `new_text`. Fix pseudocode + Edge Case 15 wording. Add regression test where staged and working-tree versions intentionally diverge — assert L2-finalize evaluates staged content, not worktree.

## Notes

- All 3 findings are architectural / contract issues. r2 redesign of A5 / A7 introduced new defects while fixing r1's. Pattern: orchestra:commit's hook-coordination contract is genuinely complex (pre-commit + commit-msg + framework + raw + tiered + index-vs-worktree + cross-commit pending-file-state).
- Multi-judge value confirmed (r1 + r2): codex caught 6 architectural defects orchestra missed across 2 iterations. orchestra caught 36 textual ambiguity / cross-ref / consistency findings codex didn't bother flagging. Different blind spots.
- Combined r2 verdict (manual chair): **fail** — codex 3 highs make impl non-functional as written.

## Iteration plateau check

Per LLD-007 § iteration handling + Interview Gate § iteration plateau heuristic:

- r1 → r2: 3 codex highs (framework snippet semantic / hook ordering / non-interactive bootstrap)
- r2 → ?: 3 codex highs (commit-msg pass_filenames / framework-install determinism / L2-finalize index-vs-worktree)

Findings overlap area: hook-ordering + framework integration + state-handling. Same architectural region across both rounds. Pattern matches LLD-005 + LLD-006 4-iteration plateau (per POSTMORTEM-2026-05-10-session-process-drift). Interview-gate fires.

## Next steps (per multi-judge protocol + interview-gate)

User decides:

1. **Iter 3** — apply r2 findings inline; re-dispatch both judges. Risk: same plateau pattern repeats; r3 surfaces new architectural defects in adjacent areas (e.g., pending-file race conditions, framework-version-skew).
2. **Reframe scope** — split LLD-008 into smaller pieces. E.g., LLD-008 = skill structure + references migration only; LLD-009 = tiered narrow-change + commit-msg L2-finalize design (separate doc; targeted spec-review on the hook-ordering complexity); LLD-010 = framework-detection redesign (separate doc; targeted on pre-commit integration). Each smaller doc is easier to converge.
3. **Pre-impl prototype** — stop iterating spec; impl a thin prototype of the hook coordination + framework path + index-vs-worktree handling; let runtime feedback drive spec corrections rather than further pre-impl review.
