# Project Documentation

Welcome. This site is built from the project's `docs/` tree using
[orchestra](https://github.com/hassan-mohiddin/orchestra) + MkDocs Material.

## Doc types

| Type | Path | Purpose |
|---|---|---|
| [Standards](STANDARDS.md) | `docs/STANDARDS.md` | Canonical doc rules (taxonomy, status lifecycle, required sections, mermaid minimums) |
| [Decisions Index](adr/DECISIONS.md) | `docs/adr/DECISIONS.md` | Auto-generated ADR index with relationship graph |
| [Architecture Decisions](adr/) | `docs/adr/` | Recorded architectural decisions (Nygard format) |
| [Feature LLDs](features/) | `docs/features/` | Low-level designs for new features |
| [Bug Reports](bugs/) | `docs/bugs/` | Investigated defects with iteration logs |
| [Design Docs](design/) | `docs/design/` | Living component-level architecture |
| [Postmortems](postmortems/) | `docs/postmortems/` | Blameless incident reviews (Google SRE format) |
| [Runbooks](runbooks/) | `docs/runbooks/` | On-call operational guides |
| [Plans](plans/) | `docs/plans/` | Implementation plans |

## Search + filter

- **Search** — top-right search box (full-text across all docs)
- **Status filter** — every doc carries a status tag (Draft / In Progress / Implemented / Verified). Browse `/tags/` for status-grouped lists
- **Type filter** — sidebar groups by doc type

## Contributing

All docs are markdown in this repo. Edit, commit, push.
Lint runs in CI: `python -m cli.lint --pre-commit`.

For new docs, see [Standards](STANDARDS.md) for required sections and metadata format.
