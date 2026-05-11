# Sonnet Judge-2 Review (LLD-009 r1)

> Reviewer: general-purpose subagent (model: sonnet) — different model than Opus author
> Date: 2026-05-11

## Adversarial Spec Review — LLD-009 commit-msg L2-finalize (Iteration 1)

---

### FINDING 1 — HIGH: Finding-index flattening is gate-order-dependent and unstable across attestations

In `_verify_finding_in_attestation`, the attestation `gates` object is iterated with `(att.get("gates") or {}).values()` — a plain dict values() call. The attestation schema (`attestation-schema-v1.0.json`) requires exactly four keys: `completeness`, `evidence`, `clarity`, `consistency`. Python 3.7+ guarantees insertion-order for dicts, but YAML `safe_load` (via PyYAML) does NOT guarantee any defined ordering. `yaml.safe_load` returns a plain `dict`; the YAML file may store gates in any textual order, and different reviewers (orchestra Sonnet vs codex) may serialize them in different orders. The flattened `all_findings` list therefore has unstable ordinal indexing: finding `3` in one attestation could be finding `5` in another, or even in a re-serialized copy of the same attestation.

The author's `Addresses:` line uses a global 1-indexed finding number (`finding 3`) that maps into this flattened list. There is no gate-name disambiguation in the commit-message format. Result: any cross-reviewer attestation or any YAML round-trip that reorders the gate keys silently shifts all finding indices, causing L2-finalize to either approve the wrong finding or reject a valid one.

Fix: `Addresses:` lines must include the gate name, e.g. `Addresses: docs/reviews/007-r5.review.yaml clarity finding 2 (Minor)`. Or: flatten in a stable canonical gate order (`["completeness","evidence","clarity","consistency"]`) hardcoded to match the schema. The current design gives neither.

---

### FINDING 2 — HIGH: `git show :0:<path>` silently fails when pre-commit framework passes a relative path different from repo root

A9 and A7 use `subprocess.check_output(["git", "show", f":0:{path}"], cwd=repo_root)`. The `path` value comes from the pending file, which was written by L2-detect during pre-commit. L2-detect obtains staged paths via `git diff --cached --name-only` (lint.py line 763) — these are repo-relative paths. However, in the pre-commit framework (`pass_filenames: false` for `orchestra-lint`), the hook fires from whatever cwd the framework establishes, which may not be the repo root. More critically, `repo_root` itself in L2-finalize must be resolved from `git rev-parse --show-toplevel` at commit-msg time. If the commit-msg hook is invoked from a subdirectory (common in IDE integrations), `cwd=repo_root` must be used — but the pending file is written to `.git/orchestra-canon-inplace-pending` where `.git` is resolved from the working tree, not necessarily `repo_root`. In `git worktree add` scenarios (Edge Case 16), `.git` for a worktree is `.git/worktrees/<name>/` not `.git/`, so `.git/orchestra-canon-inplace-pending` would be under the worktree's gitdir, not the common `.git`. The design says "should work" (Out of Scope) but the pending-file path construction `repo_root / ".git" / "orchestra-canon-inplace-pending"` is wrong for worktrees, and this is not just untested — it's broken by construction.

---

### FINDING 3 — HIGH: `FINDING_REF_RE` in BUG-011 has no line anchors; LLD-009 adds them — but the two regexes are contractually different

BUG-011 § Fix Description defines `FINDING_REF_RE` without `^` / `$` line anchors:

```python
FINDING_REF_RE = re.compile(r"Addresses:\s+(\S+\.review\.yaml)\s+finding\s+(\d+)\s+\((Minor|Important|Critical)\)")
```

LLD-009 A6 defines it WITH `^` and `$` (line-anchored, MULTILINE):

```python
FINDING_REF_RE = re.compile(r"^Addresses:\s+(\S+\.review\.yaml)\s+finding\s+(\d+)\s+\((Minor|Important|Critical)\)\s*$", re.MULTILINE)
```

The BUG-011 version matches `Addresses:` embedded mid-sentence or in prose (e.g., in a Changelog row). The LLD-009 version requires the token to occupy an entire line. These are different contracts. An `Addresses:` line embedded at end of a paragraph (e.g., `... see details. Addresses: foo.review.yaml finding 3 (Minor)`) passes BUG-011 but fails LLD-009.

