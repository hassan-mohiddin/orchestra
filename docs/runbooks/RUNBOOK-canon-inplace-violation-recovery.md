# Runbook: Canon-Inplace Violation Recovery

> **Doc ID:** RUNBOOK-canon-inplace-violation-recovery
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Runbook
> **Severity:** P3
> **Status:** Current

---

## When This Fires

A commit has body-edited a canon-frozen doc (Status ∈ `{Approved, Implemented, Verified, Fix Applied, Current}`) beyond the LLD-006-r4 narrow-change whitelist (`{Status, Iteration, Superseded by}`) AND the violation has landed in git history (committed locally OR pushed). LLD-006-r4 § narrow change requires supersession workflow for canon-frozen body edits; this runbook is the recovery procedure.

Typical tells:
- `git log --oneline` shows `fix:` or `docs:` commit modifying a doc whose Status field reads canon-frozen
- `git diff HEAD~N..HEAD docs/<type>/<doc>.md` shows changes outside whitelist (frontmatter Status/Iteration/Superseded by) AND outside append-only Changelog rows
- User observation surfaces "did you follow the archive workflow?" mid-session
- `cli.lint --pre-commit` would have rejected (but ran post-hoc against an already-committed change)

---

## Quick Reference

**Revert violating commits → archive prior canon (Status: Rejected) → create supersession `-rN.md` with patches → rewrite affected attestations via `cli.lifecycle update-attestation-paths` → re-attest new file → single `feat:` commit. Refs: <new-supersession-path>.**

---

## Diagnosis

### Step 1 — confirm violation scope

```bash
# Identify the violating commit(s) and affected file
git log --oneline --name-only <suspect-commit>..HEAD | grep '\.md$' | sort -u

# For each .md file, check Status at HEAD~1 (pre-violation state)
for f in docs/features/X.md docs/bugs/Y.md; do
  git show HEAD~1:$f | grep -E '^> \*\*Status' || echo "no Status field in $f"
done

# Confirm Status ∈ canon-frozen at HEAD~1
# Canon-frozen statuses: Approved, Implemented, Verified, Fix Applied, Current
```

Capture: list of (commit-SHA, file-path, prior-Status) tuples. These are the violations to remediate.

### Step 2 — assess body-change scope

```bash
# For each (commit, file), inspect diff. Anything outside whitelist?
git diff HEAD~1 <commit-SHA> -- <file-path>
```

Whitelist edits are: `Status:`, `Iteration:`, `Superseded by:` frontmatter fields, and append-only Changelog rows (existing rows byte-identical, only new rows added). Anything else — section headings changed, paragraphs modified, code snippets edited, Acceptance items reworded — is a violation.

### Step 3 — confirm no upstream contamination

```bash
git log <upstream-branch>..HEAD --oneline -- <file-path>
```

If output is empty: violations are local-only. Revert is clean.
If output shows commits already pushed: STOP. Do NOT force-push to overwrite. Surface to user; remediation requires upstream coordination (forward-fix via supersession is safer than rewriting public history).

---

## Mitigation

### Step 4 — revert violating commits

Single combined revert (preserves chronology, single revert commit in history):

```bash
git revert --no-commit <newest-violation-SHA> [<older-violation-SHA>...]
git status --short
git diff --cached --stat   # confirm reverted scope
git commit -m "revert: undo canon-inplace violations on <doc-path>"
```

The revert commit message MUST name each reverted SHA + reason. Example: see `68fd538` in orchestra git history.

### Step 5 — archive prior canon

```bash
# Move canon doc to archive with same path-tail
git mv docs/<type>/<doc>.md docs/archive/<type>/<doc>.md
```

Edit the archived file frontmatter (3 changes — all whitelist, narrow-change permitted):

```markdown
> **Status:** Rejected
> **Iteration:** <unchanged>
> **Reason:** <one line: what was found, why supersession needed; reference attestation path>
> **Superseded by:** docs/<type>/<doc>-r<N+1>.md
```

