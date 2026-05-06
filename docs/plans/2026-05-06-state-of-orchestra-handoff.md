# State of Orchestra — Session Handoff (2026-05-06)

> **Doc ID:** 2026-05-06-state-of-orchestra-handoff
> **Date:** 2026-05-06
> **DRI:** Hassan Mohiddin
> **Type:** Implementation Plan (subtype: Session Handoff snapshot)
> **Status:** Active
> **LLD:** Not bound to a single LLD — references 001, 002, 003 + roadmap

## Header

**Goal:** Capture full state of orchestra plugin at end of 2026-05-06 development session. Survives conversation compaction. Future sessions read this to resume work without re-discovering context.

**Why this doc exists:** A long session (v1.0 → v1.1 → v1.2 → v1.3 + 7 BUG reports + SCALE decoupling) generated dense state. Compaction loses inline conversation. This doc + auto memory + git history are the survivable record.

## Versions Shipped

| Version | Tag | Date | Highlights |
|---|---|---|---|
| **v1.0.0** | v1.0.0 | 2026-05-05 | Initial public release. design-docs skill, 7 typed templates, lint/decisions_index CLIs |
| **v1.1.0** | v1.1.0 | 2026-05-06 | `orchestra:init` + `design-docs:init` skills, setup infra, mermaid lint, pre-commit installer, v1.0→v1.1 migration. 53 pytest tests + 5/5 evals |
| **v1.2.0** | v1.2.0 | 2026-05-06 | solo↔team migration CLI, Tier 2 mermaid export, commit-msg hook. 77 pytest tests + 8/8 evals |
| **v1.3.0** | v1.3.0 | 2026-05-06 | Tier 3 doc browser via MkDocs Material. install-mkdocs / build / publish-gh-pages. 85 pytest tests + 10/10 evals |

All releases live at https://github.com/hassan-mohiddin/orchestra/releases. Plugin canonical at github.com/hassan-mohiddin/orchestra.

## Current Repo State (orchestra)

