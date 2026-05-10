# Runbook: Iteration Plateau Detection (Spec-Review Loop)

> **Doc ID:** RUNBOOK-iteration-plateau-detection
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Runbook
> **Severity:** P3
> **Status:** Current

---

## 1. When This Fires

This runbook is the **recovery procedure** that runs AFTER an Interview Gate plateau trigger has fired. The trigger logic itself is canonical in:

- `cli/templates/standards-default-7.md` § Interview Gate (orchestra-side, scaffolded into consumer projects via `cli.init`) — see template's "iteration plateau" trigger condition
- `skills/design-docs/SKILL.md` § Interview Gate (orchestra-side embed)

This runbook does NOT redefine trigger conditions; that would create policy drift. **The trigger has already fired by the time this runbook is opened.** If you arrived here without the canonical trigger having fired, return to the canonical Interview Gate definition first.

**Symptom that brought you here:** spec-review iteration on a doc has hit the canonical Interview Gate plateau condition (3+ rounds, findings overlapping or non-decreasing).

---

## 2. Quick Reference

**STOP iteration. Compute overlap signature on last two rounds. Surface to user with options (a/b/c). Wait.**

---

## 3. Diagnosis

Run all three checks before declaring plateau. Two-of-three positive = plateau confirmed.

### Step 1 — Deterministic overlap signature

Each finding has a deterministic signature: `<gate>::<normalized-location>::<normalized-issue-key>` where:
- `gate` ∈ {completeness, evidence, clarity, consistency} (from attestation YAML)
- `normalized-location` = lowercase + collapse whitespace + strip trailing punctuation from `findings[].location` (e.g., `"Design § cli.spec_review module (lines 398-403)"` → `"design § cli.spec_review module"` — line numbers stripped because they shift across rounds)
- `normalized-issue-key` = first 3 content words of `findings[].problem` lowercased + dehyphenated (e.g., `"Path traversal mitigation claimed but..."` → `"path traversal mitigation"`)

Compute signatures for round N and round N+1 from `docs/reviews/<doc-id>-rN.review.yaml`:

```bash
ATTESTATION_N="docs/reviews/<doc-id>-r<N>.review.yaml"
ATTESTATION_NPLUS1="docs/reviews/<doc-id>-r<N+1>.review.yaml"
.venv/bin/python -m cli.spec_review_overlap "$ATTESTATION_N" "$ATTESTATION_NPLUS1"
```

(Helper TBD per LLD-007 v1.6.x followup; until then, compute signatures by hand using the rules above.)

**Overlap threshold:** ≥2 findings share signature across N and N+1 → plateau signal positive.

### Step 2 — Per-gate count trajectory

For each spec-review gate, count findings per round across all rounds run so far. Plot the trajectory:

- **Strictly decreasing** (e.g., 25 → 18 → 11) → healthy convergence
- **Flat** (e.g., 12 → 12 → 11) → plateau signal positive
- **Oscillating** (e.g., 12 → 10 → 11 → 9, the LLD-006 pattern) → plateau signal positive

### Step 3 — Severity profile

Tally Critical / High / Medium / Low across rounds:

- Critical going to 0 and Highs reducing → healthy
- Severity distribution **stable** across rounds → plateau signal positive
- Severity **worsening** (new Criticals appearing late) → plateau signal positive, escalate urgency

### Decision

If 2 of 3 above suggest plateau → diagnose **context drift**. Author is fixing surface symptoms flagged by the reviewer without addressing the underlying structural problem; reviewer keeps catching the same root issue in different forms.

**Do NOT silently iterate to round N+2.** Move to Mitigation.

---

## 4. Mitigation

Apply in safety order. Do not skip steps.

1. **STOP iteration.** No round N+2 dispatched until user has chosen a path.

2. **Surface to user via Interview Gate** (canonical in orchestra: `cli/templates/standards-default-7.md` § Interview Gate + `skills/design-docs/SKILL.md` § Interview Gate; the SCALE consumer ships these via the auto-loaded `.claude/rules/interview-gate.md` generated from the orchestra template). Use this script verbatim, filling in N and the observed pattern:

   > "After {N} rounds, findings overlap and are non-decreasing. Suspect context drift. Options:
   > (a) restart with smaller scope,
   > (b) confirm direction explicitly and apply pre-dispatch checklist,
   > (c) supersede with r{N+1} fresh draft."

3. **Wait for user direction.** No autonomous choice between (a) / (b) / (c).

4. **If user picks (a) — smaller scope:** break the LLD into smaller LLDs. Precedent: LLD-006 was decomposed from atomic-5-pillar to single-concern after r2 fail. The smaller LLDs each go through their own review cycle.

5. **If user picks (b) — confirm direction + pre-dispatch checklist:** before dispatching the next round, re-read the original requirements and walk the P1-P9 pre-dispatch checklist from `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` § Pre-Dispatch Pattern Checklist. Document checklist results in the doc changelog.

6. **If user picks (c) — supersede:** mark current draft Rejected, start r{N+1} as a fresh draft with `Supersedes: <prior-rN-path>` link per `docs/features/006-archive-and-supersession-conventions-r4.md`. Do not patch the rejected draft.

---

## 5. Verification

After the chosen path produces the next review round, confirm recovery:

- **No-overlap check:** the new round's findings have **zero or near-zero** overlap with the last two pre-recovery rounds (different sections, different problem classes).
- **Count drop:** findings count drops materially. Threshold: **>30% reduction** vs. the last pre-recovery round.
- **Severity improvement:** Critical → 0; total Highs reduced.

If all three hold → plateau resolved, normal iteration resumes.
If any fail → return to Diagnosis. Plateau may have shifted shape rather than resolved.

