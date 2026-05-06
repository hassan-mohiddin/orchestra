---
name: design-docs
description: Use when a feature, bug fix, architectural decision, incident postmortem, operational runbook, or component-level architecture update needs a written design document before code is written or shipped. Triggers for new Feature LLDs, Bug Reports, ADRs, Postmortems, Runbooks, Design Doc updates, AGENTS.md / llms.txt sync, and Mermaid diagrams. Invoke this skill whenever the user mentions designing a feature, fixing a bug, recording a decision, writing up an incident, drafting a runbook, updating architecture diagrams, or producing any technical documentation — even if they don't explicitly say "design doc".
---

# Design Documentation Skill

## Overview

Industry-grade documentation discipline for AI-driven engineering. Produces typed docs (Feature LLD, Bug Report, ADR, Postmortem, Runbook) and maintains living Design Docs for system-wide architecture.

**Iron Law: No code without a design doc first.**

This skill encodes patterns from Michael Nygard (ADR), Google SRE (postmortems), Pragmatic Engineer (RFC vs ADR taxonomy), the AGENTS.md spec (Linux Foundation Agentic AI Foundation), and the llms.txt spec (Jeremy Howard / Answer.AI). The 4-gate spec review pattern is adapted from `rvdbreemen/adr-kit`.

## Setup detection (v1.1+)

Before doing anything else, check for `.claude/orchestra.json`. This is the canonical config location per ADR-001.

```
If .claude/orchestra.json exists:
  → Read config, proceed with normal skill flow.

If .claude/orchestra.json does NOT exist:
  → Check for v1.0 config at .claude/settings.local.json (orchestra namespace key).
    If found: prompt user to migrate (auto-routes to orchestra:design-docs:init).
    If not found: prompt user to run init.

Auto-prompt (when no config found):

    Orchestra not initialized in this repo. Initialize now?
    [y] Run init with defaults (recommended)
    [c] Customize first (mode / paths / doc types / optional add-ons)

  - On [y]: route to orchestra:design-docs:init skill, accept defaults.
  - On [c]: route to orchestra:design-docs:init skill, full prompt flow.
  - There is NO skip option. Orchestra is opinionated — use it or uninstall.
```

This auto-prompt path means a fresh repo install + first design-doc request triggers init automatically.

## Plugin config (when orchestra.json present)

Read the Orchestra plugin config from `.claude/orchestra.json` (primary) or `.claude/orchestra.local.json` (gitignored override):

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

If no config exists, defaults match the canonical layout. Override paths to match an existing repo structure.

### `mode` — solo or team

- **solo** (default) — Single decision-maker. RFC vocabulary suppressed. ADRs record decisions made. No reviewer-assignment workflow.
- **team** — 2+ senior engineers (industry threshold per Pragmatic Engineer). RFC vocabulary enabled. Spec review can assign reviewers. ADR `OKR Alignment` field becomes mandatory.

## Decision Tree

```
What are you producing?
  → New feature                  → Feature LLD       → templates/feature-lld.md
  → Bug fix                      → Bug Report        → templates/bug-report.md
  → Architectural decision       → ADR               → templates/adr.md (or adr-short.md)
  → Incident write-up            → Postmortem        → templates/postmortem.md
  → On-call operational guide    → Runbook           → templates/runbook.md
  → System component update      → Design Doc        → <doc_paths.design>/*.md
  → Cross-tool agent context     → AGENTS.md sync    → templates/agents-md.md
  → External LLM doc index       → llms.txt sync     → templates/llms-txt.md
  → Need a diagram               → Mermaid guide     → references/mermaid/<type>.md
```

In **team mode**, an additional decision branch fires:
- For architectural questions where the decision is NOT yet made → produce an RFC (deliberation phase) using the same `templates/adr.md` shape with status `Proposed`. Once the team decides, transition status to `Approved` and record it as an ADR.

## Step 1: Get Doc Number / ID

```bash
bash skills/design-docs/scripts/next_doc_number.sh features    # → 003
bash skills/design-docs/scripts/next_doc_number.sh bugs        # → BUG-001
bash skills/design-docs/scripts/next_doc_number.sh adr         # → ADR-001
bash skills/design-docs/scripts/next_doc_number.sh research    # → 001
bash skills/design-docs/scripts/next_doc_number.sh postmortem  # → POSTMORTEM-2026-05-06
```

Runbooks are not numbered — name describes the alert/symptom (`RUNBOOK-celery-queue-backlog.md`).

## Step 2: Load Template

Read ONLY the template you need:

