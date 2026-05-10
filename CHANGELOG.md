# Changelog

## v1.6.1 — 2026-05-10

Dogfood patches shipped via LLD-006-r4 supersession workflow. r4 dogfood
ran `/orchestra:spec-review` on LLD-007 itself using the v1.6.0 skill
just shipped — produced 13 findings; this release addresses all of
them.

### Process note

Original v1.6.1 commits (`653db4e` + `bc359e7`) made body edits
in-place on the canon-frozen LLD-007. LLD-006-r4 § narrow change
forbids canon-frozen body edits — supersession required. Original
commits reverted (`68fd538`); this release re-applies the same
content via proper supersession: archive prior LLD as Rejected,
create `-r5.md` supersession file with patches, re-attest. Tooling
gaps that allowed the violation tracked as v1.6.x followups.

### Code

- Dropped `cli.spec_review` retry loop (`MAX_RETRIES = 0`). Stdin-bound
  dispatch makes in-Python retry meaningless.
- `doc_disappeared` try/except wraps write-time `read_bytes`
- Added 1 new pytest test (`test_doc_disappeared_between_dispatch_and_write`).
  Rewrote T5/T6 for single-attempt semantics. Pytest: 143 → 144.

### Docs

- LLD-007 superseded: `docs/archive/features/007-spec-review-architecture.md`
  → `docs/features/007-spec-review-architecture-r5.md` (Iteration: 5)
- All 13 r4 findings addressed in `-r5.md`
- 3 Minor r5 findings deferred to v1.6.2 followup

### Plugin metadata

- Version 1.6.0 → 1.6.1

## v1.6.0 — 2026-05-10

LLD-007 spec-review architecture shipped. Multi-judge with manual chair —
orchestra ships exactly one judge (`orchestra:spec-review`); user manually
invokes additional judges (codex adversarial-review, cavecrew-reviewer, etc.)
and decides verdict.

### Added

- `orchestra:spec-review` skill (judge-1 default) — fresh-context subagent
  dispatch via Task tool, 7-element adversarial prompt, schema-validated YAML
  attestations at `docs/reviews/<doc-id>-rN.review.yaml`
- `/orchestra:spec-review <doc-path>` slash command
- `cli.spec_review` Python sidecar — schema validation, path canonicalization,
  hash binding, verdict authoritative-compute, stale-state byte-compare,
  atomic-write (temp+fsync+os.replace)
- Attestation schema v1.0 (JSON-schema) — 4 gates (Completeness / Evidence /
  Clarity / Consistency), severity enum {Critical, Important, Minor},
  empty-findings + justification conditional rule, location-regex enforcement
- 36 new pytest tests (107 → 143)
- 1 new eval scenario `spec-review-yaml-schema-roundtrip` (11 → 12)
- `cli.lint` ALLOWED_ATTESTATION_PATH_PREFIXES extended for `docs/plans/` +
  `docs/archive/plans/` (plans are now valid spec-review targets)

### Bias mitigations

1. Position bias — prompt instructs ordering by location, not severity
2. Self-preference — `--force` required for same-iteration overwrite
3. Length bias — `max_tokens: 4000` Task kwarg per SKILL.md
4. Same-model bias (documented) — STANDARDS recommends running
   `/codex:adversarial-review` as judge-2 for different-model coverage

### Hardening (codex round 1-3 + plan codex round 1-3)

- F1 path traversal blocked (canonicalize_doc_path fail-closed)
- F2 verdict spoofing blocked (compute_overall_verdict authoritative)
- F3 anti-sycophancy bypass blocked (schema if/then justification rule)
- F4 path identity binding (post-schema canonical-path check)
- F5 canonicalize fail-closed for resolve errors
- F6 stale-state hash gate (byte-compare, not just hash)
- F8 single-snapshot semantics (TOCTOU-free)
- F9 repo-root anchoring (cwd-independent)
- A24/PF10 atomic-write contract (temp+fsync+os.replace)

### Dependencies

- Added: `jsonschema>=4`

## v1.5.1 — 2026-05-10

Interview Gate philosophy added — first half of the "backward-flow workflow"
discipline. Auto-loaded when scaffolded via `cli.init` (`docs/STANDARDS.md`)
and surfaced in the design-docs skill.

### Philosophy