---

## 6. Escalation

If plateau persists across **5+ rounds** even after smaller scope or supersession:

### 1. Different-model judge — concrete invocation

If prior rounds used Opus-on-Opus (default orchestra:spec-review with main-agent-as-author), route next round to gpt-5-codex via codex companion script. Same-model self-preference bias (arXiv 2410.21819) may be holding the plateau.

```bash
# From target repo root
cd "$(git rev-parse --show-toplevel)"

# Verify target file resolves
ls docs/features/<id>-name.md

# Dispatch codex adversarial review (different model)
node "/Users/mohammedhassanmohiddin/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs" \
  adversarial-review "docs/features/<id>-name.md" \
  "[optional focus text — paste prior plateau-round findings + ask reviewer to look for what was missed]"

# Output is captured in chat / terminal. To save:
node ... adversarial-review ... > /tmp/codex-r<N+1>.txt 2>&1
```

After codex returns:
- Convert findings to orchestra v1.0 attestation YAML (manual until orchestra:spec-review ships); save at `docs/reviews/<doc-id>-r<N+1>.review.yaml` with `reviewer.identifier: "codex:adversarial-review+gpt-5-codex"`
- Compare overlap signature (Diagnosis Step 1) against last Opus round — if signatures differ, different-model bias was the cause; iterate

### 2. Human review of foundational assumptions

If different-model judge still produces overlapping plateau findings:

- Escalate to human review of the **problem statement** (not design). No amount of review iteration recovers from a flawed premise.
- File `docs/bugs/BUG-NNN-<doc-id>-foundational-rethink.md` capturing the plateau pattern + plateau attestations + recommendation to either rescope or archive.
- Do NOT continue iterating beyond round 5 without explicit user confirmation that the foundation is sound.

### 3. Last resort

If both routes are exhausted → archive the doc unimplemented (`Status: Rejected`, `Reason: foundational rethink required`) and reopen the upstream brainstorm at `docs/investigations/<date>-<topic>.md`.

---

## 7. Background

Pattern formalized in `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` § Pre-Dispatch Pattern Checklist (P1-P9). The pre-dispatch checklist applies to **LLD authors before subagent dispatch** to catch issues early. **This runbook applies after N reviews when plateau is detected**, to catch context drift across rounds. Roles are complementary: pre-dispatch is prevention; iteration-plateau is recovery.

**Real examples that surfaced the pattern:**

- **LLD-005:** went r1 → r2 with findings 25 → 23 (only 2 fewer; both Rejected). Insufficient progress; eventually resolved by scope decomposition.
- **LLD-006:** went r1 → r2 → r3 → r4 with findings 12 → 10 → 11 → 9 (oscillating, Evidence-pass plateau). After r3 fail, r4 was written with explicit pre-dispatch P1-P9 checklist applied — converged to conditional_pass.

**Relationship to canonical Interview Gate (orchestra-side):** `cli/templates/standards-default-7.md` § Interview Gate + `skills/design-docs/SKILL.md` § Interview Gate codify the iteration plateau heuristic as one of seven Interview Gate trigger conditions. The SCALE consumer ships these via auto-loaded `.claude/rules/interview-gate.md` generated from the orchestra template at `cli.init` time. **The rule (orchestra template) says STOP.** **This runbook says HOW to figure out + decide next step.** Single source of truth for trigger logic = orchestra template; runbook is strictly post-trigger procedure.

---

## 8. Related Documents

- `cli/templates/standards-default-7.md` § Interview Gate (orchestra-side, canonical) — defines plateau as one of seven Interview Gate trigger conditions; this runbook applies AFTER the trigger fires
- `skills/design-docs/SKILL.md` § Interview Gate (orchestra-side, canonical) — same Interview Gate philosophy embedded for the design-docs skill
- SCALE consumer auto-loaded copy at `<scale-repo>/.claude/rules/interview-gate.md` — generated from the orchestra template at `cli.init` time; do NOT reference cross-repo paths from orchestra docs (the orchestra template is the source of truth)
- `docs/features/006-archive-and-supersession-conventions-r4.md` — supersession workflow (used when path (c) chosen)
- `docs/features/007-spec-review-architecture.md` — multi-judge architecture (escalation to different-model judge)
- `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` — Pre-dispatch checklist (P1-P9) and LLD-005/006 plateau examples
- `docs/postmortems/POSTMORTEM-2026-05-07-v1.4-cargo-cult-rollback.md` — original incident that surfaced this pattern

---

## 9. Changelog

| Date | Entry |
|---|---|
| 2026-05-10 | Initial runbook drafted after observing plateau pattern in LLD-005 (4 iterations) + LLD-006 (4 iterations); converged on r4 of each via pre-dispatch checklist + scope decomposition. Status: Current. |
| 2026-05-10 | Codex round 1 review (verdict: needs-attention; 4 findings). All 4 addressed inline: IP1 (High) cross-repo path reference (`.claude/rules/interview-gate.md` is SCALE-side, not orchestra-side) — replaced with orchestra-canonical paths (`cli/templates/standards-default-7.md` § Interview Gate + `skills/design-docs/SKILL.md` § Interview Gate); IP2 (High) trigger-vs-procedure drift — § 1 rewritten to strict post-trigger framing, no local trigger redefinition; IP3 (Medium) subjective overlap criteria — replaced with deterministic signature `<gate>::<normalized-location>::<normalized-issue-key>`; IP4 (Medium) escalation referenced multi-judge architecture without invocation path — added concrete codex-companion command + attestation path. Status: Current (post-r1 fixes). |
