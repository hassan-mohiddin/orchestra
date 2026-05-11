---
name: orchestra-init
description: Use when starting orchestra in a new repo. Triggers on phrases like "set up orchestra", "initialize orchestra", "configure orchestra in this project", "orchestra init". Master init skill — v1.1 delegates to design-docs:init (which drives 3 AskUserQuestion prompts deterministically). Future versions extend with plugin scan and workflow init.
---

# Orchestra Init

Master orchestrator init skill. Composes sub-skill inits for each enabled
orchestra component.

## v1.1 scope

Currently delegates to one sub-skill:
- `orchestra:design-docs:init` — sets up design docs scaffolding (3-prompt
  flow driven by the AskUserQuestion tool)

Reserved branches (activated in later versions):
- Plugin scan (`v1.5`) — scans `~/.claude/plugins/` to build skills-registry
- Registry generation (`v1.5`) — emits `.claude/skills-registry.md`
- Workflow init (`v2.0`) — sets up `orchestra:workflow` skill scaffolding

## How to invoke

When the user asks to "set up orchestra" or similar:

1. Check for existing `.claude/orchestra.json` config in the project root.
2. If present: report current orchestra setup status; ask the user (via the
   `AskUserQuestion` tool) whether they want to re-run init or migrate to
   a newer version.
3. If absent: invoke `orchestra:design-docs:init` skill to run the 3-prompt
   setup flow. That sub-skill is REQUIRED to drive the 3 prompts via the
   `AskUserQuestion` tool — see its SKILL.md for the exact option text.
4. After design-docs:init completes, report final status:
   - Files created
   - Files skipped (already existing)
   - Next steps (write your first design doc, install pre-commit hook, etc.)

## Why AskUserQuestion is mandatory

BUG-001 root cause: skill markdown that *described* prompts (without
instructing Claude to invoke `AskUserQuestion`) left the 3-prompt flow up
to improvisation. The sub-skill `orchestra:design-docs:init` now hard-rules
the 3 prompts through `AskUserQuestion`, and this master skill must
delegate to it without short-circuiting to defaults.

## API stability

The user-facing invocation `orchestra:init` is stable from v1.1 onward.
Internal composition expands version by version, but the user-facing
contract does not change.

## Related skills

- `orchestra:design-docs` — main design-docs skill (use for writing typed docs)
- `orchestra:design-docs:init` — sub-skill that runs the 3-prompt setup flow

## CLI fallback (programmatic only — CI / automation)

If a consumer wants to skip the interactive 3-prompt flow entirely (e.g., in
CI), they can call the CLI directly with all three answers as flags. This
bypasses the skill and the AskUserQuestion prompts.

```bash
python -m cli.init --preset default-7 --mode solo --addons yes
```

This is the only path that should ever skip AskUserQuestion. When a human
invokes `/orchestra:init` interactively, the 3 prompts MUST fire.
