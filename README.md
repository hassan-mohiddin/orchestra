# design-docs

> Industry-grade documentation discipline for AI-driven engineering. The Claude Code plugin that turns "let me write a design doc first" from a habit into an enforced workflow.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-orange.svg)](https://docs.claude.com/en/docs/claude-code/plugins)

---

## What this plugin does

The `design-docs` skill ships:

- **7 typed doc templates** — Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc (living component-level), and short-form ADR. Every template has STANDARDS-aligned required sections.
- **2 cross-tool AI doc standards** — `AGENTS.md` (Linux Foundation Agentic AI Foundation, 60k+ projects) at repo root, and `llms.txt` (Jeremy Howard / Answer.AI) for external LLMs.
- **4-gate spec review** — Completeness / Evidence / Clarity / Consistency. Pattern adapted from `rvdbreemen/adr-kit`. Failures are named, not vague.
- **Auto-numbering** — `next_doc_number.sh` returns `003`, `BUG-014`, `ADR-007`, `POSTMORTEM-2026-05-06`. Bash octal-safe.
- **Mandatory mermaid diagrams** — Sequence (LLD/Bug/Postmortem), Activity (workflows), Architecture (system), Deployment (infra). 5 diagram-type guides + 28-error troubleshooting reference.
- **Industry-aligned vocabulary** — ADR is RECORDED, not deliberated (Nygard 2011). Design Doc replaces deprecated HLD. RFC opt-in for team mode only.
- **Bug iteration loop** — One BUG-NNN doc spans all fix attempts. `fix:` commit only after user confirms. No more orphan fix-commits.
- **Doc gates** — Discovery / Design / Spec Review / Commit / Implementation Sync. Five named gates that block code from drifting from docs.
- **Lint CLI** — `python -m design_docs.lint` validates `Refs:` line on `fix:` / `feat:` commits, doc metadata, status enums. Pre-commit + GitHub Action ready.
- **Auto `DECISIONS.md` index** — `python -m design_docs.decisions_index` generates a searchable ADR index with relationship types (Supersedes / Superseded by / Related).

---

## Why another doc plugin

| Plugin | Doc types | Gates | Bug iteration | Mandatory mermaid | Trigger accuracy |
|---|---|---|---|---|---|
| design-docs (this) | **7** | **5 (Discovery / Design / Spec Review / Commit / Sync)** | ✅ One-doc-spans-attempts | ✅ Required for LLD/Bug/Postmortem | Tightened via skill-creator iteration |
| Pimzino/claude-code-spec-workflow | 4 | 0 | ❌ | Optional | High mindshare (3.7k★) |
| rvdbreemen/adr-kit | 1 (ADR) | 4 (Completeness/Evidence/Clarity/Consistency) | n/a | ❌ | n/a |
| anthropics/skills doc-coauthoring | Generic | 0 | ❌ | ❌ | n/a |
| SpillwaveSolutions/design-doc-mermaid | 5 (design only) | 0 | ❌ | Embedded | Abandoned |

No competitor combines typed taxonomy + 5 gates + bug iteration + mandatory mermaid. This plugin does.

---

## Install

### Via plugin marketplace (recommended)

```bash
/plugin marketplace add mohammedhassanmohiddin/design-docs-claude
/plugin install design-docs
```

### Direct git install

```bash
/plugin install mohammedhassanmohiddin/design-docs-claude
```

### Local development

```bash
git clone https://github.com/mohammedhassanmohiddin/design-docs-claude.git
claude --plugin-dir ./design-docs-claude
```

---

## Usage

Trigger the skill by describing your situation. The skill description matches naturally:

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

## Configuration

Edit your project's `.claude/settings.local.json` or `.claude/settings.json`:

```json
{
  "design-docs": {
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

- **solo** (default) — Single decision-maker. RFC vocabulary is suppressed. ADRs record decisions you've made. No reviewer-assignment workflow.
- **team** — Two or more senior engineers. RFC vocabulary enabled (deliberation phase before ADR), reviewer assignment in spec review, OKR-alignment field on ADRs becomes mandatory.

Industry threshold for switching from solo to team is 2+ senior engineers per Pragmatic Engineer / Bruno Scheufler taxonomy. Re-evaluate when team grows.

### `doc_paths` — repo layout overrides

Default paths match the SCALE / industry-canonical layout. Override any path to point at your existing structure (e.g. `docs/design/specs/` instead of `docs/features/`).

### `spec_review_skill` — Step 4.5 binding

The skill that handles Step 4.5 spec review. Default points at `superpowers:requesting-code-review`. Set to your own project's review skill, or `null` to skip review (not recommended).

---

## CLI tools

### `design-docs lint`

Validates that:

- Every `fix:` / `feat:` commit has a `Refs:` line pointing to a real `docs/` file
- Every doc has the required metadata block (Doc ID, Date, Status)
- Status enum values are valid per doc type
- Mandatory sections are present + non-empty

```bash
# Lint last commit
python -m design_docs.lint --commit HEAD

# Lint range
python -m design_docs.lint --range main..HEAD

# Lint a specific doc
python -m design_docs.lint --doc docs/bugs/BUG-014-auth-leak.md

# Pre-commit hook mode (reads staged files)
python -m design_docs.lint --pre-commit
```

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: design-docs-lint
      name: design-docs lint
      entry: python -m design_docs.lint --pre-commit
      language: python
      stages: [pre-commit]
```

GitHub Action template ships at `.github/workflows/lint.yml`.

### `design-docs decisions-index`

Auto-generates `docs/adr/DECISIONS.md` — a searchable index of all ADRs with relationship types (Supersedes / Superseded by / Related).

```bash
python -m design_docs.decisions_index --adr-dir docs/adr/ --output docs/adr/DECISIONS.md
```

Run as a post-commit hook to keep the index fresh.

---

## Examples

See `examples/` for filled-in samples of every doc type:

- `examples/features/003-transaction-search.md`
- `examples/bugs/BUG-014-auth-token-leak.md`
- `examples/adr/ADR-007-postgres-to-timescale.md`
- `examples/postmortems/POSTMORTEM-2026-05-06-auth-outage.md`
- `examples/runbooks/RUNBOOK-celery-queue-backlog.md`
- `examples/design/api-design.md`

---

## Industry alignment

Patterns adopted from public sources:

- **ADR format** — Michael Nygard, *Documenting Architecture Decisions* (Cognitect 2011)
- **Postmortem template** — Google SRE Book, *Postmortem Culture: Learning from Failure*
- **AGENTS.md spec** — [agents.md](https://agents.md/) (Linux Foundation Agentic AI Foundation, Dec 2025)
- **llms.txt spec** — [llmstxt.org](https://llmstxt.org/) (Jeremy Howard / Answer.AI, Sept 2024)
- **4-gate review** — `rvdbreemen/adr-kit` (Apr 2026)
- **Conventional Commits** — [conventionalcommits.org/v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- **Mermaid C4** — Simon Brown's C4 model adapted for inline markdown rendering

Researched competitor landscape (16 plugins) — see `docs/competitor-analysis.md` if you want the full survey.

---

## Roadmap

- [ ] v1.1 — Live mermaid preview integration (via `veelenga/claude-mermaid` MCP, optional)
- [ ] v1.2 — Bidirectional ADR↔code traceability scanner (find ADR refs in code; find code-affecting ADRs)
- [ ] v1.3 — Plan→GitHub Issues converter (delegate to `mattpocock-skills:to-issues`)
- [ ] v1.4 — Reader Testing sub-flow (fresh Claude reads the doc back, surfaces context-bleed)
- [ ] v2.0 — Real-time progress dashboard (web UI)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome — especially:

- New doc-type templates with industry citations
- Additional mermaid diagram types
- Lint CLI improvements
- Config conveniences for non-default repo layouts

---

## Acknowledgements

- Patterns from Michael Nygard, Google SRE, Pragmatic Engineer's *RFCs and Design Docs*, Bruno Scheufler, Martin Fowler's *Architecture Decision Record* bliki
- Skill structure inspired by `obra/superpowers`, `mattpocock/skills`, `anthropics/skills`
- 4-gate review naming adapted from `rvdbreemen/adr-kit`
- Mermaid troubleshooting reference adapted from `SpillwaveSolutions/design-doc-mermaid`

---

## License

MIT — see [LICENSE](LICENSE).