More importantly: BUG-011 is the source bug this LLD closes (A14). If BUG-011 ships first with the old regex in tests, and LLD-009 replaces the constant, existing tests expecting the unanchored regex would break. The LLD does not address this contract divergence or specify which version's tests the 5 BUG-011 tests (`test_minor_finding_*`) will be rewritten against. This is a real regression risk at the test suite level.

---

### FINDING 4 — HIGH: Pending-file cleanup races with `git commit --amend`

A3 says "Commit-msg re-fires" on amend, and the design says "same flow as fresh commit" (Edge Case 3). But the flow is:

1. `git commit --amend` fires pre-commit → writes pending file (truncate-then-append)
2. pre-commit passes → fires commit-msg → L2-finalize reads pending + cleans up

However: `git commit --amend --no-edit` does NOT re-fire pre-commit in all configurations. The git documentation specifies pre-commit fires for `--amend`; but when `SKIP=orchestra-lint` or `ORCHESTRA_BYPASS=1` is set for the amend run, the pending file from the original pre-commit run is gone (cleaned up at original commit-msg time), but a NEW pending file from this amend's pre-commit would exist. This is the stated flow. The unstated failure mode: if the user runs `git commit --amend` with `--no-verify` (skips pre-commit), no new pending file is written; L2-finalize sees no pending file and exits 0. This means an amend can silently bypass L2-detect by using `--no-verify`. The design's security section doesn't acknowledge this. Since `--no-verify` is the stated "only bypass" for mechanical backstops (LLD-008 Glossary § mechanical backstop), this is by design — but LLD-009 doesn't state it explicitly, leaving an undocumented hole.

---

### FINDING 5 — MEDIUM: `_verify_changelog_row_per_finding` tolerant-search is gameable by coincidence

The Changelog row check uses:

```python
found = any(att_basename in row and finding_marker in row for row in rows)
```

Where `att_basename = Path(attestation_path).name` (e.g., `007-spec-review-architecture-r5.review.yaml`) and `finding_marker = f"finding {finding_n}"`.

The string `finding 3` appears in many natural-language Changelog entries (e.g., "Fixed 3 findings"). The basename check is more specific but `att_basename` is still a substring match. An existing Changelog row from a prior narrow-change that happens to mention the same attestation basename and "finding 3" in a different context would satisfy the check without a new row being added. This is a false-accept path. The check should require a NEW row (i.e., one added after the prior Changelog content), not any row in the full Changelog. The function receives only `new_text` — it should compare new rows vs prior Changelog rows to detect newly appended ones. As written, it matches against the entire Changelog, including historic entries.

---

### FINDING 6 — MEDIUM: ORCHESTRA_BYPASS audit log loses commit SHA before commit lands

A10 specifies the audit log format as `<ISO-8601-timestamp>  <commit-sha-prefix>  <user@host>  <commit-msg-first-line>`. But L2-finalize runs at commit-msg time — before the commit exists. No SHA is available yet. The `git log --format=%H -1` would return the PREVIOUS commit's SHA, not the bypassed one. The LLD uses the term "commit-sha-prefix" without explaining how it's obtained at commit-msg time. There are two plausible implementations: (a) use `HEAD` SHA (previous commit — wrong semantics), (b) omit SHA entirely. Neither matches the stated format. The test T10b asserts the format `<ts>  <sha>  <user@host>  <subject>` — but the implementation cannot satisfy this since the SHA doesn't exist yet. Either the format spec is wrong (should say "commit-msg subject as proxy") or the implementation must use a placeholder like `<pending>`.

---

### FINDING 7 — MEDIUM: `lint_commit_msg_finalize` has TOCTOU between pending-sha re-check and `_read_staged_content`

The SHA re-check at A2 confirms `current_sha == pending_sha` before reading staged content. But `_read_staged_content` makes a separate `git show :0:<path>` call. Between the sha check and the content read, there is a tiny window (TOCTOU) where `git add <file>` on a different terminal could update the index. This is extremely unlikely in practice but the design claims "staged drift → `staged_drift` error" covers this. In fact the staged-drift check uses `_get_staged_blob_sha` (a separate subprocess) then `_read_staged_content` (another subprocess) — two calls, no atomic lock. If the index changes between them, the content read returns different content than the sha check confirmed. The pending sha was written for the pre-commit-era blob; if re-add happens between the two calls, L2-finalize evaluates different staged content than it validated the sha for. This is a well-known TOCTOU but the design presents the sha check as a complete defense. It isn't.

---

### FINDING 8 — MEDIUM: `--pre-stage-check` works against WORKING TREE but `is_narrow_change` extension requires `repo_root` for attestation resolution