| Work type | Template | Output path (default) |
|-----------|----------|----------------------|
| Feature | `templates/feature-lld.md` | `docs/features/NNN-name.md` |
| Bug fix | `templates/bug-report.md` | `docs/bugs/BUG-NNN-name.md` |
| ADR (architectural decision) | `templates/adr.md` | `docs/adr/ADR-NNN-name.md` |
| ADR — short form | `templates/adr-short.md` | `docs/adr/ADR-NNN-name.md` |
| Postmortem | `templates/postmortem.md` | `docs/postmortems/POSTMORTEM-YYYY-MM-DD-name.md` |
| Runbook | `templates/runbook.md` | `docs/runbooks/RUNBOOK-name.md` |
| System component | `templates/api-design-template.md`, `database-design-template.md` | `docs/design/*.md` |
| AGENTS.md | `templates/agents-md.md` | `AGENTS.md` (repo root) |
| llms.txt | `templates/llms-txt.md` | `llms.txt` (site root) |

If `doc_paths` is overridden in plugin config, substitute those paths instead.

Fill ALL sections. No placeholders. No TODOs.

**Vocabulary:**
- "Design Doc" is the canonical term for living component-level architecture. The deprecated term "HLD" is no longer used.
- "ADR" records a decision that has been made. Long "Options Considered" sections without a chosen direction = RFC, not ADR. In **solo mode**, RFC vocabulary is not used. In **team mode**, RFCs can exist as ADRs in `Proposed` status during deliberation.

## Step 3: Add Mermaid Diagram

Per `STANDARDS.md` (this plugin ships its own copy as a reference):

| Doc Type | Minimum |
|----------|---------|
| Feature LLD | 1 (sequence or activity) |
| Bug Report | 1 (sequence showing bug data path) |
| Postmortem | 1 (failure path: trigger → system → users) |
| ADR | 0–1 (current → proposed if architecture change) |
| ADR (short) | 0 |
| Runbook | 0 |
| Design Doc | 3+ (architecture + data flow + deployment) |

Load ONLY the guide you need:

| Diagram type | When | Load |
|-------------|------|------|
| Sequence | API flows, service interactions, bug paths, failure paths | `references/mermaid/sequence-diagrams.md` |
| Activity/Flowchart | Workflows, business logic | `references/mermaid/activity-diagrams.md` |
| Architecture | System components, C4 | `references/mermaid/architecture-diagrams.md` |
| Deployment | Infrastructure, Docker, cloud | `references/mermaid/deployment-diagrams.md` |
| Symbols | Unicode catalog | `references/mermaid/unicode-symbols.md` |

**Diagram validation:** `references/resilient-workflow.md`
**If diagram fails to render:** `references/troubleshooting.md` (28 known errors)

**Style rules:**
1. Unicode symbols always (🔐 🌐 ⚙️ 💾 📬 👤)
2. High-contrast accessible colors
3. Descriptive labels ("Auth Service (JWT)" not "Service A")

## Step 4: Design Doc Sync Check + Changelog

After any Feature LLD, Bug Report, or Postmortem, check if a living Design Doc needs updating:

1. Read `references/design-doc-sync-protocol.md`
2. Identify affected Design Doc files
3. Update affected sections + add changelog entry at bottom

After any major doc change (new doc type, new convention, new command), check if `AGENTS.md` and `llms.txt` need updating:

1. Read `references/agents-md-llms-txt.md`
2. Update AGENTS.md if a new agent-relevant convention was added
3. Update llms.txt entries if architecture or public docs changed

**All docs require a Changelog section.** Add an entry on creation and on every status transition or material edit.

## Step 4.5: Spec Review — Four Gates (MANDATORY)

After writing or updating ANY doc destined for `docs/` and a commit — before committing — run a spec review against four named gates.

The spec-review skill is configured via plugin config (`spec_review_skill`). Default: `superpowers:requesting-code-review`. Set to your project's review skill, or `null` to skip review (not recommended).

**The four gates** (full detail in `references/spec-review-gates.md`):

| # | Gate | What it checks |
|---|------|----------------|
| 1 | **Completeness** | All required sections present and filled — no `TBD`, no empty tables |
| 2 | **Evidence** | Every claim has a backing artifact (file:line, benchmark, log, citation) |
| 3 | **Clarity** | A fresh reader can act on the doc without prior conversation context |
| 4 | **Consistency** | Doc agrees with itself, peer docs, and current code |

**Review focus by doc type:** see `references/spec-review-gates.md`.

**Process:**

1. Invoke spec-review skill (per config), passing the four-gate reference
2. Fix all issues found, naming the failing gate ("Gate 2 fails — root cause has no file:line citation")
3. Re-invoke until all gates pass
4. Max 3 iterations; if still failing, surface to user — the doc may need design rework

**Block commit until spec review passes.** A doc with open review issues is not ready to commit.

**Scratch carve-out:** Step 4.5 applies to docs destined for commit. Workspace scratch (`.eval-workspace/`, `.scratch/`, etc.) may skip — but must be deleted or promoted to `docs/` (with full review) before any code references them.

