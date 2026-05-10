# State of Orchestra — LLD-006-r4 Implementation Handoff

> **Doc ID:** 2026-05-08-state-of-orchestra-lld-006-handoff
> **Date:** 2026-05-08
> **DRI:** Hassan Mohiddin
> **Type:** Implementation Handoff / Session State Snapshot
> **Status:** Active

## Session Arc Summary (2026-05-07 + 2026-05-08)

### What started

Session 2026-05-07 began with v1.4 cleanup release (8 BUGs queued from prior session). Began implementing BUG-008 + BUG-001 + BUG-002. User caught Gate 3 violation: agent added "Iteration N spec review — X/4 gates pass" markers WITHOUT actually running review. Cargo-cult marker pattern (compliance theater).

### What unfolded

Decided Path B: rollback v1.4 work + redesign architecture. 4 unpushed commits dropped via `git reset --hard f88abb7`.

**Six research rounds dispatched** (all in `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md`):

1. Workflow + spec-review architecture → **Attested Supersession with Out-of-Context Review** pattern
2. Context rot + rule drift → **4-placement architecture** (system prompt / UserPromptSubmit hook / fresh subagent / PreToolUse JIT)
3. Memory architectures → **L0 Claude Code primitives only**; no RAG/vector for ≤1000 docs
4. Gates + philosophy audit → policy-as-code lineage; rebuild Gate 3 + Gate 5; remove "markdown > code" stance
5. File format choice → markdown body + YAML frontmatter for prose; YAML sidecars for attestations; JSONL for metrics
6. Spec-review skill architecture (LLD-007 prep) → builder/validator pattern; Codex schema-forced JSON; cavecrew one-line/severity-emoji format; superpowers placeholder template; LLM-judge bias mitigations

### LLD attempts (5 iterations)

| Doc | Status | Attestation | Verdict |
|---|---|---|---|
| LLD-005 r1 (5-pillar atomic) | Rejected | `docs/reviews/005-r1.review.yaml` | FAIL (25 findings) |
| LLD-005 r2 | Rejected | `docs/reviews/005-r2.review.yaml` | FAIL (23 findings) |
| LLD-006 r1 (smaller scope: doc-handling conventions only) | Rejected | `docs/reviews/006-r1.review.yaml` | FAIL (12 findings) |
| LLD-006 r2 | Rejected | `docs/reviews/006-r2.review.yaml` | FAIL (10 findings; Evidence PASS) |
| LLD-006 r3 | Rejected | `docs/reviews/006-r3.review.yaml` | FAIL (11 findings; Evidence PASS) |
| **LLD-006 r4** | **CANON (conditional_pass)** | `docs/reviews/006-r4.review.yaml` | conditional_pass after 7 inline fixes |

### Migration dogfood executed 2026-05-08

Per LLD-006-r4 § Migration:
- LLD-005 r1 + r2 → `docs/archive/features/` (Status: Rejected)
- LLD-006 r1 + r2 + r3 → `docs/archive/features/` (Status: Rejected per promotion rule branch 2)
- LLD-006-r4 → stays at `docs/features/` (canon-frozen pending implementation)
- Attestations stay at `docs/reviews/` with updated `doc_subject.path` fields

**v1.5 architecture validated end-to-end on its own design docs.**

## Current Repo State