A9 calls `is_narrow_change(prior_text, new_text, commit_msg=commit_msg_draft, repo_root=repo_root)`. The `_verify_finding_in_attestation` helper does `full = repo_root / attestation_path` — reads the attestation file from disk. For `--pre-stage-check` (author-iteration tool), this is fine IF the attestation YAML is already committed to the repo. But a workflow where the author simultaneously creates a new attestation (spec-review result not yet committed) and then runs `--pre-stage-check` against a draft commit message referencing it will get `missing_attestation` error. This is expected, but the pre-stage checklist prose in A8 doesn't mention this ordering constraint — author must commit the attestation before using `--pre-stage-check`. The failure message `missing_attestation: <path>` doesn't explain "commit the attestation first."

---

### FINDING 9 — MEDIUM: BUG-011 status contradiction is under-resolved by A14

A14 acknowledges the contradiction: BUG-011 frontmatter says `Status: Investigating` but Changelog r1 says "Status: Draft → Implemented". A14 says "flip to Fix Applied on this LLD's impl ship" and claims BUG-011 is currently `Investigating` (not canon-frozen), so full edit is permitted.

However the Changelog entry reads: `r1 ... Status: Draft → Implemented`. The GROUND TRUTH is the frontmatter (per LLD-009 Glossary: "frontmatter source of truth"). So BUG-011 is `Investigating`. But the Changelog says it was flipped to `Implemented` — implying an implementor already did the status flip in the Changelog but missed the frontmatter. This is a documentation error that should have triggered Gate 1 on investigation. A14 just schedules a fix rather than declaring the correct current state. The LLD should explicitly state: "BUG-011 frontmatter Status is currently `Investigating` (NOT `Implemented`); the Changelog r1 entry claiming `Draft → Implemented` was incorrect — BUG-011 has NOT been implemented." This should be a committed BUG-011 narrow-change (since Investigating is not canon-frozen, full edit permitted) BEFORE this LLD's acceptance items are marked done, not deferred to impl ship.

---

### FINDING 10 — MEDIUM: Important-count threshold logic does not aggregate across all findings before rejecting Critical

In the tiered rule pseudocode, the loop iterates findings and returns `(False, ...)` immediately on `severity == "Critical"`. This early return means the `important_count` is never fully accumulated before rejection. That's fine for Critical (always rejects). But the Important threshold check (`if important_count >= 4`) runs AFTER the loop ends. Consider: 1 Critical finding + 2 Important findings in the commit message. The loop hits the Critical and returns immediately — never reaching the `important_count >= 4` check. The commit is rejected with "Critical finding... cannot be fixed via narrow-change" — correct outcome. Now consider: 5 Important findings + 1 Critical finding, but the Critical appears LAST in the `refs` list. The loop counts 5 Important findings first, then hits Critical and returns with a Critical-rejection message. The `important_count >= 4` threshold message is never emitted. This is correct behavior (Critical rejects regardless) but the error message could be more useful if it called out BOTH the Critical AND the Important overflow. Minor UX issue elevated to medium because it may confuse authors who see only "Critical" rejection and miss that they also have 5 Important findings.

---

### FINDING 11 — LOW: `FINDING_REF_RE` does not anchor `\S+\.review\.yaml` to prevent path-traversal in attestation_path

The attestation path group `(\S+\.review\.yaml)` matches any non-whitespace string ending in `.review.yaml`. An author could supply `../../etc/passwd.review.yaml` (unlikely, but possible in a malicious commit message). `_verify_finding_in_attestation` does `full = repo_root / attestation_path` — Path concatenation does NOT protect against path traversal when `attestation_path` begins with `..` or `/`. The security section states "no untrusted-input injection" but does not address this path. Should add: `if not attestation_path.startswith("docs/reviews/")` → reject as malformed.

---

### FINDING 12 — LOW: `commit-msg.sh` Refs:-line check greps only the SUBJECT line but L1 validates entire body

In the shell template (A12), the Refs:-line check is:

```bash
SUBJECT=$(head -n1 "$MSG_FILE")
if echo "$SUBJECT" | grep -qE '^(fix|feat)(\(.*\))?:'; then
    if ! grep -q '^Refs: docs/' "$MSG_FILE"; then
```