```
orchestra/
├── .claude-plugin/plugin.json    (v1.3.0)
├── pyproject.toml                (v1.3.0, Python ≥3.10)
├── cli/
│   ├── __init__.py
│   ├── config.py                 (v1.1 — schema parser/validator + deep_merge)
│   ├── decisions_index.py        (v1.0 — auto DECISIONS.md)
│   ├── init.py                   (v1.1 — scaffold_bucket_1 + STANDARDS gen + invariants
│   │                              + v1.0→v1.1 migration. v1.2 added migrate.py-friendly helpers)
│   ├── install_hooks.py          (v1.1+v1.2 — pre-commit + commit-msg hooks)
│   ├── lint.py                   (v1.0+v1.1 — Refs/metadata/status + --mermaid flag)
│   ├── migrate.py                (v1.2 — solo↔team mode flip + ADR scan)
│   ├── viewer.py                 (v1.2 Tier 2 + v1.3 install-mkdocs/build/publish)
│   └── templates/
│       ├── AGENTS.md.template
│       ├── llms.txt.template
│       ├── orchestra-lint.yml
│       ├── pre-commit.sh
│       ├── commit-msg.sh
│       ├── standards-default-7.md
│       ├── mkdocs.yml
│       ├── docs-index.md
│       ├── requirements-docs.txt
│       └── mkdocs_hooks.py
├── eval/
│   ├── __init__.py
│   ├── run.py                    (eval runner)
│   └── scenarios/
│       ├── orchestra-fresh-init.json
│       ├── orchestra-custom-rename-rejected.json
│       ├── orchestra-rerun-idempotent.json
│       ├── orchestra-mermaid-lint.json
│       ├── orchestra-v10-migration.json
│       ├── migrate-solo-to-team.json
│       ├── mermaid-export.json
│       ├── commit-msg-hook.json
│       ├── mkdocs-install.json
│       └── mkdocs-build.json     (10 total)
├── tests/
│   ├── conftest.py               (tmp_repo + tmp_repo_no_git fixtures)
│   ├── test_config.py
│   ├── test_cli_init_bucket1.py
│   ├── test_cli_init_bucket2.py
│   ├── test_decisions_seeding.py
│   ├── test_standards_generator.py
│   ├── test_cli_lint_mermaid.py
│   ├── test_cli_install_hooks.py
│   ├── test_cli_migrate.py
│   ├── test_cli_viewer.py
│   ├── test_migration_v10_to_v11.py
│   └── test_sanity.py            (deletable in v1.4)
├── schema/orchestra.config.v1.1.json
├── skills/
│   ├── init/SKILL.md             (v1.1)
│   └── design-docs/
│       ├── SKILL.md              (v1.0+v1.1 auto-prompt)
│       ├── STANDARDS.md          (canonical doc rules — used as default-7 template source)
│       ├── init/
│       │   ├── SKILL.md
│       │   └── prompts.md
│       ├── references/           (mermaid guides, troubleshooting, spec-review-gates)
│       ├── scripts/
│       │   ├── extract_mermaid.py    (v1.0 — exposes extract_diagrams_from_file + basic_syntax_check in v1.1)
│       │   ├── mermaid_to_image.py
│       │   ├── next_doc_number.sh
│       │   └── resilient_diagram.py
│       └── templates/            (Feature LLD, Bug Report, ADR, Postmortem, Runbook, etc.)
├── docs/
│   ├── STANDARDS.md
│   ├── adr/
│   │   ├── ADR-001-orchestra-config-storage.md (Implemented)
│   │   └── DECISIONS.md
│   ├── bugs/                     (7 NEW bug reports — see "Pending v1.4" below)
│   ├── design/orchestra-philosophy.md
│   ├── features/
│   │   ├── 001-design-docs-init.md (Verified)
│   │   ├── 002-v1.2-migration-viewer-commit-msg.md (Verified)
│   │   └── 003-v1.3-doc-browser-mkdocs.md (Verified)
│   └── plans/
│       ├── 2026-05-06-orchestra-roadmap.md
│       ├── 2026-05-06-orchestra-v1.1-implementation.md (Implemented)
│       ├── 2026-05-06-orchestra-v1.2-implementation.md (Implemented)
│       ├── 2026-05-06-orchestra-v1.3-implementation.md (Implemented)
│       └── 2026-05-06-state-of-orchestra-handoff.md (THIS DOC)
├── .github/workflows/lint.yml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── examples/                     (v1.0 example bug/adr/postmortem)
└── .gitignore
```

## SCALE Decoupling (2026-05-06)

SCALE was previously a development workspace for orchestra (`orchestra-dev/` mirrored to `orchestra/docs/`). Decoupled mid-session:

- **Removed from SCALE:** `orchestra-dev/`, `.claude/skills/design-docs/`, `.claude/skills/design-docs-workspace/`, `sync-orchestra-dev.sh`
- **Updated in SCALE:** `.claude/skills-registry.md`, `.claude/CLAUDE.md`, `.claude/rules/{documentation-gate,skills-routing}.md` now reference `orchestra:design-docs` user-scoped plugin
- **Applied orchestra:init in SCALE:** `.claude/orchestra.json` + Bucket 1 + Bucket 2 + MkDocs install
- **Final SCALE state:** uses orchestra plugin via Claude Code skill resolution. No file-level coupling.

SCALE commit `ae87e12` (clean break + init applied). Pushed to `hassang371/spendsmart-dashboard`.

## Pending: v1.4 Cleanup Release (7 BUGS Filed)

All filed at `docs/bugs/BUG-NNN-*.md` Status: Investigating. Target fix v1.4.

| ID | Severity | Title |
|---|---|---|
| BUG-001 | Critical | orchestra:init 3-prompt flow markdown-only, not interactive |
| BUG-002 | High | cli.init silently gitignores paths with tracked files |
| BUG-003 | High | mkdocs tags plugin missing tags_file config + tags.md |
| BUG-004 | Medium | AGENTS.md / llms.txt not project-aware |
| BUG-005 | Medium | mkdocs.yml nav doesn't auto-detect extra docs/ subdirs |
| BUG-006 | Low | install_hooks doesn't detect pre-commit.com framework |
| BUG-007 | Medium | mkdocs.yml YAML python-tag breaks strict check-yaml |

