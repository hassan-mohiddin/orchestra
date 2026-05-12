---
description: Produce or update an orchestra design doc (Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc) — iron law "no code without a design doc first" + 4-gate spec review + mermaid diagram requirements.
---

Invoke skill `orchestra:design-docs`.

The skill routes by doc type:

| Work type | Template | Output path (default) |
|-----------|----------|----------------------|
| Feature | `templates/feature-lld.md` | `docs/features/NNN-name.md` |
| Bug fix | `templates/bug-report.md` | `docs/bugs/BUG-NNN-name.md` |
| ADR | `templates/adr.md` | `docs/adr/ADR-NNN-name.md` |
| Postmortem | `templates/postmortem.md` | `docs/postmortems/POSTMORTEM-YYYY-MM-DD-name.md` |
| Runbook | `templates/runbook.md` | `docs/runbooks/RUNBOOK-name.md` |
| Design Doc | `templates/design-doc.md` | `docs/design/<component>.md` |

Pipeline:

1. **Setup detection** — read `.claude/orchestra.json`. If absent, auto-prompt to run init (auto-routes to `orchestra:init` master skill).
2. **Get doc number** — `scripts/next_doc_number.sh <type>` for auto-incremented IDs.
3. **Load template** + fill all sections (no placeholders, no TODOs).
4. **Add mermaid diagram** — per-doc-type minimums in `STANDARDS.md § Mermaid Diagram Requirements`.
5. **Spec review** — invoke `orchestra:spec-review` v2 (6-sub-judge ensemble) before commit.
6. **Commit docs before code** — `docs:` prefix; gate code work behind the design doc.

See `skills/design-docs/SKILL.md` for the full skill body, references, and scripts.