When ANY of these hit, STOP and ask the user before proceeding silently:

- Low context / ambiguous instruction (blast radius >10 min)
- Silent design decision (architecture not in the doc/instruction)
- Ambiguous scope ("fix X" but multiple things qualify)
- Judgment call between roughly equal options (blast radius >10 min)
- Iteration plateau (same review/test failing 3+ times → context drift)
- Pre-dispatch checklist P3 (OR / "alternatively") or P8 ("improvise it")

Format: state + decision point + 2-4 options (one Recommended with reason).
Then stop and wait — do NOT pre-implement.

### NOT triggers

Mechanical execution, single-step ops with obvious answer, user said "use your
judgment", auto-mode with small blast radius.

### Files

- `cli/templates/standards-default-7.md` — Interview Gate section (scaffolds
  on init via `cli.init`)
- `skills/design-docs/SKILL.md` — Interview Gate addendum
- `docs/design/orchestra-philosophy.md` — Changelog v1.5.1 entry

### Origin

BUG-008 root-cause: silent design decisions + cargo-cult markers. Pre-dispatch
checklist P1-P9 (LLD-006-r4 brainstorm scratch) encodes same discipline at
LLD-author level. Interview Gate extends to general agent behavior.

### Deferred

Backward-flow workflow primitives (return-to-phase, feedback-loop state
machine, persistence) deferred to v2.0+ (LLD-011+ per orchestra roadmap).
Interview Gate ships standalone because it costs nothing to encode and
prevents the failure mode immediately.

## v1.5.0 — 2026-05-10

Implements LLD-006-r4 — archive + supersession file conventions. v1.4 burnt
(rolled back via `git reset --hard f88abb7` 2026-05-07; never released).

### New CLI

- **`python -m cli.lifecycle reject --file <path> --reason <line>`** — sets Status: Rejected + Reason: line. Idempotent.
- **`python -m cli.lifecycle update-attestation-paths --reviews <yaml>...`** — rewrites `doc_subject.path` after canon→archive moves. Idempotent.
- **`python -m cli.lint --attestations`** — runs L3 across all `docs/reviews/*.review.yaml`.

### New lint checks (cli/lint.py)

- **L1 Refs:-eligibility** — Refs: line on fix:/feat: must point to canon-frozen doc under one of `{features, bugs, adr, design, postmortems, runbooks}/`. Plans, archive, investigations, reviews are NOT Refs:-eligible.
- **L2 narrow-change** — in-place edit of canon-frozen doc allowed only for whitelisted frontmatter fields {Status, Iteration, Superseded by} + Changelog table append-only.
- **L3 attestation path-mutation** — `doc_subject.path` in review YAMLs must resolve to existing file under canon-or-archive prefix.
- **L4 doc-id-burn** — first-iteration doc-id strict-greater than max(canon ∪ archive); supersession-iteration `-rN` filenames exempt with r-suffix uniqueness.

### Conventions

- Archive directory: `docs/archive/<type>/` for Rejected + Superseded docs
- Supersession workflow: new `-rN` file with `Supersedes:` link → prior moves to archive (narrow-change Status flip permitted)
- Rejected-supersession rule: failed Draft revision moves to archive Rejected; prior frontmatter NOT mutated
- Filename: first iteration `NNN-name.md`; iterations 2+ `NNN-name-rN.md`
- Refs: line never points to plans/, archive/, investigations/, reviews/

### Dogfood migration

- `docs/archive/features/` populated with 5 Rejected docs: LLD-005 r1+r2, LLD-006 r1+r2+r3
- Architecture validated end-to-end on its own design docs

### Tests + eval

- 107 pytest tests (85 v1.3 baseline + 22 new v1.5 lint tests across L1-L4)
- 11/11 eval scenarios (10 v1.3 + 1 new: archive-refs-blocked)

### Dependencies

- python-frontmatter (>=1.1) — YAML frontmatter parsing for narrow-change check
- PyYAML (>=6.0) — attestation parsing

### Docs

- `docs/features/006-archive-and-supersession-conventions-r4.md` (canon LLD, conditional_pass)
- `cli/templates/standards-default-7.md` adds Archive Convention + Supersession + Doc-ID Burn + Refs sections
- `skills/design-docs/SKILL.md` adds Archive + Supersession Workflow section

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
