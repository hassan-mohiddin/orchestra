---
description: Scan recurring violation lessons (≥3×) and write proxy mutation artifact to docs/proposed-rule-mutations/ — LLD-012 SC-6/SC-8. Does NOT auto-trigger spec-review (Class-B reconciliation).
arguments: []
---

Invoke `cli.lessons_lint` to scan the last 90 days of lessons,
detect ≥3× recurrence of the same `rule_violated` value (skipping entries
with `source: auto-promote` per the recursion guard), and write one
proxy review artifact per recurring rule to
`docs/proposed-rule-mutations/<rule>-<YYYY-MM-DD>.md`. The shim runs:

```bash
python -m cli.lessons_lint
```

(or `.venv/bin/python -m cli.lessons_lint` if the repo uses a venv-pinned
interpreter).

Per LLD-012 SC-8 (Class-B reconciliation), this command emits proxy
artifacts only — it does NOT auto-trigger spec-review. The user reviews
the proxy + runs `/orchestra:spec-review docs/proposed-rule-mutations/<...>.md`
when ready. After a passed attestation, `python -m cli.lessons_apply
<proxy-path>` mutates the schema-layer target and appends the
`source: auto-promote` marker entry.

Exit codes:
- 0 — scan completed (zero or more proxy artifacts written)
- 2 — filesystem error or invalid lessons file

See `skills/lessons/SKILL.md` for the auto-promotion pipeline + LLD-012
§lessons_lint for tie-break rules.
