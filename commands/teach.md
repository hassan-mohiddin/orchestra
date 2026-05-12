---
description: Capture a free-text teach lesson (LLD-012 SC-6) — durable but NEVER injected into system-priority context per SC-11 allowlist
arguments:
  - name: text
    description: Free-text lesson body (any length; max useful ~1KB)
    required: true
---

Invoke `cli.lessons_teach` to append a `kind=teach, source=user, inject=false`
lesson entry to `docs/lessons/<YYYY-MM>-lessons.md`. The shim runs:

```bash
python -m cli.lessons_teach -- "${text}"
```

(or equivalently `.venv/bin/python -m cli.lessons_teach -- "${text}"` if the
repo is on a venv-pinned interpreter — `python -m` will resolve via the
shell's `python` if no venv is active).

The teach entry captures the user's free-text note for audit + future
maintainer ratification (v2.2+ ratification path is out of scope). Per
LLD-012 SC-11, free-text bodies are NEVER injected into `<system-reminder>`
blocks; the SessionStart + UserPromptSubmit hooks filter for
`kind=violation AND inject=true` only. Use `/orchestra:violation` instead
when the lesson must surface as system-priority guidance to future
sessions.

Exit codes:
- 0 — lesson appended
- 2 — empty body, store validation error, or filesystem error

See `skills/lessons/SKILL.md` for the full schema + injection contract.