```
docs/
├── features/                                                  # canon
│   ├── 001-design-docs-init.md                                  (v1.1, Verified)
│   ├── 002-v1.2-migration-viewer-commit-msg.md                  (v1.2, Verified)
│   ├── 003-v1.3-doc-browser-mkdocs.md                           (v1.3, Verified)
│   └── 006-archive-and-supersession-conventions-r4.md           (LLD-006-r4, conditional_pass canon)
├── archive/
│   └── features/                                               # 5 rejected docs
│       ├── 005-v1.5-enforcement-core.md                         (Rejected)
│       ├── 005-v1.5-enforcement-core-r2.md                      (Rejected)
│       ├── 006-archive-and-supersession-conventions.md          (r1, Rejected per promotion rule)
│       ├── 006-archive-and-supersession-conventions-r2.md       (r2, Rejected)
│       └── 006-archive-and-supersession-conventions-r3.md       (r3, Rejected)
├── reviews/                                                   # 6 attestations
│   ├── 005-r1.review.yaml
│   ├── 005-r2.review.yaml
│   ├── 006-r1.review.yaml
│   ├── 006-r2.review.yaml
│   ├── 006-r3.review.yaml
│   └── 006-r4.review.yaml                                       (conditional_pass)
├── investigations/
│   └── 2026-05-07-workflow-spec-review-brainstorm.md            (6 research rounds + grill answers + pre-dispatch checklist)
├── plans/
│   └── 2026-05-08-state-of-orchestra-lld-006-handoff.md         (this file)
├── bugs/                                                      # 8 BUGs from session 1 (untouched, awaiting v1.6+)
│   ├── BUG-001-init-flow-not-interactive.md
│   ├── BUG-002-gitignore-affects-tracked-files.md
│   ├── BUG-003-mkdocs-tags-page-missing.md
│   ├── BUG-004-templates-not-project-aware.md
│   ├── BUG-005-mkdocs-nav-no-auto-detect.md
│   ├── BUG-006-install-hooks-precommit-framework.md
│   ├── BUG-007-mkdocs-yaml-python-tag-strict-validators.md
│   └── BUG-008-spec-review-gate3-no-enforcement.md              (will be superseded by LLD-007)
├── adr/, design/, postmortems/, runbooks/                     # unchanged from v1.3 ship
```

## What LLD-006-r4 Specifies (recap for fresh session)

**Scope:** Pure organizational. NO new features beyond file conventions + lint enforcement.

**5 deliverables:**

1. **Archive directory convention** — `docs/archive/<type>/` for rejected + superseded docs
2. **Supersession workflow** — never in-place edit canon-frozen; new revision = `-rN` suffix file with `Supersedes:` link; prior moves to archive
3. **Doc-id-burn policy** — first-iteration ids never reused; supersession-iteration files exempt (use r-suffix uniqueness instead)
4. **4 lint checks** — L1 Refs:-eligibility / L2 narrow-change enforcement / L3 attestation path-mutation guard / L4 doc-id-burn (first-iter + supersession-iter handling)
5. **`cli.lifecycle` helper** — small CLI for `reject` and `update-attestation-paths` operations

**13 unit tests + 1 eval scenario specified.**

**Plugin version:** 1.3.0 → 1.5.0 (1.4 burnt; never released).

**Pytest baseline:** 85 tests (verified 2026-05-07). Target post-merge: 98.

## v1.6 Followup Items (from r4 attestation)

Tracked in `docs/reviews/006-r4.review.yaml`:

1. L4 self-check path-resolution refinement (`samefile`/`normpath` or require resolved Path at function entry)
2. Validate `cli.lifecycle` against real implementation; surface spec gaps via tests
3. Migration window contract: rejection-finalization → git mv → attestation update ordering
4. Refs-target-archived-in-subsequent-commit semantics

## Resume Instructions for Fresh Session

### Immediate next step: Implement LLD-006-r4

Read in this order:
1. `docs/features/006-archive-and-supersession-conventions-r4.md` (the LLD)
2. `docs/reviews/006-r4.review.yaml` (attestation + v1.6 followups)
3. THIS handoff doc
4. `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` (research history; only sections relevant to LLD-006 are early; LLD-007 architecture in Round 6)

### Implementation tasks (LLD-006-r4)

In dependency order:

1. **`cli/lint.py` extensions:**
   - L1: `lint_commit_refs_eligible()` — Refs:-eligible check on all commit types; rejects archive/, investigations/, reviews/, plans/, non-canon-frozen docs
   - L2: `lint_commit_no_canon_inplace_edit()` + `is_narrow_change()` — uses `python-frontmatter` lib; whitelist {Status, Iteration, Superseded by} + Changelog append-only
   - L3: `lint_attestation_path_resolution()` — two-locations rule (canon prefix OR archive prefix) + existence
   - L4: `lint_doc_id_burn()` — first-iteration vs supersession-iteration handling; glob excludes file-being-added (P9 checklist)

2. **NEW `cli/lifecycle.py`:**
   - `reject` subcommand: Status: Rejected + Reason + Iteration unchanged
   - `update-attestation-paths` subcommand: rewrite `doc_subject.path` field per `resolve_supersession_link()`

3. **`cli/templates/standards-default-7.md`** — add Archive Convention + Supersession Workflow + Rejected-supersession + Doc-ID Burn + Refs Line Restriction sections

