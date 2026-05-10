# Runbook: Spec-Review Bootstrap Mismatch

> **Doc ID:** RUNBOOK-spec-review-bootstrap-mismatch
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Runbook
> **Severity:** P3
> **Status:** Current

---

## When This Fires

Running `/codex:adversarial-review <target-doc>` returns a review that discusses an **unexpected branch, repo, or set of files** — content unrelated to the doc you asked it to review.

Typical tells:
- "Target:" line in codex output names a path or branch you did not request
- Findings cite source files from a different project (e.g. `apps/api/...` when you targeted an orchestra LLD)
- Findings reference a feature branch (e.g. `feature/prediction-engine-v1`) instead of the target doc

---

## Quick Reference

**Codex `Target:` line shows wrong repo? STOP. `cd` into target repo root and re-run.** (full procedure: see Diagnosis + Mitigation)

---

## Diagnosis

1. **Inspect the codex output header.** Save invocation output and grep target metadata:
   ```bash
   # Capture the most recent codex output to a file
   /codex:status > /tmp/codex-last.txt 2>&1 || true   # or copy from terminal scrollback
   # Extract target/repo/branch lines:
   grep -E '^(Target|Repo|Branch):' /tmp/codex-last.txt
   ```
   Expected: `Target:` line references the doc path you passed; `Repo:`/`Branch:` (if present) matches target repo.
   Actual on mismatch: shows a different repo root or a branch name from another project (e.g., `feature/prediction-engine-v1` when reviewing an orchestra doc).

2. **Check current shell cwd at time of invocation.**
   ```bash
   pwd
   ```
   Expected: target repo root (e.g. `.../orchestra`).
   Actual on mismatch: a sibling repo root (e.g. `.../SCALE APP`).

3. **Resolve the path argument from current cwd.**
   ```bash
   ls <path-you-passed-to-codex>
   ```
   Expected: file exists.
   Actual on mismatch: `No such file or directory` — codex silently fell back to "branch diff against main" of the cwd repo.

4. **Confirm cwd's git repo.**
   ```bash
   git rev-parse --show-toplevel
   git rev-parse --abbrev-ref HEAD
   ```
   Expected: target repo root + an expected branch.
   Actual on mismatch: a different repo + that repo's current branch (which is what codex actually reviewed).

If any of steps 1–4 confirm mismatch → mitigate. Do not interpret the off-target findings.

---

## Mitigation

Steps in safety order:

1. **Stop acting on the off-target review.** Findings reference the wrong repo; treat them as invalid for the intended target.

2. **Move shell into target repo root.**
   ```bash
   cd "$(git -C <target-repo-path> rev-parse --show-toplevel)"
   ```

3. **Verify environment.**
   ```bash
   git status                         # expected branch, clean or expected dirty state
   ls <target-doc-relative-path>      # file resolves
   ```

4. **Re-run the review with the same path argument.**
   ```bash
   /codex:adversarial-review <target-doc-relative-path>
   ```

---

## Verification

All checkboxes must be checked before treating the re-run as on-target. Do NOT proceed unless all four pass:

- [ ] Codex output's `Target:` line references the intended doc path (e.g. `docs/features/007-spec-review-architecture.md`)
- [ ] First 3+ findings discuss content found IN that doc (open the doc, grep for keywords cited in findings)
- [ ] No mention of unrelated branches (e.g. no `feature/prediction-engine-v1` references when reviewing an orchestra doc)
- [ ] `pwd` at re-run time matches `git rev-parse --show-toplevel` of the target repo (not a sibling)

**Pass gate: 4 of 4 checked → on-target. < 4 → return to Diagnosis or Escalate.**

---

## Escalation

If cwd is verified correct (steps 2–4 of Diagnosis all pass) but codex still produces an off-target review:

**Required artifact bundle for escalation:**
1. Both invocations' transcripts (off-target + on-target attempt)
2. `pwd` output at time of each invocation
3. `git rev-parse --show-toplevel` + `git rev-parse --abbrev-ref HEAD` outputs
4. Exact slash-command line used (verbatim)

**Escalation routing (role-based; never person-named):**
- **Primary:** orchestra plugin DRI (current: doc DRI in this runbook's metadata block). Open issue at `docs/bugs/BUG-NNN-codex-companion-cwd-validation.md` with the artifact bundle attached.
- **Fallback:** if primary unavailable >24h, file upstream issue at the codex plugin source: https://github.com/openai/codex (or wherever the codex-companion.mjs script is maintained). Reference orchestra repo + this runbook + artifact bundle.
- **Channel:** in-repo BUG-NNN doc is the durable record. Avoid ephemeral channels (chat) for escalation — they don't survive context resets.

Do not retry blindly more than once after a verified-cwd failure. Escalation gates further attempts.

---

## Background

Two repos coexist on the developer machine: `orchestra` (orchestra-dev workspace) and `SCALE APP` (consumer of orchestra). Slash commands run in the current shell cwd. The codex companion script (`codex-companion.mjs`) operates relative to that cwd; when the path argument does not resolve under cwd, codex falls back to reviewing the **branch diff against main** of whatever repo cwd points at — silently, without warning.

This footgun was caught during orchestra v1.5/v1.6 dogfooding on 2026-05-10: a review of orchestra LLD-007 was attempted with cwd = SCALE app dir. Codex produced a review of SCALE's `feature/prediction-engine-v1` branch (forecasting domain, prediction evaluation code) instead of the LLD. Wasted ~3 min of codex compute. Detection was manual: the human reader noticed findings referenced files unrelated to the requested target.

There is currently no preflight that validates `path-arg ⊂ cwd-repo` before invoking codex. Until that lands, this runbook is the mitigation.

---

## Related Documents

- `docs/postmortems/POSTMORTEM-2026-05-07-v1.4-cargo-cult-rollback.md` — codex review introduced as v1.4-rollback redesign (context for why codex is in the spec-review path)
- `docs/features/007-spec-review-architecture.md` — LLD defining `orchestra:spec-review`; this runbook applies to codex as the judge-2 alternative
- Codex companion script: `~/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs`

---

## Changelog

| Date | Entry |
|---|---|
| 2026-05-10 | Initial runbook drafted after 2026-05-10 incident (orchestra LLD-007 review with wrong cwd → SCALE repo reviewed instead). Status: Current. |
| 2026-05-10 | Codex round 1 review (verdict: needs-attention; 4 findings). All 4 addressed inline: RB1-1 (High) escalation person-bound — replaced with role/channel-based routing (primary: orchestra plugin DRI + BUG-NNN doc; fallback: codex upstream issue tracker; durable channel: in-repo BUG doc); RB1-2 (Medium) Quick Reference multi-step block — replaced with single-line STOP+fix directive; RB1-3 (Medium) Diagnosis Step 1 placeholder comment — replaced with concrete capture commands (save invocation output + grep target metadata); RB1-4 (Medium) Verification not checkbox-gated — converted to `- [ ]` checkboxes with explicit pass gate (4 of 4 required). Status: Current (post-r1 fixes). |