`<N+1>` is the new supersession-iteration number (max(canon ∪ archive iteration) + 1).

### Step 6 — create supersession file

```bash
cp docs/archive/<type>/<doc>.md docs/<type>/<doc>-r<N+1>.md
```

Edit the new file frontmatter:

```markdown
> **Status:** Draft       # full edit allowed during supersession-iteration
> **Iteration:** <N+1>
> **Supersedes:** docs/archive/<type>/<doc>.md
```

(Remove `Reason:` field if copied — that belongs only on the archived rejected doc.)

Apply the original substantive changes (the patches that prompted supersession) to the new file. Status: Draft permits full edit per LLD-006-r4 narrow-change rule (only canon-frozen statuses are restricted).

### Step 7 — rewrite affected attestations

Prior attestations of the canon doc reference its pre-archive path. cli.lint L3 rejects attestations whose `doc_subject.path` does not resolve to a real file. Rewrite per attestation:

```bash
# Loop over each affected attestation. CLI takes one --reviews path per call.
for f in docs/reviews/<doc-id>-r1.review.yaml \
         docs/reviews/<doc-id>-r2.review.yaml ; do
  python -m cli.lifecycle update-attestation-paths --reviews "$f"
done
# (Add additional .review.yaml lines to the for-loop list as needed.)
```

Each invocation rewrites `doc_subject.path` from `docs/<type>/<doc>.md` → `docs/archive/<type>/<doc>.md`. Idempotent.

### Step 8 — re-attest new supersession file

Run `/orchestra:spec-review docs/<type>/<doc>-r<N+1>.md`. The skill produces a new attestation YAML at `docs/reviews/<doc-id>-r<N+1>.review.yaml`. Verdict ≥ conditional_pass to proceed; verdict=fail → iterate via narrow-change appends until conditional_pass or another supersession round (rare).

After re-attestation passes, flip new supersession file Status: `Draft → Implemented` (whitelist edit; narrow-change permitted).

### Step 9 — single feat: commit

```bash
git add -A
git commit -m "feat: ship <version> via LLD-006-r4 supersession workflow

[describe the supersession + what patches were applied]

Refs: docs/<type>/<doc>-r<N+1>.md"
```

Example: see `2ce394a` in orchestra git history.

---

## Verification

Before considering recovery complete, all 5 must hold:

- [ ] `git log --oneline -10` shows: original violation commit(s) → revert commit → supersession feat: commit (in this order)
- [ ] `python -m cli.lint --attestations` exits 0 (no broken `doc_subject.path` references)
- [ ] Archived doc Status: Rejected with Reason + Superseded by fields populated
- [ ] New supersession file Status: Implemented (post re-attestation) with Supersedes link to archive path
- [ ] Latest attestation file at `docs/reviews/<doc-id>-r<N+1>.review.yaml` exists; `overall_verdict ∈ {pass, conditional_pass}`

If any item false → STOP. Do NOT proceed to push or further work. Surface to user.

---

## Escalation

- **Tooling DRI** — orchestra plugin DRI (Hassan Mohiddin) for L2-not-in-lint_commit gap and pre-commit-hook-not-installed gap (tracked: BUG-009, BUG-010 per POSTMORTEM-2026-05-10-canon-inplace-violation Action Items)
- **Upstream contamination case** (Step 3 detected pushed commits) — surface to user before any history-rewriting action; do NOT `git push --force` automatically
- **Multiple-doc violation in single session** — file or update POSTMORTEM-session-process-drift; pattern is durable (see Background § same-session recurrence note)

---

## Background

LLD-006-r4 (orchestra v1.5.0) shipped archive + supersession conventions. § narrow change forbids canon-frozen body edits — supersession is the only sanctioned path. Three enforcement layers exist:

