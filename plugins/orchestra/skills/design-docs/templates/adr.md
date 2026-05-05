# ADR-NNN: [Title]

> **Doc ID:** ADR-NNN-kebab-name
> **Date:** YYYY-MM-DD
> **DRI:** [Name — Directly Responsible Individual]
> **Status:** Draft | Proposed | Approved | Implemented | Superseded | Rejected
> **OKR Alignment:** [Which objective does this serve?]

ADRs RECORD a decision that has been made. They are not RFCs — they do not deliberate. If you find yourself writing a long "Options Considered" section weighing alternatives without a chosen direction, you wrote an RFC. Decide first (use brainstorm/grilling skills), then record here.

## Context

What situation forced this decision? What constraints, signals, or pressures led here? Cite specific evidence: load, cost, regulation, deadline, prior incident, capability gap.

This section is *background* — not deliberation. Keep to facts and forces, not options.

## Decision

State the decision directly. One sentence ideally. Then 1-3 short paragraphs of supporting detail.

> **We will [chosen approach].**

If the decision involves architecture or data flow, include a current → proposed diagram:

```mermaid
graph LR
    A[Current State] -->|Migration path| B[Decided Approach]
```

### Detailed shape (optional)

[Schema changes, API contracts, deployment topology — only what's load-bearing for the decision. Detail belongs in Feature LLDs, not here.]

## Consequences

What becomes easier? What becomes harder? What does this commit us to?

### Positive

- [What problem this solves; what new capability it enables]

### Negative

- [What flexibility we lose; what complexity we accept]

### Neutral / commitments

- [Migration cost; ongoing operational burden; coupling introduced]

## Alternatives Briefly Rejected

Two-sentence dismissals only. If alternatives need more than two sentences each, this is an RFC, not an ADR — go decide first.

| Option | Why rejected |
|--------|--------------|
| [Option A] | [One-line reason] |
| [Option B] | [One-line reason] |

## Related Documents

- Supersedes: [ADR-NNN if this replaces a prior decision]
- Superseded by: [ADR-NNN if a later decision replaced this one]
- Related: [Other ADRs, Feature LLDs, Design Docs that depend on this decision]

## Changelog

Append-only. Add an entry on each status transition. ADRs are immutable in spirit — if the decision changes, write a new ADR with `Supersedes: ADR-NNN` and set this one's status to `Superseded`.

| Date | Change |
|------|--------|
| YYYY-MM-DD | Initial draft — Status: Draft |
