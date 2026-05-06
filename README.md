# Orchestra

> Disciplined AI engineering toolkit. Many skills playing together. One conductor.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-orange.svg)](https://docs.claude.com/en/docs/claude-code/plugins)

By [Hassan Mohiddin](https://github.com/hassan-mohiddin) — founder/CEO of SCALE.

---

## What is Orchestra

Orchestra is a Claude Code plugin that ships a curated set of skills for **doc-driven, gate-enforced AI engineering**. Each skill encodes an industry-grade pattern; together they form a workflow that prevents the most common failure modes of agent-led code change (orphan fix-commits, design drift, doc rot, undisciplined multi-attempt bug fixes).

The metaphor: an orchestra has many instruments, but they all play to the same score. Each Orchestra skill plays its part in a unified discipline.

## What ships in v1.0

**🎼 design-docs** — typed documentation discipline (the first instrument)

Triggers when a feature, bug, architectural decision, incident, runbook, or component architecture needs writing up before code is written.

- **7 typed doc templates** — Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc (living), short-form ADR. Every template has industry-canonical sections.
- **2 cross-tool AI standards** — `AGENTS.md` (Linux Foundation Agentic AI Foundation, 60k+ projects) at repo root, `llms.txt` (Jeremy Howard / Answer.AI) for external LLMs.
- **4-gate spec review** — Completeness / Evidence / Clarity / Consistency. Failures named, not vague.
- **Auto-numbering** — `next_doc_number.sh` returns `003`, `BUG-014`, `ADR-007`, `POSTMORTEM-2026-05-06`. Bash octal-safe.
- **Mandatory mermaid diagrams** — sequence (LLD/Bug/Postmortem), activity (workflows), architecture (system), deployment (infra). 5 diagram-type guides + 28-error troubleshooting reference.
- **Industry-aligned vocabulary** — ADR is RECORDED, not deliberated (Nygard 2011). Design Doc replaces deprecated HLD. RFC opt-in for team mode only.
- **Bug iteration loop** — One BUG-NNN doc spans all fix attempts. `fix:` commit only after user confirms. No more orphan fix-commits.
- **Doc gates** — Discovery / Design / Spec Review / Commit / Implementation Sync. Five named gates that block code from drifting from docs.
- **Lint CLI** — `python -m cli.lint` validates `Refs:` line on `fix:` / `feat:` commits, doc metadata, status enums. Pre-commit + GitHub Action ready.
- **Auto `DECISIONS.md` index** — `python -m cli.decisions_index` generates a searchable ADR index with relationship types (Supersedes / Superseded by / Related) + bidirectional consistency checking.

## Roadmap — future instruments

The Orchestra umbrella will absorb additional skills over time. Planned:

| Skill | Purpose | Status |
|-------|---------|--------|
| `orchestra:design-docs` | Typed docs + 4-gate review (this release) | ✅ v1.0 |
| `orchestra:workflow` | Master workflow file with situation-language routing | 🟡 v1.1 |
| `orchestra:skills-registry` | Situation → skill binding table + override rules | 🟡 v1.1 |
| `orchestra:tasks` | Task-tracking discipline + cross-agent state | 🟡 v1.2 |
| `orchestra:gates` | Pre-commit / CI gate enforcement (broader than docs) | 🟡 v1.2 |
| `orchestra:plans` | Plan-as-source artifact with TDD vertical slicing | 🟡 v1.3 |

Subscribe via repo watch for releases.

---

## Why another doc / orchestration plugin

| Plugin | Doc types | Gates | Bug iteration | Mandatory mermaid | Multi-skill umbrella |
|---|---|---|---|---|---|
| **orchestra** (this) | **7** | **5 (Discovery / Design / Spec Review / Commit / Sync)** | ✅ One-doc-spans-attempts | ✅ Required for LLD/Bug/Postmortem | ✅ (v1.1+) |
| Pimzino/claude-code-spec-workflow | 4 | 0 | ❌ | Optional | ❌ |
| rvdbreemen/adr-kit | 1 (ADR) | 4 | n/a | ❌ | ❌ |
| anthropics/skills doc-coauthoring | Generic | 0 | ❌ | ❌ | ❌ |
| obra/superpowers | n/a (process skills) | n/a | n/a | n/a | ✅ |
| mattpocock-skills | n/a (process skills) | n/a | n/a | n/a | ✅ |

No competitor combines typed doc taxonomy + 5 gates + bug iteration loop + mandatory mermaid + multi-skill orchestration umbrella. Orchestra does.

---

## Install

### Via plugin marketplace (recommended once approved)

```bash
/plugin marketplace add hassan-mohiddin/orchestra
/plugin install orchestra
```

### Direct git install

```bash
/plugin install hassan-mohiddin/orchestra
```

### Local development

```bash
git clone https://github.com/hassan-mohiddin/orchestra.git
claude --plugin-dir ./orchestra
```

---

## Usage — design-docs skill

Trigger by describing your situation. Description matches naturally:

| You say | Skill produces |
|---|---|
| "I want to add transaction search" | Feature LLD at `docs/features/NNN-name.md` |
| "Found a bug — auth tokens leak on refresh" | Bug Report at `docs/bugs/BUG-NNN-name.md` |
| "We've decided to migrate to Postgres" | ADR at `docs/adr/ADR-NNN-name.md` |
| "Auth had a 23-min outage this morning" | Postmortem at `docs/postmortems/POSTMORTEM-YYYY-MM-DD-name.md` |
| "Need a runbook for queue backlogs" | Runbook at `docs/runbooks/RUNBOOK-name.md` |
| "Update the api-design doc — v2 endpoint shipped" | Updates `docs/design/api-design.md` + Changelog |
| "Set up AGENTS.md so Cursor + Codex see context" | `AGENTS.md` + symlink instructions |

For every produced doc, the skill walks you through:

1. **Get doc number** — `bash skills/design-docs/scripts/next_doc_number.sh <type>` returns the next ID
2. **Load template** — only the template you need (progressive disclosure)
3. **Fill all sections** — no `TBD`, no placeholders
4. **Add mermaid diagram** — sequence/activity/architecture/deployment per type
5. **Run 4-gate spec review** — Completeness / Evidence / Clarity / Consistency
6. **Commit doc before code** — `Refs:` line links every `fix:`/`feat:` to its doc

---

## Viewing diagrams

Orchestra docs include mermaid diagrams in markdown code fences. Render them with:

| Tool | Setup | Use case |
|---|---|---|
| **GitHub** | None — native render in markdown preview, PRs, issues, README | Reading docs in PR review or browsing repo on github.com |
| **VS Code** | Install ["Markdown Preview Mermaid Support"](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) extension | Local editing + preview side-by-side |
| **JetBrains IDEs** | Install [Mermaid plugin](https://plugins.jetbrains.com/plugin/20146-mermaid) | Same — preview pane in IntelliJ/PyCharm/etc. |
| **mermaid.live** | None — paste markdown into [mermaid.live](https://mermaid.live) | Ad-hoc editing, sharing renderable links |
| **CLI offline** | `npx -y @mermaid-js/mermaid-cli -i doc.md` (no install needed; fetches per-invocation) | Air-gapped environments, batch export to PNG/SVG |
| **`cli.viewer` (v1.2)** | `python -m cli.viewer render docs/path.md` (or `render-all`) | Orchestra-managed export to `docs/.rendered/`. Auto-appends `docs/.rendered/` to `.gitignore` on first run. `--format png\|svg`, `--output <dir>`. |
| **MkDocs site (v1.3 — Tier 3)** | `python -m cli.viewer install-mkdocs` → `pip install -r requirements-docs.txt` → `mkdocs serve` | Full doc browser at `http://localhost:8000`. Mermaid renders natively, full-text search, type/status filters, GitHub Pages publish via `python -m cli.viewer publish-gh-pages`. |

Mermaid validation is built into `python -m cli.lint --doc` and `--pre-commit` modes (default-on; opt out via `--no-mermaid`). Lint catches syntax errors at commit time so broken diagrams never land in main.

## Configuration

Edit your project's `.claude/settings.local.json` or `.claude/settings.json`:

```json
{
  "orchestra": {
    "mode": "solo",
    "doc_paths": {
      "features": "docs/features",
      "bugs": "docs/bugs",
      "adr": "docs/adr",
      "design": "docs/design",
      "postmortems": "docs/postmortems",
      "runbooks": "docs/runbooks",
      "plans": "docs/plans"
    },
    "spec_review_skill": "superpowers:requesting-code-review"
  }
}
```

### `mode` — solo or team

- **solo** (default) — Single decision-maker. RFC vocabulary suppressed. ADRs record decisions you've made. No reviewer-assignment workflow.
- **team** — 2+ senior engineers (industry threshold per Pragmatic Engineer). RFC vocabulary enabled (deliberation phase before ADR). Spec review can assign reviewers. ADR `OKR Alignment` field becomes mandatory.

### `doc_paths` — repo layout overrides

Default paths match the canonical layout. Override any path to point at your existing structure.

### `spec_review_skill` — Step 4.5 binding

The skill that handles Step 4.5 spec review. Default points at `superpowers:requesting-code-review`. Set to your own project's review skill, or `null` to skip review (not recommended).

---

## CLI tools

### `orchestra lint`

```bash
python -m cli.lint --commit HEAD                       # Lint a commit
python -m cli.lint --range main..HEAD                  # Lint a commit range
python -m cli.lint --doc docs/bugs/BUG-014-leak.md     # Lint a single doc
python -m cli.lint --pre-commit                        # Pre-commit hook mode
```

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: orchestra-lint
      name: orchestra lint
      entry: python -m cli.lint --pre-commit
      language: python
      stages: [pre-commit]
```

GitHub Action template ships at `.github/workflows/lint.yml`.

### `orchestra decisions-index`

Auto-generates `docs/adr/DECISIONS.md` — a searchable ADR index with relationship types and bidirectional supersession consistency checking.

```bash
python -m cli.decisions_index --adr-dir docs/adr/ --output docs/adr/DECISIONS.md
```

---

## Examples

See `examples/` for filled-in samples (all lint-green):

- `examples/bugs/BUG-001-checkout-double-charge.md`
- `examples/adr/ADR-001-postgres-to-timescale.md`
- `examples/postmortems/POSTMORTEM-2026-04-22-auth-token-expiry-boundary.md`

More examples (Feature LLD, Runbook, Design Doc, AGENTS.md) ship in v1.1.

---

## Industry alignment

Patterns adopted from public sources:

- **ADR format** — Michael Nygard, *Documenting Architecture Decisions* (Cognitect 2011)
- **Postmortem template** — Google SRE Book, *Postmortem Culture: Learning from Failure*
- **AGENTS.md spec** — [agents.md](https://agents.md/) (Linux Foundation Agentic AI Foundation, Dec 2025)
- **llms.txt spec** — [llmstxt.org](https://llmstxt.org/) (Jeremy Howard / Answer.AI, Sept 2024)
- **4-gate review** — [`rvdbreemen/adr-kit`](https://github.com/rvdbreemen/adr-kit) (Apr 2026)
- **Conventional Commits** — [conventionalcommits.org/v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- **Mermaid C4** — Simon Brown's C4 model adapted for inline markdown rendering
- **RFC vs ADR taxonomy** — *RFCs and Design Docs* (Pragmatic Engineer)

Surveyed 16 competing plugins to inform positioning. See `docs/competitor-analysis.md` (ships in v1.1).

---

## Skill structure

```
orchestra/
├── .claude-plugin/plugin.json         # Plugin metadata + config defaults
├── skills/
│   └── design-docs/                   # First skill (more coming)
│       ├── SKILL.md                   # Skill instructions + decision tree
│       ├── STANDARDS.md               # Canonical doc-section requirements
│       ├── templates/                 # 8 templates (Feature LLD, Bug, ADR, etc.)
│       ├── references/                # Spec review gates, mermaid guides, etc.
│       └── scripts/                   # next_doc_number.sh + diagram tooling
├── cli/
│   ├── lint.py                        # Refs: gate + metadata + status validator
│   └── decisions_index.py             # Auto DECISIONS.md generator
├── examples/                          # Filled-in lint-green sample docs
├── hooks/hooks.json                   # Hook stubs for project customization
├── .github/workflows/lint.yml         # CI lint workflow template
├── README.md                          # This file
├── LICENSE                            # MIT
├── CHANGELOG.md
└── CONTRIBUTING.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome — especially:

- New doc-type templates with industry citations
- Additional mermaid diagram types
- Lint CLI improvements
- Config conveniences for non-default repo layouts
- Future Orchestra skills (workflow, registry, tasks, etc.)

---

## Acknowledgements

- Patterns from Michael Nygard, Google SRE, Pragmatic Engineer's *RFCs and Design Docs*, Bruno Scheufler, Martin Fowler's *Architecture Decision Record* bliki
- Plugin structure inspired by [`obra/superpowers`](https://github.com/obra/superpowers) and `mattpocock-skills`
- 4-gate review naming adapted from [`rvdbreemen/adr-kit`](https://github.com/rvdbreemen/adr-kit)
- Mermaid troubleshooting reference adapted from [`SpillwaveSolutions/design-doc-mermaid`](https://github.com/SpillwaveSolutions/design-doc-mermaid)

---

## License

MIT — see [LICENSE](LICENSE). Created and maintained by [Hassan Mohiddin](https://github.com/hassan-mohiddin).
