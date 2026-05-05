# Changelog

## v1.0.0 — 2026-05-06

Initial public release. Extracted from SCALE project's internal `design-docs` skill after iteration-1 eval landed at 100% pass on 8 scenarios.

### Ships

- 7 typed doc templates (Feature LLD, Bug Report, ADR, ADR-short, Postmortem, Runbook, Design Doc)
- 2 cross-tool AI doc standards (AGENTS.md, llms.txt)
- 4-gate spec review (Completeness / Evidence / Clarity / Consistency)
- Auto-numbering script (octal-safe)
- 5 mermaid diagram-type guides + 28-error troubleshooting reference
- Solo / team mode toggle via plugin config
- `design_docs.lint` CLI (Refs:-line gate, metadata, status enums)
- `design_docs.decisions_index` CLI (auto `DECISIONS.md` with relationship types)
- GitHub Action template for CI lint
- Example doc per type