The second grep correctly searches the entire `$MSG_FILE` for `Refs: docs/`. But the first grep tests only `$SUBJECT` (line 1). This matches `cli.lint` L1 behavior (CONVENTIONAL_PREFIX_RE matches commit subject). Consistent. Not a bug. However the comment in A12 says "Existing Refs:-line check" implying this is unchanged from LLD-008 ship. If LLD-008 ships first without L2-finalize in the commit-msg.sh (since LLD-009 adds it later per A12), there will be a window where the deployed commit-msg.sh has no L2-finalize invocation. The "template content" for LLD-008's ship must be explicitly different from LLD-009's ship. A13 says "pre-commit.sh template unchanged from LLD-008 ship" but there is no corresponding acceptance item verifying that the LLD-008 commit-msg.sh content is the SUBSET of LLD-009's commit-msg.sh. A version mismatch between template in LLD-008 and template in LLD-009 could cause test T12 to fail or T13 to pass incorrectly.

---

### FINDING 13 — LOW: No test covers `FINDING_REF_RE.findall()` returning duplicate `(attestation, N, severity)` tuples

An author could write the same `Addresses:` line twice in a commit message (e.g., copy-paste). `FINDING_REF_RE.findall()` returns both occurrences. The tiered loop counts duplicate Important findings toward the `important_count`. Two lines referencing the same Important finding = `important_count = 2`. Four identical lines = threshold rejection. The test matrix (T3c, T3d) does not test this deduplication-or-not decision. If deduplication is intended (count unique findings, not total Addresses lines), the design must state it. If not, the doc should acknowledge that duplicates inflate the Important counter.

---

### FINDING 14 — LOW: `extract_changelog_and_strip` strips the sentinel placeholder `<<CHANGELOG_BLOCK>>`; `_verify_changelog_row_per_finding` receives `new_text` not `new_body`

`_verify_changelog_row_per_finding(new_text, refs)` calls `extract_changelog_and_strip(new_text)`. But `extract_changelog_and_strip` (lint.py line ~340) operates on body text extracted from `_split_metadata_and_body`. If `new_text` is the full file including metadata block, the Changelog detection must find the `## Changelog` heading in the full file. `lint_commit_msg_finalize` passes the full file content to `is_narrow_change(prior_text, new_text, commit_msg=msg, repo_root=repo_root)`, which then calls `_verify_changelog_row_per_finding(new_text, refs)`. But `is_narrow_change` calls `_split_metadata_and_body` on both texts and passes the body to `extract_changelog_and_strip`. The `_verify_changelog_row_per_finding` helper takes `new_text` directly — not `new_body`. If called with the full file text, `extract_changelog_and_strip` must handle the metadata block prefix. Review of the existing code (lines 340-366) shows it does a linear scan for `## Changelog` — this works on full text. But the interface contract for `_verify_changelog_row_per_finding` should document whether it takes full text or body. As written in A5 pseudocode, it receives `new_text` from the caller in `is_narrow_change`, but `is_narrow_change`'s internal flow calls it after `_split_metadata_and_body` has been applied — meaning `new_body` is available in scope. The pseudocode passes `new_text` to `_verify_changelog_row_per_finding`, while `is_narrow_change`'s own `_verify_changelog_row_per_finding` call (in the pseudocode at line ~200) passes `new_text` directly. This needs to be `new_body` (post-split) to be consistent with how `extract_changelog_and_strip` is used elsewhere in `is_narrow_change`.

---

## Verdict: **needs-attention**

The doc is architecturally sound on the primary hook-ordering insight (L2-detect vs L2-finalize split is correct; the core design is justified). However, Findings 1–4 are high-severity defects that would cause the implementation to be incorrect or gameable:

- Finding 1 (gate-order YAML flattening) is a correctness defect: finding indices are unstable. This must be fixed before implementation — either by locking canonical gate iteration order or extending the commit-message `Addresses:` format to include the gate name.
- Finding 2 (worktree pending-file path) is a stated known issue but is incorrectly characterized as "tested implicitly" — it is not. The path `repo_root / ".git" / "orchestra-canon-inplace-pending"` is structurally wrong for worktrees. Either restrict explicitly or fix.
- Finding 3 (regex divergence with BUG-011) creates a contract break at the test suite boundary. Must be explicitly resolved — state which regex wins and update BUG-011 tests to match before impl.
- Finding 6 (audit log commit SHA unavailable at commit-msg time) is a format spec error — the stated audit log format cannot be implemented as written.

Findings 5, 7, 8, 9 are implementation-correctness risks. All four should be addressed in the doc before marking the spec approved for implementation. Finding 14 is a subtle argument-passing bug in the pseudocode that will surface immediately in TDD slice T5a.