## Step 5: Commit Docs Before Code

```bash
git add docs/
git commit -m "docs: add LLD for <feature-name>"
```

Use the plugin's `cli/lint.py` to validate before commit:

```bash
python -m cli.lint --pre-commit
```

For bug fixes, no `fix:` commit until the user explicitly confirms the bug is resolved. Use `wip:` during iteration. The `cli/lint.py` checks the `Refs:` line on every `fix:`/`feat:` commit — orphan commits (no `Refs:` pointing to a real doc) fail.

## Reference Index (load on demand — do NOT preload all)

| File | Load when |
|------|-----------|
| `STANDARDS.md` (in this plugin) | Before writing any doc — canonical required fields and sections |
| `references/spec-review-gates.md` | Running spec review (Step 4.5) |
| `references/doc-standards.md` | Need implementation notes (scripts, auto-numbering) |
| `references/design-doc-sync-protocol.md` | After writing any LLD or Bug Report — Design Doc sync rule |
| `references/agents-md-llms-txt.md` | Initializing or syncing AGENTS.md / llms.txt |
| `references/resilient-workflow.md` | Generating or validating diagrams |
| `references/troubleshooting.md` | Diagram fails to render |
| `references/mermaid/activity-diagrams.md` | Need workflow/process diagram |
| `references/mermaid/sequence-diagrams.md` | Need API/data flow diagram |
| `references/mermaid/architecture-diagrams.md` | Need component diagram |
| `references/mermaid/deployment-diagrams.md` | Need infrastructure diagram |
| `references/mermaid/unicode-symbols.md` | Need symbol reference |

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/next_doc_number.sh` | Auto-increment doc number / emit date prefix | `bash scripts/next_doc_number.sh features\|bugs\|adr\|research\|postmortem` |
| `scripts/extract_mermaid.py` | Extract/validate diagrams in a doc | `python scripts/extract_mermaid.py doc.md --validate` |
| `scripts/resilient_diagram.py` | Generate + validate + save diagram | `python scripts/resilient_diagram.py --code "..." --title "flow"` |
| `scripts/mermaid_to_image.py` | Convert .mmd to PNG/SVG | `python scripts/mermaid_to_image.py diagram.mmd output.png` |

## CLI tools (plugin-level)

| Tool | Purpose |
|------|---------|
| `python -m cli.lint --pre-commit` | Pre-commit hook: validate Refs: line, doc metadata, status enums |
| `python -m cli.lint --range main..HEAD` | CI: lint commit range for orphan fix:/feat: commits |
| `python -m cli.lint --doc <path>` | Lint a single doc against STANDARDS |
| `python -m cli.decisions_index` | Auto-generate `docs/adr/DECISIONS.md` index with relationship types |

## Pitfall Rules (industry-research-derived)

1. **ADR is RECORDED, not deliberated.** Long "Options Considered" weighing alternatives without a chosen direction = RFC, not ADR. In solo mode, decide first; record after. In team mode, deliberation can use ADR-template-with-Proposed-status as an RFC.
2. **LLD vs Plan no-overlap.** LLD = WHAT to build (design, contracts, edge cases). Plan = HOW + ORDER (steps, dependencies, sequencing). A Plan re-stating LLD design content is doing the wrong thing.
3. **Bug iteration loop = one doc spans attempts.** Don't create BUG-001-attempt-1, BUG-001-attempt-2. One BUG-NNN doc, append Iteration Log entries, `fix:` only after user confirms.
4. **Postmortems are blameless.** Refer to roles ("the on-call engineer"), never names. The "Where We Got Lucky" section surfaces near-miss risks — highest-signal section.
5. **Runbooks rot fastest.** Update after every incident the runbook was used in. Mark `Outdated` if the system changed materially without runbook update.
6. **Design Docs are LIVING.** Sync them in the same commit as the feature, not in a follow-up PR. Use the changelog to record deviations from the original design.
7. **Skipping spec review on "small" updates is how docs rot.** Adding a changelog entry to a Design Doc still requires a Step 4.5 pass. The discipline IS the point.

## Industry citations

- ADR pattern — Michael Nygard, *Documenting Architecture Decisions* (Cognitect 2011)
- Postmortem template — Google SRE Book, *Postmortem Culture: Learning from Failure*
- 4-gate review — `rvdbreemen/adr-kit` (Apr 2026)
- ADR vs RFC distinction — *RFCs and Design Docs* (Pragmatic Engineer)
- AGENTS.md spec — Linux Foundation Agentic AI Foundation (agents.md)
- llms.txt spec — Jeremy Howard / Answer.AI (llmstxt.org, Sept 2024)
- Conventional Commits — conventionalcommits.org/v1.0.0
- C4 model — Simon Brown
