# 4-Gate Rubric — Spec Review Pass/Fail Criteria

Per-gate verdict ∈ `{pass, conditional_pass, fail}`. Overall verdict = worst-case across gates (any `fail` → `fail`; else any `conditional_pass` → `conditional_pass`; else `pass`).

## Gate 1 — Completeness

**Pass:** All required sections for the doc type are present and filled. No empty placeholders. Header metadata block populated (Doc ID, Date, DRI, Type, Status, Iteration).

**Conditional pass:** All required sections present; one or more contain only stub-level content but author has flagged TBD with tracked followup.

**Fail:** Required section(s) missing. OR present but empty / lorem-ipsum / "TODO" without followup ref. OR Iteration field absent.

### Required sections by doc type

| Doc type | Required sections |
|---|---|
| Feature LLD | Header, Glossary (if novel terms), Problem Statement, Success Criteria (Acceptance items + Deliverables), Scope (In/Out), Design, Edge Cases, Security, Testing, Related Documents, Changelog |
| Bug Report | Header, Symptom, Root Cause, Reproduction, Fix Design, Test Plan, Risk, Changelog |
| ADR | Header, Context, Decision, Consequences (Positive/Negative), Alternatives Considered (recorded, not deliberated), Changelog |
| Postmortem | Header (incl. Severity), Summary, Impact, Timeline, Root Cause, What Went Well, What Went Wrong, Where We Got Lucky, Action Items, Lessons Learned, Related Documents, Changelog |
| Runbook | Header (incl. Severity), When This Fires, Quick Reference, Diagnosis, Mitigation, Verification, Escalation, Background, Related Documents, Changelog |
| Design Doc | Header, Overview, Architecture, Interfaces, Invariants, Failure Modes, Changelog |
| Plan | Header (incl. LLD reference), File Structure, Tasks, Dependencies, Sequencing rule, Estimated time, Changelog |

## Gate 2 — Evidence

**Pass:** Every claim has a citation: `file:line` reference, benchmark URL, external research link, or runtime-output excerpt. Architectural decisions cite the constraint that drives them.

**Conditional pass:** Most claims cited; 1-2 unsupported assertions remain but are non-load-bearing.

**Fail:** Load-bearing claim made without evidence. "Should work" / "we believe" / "industry standard" without citation. Fabricated references (citations to papers/docs that don't exist or don't say what is claimed).

### Examples of acceptable evidence

- `apps/api/main.py:42` — points to specific code
- `https://arxiv.org/abs/2410.21819` — verifiable external research
- `$ pytest tests/ → 107 passed` — runtime output excerpt
- `LLD-006-r4 § Glossary` — peer doc cross-reference

### Examples of unacceptable

- "This pattern is widely used" — no citation
- "The standard approach is X" — no citation
- "Industry research shows Y" — citation needed
- Fabricated file path or arXiv ID

## Gate 3 — Clarity

**Pass:** A fresh reader (no session history, no DM access to author) can act on the doc. Glossary defines novel/ambiguous terms. Diagrams render. Code blocks are language-tagged. Decisions stated declaratively, not deliberatively (esp. ADRs).

**Conditional pass:** Doc is mostly clear; 1-2 sections require re-reading or peer-doc lookup that could be inlined.

**Fail:** Reader cannot determine what to build / fix / decide from the doc alone. Critical term used without definition. Pronouns with ambiguous antecedents in load-bearing sentences. Mermaid syntax broken. Decisions framed as options without commitment ("we could X, or alternatively Y" — P3 violation).

## Gate 4 — Consistency

**Pass:** Doc agrees with itself (no contradiction across sections). Doc agrees with peer docs cited (cross-refs resolve correctly). Doc agrees with code (acceptance items match real test names; file paths exist). Status field matches actual lifecycle stage.

**Conditional pass:** Minor self-contradictions on non-load-bearing details; cross-refs broken on archived docs (acceptable if supersession recorded).

**Fail:** Self-contradiction in load-bearing claim (e.g., spec says X in Design; Tests verify ¬X). Cross-ref to a doc that does not exist or has been superseded without supersession marker. Acceptance item maps to a test that doesn't exist. File path cited that does not resolve.

## Severity calibration

| Severity | Use when |
|---|---|
| **Critical** | Fact wrong, contract broken, security gap, fabricated reference, or doc would mislead any reader following it. Reader writes wrong code / makes wrong decision. |
| **Important** | Omission, ambiguity, or stale reference that a reader could reasonably misinterpret. Reader pauses to ask author. |
| **Minor** | Small inconsistency, missing detail, undocumented edge case. Reader proceeds with mild concern but builds the right thing. |

## Anti-patterns (NEVER report)

- Formatting nits (line length, blank-line count) unless they break rendering
- Style preferences without correctness reason
- "Could be more concise" — clarity ≠ brevity
- Suggestions to add features / scope / sections not required by doc type
- Praise / encouragement / "this is well-written" — anti-sycophancy
- Findings without parsable `location` (regex `^(.+\s+§\s+.+|line\s+\d+)$`)

## Empty-findings discipline

If a gate has zero findings, the gate's `justification` field MUST contain ≥10 chars stating WHY no findings exist (e.g., "All 11 required postmortem sections present and filled with concrete content"). Schema rejects empty `findings: []` without justification (anti-sycophancy enforcement).
