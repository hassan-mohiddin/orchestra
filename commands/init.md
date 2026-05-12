---
description: Initialize orchestra in a new repo — master init skill (delegates to design-docs:init for v1.1 scope; v1.5+ adds plugin scan + registry-gen; v2.0+ adds workflow init).
---

Invoke skill `orchestra:init`.

The skill runs the master orchestra initialization flow:

1. **v1.1 scope** — delegates to `orchestra:design-docs:init` sub-skill (internal composition; sub-skill drives 3-prompt setup via `AskUserQuestion` tool: mode / doc-types / add-ons).
2. **Reserved branches** (activated in later orchestra versions):
   - v1.5 — plugin scan (`~/.claude/plugins/`) + `.claude/skills-registry.md` generation
   - v2.0 — `orchestra:workflow` skill scaffolding

The init flow is deterministic: it MUST use the `AskUserQuestion` tool for every prompt, never descriptive markdown, never silent defaults. See `skills/init/SKILL.md` for the full skill body.

When complete, the master skill emits a canonical final-summary message confirming `.claude/orchestra.json` was written + scaffolding created.