4. **`skills/design-docs/SKILL.md`** — add Archive + Supersession + Rejected-supersession workflow section

5. **`skills/design-docs/init/prompts.md`** — terminology refresh

6. **13 new tests** per Testing § (T1, T2, T3, T4, T5, T6, T7, T8, T9, T10a, T10b, T10c, T11)

7. **1 new eval scenario** at `eval/scenarios/archive-refs-blocked.json`

8. **Version bump** `pyproject.toml` + `.claude-plugin/plugin.json`: 1.3.0 → 1.5.0

9. **CHANGELOG.md** v1.5.0 entry

10. **Status updates:** LLD-006-r4 Status Draft → Implemented (after `make check` green) → Verified (after eval all-pass)

### Process discipline going forward

The architecture LLD-006-r4 defines is NOT YET ENFORCED in code — it's specified. Until `cli.lint` extensions ship, supersession + archive conventions are honor-system. Lint tests T1-T11 will validate the rules once implemented.

For LLD-007 (next), apply the same 4-gate review process via fresh subagent dispatch + YAML attestation. r4's review pattern is the canonical example.

## v1.6+ Roadmap (NOT yet planned in detail)

After LLD-006-r4 implementation:

| Version | Scope | Notes |
|---|---|---|
| v1.5.x patches | LLD-006-r4 v1.6 followups (4 items above) | Address as observed in real usage |
| v1.6 | LLD-007 — orchestra:spec-review skill + attestation creation | Round 6 architecture ready; build using LLD-006 supersession primitives |
| v1.7+ | Backfill 8 v1.4 BUGs under v1.5 process | Each fix uses subagent review + attestation |
| v1.8+ | Memory architecture (4-placement) | LLD-008 |
| v1.9+ | Lessons capture (capture-only first) | LLD-009 |
| v2.0+ | Skills registry auto-population | LLD-010 |
| v2.x | Workflow orchestration + backward-flow process workflow | Beyond file-level supersession |

## Honest Caveats

- **r4 attestation reflects author-applied fixes after fresh subagent review, not a second independent review pass.** A second subagent run on fixed r4 would be more rigorous; deferred per session direction to proceed.
- **content_hash mismatch in archived attestations is benign.** Hashes were computed against pre-rejection-finalization Draft state. Post-rejection edits add Status + Reason to frontmatter. r4 L3 lint check validates path resolution + existence, NOT hash; mismatch on archived docs is correct audit-snapshot semantics.
- **Five-iteration cap:** LLD-006 chain hit 4 attempts before converging. The slow-but-real progress (25 → 23 → 12 → 10 → 11 → 9 → 2 findings) suggests bootstrap-mode design (writing the LLD that defines the primitives that don't yet exist) is genuinely token-expensive. Future LLDs should ship under v1.5 process (working primitives) and converge faster.
- **Pre-dispatch pattern checklist** (P1-P9 in brainstorm scratch) was added after r2 fail. Apply to every future LLD draft before subagent dispatch.

## Pre-Dispatch Pattern Checklist (apply before every subagent review)

| # | Pattern | Catch by |
|---|---|---|
| P1 | Citations without URLs | Every external ref must include URL or be removed |
| P2 | Hand-wavy helper functions ("details in implementation") | Every helper either fully specified OR named with cited parser library |
| P3 | OR / "alternatively" in design decisions | Every design decision commits to ONE; if undecided → open question, don't OR |
| P4 | Multiple definitions of same term | Single source of truth (Glossary); other sections reference Glossary |
| P5 | Acceptance items without tests | Every acceptance item maps 1:1 to a test in Testing § |
| P6 | Self-conflict (rule applied to its own LLD breaks) | Apply each new rule to the LLD itself as sanity check before dispatch |
| P7 | Temporal ambiguity (current vs post-merge) | Explicit "BEFORE merge" / "AFTER merge" labels on every dual-state mention |
| P8 | Silent decisions / "improvise it" | Interview Gate — surface to user before deciding silently |
| P9 | New machinery without interaction-check vs existing rules | Run mental test: does new rule break any existing rule on dogfood case? |

## Changelog

| Date | Change |
|---|---|
| 2026-05-08 | Handoff doc created post-LLD-006-r4 conditional_pass + dogfood migration. Status: Active. Next session: implement LLD-006-r4 per "Resume Instructions" section above. |
