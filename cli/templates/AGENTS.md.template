# AGENTS.md

> Cross-tool AI agent context file. Conformant with the AGENTS.md spec
> (Linux Foundation Agentic AI Foundation, Dec 2025).

## Project

This repository uses [orchestra](https://github.com/hassan-mohiddin/orchestra)
for documentation discipline.

## Documentation

- All design docs live under `docs/`.
- Doc taxonomy + writing standards: `docs/STANDARDS.md` (canonical).
- Architecture Decision Records: `docs/adr/`.
- Feature designs: `docs/features/`.
- Living component architecture: `docs/design/`.
- Bug investigations: `docs/bugs/`.
- Incident postmortems: `docs/postmortems/`.
- Operational runbooks: `docs/runbooks/`.
- Implementation plans: `docs/plans/`.

## Workflow

- No code change without a design doc first.
- Spec review (4-gate) on every doc before commit.
- `Refs:` line on every `fix:` and `feat:` commit pointing to a real `docs/` file.
- Run `python -m cli.lint --pre-commit` before commit.

## For AI agents

When asked to write a design doc, follow `docs/STANDARDS.md`.
When asked to fix a bug, create `docs/bugs/BUG-NNN-name.md` first, then code.
When asked to record an architectural decision, write `docs/adr/ADR-NNN-name.md`.
