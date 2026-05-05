# Doc Standards — Claude Implementation Notes

> **Canonical standard lives at `docs/STANDARDS.md`.**
> This file covers Claude-specific implementation details only.

## Auto-Numbering

Use the script to get the next doc number before creating any doc:

```bash
bash .claude/skills/design-docs/scripts/next_doc_number.sh features   # → returns next available (e.g., 008)
bash .claude/skills/design-docs/scripts/next_doc_number.sh bugs       # → returns next available (e.g., BUG-014)
bash .claude/skills/design-docs/scripts/next_doc_number.sh adr        # → returns next available (e.g., ADR-001)
```

## Template Selection

| Situation | Template |
|---|---|
| New feature | `templates/feature-lld.md` |
| Bug fix | `templates/bug-report.md` |
| Significant architectural decision | `templates/adr.md` |
| Small architectural decision (≤4 sections) | `templates/adr-short.md` |
| Living component Design Doc | `templates/system-design-template.md` / `api-design-template.md` / `database-design-template.md` |

## Vocabulary Reference

- **Design Doc** = canonical name for living component-level architecture in `docs/design/`. The deprecated term "HLD" is no longer used.
- **ADR** = recorded architectural decision in `docs/adr/`. RFC vocabulary is not used in SCALE.
- **Feature LLD** = feature low-level design in `docs/features/`. The "low-level" wording stays — clearly scoped to a feature, not waterfall echo.

## Quality Checklist (Claude)

Before committing any doc, verify ALL of:

- [ ] Metadata block at top (Doc ID, Date, Status, DRI)
- [ ] Status set to `Draft` or `Proposed`
- [ ] All required sections filled — no placeholders, no TODOs
- [ ] At least one Mermaid diagram (Feature LLD + Bug Report mandatory; ADR optional; ADR-short optional)
- [ ] Changelog section present with at least one entry
- [ ] Design Doc sync check done (`references/design-doc-sync-protocol.md`)
- [ ] **Spec review passed** — invoke the spec-review situation skill from `.claude/skills-registry.md`, fix issues, re-review clean
- [ ] For Bug Report: Iteration Log section present (one entry per attempt, even if only one)
- [ ] File committed before any code touches the repo

## Pitfall checks

- [ ] **ADR is RECORDED, not deliberated.** No long "Options Considered" without a chosen decision.
- [ ] **LLD vs Plan no-overlap.** Plan describes HOW + ORDER. LLD describes WHAT. Don't duplicate.
- [ ] **Investigation graduation.** If a `docs/investigations/` scratch note confirmed a defect, it must already be promoted to a Bug Report doc — investigation scratch is for unconfirmed observations only.

## Mermaid Help

- Diagram generation: `scripts/resilient_diagram.py`
- Rendering errors: `references/troubleshooting.md` (28 documented errors)
- Diagram guides: `references/mermaid/<type>.md`
