# Orchestra Roadmap

> **Doc ID:** 2026-05-06-orchestra-roadmap
> **Date:** 2026-05-06
> **DRI:** Hassan Mohiddin
> **Type:** Roadmap (subtype of Implementation Plan)
> **Status:** Active
> **LLD:** Not bound to single LLD — covers v1.1 through v2.0

## Header

**Goal:** Define version targets for orchestra plugin from v1.1 (in progress) through v2.0 (positioning relaunch). Each version is independently shippable. Targets are aspirational, not commitments — slip is allowed when reality demands.

**Architecture context:** Orchestra is a master-orchestrator plugin layered above other Claude Code plugins (superpowers, mattpocock-skills, gsd, etc.). Currently ships one skill (`orchestra:design-docs`); future versions add `orchestra:init`, `orchestra:design-docs:init`, `orchestra:workflow`, plugin-scan, registry-gen.

**Tech stack:** Claude Code plugin (skills + CLI), Python 3.14 (`cli/` flat module package), bash scripts (`scripts/`), markdown (`docs/`, `templates/`), GitHub-hosted schema files.

**LLD references:**
- v1.1 → `orchestra-dev/features/001-design-docs-init.md`
- v1.2+ → LLDs to be authored as each version starts
- Philosophy reference: `orchestra-dev/design/orchestra-philosophy.md`

## File Structure (high-level — per-version detail in implementation plans)

Per-version, file additions/modifications happen in `orchestra/`:

```
orchestra/
├── .claude-plugin/plugin.json    (version bumps per release)
├── skills/
│   ├── design-docs/              (v1.0 — existing)
│   ├── design-docs/init/         (v1.1 — new sub-skill)
│   ├── init/                     (v1.1 — new master init skill)
│   └── workflow/                 (v2.0 — new workflow skill)
├── cli/
│   ├── lint.py                   (v1.0 — extended in v1.1 with --mermaid)
│   ├── decisions_index.py        (v1.0)
│   ├── init.py                   (v1.1 — new)
│   ├── install_hooks.py          (v1.1 — new)
│   ├── migrate.py                (v1.2 — new, solo→team migration)
│   ├── plugin_scan.py            (v1.5 — new)
│   ├── registry_gen.py           (v1.5 — new)
│   └── viewer.py                 (v1.3+ — new, doc browser)
├── schema/
│   └── orchestra.config.v1.1.json (v1.1 — new)
├── docs/                         (mirrored from orchestra-dev during dev phase)
└── examples/                     (per-version expansions)
```

## Version Tasks

Each version has its own implementation plan written when work starts. This roadmap captures intent + rough scope only.

### v1.1 — design-docs:init + setup infrastructure (active)

**Status:** In progress (implementation plan: `orchestra-dev/plans/2026-05-06-orchestra-v1.1-implementation.md`)

**Scope:**
- `orchestra:init` skill (skeleton — delegates to design-docs:init only)
- `orchestra:design-docs:init` skill (3-prompt flow)
- Hybrid auto-prompt path
- Bucket 1 (always created) + Bucket 2 (prompted) setup
- Custom doc-types (default-7 / subset-rename / full-custom)
- Config: `.claude/orchestra.json` (per ADR-001) + `.local.json` override
- Mermaid lint integration (consumes existing `extract_mermaid.py`)
- Pre-commit hook installer (`cli/install_hooks.py`)
- v1.0.0 → v1.1 migration handling
- Mermaid viewing Tier 1 (README docs)
- 5 new eval scenarios

**Target ship:** 2026-05-20 (2 weeks from start)

**Commit message convention:** `feat: <component> per LLD-001 — <one-line>` with `Refs: docs/features/001-design-docs-init.md`.

### v1.2 — solo→team migration + Tier 2 viewing + commit-msg hook

**Status:** Pending v1.1 ship

**Scope:**
- `cli/migrate.py --solo-to-team` — backfills mandatory `OKR Alignment` field on existing ADRs; flips `mode` in config
- `cli/migrate.py --team-to-solo` — reverse migration (less common but supported)
- Mermaid CLI export tool — `python -m cli.viewer render <doc.md>` extracts blocks, exports PNG/SVG to `docs/.rendered/`
- `commit-msg` hook addition to `cli/install_hooks.py` — Refs: line check at message-author time (not just file-content time)
- Eval expansion: 3 new scenarios (migrate-solo-to-team, mermaid-export, commit-msg-hook)

**Target ship:** 2026-06-03 (2 weeks after v1.1)

### v1.3 — Orchestra-flavored doc browser (Tier 3 viewing)

**Status:** Pending v1.2

**Scope:**
- `python -m cli.viewer serve` — local server (port auto-pick), serves `docs/` with mermaid rendered + cross-doc nav
- Status filter (Current / Implemented / Superseded)
- Type filter (Feature LLD / Bug Report / ADR / etc.)
- Search across docs (full-text)
- Auto-rebuilds DECISIONS.md on file watch
- Optional GitHub Pages publish path (read-only public view of docs)
- Eval: 1 scenario (viewer-renders-correctly)

