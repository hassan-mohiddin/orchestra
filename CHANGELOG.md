# Changelog

## v1.3.0 — 2026-05-06

Adds Tier 3 doc browser via MkDocs Material — orchestra docs become a fully searchable, navigable, GitHub-Pages-publishable site.

### New CLI

- **`python -m cli.viewer install-mkdocs`** — writes 4 files (mkdocs.yml + docs/index.md + requirements-docs.txt + mkdocs_hooks.py) and appends `site/` to .gitignore. Idempotent skip-existing; `--force` overwrites.
- **`python -m cli.viewer build`** — wraps `mkdocs build`. Validates mkdocs installed.
- **`python -m cli.viewer publish-gh-pages`** — wraps `mkdocs gh-deploy`. Refuses if working tree dirty.

### MkDocs config (orchestra-flavored)

- Material theme with light/dark toggle
- mermaid2 plugin (mermaid 10.9.1) for native diagram rendering
- tags plugin for status-based filtering
- Navigation pre-grouped by orchestra doc types (Features / Bugs / ADRs / Postmortems / Runbooks / Plans)
- mkdocs_hooks.py auto-extracts `Status:` from existing metadata blocks → tags (no front-matter retrofit)

### Decision

- **MkDocs over custom Flask/FastAPI server** (resolves roadmap open question). Industry-standard, Material theme polish, GitHub Pages built-in, less code to maintain.

### Tests + eval

- 85 pytest tests (77 v1.2 + 8 v1.3 new)
- 10/10 eval scenarios pass (8 v1.2 + 2 v1.3: mkdocs-install + mkdocs-build)

### Docs

- README "Viewing diagrams" gets Tier 3 row

### Backward compatibility

- v1.2 `cli.viewer render` / `render-all` unchanged
- v1.1 hooks + skills unchanged
- New subcommands extend existing argparse — no breaking changes

### Roadmap reconciliation

- Original v1.3 roadmap row mentioned `cli.viewer serve` (custom server) and DECISIONS.md auto-rebuild on file watch. Both deferred — `mkdocs serve` provides local dev server natively; cross-tool DECISIONS.md watcher requires extra orchestration, deferred to v1.4+.

## v1.2.0 — 2026-05-06

Adds solo↔team migration CLI, Tier 2 mermaid export, and commit-msg hook for proactive Refs: validation.

### New CLI

- **`python -m cli.migrate --solo-to-team`** — flips `orchestra.mode` and reports ADRs missing `OKR Alignment` field (lint-mandatory in team mode)
- **`python -m cli.migrate --team-to-solo`** — reverse migration
- **`python -m cli.migrate --dry-run`** — preview without writing config
- **`python -m cli.viewer render <doc>`** — extract mermaid blocks → PNG/SVG in `docs/.rendered/`
- **`python -m cli.viewer render-all`** — walk `docs/`, render all
- **`--format png|svg`** + **`--output <dir>`** flags
- **`python -m cli.install_hooks --commit-msg`** — install commit-msg hook (Refs: at message-author time)
- **`python -m cli.install_hooks --all`** — install both pre-commit + commit-msg in one call

### New hook

- **commit-msg** — fires when user types commit message. On `fix:`/`feat:` subject without `Refs: docs/...` body line, exit 1 + abort. Complementary to v1.1 pre-commit (file content) hook.

### Atomic writes

- `cli.migrate` writes config via `.tmp` + `os.replace` (POSIX atomic) — no partial corruption on interrupt.
- Path traversal guards in `_scan_adrs_for_okr` (rejects absolute paths and `..` traversal).

### Tests + eval

- 22 new pytest tests (migrate: 8, viewer: 9, install_hooks v1.2 extension: 7) — total 75 tests across orchestra
- 3 new eval scenarios: `migrate-solo-to-team`, `mermaid-export`, `commit-msg-hook` — total 8/8 scenarios green

### Docs

- README "Viewing diagrams" gets Tier 2 row for `cli.viewer`

### Compatibility

- Backward-compatible with v1.1
- `install_hook` v1.1 entry point preserved for callers (now alias for `install_one_hook("pre-commit")`)

## v1.1.0 — 2026-05-06

Adds setup infrastructure + skill init flow + mermaid lint integration. v1.0 plugin shipped inert text — v1.1 makes it actually usable in fresh repos.

### New skills

- `orchestra:init` — master init skill (delegates to design-docs:init in v1.1; reserved entry for v1.5+ plugin scan + v2.0 workflow init)
- `orchestra:design-docs:init` — 3-prompt setup flow (mode / doc-types / optional add-ons)
- Auto-prompt detection in `orchestra:design-docs` skill — fires `[y]` init / `[c]` customize prompt when `.claude/orchestra.json` is missing

### New CLI

- `python -m cli.init` — programmatic init mirroring skill flow (`--mode`, `--preset`, `--addons`, `--force`)
- `python -m cli.install_hooks` — installs `.git/hooks/pre-commit` calling `cli.lint --pre-commit`
- `cli.lint --mermaid` / `--no-mermaid` — mermaid block validation via `npx @mermaid-js/mermaid-cli` (graceful fallback to syntax-only check if npx absent)

### Config

- New canonical config at `.claude/orchestra.json` (committed by default per ADR-001)
- New override location `.claude/orchestra.local.json` (gitignored)
- Schema published at `schema/orchestra.config.v1.1.json`
- v1.0 → v1.1 migration: detects `.claude/settings.local.json` orchestra block, prompts to migrate, preserves v1.0 file (non-destructive)

### Setup scope

- **Bucket 1 (always):** 7 docs/ subdirs + STANDARDS.md + .gitignore append + DECISIONS.md seeding
- **Bucket 2 (prompted):** `.github/workflows/orchestra-lint.yml`, AGENTS.md, llms.txt
- Custom doc-types: default-7 / subset-rename (with formal-vocab whitelist) / full-custom (with invariants enforced)

### Eval framework

- New in-repo eval framework at `eval/run.py` (v1.0 had no in-repo evals)
- 5 scenarios: fresh-init, custom-rename-rejected, rerun-idempotent, mermaid-lint, v10-migration

### Tests

- 39 pytest tests across config, init, standards generator, lint mermaid, install_hooks, migration

### Docs

- README: new "Viewing diagrams" section (Tier 1) — GitHub native, VS Code, JetBrains, mermaid.live, npx mermaid-cli

### Compatibility

- Backward-compatible with v1.0 — existing installs see migration prompt on first design-docs invocation under v1.1
- `python -m design_docs.lint` invocation remains the same name internally? No — actual module is `cli.lint`. v1.0 docstring drift fixed.

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