Each bug ships with mermaid diagram + concrete fix design + regression test plan. Bug list discovered via real-world `/orchestra:init` audit in SCALE on 2026-05-06.

## Roadmap (`docs/plans/2026-05-06-orchestra-roadmap.md`)

```
v1.0  ✅ shipped 2026-05-05
v1.1  ✅ shipped 2026-05-06 — design-docs:init + setup infra
v1.2  ✅ shipped 2026-05-06 — migration + Tier 2 mermaid + commit-msg
v1.3  ✅ shipped 2026-05-06 — Tier 3 MkDocs browser
v1.4  📋 next — Cleanup release (7 BUGs from real-world audit)
v1.5  📋 future — Plugin scan + skills registry + plugin manifest spec (POSITIONING SHIFT)
v2.0  📋 future — orchestra:workflow skill + relaunch
```

## Key Architectural Decisions (Recorded)

- **ADR-001** (Implemented): config storage at `.claude/orchestra.json` (committed by default), `.claude/orchestra.local.json` (gitignored override). Replaces v1.0 `.claude/settings.local.json` orchestra block.
- **MkDocs over Flask/FastAPI** (LLD-003): industry-standard, Material theme, GitHub Pages built-in, less code to maintain.
- **importlib path-loading for extract_mermaid** (LLD-001 line 295-298 option a): chosen over rename-with-init.py.
- **Invariants folded into cli/init.py** (LLD-002 deviation): no separate cli/invariants.py module — single-module simplicity.
- **RFC vocabulary suppressed across both modes**: orchestra philosophy is ADR-only. Re-evaluate at v2.0+.
- **Formal vocabulary whitelist** for subset-rename mode: industry terms only ("Tech Spec", "Decision Record", etc.). Rejects informal ("doc", "thing", "writeup"). RFC explicitly excluded.
- **Solo vs team mode**: only differs in ADR `OKR Alignment` field requirement. Lint enforces in team mode.

## Process Discipline Notes (Lessons from this session)

1. **Gate 3 retroactive review caught real defects.** v1.2 plan was committed without spec review (gate violation). Subsequent retroactive review found 2/4 gates failing (Task 1 stale state, mild LLD-overlap). Discipline gates work.

2. **Reviewer agents catch what direct review misses.** v1.2 Task 1 (`cli.migrate`) committed → reviewer subagent surfaced 4 real issues (dead `write_v11_config` import, weak dry_run test, missing path traversal validation, fragile string match). Fixed in follow-up. **Pattern: spawn cavecrew-reviewer after every non-trivial code commit.**

3. **LLD vs Plan no-overlap pitfall is REAL.** v1.2 plan first invented `cli/invariants.py` not in LLD-002. Spec review caught it. Resolution: fold into `cli/init.py`, update LLD-002 with deviation entry.

4. **Real-world install audits surface bugs spec review can't.** SCALE init session 2026-05-06 produced 7 bugs none caught during pre-ship review. Pattern: ship + audit in production-like repo + file bugs.

5. **Pre-commit hook conflicts are real.** SCALE uses pre-commit.com framework. orchestra's raw bash hook would have corrupted it. Plugin needs framework detection (BUG-006).

## Verification State

- pytest: **85 tests pass**
- eval scenarios: **10/10 pass**
- All 4 versions tagged + GitHub-released
- Two repos pushed to remote and decoupled

## Resuming Next Session

A fresh session should:

1. Read this doc + `docs/plans/2026-05-06-orchestra-roadmap.md` + `docs/design/orchestra-philosophy.md`
2. Read auto memory `MEMORY.md` for user context
3. Check `docs/bugs/BUG-001` through `BUG-007` for pending v1.4 scope
4. Decide entry point:
   - **v1.4 cleanup** — write LLD-004 covering all 7 bugs, plan, execute. Fast (most fixes are localized).
   - **v1.5 positioning shift** — bigger scope (plugin scan + registry gen). LLD-005 + roadmap deviation log if priorities change.
   - **Other** — user-directed.

## Changelog

| Date | Change |
|---|---|
| 2026-05-06 | Initial handoff doc. Captures v1.0-v1.3 ship + SCALE decoupling + 7 BUGs filed. Status: Active. |