**Target ship:** 2026-06-24 (3 weeks after v1.2)

**Open question:** static-site-generator approach (e.g., MkDocs theme) vs custom Flask/FastAPI server. Decide during LLD-2 authoring at v1.3 start.

### v1.5 — Plugin scan + skills registry + plugin manifest spec (positioning shift)

**Status:** Pending v1.3

**Scope:** This is the big one — orchestra rebrands from "doc-skill that also has CLI tooling" to "master orchestrator for Claude Code skills."

- `cli/plugin_scan.py` — scans `~/.claude/plugins/`, reads SKILL.md frontmatter + body, builds capability map
- `cli/registry_gen.py` — generates `.claude/skills-registry.md` (situation → skill bindings) from scan results + user prompts
- `orchestra:init` master skill expanded — runs plugin_scan + registry_gen as core init steps (no longer a thin skeleton)
- Conflict resolution UX — when multiple skills could handle a situation, prompt user to pick canonical + alternates
- Plugin manifest spec — `orchestra.json` contract for plugin authors. Plugins that ship the manifest declare categories, alternates, conflicts. Orchestra honors them. Plugins without manifest still work via heuristic analysis.
- Lazy revalidation — registry rebuild on session start if `~/.claude/plugins/` mtime changed
- Eval: 5 scenarios (scan-detects-superpowers, scan-detects-mattpocock, conflict-resolution, manifest-honored, lazy-revalidate)

**Target ship:** 2026-08-05 (6 weeks after v1.3)

**Marketing:** v1.5 release notes emphasize the positioning shift. README rewrite candidate. Considered as v2.0 if positioning maturity warrants.

### v2.0 — orchestra:workflow skill + relaunch

**Status:** Pending v1.5

**Scope:**
- `orchestra:workflow` skill — master 8-step pipeline composing other skills via the registry
- Demotes design-docs from top-level skill to sub-component invoked by workflow
- Replaces SCALE-style hand-rolled `.claude/workflow.md` files with plugin-shipped workflow
- README rewrite emphasizing orchestrator positioning (deferred from v1.5 if not done there)
- Marketing relaunch: HN post, r/ClaudeAI, Twitter/X, Dev.to, LinkedIn (drafts already exist; reframe for v2.0 substance)
- Anthropic marketplace re-submission with updated description
- Eval: 8 scenarios (full workflow end-to-end across solo + team modes)

**Target ship:** 2026-10-07 (9 weeks after v1.5)

**Open question:** does v2.0 merge plugin-scan + workflow skill, or keep them as separate features? Decide during LLD authoring.

### Beyond v2.0

Not committed. Candidates:
- **v2.x** — additional sub-skills (gsd-style task tracking, gates as skill, brainstorm orchestration)
- **v3.0** — Claude Code Sonnet 4.x compatibility check + multi-agent extension
- **v3.x** — collaborative editing UX for team mode (real-time spec review)

## Sequencing Notes

**Strict dependencies:**
- v1.5 requires v1.1 setup infra (plugin_scan reads `.claude/orchestra.json`)
- v2.0 requires v1.5 registry (workflow consumes registry to route situations)

**Soft dependencies:**
- v1.2 commit-msg hook depends on v1.1 install_hooks.py being present
- v1.3 viewer depends on v1.2 mermaid export (CLI shares some rendering logic)

**Independent / parallelizable:**
- v1.2 migrate.py can ship without v1.2 viewer
- v1.5 plugin manifest spec can be drafted before plugin_scan implementation (spec-first)

## Commit Strategy Per Version

Per `.claude/rules/commit-strategy.md`:
- Each version's implementation work uses `feat:` commits with `Refs: docs/features/NNN-<name>.md`
- Each version's design docs use `docs:` commits (no Refs: required, but recommended)
- Status updates to design docs commit BEFORE or ALONGSIDE final feature commit (status → `Implemented` or `Verified`)
- No `fix:` commits during version development — bug iterations during dev = `wip:` until user confirms post-ship

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| v1.5 plugin scan reveals incompatible skill formats across companion plugins | Medium | High | Heuristic analysis fallback; spec-first plugin manifest gives authors clear contract. |
| v2.0 workflow skill conflicts with mattpocock-skills:tdd's horizontal-slice prescription | Medium | Medium | Vertical-slice principle wins per skills-registry override (already documented in SCALE skills-registry.md). Codify in orchestra:workflow. |
| Schema URL `raw.githubusercontent.com/hassan-mohiddin/orchestra/main/schema/...` returns 404 if main branch is renamed | Low | High | Pin schema URL to a commit SHA after first publish, OR add CI check that schema file exists on every PR. |
| Anthropic marketplace re-submission rejected for v2.0 positioning shift | Low | Medium | Submit early; have legacy listing fallback. |
| Breaking config schema between v1.x and v2.0 | High | Medium | Migration code in `cli/migrate.py` matures across versions; semver-tracked. |

## Changelog

| Date | Change |
|---|---|
| 2026-05-06 | Initial roadmap drafted alongside LLD-001 + philosophy Design Doc + ADR-001. Status: Active. |