1. **L2 lint** (`cli/lint.py:490-521` — `lint_commit_no_canon_inplace_edit` function body) — fires inside `lint_staged()` (`cli/lint.py:705-728`, line 728 is the L2 call site)
2. **Pre-commit hook** — installed via `python -m cli.install_hooks --pre-commit --repo <path>`, invokes `lint_staged()` before commit lands
3. **Interview Gate** (orchestra v1.5.1) — agent rule "before commit modifying canon-frozen doc, ASK"

Session 2026-05-10 demonstrated all three layers can fail simultaneously: orchestra repo never installed its own hook, `cli.lint --commit` (`cli/lint.py:668-682`) does not include L2, and agent self-check missed Interview Gate trigger during dogfood action loop. Outcome: two canon-inplace commits (`653db4e` v1.6.1 + `bc359e7` r5) landed locally; user observation caught violation within 25 min; this runbook documents the recovery procedure used in `2ce394a`.

Same-session recurrence: this was the SECOND canon-discipline failure in the same session (after v1.4 cargo-cult rollback per POSTMORTEM-2026-05-07). Pattern is durable; tooling gaps must close (BUG-009, BUG-010) AND agent rule discipline must improve (POSTMORTEM-session-process-drift consolidation).

---

## Related Documents

- `docs/postmortems/POSTMORTEM-2026-05-10-canon-inplace-violation.md` — incident postmortem; this runbook distilled from its Action Items
- `docs/postmortems/POSTMORTEM-2026-05-07-v1.4-cargo-cult-rollback.md` — prior canon-discipline incident
- `docs/features/006-archive-and-supersession-conventions-r4.md` — LLD-006-r4 § narrow change (the rule this runbook recovers from violation of)
- `cli/lint.py:490-521` — L2 implementation function body (`lint_commit_no_canon_inplace_edit`)
- `cli/lint.py:668-682` — `lint_commit()` (the gap — does NOT include L2)
- `cli/lint.py:705-728` — `lint_staged()` (the pre-commit path — DOES include L2 at line 728)
- `cli/lifecycle.py` — `update_attestation_paths()` function; invoked from CLI in Step 7 as `python -m cli.lifecycle update-attestation-paths --reviews <yaml-path>` (CLI subcommand verified at `cli/lint.py:774` for `--attestations` flag — checked in Verification Step 2)
- Reference recovery: orchestra git history `68fd538` (revert) + `2ce394a` (supersession ship)

---

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Runbook written + spec-reviewed in single uncommitted working-tree session. Initial draft opened at Status: Current (file is new — no prior canon to violate per L2 implementation `try: git show HEAD:path; except: continue`). r1 spec-review (verdict: conditional_pass; 4 findings: 1 Important / 3 Minor) addressed in same working tree before commit: line-range citation reconciled to 490-521 (function body) in both Background and Related Documents (was inconsistent 486-521 vs 490-521); Step 7 bash loop literal `...` replaced with valid syntax + explanatory comment; cli.lifecycle CLI-vs-helper framing tightened in Related Documents with explicit `python -m cli.lifecycle update-attestation-paths` invocation form; `--attestations` flag verified present at `cli/lint.py:774`. Captures the 9-step procedure used in `2ce394a` to remediate two canon-inplace commits via revert + archive + supersession + attestation-path-rewrite + re-attest + single feat-commit. P3 severity. Status: Current. |
| 2026-05-11 | orchestra v1.7.0 (LLD-009 r6) ships BUG-011 tiered narrow-change rule. Supersession remains the canonical recovery path for Critical findings; this 9-step procedure applies as-written. For non-Critical findings (Minor any-count, Important ≤3), tiered narrow-change may now substitute supersession via `Addresses: docs/reviews/<doc-id>-rN.review.yaml gate <gate> finding <N> (Minor\|Important)` commit-msg lines + per-finding Changelog rows. Mechanical enforcement: `cli.lint --commit-msg-finalize` at commit-msg hook fire. Author pre-flight: `cli.lint --pre-stage-check <doc> --commit-msg-draft "<msg>"`. Full decision tree at `skills/commit/references/supersession-decision.md`. Status remains Current. |
