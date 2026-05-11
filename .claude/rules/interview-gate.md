# Interview Gate

This rule is auto-loaded every session. It defines when Claude must STOP and ask
the user before proceeding silently with a decision.

The Interview Gate is the cheap, immediately-actionable half of "backward-flow
workflow." The heavy half (state-machine workflow + phase return + feedback-loop
primitives) is deferred to v2.0 (orchestra LLD-011+ per handoff). Interview Gate
ships standalone because it costs nothing to encode and prevents the failure
mode that produced BUG-008 (cargo-cult markers, silent design decisions).

---

## When to interview (any of these → STOP, ask)

1. **Low context** — not enough info to make the decision well; would have to
   guess at user intent.
2. **Ambiguous instruction** — multiple plausible readings; choice has
   non-trivial blast radius (>10 min of work to undo).
3. **Silent design decision** — about to commit to architecture/approach not
   stated in the user's instruction or the design doc.
4. **Ambiguous scope** — user said "fix X" but multiple things qualify as X.
5. **Pre-dispatch checklist hit** — P3 (OR / "alternatively" without commitment)
   or P8 ("improvise it" silently). See orchestra LLD-006-r4 brainstorm scratch
   for full P1-P9 list.
6. **Judgment call** — choice between two roughly equal options where blast
   radius > 10 min of work.
7. **Iteration plateau** — same review/test failing 3+ times with similar
   findings → context drift suspected; interview before iter 4.

## What to do when triggered

Use `AskUserQuestion` (preferred — structured) or chat-text question (when
nuance > 4 options). Format:

```
[1-sentence current state]
[1-sentence decision point]
[2-4 concrete options, one labeled (Recommended) with 1-line reason]
```

Then **stop and wait**. Do not keep working in the background. Do not
pre-implement the recommended option "to save time."

## What is NOT a trigger (proceed silently)

- Mechanical task execution: run tests, format file, rename variable per
  instruction.
- Single-step ops with obvious correct answer.
- User explicitly said "use your judgment" or "decide" or "your call."
- User in auto mode / minimize-interruptions mode — bias toward action; only
  interview when blast radius is large (irreversible / cross-file / changes
  user-visible behavior).
- Reading files / running greps / lookups — research, not decisions.

## Anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Asking permission for low-blast-radius task work | Wastes user time | Just do it; describe in 1 line after |
| Sequential ping-pong questions | Round-trip cost compounds | Batch into single `AskUserQuestion` (multiple questions param) |
| Generic "should I?" | Forces user to construct options | Be specific: "X or Y?" with each option spelled out |
| Building a long plan before interviewing | Sunk-cost bias on bad direction | Interview FIRST when low-context, not after 80% wasted work |
| Asking after deciding | Theater | Interview is for unknown direction, not approval-rubber-stamp |

## Examples

### GOOD — ambiguous scope

> User: "fix the bug"
> Me: "Three open BUGs match recent context: BUG-003 (mkdocs tags),
> BUG-006 (precommit framework), BUG-007 (mkdocs yaml validators). Which?"

### GOOD — judgment call with blast radius

> User: "ship it"
> Me: "Two paths: (a) push to origin/main, (b) cut release tag v1.5.0 then
> push tag (implies a). Recommend (b) — produces a referenceable release.
> Confirm?"

### BAD — silent design decision

> User: "add archive support"
> Me: [picks `docs/archive/<type>/` over `docs/<type>/archive/` silently;
> picks rejection-finalization edit semantics silently;
> ships 600-line LLD with 12 silent decisions baked in]

### BAD — over-asking

> User: "rename `foo` to `bar` everywhere"
> Me: "Should I use sed or grep+edit? Should I update tests? Should I
> commit after?" [user wanted: just do it]

## Relationship to other gates

- **Gate 1 (Discovery)** — when investigation surfaces a defect, Discovery
  fires immediately. Interview Gate fires only if scope/severity is unclear
  before BUG-NNN is filed.
- **Gate 2 (Design)** — Interview Gate fires when design ambiguity exceeds
  what the doc specifies; Gate 2 itself blocks code without a doc.
- **Gate 3 (Spec Review)** — independent. Spec review judges output;
  Interview Gate prevents silent input. Both must pass.
- **Gate 5 (Implementation Sync)** — Interview Gate fires if a deviation
  choice is non-obvious. Default: small deviation → record in Changelog;
  large deviation → interview before deviating.

## Iteration plateau heuristic

If the same review or test cycle is failing iteration N+1 with findings that
overlap N's findings, interview the user. Do not silently iterate to N+2.
Pattern observed: LLD-005 + LLD-006 needed 4 iterations each — symptom of
context drift / silent decisions accumulating. Interview at iter 3 → either
restart with smaller scope OR confirm direction with user explicitly.

## What this rule does NOT do

- Define backward-flow workflow primitives (return to earlier phase, loop a
  feedback iteration). Deferred to v2.0 — needs state-machine + persistence
  - hook plumbing. See orchestra roadmap, LLD-011+.
- Replace `.claude/rules/skills-routing.md`. Skills-routing handles
  situation → skill resolution; this rule handles decision-point detection.
- Override user instructions. Interview Gate triggers describe when to PAUSE,
  not what to OVERRIDE.

## Why this rule exists

BUG-008 root cause: silent decisions + compliance theater. Agent added
"Iteration N spec review — 4/4 gates pass" markers without running review.
Discovery: zero of the silent decisions had been validated with the user.
Fix: surface decisions before locking them in. This rule is the first
enforcement primitive.

The pre-dispatch pattern checklist (P1-P9) in orchestra brainstorm scratch
encodes the same discipline at the LLD-author level. Interview Gate extends
it to general agent behavior.
