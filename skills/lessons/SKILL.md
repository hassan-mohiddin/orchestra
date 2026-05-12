---
name: lessons
description: Use when capturing or surfacing learnings about agent behavior — runtime violations user observed (`/orchestra:violation --rule=<id> --observed=<X> --expected=<Y>`), free-text teach notes (`/orchestra:teach <text>`), or recurrence scans (`/orchestra:lessons-lint`). Lessons live in `docs/lessons/<YYYY-MM>-lessons.md` and feed the SessionStart + UserPromptSubmit hook injection layer (LLD-012 SC-3, SC-7, SC-11, SC-14).
---

# orchestra:lessons

## Purpose

Durable feedback-capture layer (LLD-012 §Learning Layer). User-observed agent
violations are recorded as structured YAML entries and re-injected via the
SessionStart + UserPromptSubmit hooks so the same violation does not recur
across sessions. Free-text "teach" notes are durable and lintable but never
injected into system-priority context (LLD-012 SC-11 allowlist).

## Slash commands

| Command | Purpose | Injected? |
|---|---|---|
| `/orchestra:teach <free-text>` | Fast lesson capture (kind=teach) | No (free-text never injected in v2.1) |
| `/orchestra:violation --rule=<id> --observed=<X> --expected=<Y>` | Structured violation capture | **Yes** — surfaces in `[ORCHESTRA TLDR]` block |
| `/orchestra:lessons-lint` | Scan ≥3× recurrence + write proxy artifact | n/a (writes to `docs/proposed-rule-mutations/`) |

Each command is declared via `commands/<name>.md` shim per existing orchestra
repo convention (matches `commands/spec-review.md` pattern). Claude Code's
dispatch reads `commands/<name>.md` files directly — this SKILL.md does NOT
use a frontmatter `commands:` list (LLD-012 SC-6).

## Entry schemas (per LLD-012 § Lessons skill)

### teach (kind=teach, inject=false)
```yaml
- id: <uuid>
  ts: <ISO-8601 UTC>
  kind: teach
  rule_violated: null
  body: "<free-text>"
  source: user
  inject: false   # explicit marker; hooks honor this
```

### violation (kind=violation, inject=true)
```yaml
- id: <uuid>
  ts: <ISO-8601 UTC>
  kind: violation
  rule_violated: <rule_id>     # validated against allowlist
  observed: "<X>"              # HTML-escaped, max 200 chars
  expected: "<Y>"              # HTML-escaped, max 200 chars
  source: user
  inject: true
```

### promotion-marker (kind=promotion-marker, inject=false)
Written exclusively by `cli.lessons_apply` after a schema-layer mutation;
closes the recursion guard so `cli.lessons_lint` skips it on the next scan.

```yaml
- id: <uuid>
  ts: <ISO-8601 UTC>
  kind: promotion-marker
  rule_violated: <rule_id>
  proxy_artifact: docs/proposed-rule-mutations/<rule>-<date>.md
  source_lesson_ids: [<uuid>, <uuid>, ...]
  source: auto-promote
  inject: false
```

## Injection contract

`SessionStart` and `UserPromptSubmit` hooks emit an `[ORCHESTRA TLDR]`
block (literal opening line of `hookSpecificOutput.additionalContext`,
BEFORE the `<system-reminder>` wrap — per LLD-012 §Edge Cases marker
contract for cross-plugin disambiguation).

Hook output filters to `kind == "violation" AND inject == True` and emits
ONLY the three allowlisted fields (rule_violated / observed / expected),
each HTML-escaped + 200-char-capped via fixed template. Free-text teach
body is NEVER present in injection output.

## Rule-id allowlist

`--rule=<id>` is validated against basenames of `.claude/rules/*.md`
(minus extension) plus `CLAUDE.md` and `workflow.md`. Unknown rule-id →
command exits 2 with helpful error listing known rule IDs. Defends against
path-traversal (`--rule=../../../etc/passwd`) by requiring an exact basename
match (no directory components allowed).

## Recursion guard

`cli.lessons_lint` skips `source: auto-promote` entries when scanning for
≥3× recurrence. This prevents the promote → inject → re-detect loop
(LLD-012 §lessons_lint step 1).

## Auto-promotion pipeline (manual review gate)

1. `cli.lessons_lint` detects ≥3× recurrence of the same `rule_violated`
   value, drafts a proposed TLDR mutation, and writes a **proxy review
   artifact** to `docs/proposed-rule-mutations/<rule>-<date>.md`. No
   spec-review is auto-triggered (Class-B reconciliation, LLD-012 SC-8).
2. User runs `/orchestra:spec-review` on the proxy artifact.
3. On passed attestation, user runs `python -m cli.lessons_apply
   <proxy-path>` to mutate the schema-layer target + append the
   `source: auto-promote` marker entry.

## Related

- `docs/features/012-rule-durability-and-learning-layer.md` — full LLD
- `cli/hooks/session_start_inject.py` — emission point (TLDR + violations)
- `cli/hooks/user_prompt_reinject.py` — Nth-turn re-injection (SC-14)
- `cli/lessons_store.py` — append + read primitives
