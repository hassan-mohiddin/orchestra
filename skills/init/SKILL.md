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

1. **Read `.claude/orchestra.json` via the `Read` tool.** Do NOT use Bash
   `cat`/`test`/`ls` — use the Read tool directly. If the file does not
   exist, the Read tool returns an error → branch to Step 3 (fresh init).
   If the file exists, branch to Step 2 (re-run / migrate flow).
2. **Re-run / migrate branch (file present):** Read the `version` field
   from `.claude/orchestra.json`. Then invoke the `AskUserQuestion` tool
   ONCE with the payload defined in `skills/design-docs/init/prompts.md`
   § "Re-run prompt (only if .claude/orchestra.json already exists)".
   Required option labels are:
   - `Re-run init` — regenerate STANDARDS.md, replace add-ons (`--force`)
   - `Migrate` — only offered if `version` field is older than current
     (currently `1.1`); copies old fields into new schema
   - `Keep current` — abort, leave config untouched
   Map the user's answer to the corresponding CLI flag or exit code; do
   not improvise additional options.
3. **Fresh-init branch (file absent):** Invoke the
   `orchestra:design-docs:init` skill (read its SKILL.md and follow the
   HARD RULE for the 3-prompt flow). That sub-skill REQUIRES driving the
   3 prompts through the `AskUserQuestion` tool — see its SKILL.md for
   the exact option text. Do not skip its STEP 0 (v1.0 detection).
4. **After design-docs:init completes**, emit the canonical final-summary
   chat message defined in
   `skills/design-docs/init/prompts.md` § "Final summary (chat message
   after CLI completes)". Copy that template verbatim — substitute only
   the file counts and the list contents. Do NOT invent your own
   summary format.

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
