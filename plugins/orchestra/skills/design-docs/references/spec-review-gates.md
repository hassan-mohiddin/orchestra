# Spec Review — Four Gates

A doc passes spec review when all four gates pass. Pattern adapted from `rvdbreemen/adr-kit`. Gates are named so feedback can be specific ("Gate 2 fails — root cause has no file:line citation") rather than vague ("doc needs work").

## Gate 1 — Completeness

All required sections per `docs/STANDARDS.md` are present and filled. No `TBD`, no `[fill in]`, no empty tables.

**Per doc type — required sections:**
- **Feature LLD:** Problem / Success Criteria / Scope / Design + Diagram / API / DB / Edge Cases / Security / Testing / Related Docs / Changelog
- **Bug Report:** Observed / Expected / Reproduce / Environment / Root Cause + Diagram / Fix / **Iteration Log** / Regression / Related / Changelog
- **ADR:** Context / Decision / Consequences / Alternatives Briefly Rejected / Related / Changelog
- **Postmortem:** Summary / Impact / Timeline / Root Cause / What Went Well / Wrong / **Where We Got Lucky** / Action Items / Lessons / Related / Changelog
- **Runbook:** When Fires / Quick Reference / Diagnosis / Mitigation / Verification / Escalation / Related / Changelog
- **Design Doc:** Overview / 3+ Diagrams / Domain Details / Key Decisions (ADR links) / Changelog

**Failure example:** "Bug Report has no Iteration Log section" → Gate 1 fails.

## Gate 2 — Evidence

Every claim has a backing artifact. No vibes, no "should work", no "I think".

**What to check:**
- Root cause cites specific files + line numbers (`apps/api/auth.py:42`)
- Success criteria are measurable (numbers, thresholds, checkboxes — not adjectives)
- Test names are exact function paths (`tests/test_auth.py::test_token_expiry_boundary`)
- Performance claims have benchmark links / numbers
- ADR Context section cites the constraint or signal (incident, deadline, regulation, cost)
- Postmortem timeline has real timestamps from logs / pagers
- Runbook commands are exact, not pseudo-code

**Failure example:** "Root Cause says 'race condition somewhere in worker pool' with no file or trace" → Gate 2 fails.

## Gate 3 — Clarity

A reader who hasn't seen the conversation can act on the doc. No insider shorthand, no dangling references, no ambiguous pronouns.

**What to check:**
- Acronyms expanded on first use
- Diagrams have descriptive labels ("Auth Service (JWT)" not "Service A")
- "It" / "this" / "that" have clear antecedents
- Code snippets are runnable — no `<placeholder>` left unfilled
- Decision section in ADR is one declarative sentence (not hedged with "we should consider")
- Mitigation in Runbook is imperative + 3am-friendly (action, then explanation — not the reverse)

**Failure example:** "Decision section says 'We will probably go with Postgres for now' " → Gate 3 fails (hedged).

## Gate 4 — Consistency

Doc agrees with itself, with peer docs, and with code.

**What to check:**
- Status field matches lifecycle (no "In Progress" status without deviation entry)
- Diagram service / table names match the prose
- Refs to other docs point to real files (no dangling `docs/adr/ADR-999`)
- Code-citing claims are still true at HEAD (file at line still exists)
- ADR superseded chain is bidirectional (old ADR has `Superseded by:`, new ADR has `Supersedes:`)
- Design Doc updates have changelog entries, not silent edits

**Failure example:** "LLD shows POST /api/v2/transactions but the API Changes table says /api/v1/" → Gate 4 fails.

## Gate sequence

Run gates in order. If Gate 1 fails, fix before checking Gate 2 — incompleteness invalidates the others. If Gate 4 fails on bidirectional ADR refs, fix the peer doc too.

Max 3 review iterations. If still failing after 3, escalate to user — the doc may have a deeper problem that needs design rework, not editing.

## How this maps to the skill flow

The `design-docs` SKILL.md "Step 4.5: Spec Review" step says to invoke the review skill bound in `.claude/skills-registry.md`. The review skill should evaluate against these four gates, naming each in its feedback. Project-internal SCALE setup binds spec-review to `superpowers:requesting-code-review` — that skill should be parameterized with this gates reference.

## Why four gates, not more, not fewer

- Fewer (e.g., one "looks good" gate) → vague feedback, no actionable failures
- More (e.g., 8 gates with subtle distinctions) → review fatigue, gates blur into each other
- Four maps to the actual failure modes seen in practice: missing sections, unsupported claims, unclear writing, contradictions
