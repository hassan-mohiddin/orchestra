# Skills Routing

This rule is auto-loaded every session. It defines how Claude resolves a "situation" in the
workflow file to a concrete skill, and what to do when resolution fails.

---

## The Three-File System

| File | Purpose |
|---|---|
| `.claude/workflow.md` | Master workflow. Uses SITUATION language only. Stable across plugin changes. |
| `.claude/skills-registry.md` | Situation → skill binding table. The ONLY place skill names live. |
| `.claude/rules/skills-routing.md` (this file) | How to resolve, fallback, precedence, overrides. |

When workflow says "run spec review", the lookup goes:

1. Check `skills-registry.md` "Always-on situational bindings" table
2. Find row where situation = "spec review"
3. Use the `Skill` value in that row

---

## Resolution algorithm

```
SITUATION = e.g. "spec review", "TDD execution", "adversarial review"

1. Look up SITUATION in skills-registry.md "Always-on situational bindings"
2. Get bound SKILL_NAME (e.g. "superpowers:requesting-code-review")
3. Check if SKILL_NAME is in current session's available-skills list (the system reminder at session start)
4. If yes → invoke via Skill tool (apply any override rules from registry)
5. If no → fallback procedure (below)
```

---

## Fallback when bound skill not available

When the registry says "use X" but X isn't loaded:

1. **Verify plugin is enabled.** Check `~/.claude/plugins/installed_plugins.json` and the
   `enabledPlugins` blocks in user/project/local settings. If disabled → tell user, suggest enable.
2. **Check `/reload-plugins`.** Plugins may have been added without reload.
3. **Look for an alternative in registry "Skills available but NOT bound to situations".**
   Some skills are alternates and can serve in a pinch.
4. **If still no candidate → STOP and tell user.** Do not silently skip the workflow step.
   Skipping = drift. Always surface.

**Never invent skill names by guessing.** If the registry says `mattpocock-skills:tdd` and
that exact string isn't in the available-skills list, you have a registration problem, not
a typo to fix in your head.

---

## Override rules (applied AFTER skill resolution)

These are recorded in `skills-registry.md` under "Override rules." Common overrides:

| Override | Resolution |
|---|---|
| Save path | Skill saves to plugin path → re-route to project path. E.g. plans go to `docs/plans/`, never `docs/superpowers/specs/`. |
| Doc vocabulary | Skill produces PRD-style doc → suppress, use `orchestra:design-docs` skill for SCALE LLD vocab. |
| Workflow shape | Skill prescribes horizontal-slice TDD → enforce vertical-slice principle (mattpocock-skills:tdd shape wins). |
| Duplicate skills | Two skills with similar names (e.g. `caveman:caveman` and `mattpocock-skills:caveman`) → registry chooses one canonical. Use only the canonical. |

---

## Precedence rules (when conflicts arise)

In order, highest first:

1. **User instruction in current message** — overrides everything
2. **Project rules in `.claude/rules/`** — auto-loaded, project-canonical
3. **Skills registry decisions** — situation bindings + overrides
4. **Plugin SKILL.md content** — what the skill itself says
5. **Default Claude Code behavior** — lowest priority

If a plugin SKILL.md says "save here" and the registry override says "save there", the
registry wins (rule 3 > rule 4).

If a project rule contradicts a registry decision, fix the rule or update the registry —
do not let them silently disagree.

---

## Adding / removing skills

See `skills-registry.md` § "Adding a new skill / plugin" and "Removing a skill / plugin"
for the maintenance procedure. Both are short.

---

## Anti-patterns to avoid

- **Skill name in workflow file** — workflow.md must stay situation-language only. If you
  catch yourself writing "invoke superpowers:X" in workflow.md, move it to the registry.
- **Hardcoded plugin path in any rule** — paths like `~/.claude/plugins/cache/.../X` are
  fragile. Use the skill name; let Claude Code resolve the path.
- **Silent skip on resolution failure** — see fallback procedure. Never proceed past a
  workflow step whose skill couldn't be resolved.
- **Multiple skills doing the same situation** — registry has ONE skill per situation. If
  two could fit, choose; if both genuinely needed, split the situation into two.

---

## How this file gets updated

- When `skills-registry.md` changes and the resolution algorithm or fallback procedure
  needs adjustment → update this file
- When you discover a new conflict pattern → encode it as a new override rule
- This file should change rarely. The registry changes more often (plugin churn).

The registry is the moving piece. This file is the stable rule.
