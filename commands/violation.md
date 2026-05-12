---
description: Capture a structured agent-violation lesson (LLD-012 SC-6/SC-11). Surfaces in [ORCHESTRA TLDR] system-priority blocks on SessionStart + every Nth UserPromptSubmit.
arguments:
  - name: rule
    description: Rule ID — basename (without .md) of `.claude/rules/*.md`, or `CLAUDE` / `workflow`. Validated against allowlist; path-traversal blocked.
    required: true
    flag: --rule
  - name: observed
    description: What the agent actually did. Max ~200 chars; HTML-encoded on write.
    required: true
    flag: --observed
  - name: expected
    description: What the agent should have done. Max ~200 chars; HTML-encoded on write.
    required: true
    flag: --expected
---

Invoke `cli.lessons_violation` to append a `kind=violation, source=user,
inject=true` lesson entry to `docs/lessons/<YYYY-MM>-lessons.md`. The shim
runs:

```bash
python -m cli.lessons_violation --rule="${rule}" --observed="${observed}" --expected="${expected}"
```

(or `.venv/bin/python -m cli.lessons_violation ...` if the repo uses a
venv-pinned interpreter).

The structured violation surfaces in the SessionStart + UserPromptSubmit
hook injection via the fixed allowlisted-fields template (rule_violated /
observed / expected only) — free-text body never reaches system context.
After ≥3 recurrences of the same `rule_violated`, `cli.lessons_lint` will
draft a proposed TLDR mutation to `docs/proposed-rule-mutations/`.

Exit codes:
- 0 — violation appended
- 2 — path-traversal in --rule, unknown rule id, store validation error, or filesystem error

See `skills/lessons/SKILL.md` for the full schema + injection contract.
