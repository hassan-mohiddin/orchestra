# Migration Plan — Controlled Vocabulary Canon

> **Doc ID:** 2026-05-11-vocab-canon-migration
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Implementation Plan
> **Status:** Implemented
> **Iteration:** 5
> **LLD:** `docs/design/controlled-vocabulary.md` (Design Doc, iter-7, Status: Current)
> **Related:** `docs/bugs/BUG-016-scattered-vocabulary-no-canon.md`

---

## Header

**Goal.** Retire every scattered controlled-vocabulary copy in the orchestra repo; replace with eager-load reads from `docs/design/controlled-vocabulary.md` via a new parser module `cli/vocabulary.py`. Ship canon-driven L1-L5 lint, canon-generated template, canon-cross-referenced STANDARDS.md, and per-judge attestation filename convention.

**Architecture.** Canon parser → all consumers. The canon Design Doc at `docs/design/controlled-vocabulary.md` defines a contract enforced via a new `cli/vocabulary.py` module that eager-loads 13 public symbols from the canon's §4 markdown tables. All scattered vocabulary copies (currently in `cli/lint.py` constants, `cli/templates/*.md` mirrors, `skills/spec-review/*.json+.md` schema, `docs/STANDARDS.md` enum tables) become either generated artifacts, transcluded references, or canon-import readers. Lint runs L1-L5 sourced from canon. See Design Doc §Architecture (Diagrams 1-3) and §Domain/Module/Endpoint Details for the full contract this plan implements. Plan describes ORDER only, no design decisions.

**Tech stack.** Python 3.12 (`.venv/bin/python3.12`), pytest, pyrefly, orchestra's own `cli.lint` + `cli.spec_review`. No new deps.

**Estimated time.** 8-12 hours across 11 vertical slices. Slices 1-5 are blocking; 6-11 are sequencing-flexible.

**Acceptance criteria.**

- [ ] `cli/vocabulary.py` exists, parses canon §4 deterministically, exposes 13 public symbols matching canon Design Doc §Public symbols.
- [ ] `cli/lint.py` imports all enums from `cli.vocabulary`; no inline `set` / `tuple` / `dict` literals for vocabulary.
- [ ] L5 lint check active: strict enum match for every doc's metadata.
- [ ] `cli.lint § REQUIRED_SECTIONS` matches `docs/design/controlled-vocabulary.md § 4.8` (which mirrors `docs/STANDARDS.md`).
- [ ] L4 lint accepts bare-name design supersession (also closes BUG-014).
- [ ] L1/L4 lint accepts `POSTMORTEM-YYYY-MM-DD-name(-rN)?.md` + `RUNBOOK-name(-rN)?.md` patterns per canon §4.10.
- [ ] All `*.review.yaml` files present in `docs/reviews/` at slice-6 execution time renamed to `<stem>.orchestra.review.yaml`. At plan iter-4 draft time, `ls docs/reviews/*.review.yaml | wc -l` = 45; slice 6 captures the actual set at execution time. Future attestations write the new convention from slice 7 onward per LLD §4.11.
- [ ] `cli/spec_review.py § compute_attestation_path` writes `.orchestra.review.yaml`.
- [ ] `cli/templates/vocabulary-default-1.md` generated from canon; CI drift test passes.
- [ ] `cli/templates/standards-default-7.md` cross-references canon for enum tables (no duplication).
- [ ] `docs/STANDARDS.md` enum tables replaced with transclude references to canon §4.X.
- [ ] `skills/spec-review/attestation-schema-v1.0.json` + `prompt-template.md` severity values match canon §4.3 `finding_gravity`; CI drift test gates.
- [ ] All existing tests pass; pyrefly 0 errors; `make check` clean. New test count target: 259 baseline + roughly 80-100 new tests across slices 1 (~19+: shared utility + 13 symbol tests + 5 failure modes), 3 (~50-60: one test per required-section per doc-type plus conditional-section optional tests), 4 (~6: design bare-name + POSTMORTEM + RUNBOOK first/supersession), 5 (~4: status/severity/verdict/gate-name invalid-value), 6 (1: filename regex assertion), 8 (1: template drift), 11 (~4: schema severity + verdict + gate names + prompt). Final exact count is determined by the matrix in slice 3.1 (canon §4.8 row sizes).
- [ ] Canon Design Doc transitions Status: Draft → Approved → Current (post-merge).

---

## File Structure

**New files (create):**

```
cli/_shared.py                                 # NEW walk-up _repo_root() for canon parser; imported by cli.vocabulary (NOT extracted from cli.lint — see slice 1.0a)
cli/vocabulary.py                              # parser + 13 public symbols
scripts/generate_vocab_template.py             # canon → cli/templates/vocabulary-default-1.md
cli/templates/vocabulary-default-1.md          # generated mirror
tests/test_vocabulary.py                       # parser tests
tests/test_lint_l5.py                          # L5 strict-enum-match tests
tests/test_template_drift.py                   # CI drift test
tests/test_review_filenames.py                 # canon §4.11 filename-regex assertion against docs/reviews/*
tests/test_spec_review_canon_drift.py          # schema severity/verdict drift gate
```

**Modified files:**

```
cli/lint.py                                    # repo-root NOT touched (existing repo_root_from_cwd at :1233 stays as-is — separate git-aware algorithm); remove inline literals (lines 62-72, 75-77, 81-84, 87, 90-96, 105-130, 137); import from cli.vocabulary; extend REQUIRED_SECTIONS via canon; add filename regexes; add L5 check
cli/spec_review.py                             # update § compute_attestation_path to emit .orchestra.review.yaml; delete orchestra_path inline f-string inside § render_cross_judge_report (now calls compute_attestation_path)
docs/STANDARDS.md                              # replace enum tables with transclude references to canon
cli/templates/standards-default-7.md           # same transclude rewrite (mirror)
skills/spec-review/attestation-schema-v1.0.json  # add comment/source-link to canon §4.3 finding_gravity (no value change, schema stays v1.0)
skills/spec-review/prompt-template.md          # same — source link, no value change
tests/test_lint.py                             # update for new REQUIRED_SECTIONS + filename regexes
tests/test_spec_review.py                      # update for new attestation_path output
docs/design/controlled-vocabulary.md           # Status: Draft → Approved → Current (status flips, not content edit)
```

**Renamed files (no content change) — all `*.review.yaml` in docs/reviews/ at slice-6 execution time.**

At plan iter-4 draft time (2026-05-11), `ls docs/reviews/*.review.yaml | wc -l` = 45. Slice 6 captures the actual set at execution time via that same command. No file is left unmigrated.

5 illustrative examples (most-recent at draft time):

```
docs/reviews/controlled-vocabulary-r5.review.yaml                            → controlled-vocabulary-r5.orchestra.review.yaml
docs/reviews/2026-05-11-vocab-canon-migration-r3.review.yaml                 → 2026-05-11-vocab-canon-migration-r3.orchestra.review.yaml
docs/reviews/008-commit-skill-r8.review.yaml                                 → 008-commit-skill-r8.orchestra.review.yaml
docs/reviews/BUG-014-l4-bare-name-design-supersession-r1.review.yaml         → BUG-014-l4-bare-name-design-supersession-r1.orchestra.review.yaml
docs/reviews/orchestra-philosophy-r2.review.yaml                             → orchestra-philosophy-r2.orchestra.review.yaml
```

Full transformation: every `docs/reviews/X.review.yaml` → `docs/reviews/X.orchestra.review.yaml`. Cross-doc reference fix-up in slice 6.2 covers `docs/HANDOFF.md`, `CLAUDE.md`, `.claude/**`, plus body-text refs in any other doc naming a specific attestation. Git history is NOT in scope.

---

## Tasks

TDD vertical slicing per `.claude/rules` — each slice = failing test first, implementation second, commit third. Sequencing column lists slice dependencies. Each slice ends with `make check` + commit.

**Cite stability rule.** All `cli/*.py § <function>` cites in this plan use function-name form (no line numbers) because `cli/spec_review.py` and `cli/lint.py` are being actively edited concurrently. Executor MUST resolve current line numbers via `grep -n "def <name>"` at slice execution time before editing. Constants ranges (`cli/lint.py:62-130, :137`) are stable until slice 2 deletes them all; those ranges are retained as direct line-number cites since deletion bounds drift.

### Slice 1 — `cli/_shared.py` extract + `cli/vocabulary.py` parser foundation

**Files:**

- `cli/_shared.py` (new — extracts `_repo_root` from `cli/lint.py`)
- `cli/lint.py` (modify — re-import `_repo_root` from `cli/_shared.py`)
- `cli/vocabulary.py` (new)
- `tests/test_vocabulary.py` (new)
- `tests/test_shared.py` (new — covers _repo_root walk-up + max-levels behaviour)
- `docs/design/controlled-vocabulary.md` (read-only — input)

**Dependencies:** none. First slice.

**Tasks:**

1.0. Failing test: `test_shared.py::test_repo_root_walks_up_to_plugin_json` — creates tmpdir tree with `.claude-plugin/plugin.json` at root + nested `__file__`-like path; assert `_repo_root()` returns the tmpdir root. Plus failing test for max-8-levels guard (`RuntimeError("orchestra repo root not found")`).

1.0a. Implementation: create `cli/_shared.py` with `_repo_root()` implementing **walk-up from `__file__` looking for `.claude-plugin/plugin.json`, max 8 levels** — this is a NEW function, not extracted (no `_repo_root` function exists in cli/lint.py today; `cli/lint.py § repo_root_from_cwd` uses `git rev-parse --show-toplevel`, a separate git-aware algorithm kept as-is for git-driven contexts). `cli/_shared.py` is imported by `cli/vocabulary.py` (slice 1.2 onward) and may also be imported by future canon-aware consumers. No changes to existing `cli/lint.py` consumers of `repo_root_from_cwd`.

1.1. Failing test: `test_vocabulary.py::test_status_enums_match_canon` asserts `cli.vocabulary.STATUS_ENUMS == { 'feature': frozenset({...}), ... }` matching canon §4.1 byte-for-byte.

1.2. Implement minimum parser to make 1.1 pass: locate `### 4.1` header, parse markdown table, return `frozenset`-valued `dict`. Eager-load at module import. `cli/vocabulary.py` imports `_repo_root` from `cli/_shared.py`.

1.3. Add failing test per remaining §4.X table: §4.2 `CANON_FROZEN_STATUSES`, §4.3 `SEVERITY_ENUMS`, §4.4 `VERDICT_ENUM`, §4.5 `DOC_TYPE_ENUM`, §4.6 `REFS_ELIGIBLE_PREFIXES`, §4.7 `ALLOWED_ATTESTATION_PATH_PREFIXES`, §4.8 `REQUIRED_SECTIONS`, §4.9 `REVIEW_GATE_NAMES`, §4.10 `FILENAME_GRAMMAR`, §4.11 `REVIEW_DOC_FILENAME_REGEX`, §4.12 `TERMINAL_STATE_SUFFIX`, §4.13 `WHITELIST_FRONTMATTER_FIELDS`. One test per symbol.

1.4. Implement remaining parser logic to make each test pass — incremental, one symbol at a time. Use canon Design Doc §Parse contract (under §Domain/Module/Endpoint Details) as the implementation contract.

1.5. Add failing tests for the 5 failure modes (canon §Failure modes table): subsection missing, table malformed, illegal value, header renumbered, file missing. Each test mutates a copy of the canon file in a tmpdir + asserts `RuntimeError` with the expected message prefix.

1.6. Implement failure-mode handling.

**Commit:** `feat(vocabulary): add cli.vocabulary canon parser`

Body: parses §4.X tables from `docs/design/controlled-vocabulary.md`; eager-load at import; 13 public symbols + 5 failure modes. Refs: docs/design/controlled-vocabulary.md.

### Slice 2 — Migrate `cli/lint.py` constants to canon

**Files:**

- `cli/lint.py` (modify)
- `tests/test_lint.py` (modify — read existing tests, ensure they still pass)

**Dependencies:** slice 1.

**Tasks:**

2.1. Failing test (already exists if tests cover lint constants): ensure `cli.lint.STATUS_ENUMS == cli.vocabulary.STATUS_ENUMS`, etc., for all 7 shared constants (status enums, canon-frozen, refs-prefixes, whitelist, attestation-prefixes, gate names, required-sections).

2.2. Implementation: delete the following inline literals from `cli/lint.py`: `STATUS_ENUMS` (lines 62-72), `CANON_FROZEN_STATUSES` (lines 75-77), `REFS_ELIGIBLE_PREFIXES` (lines 81-84), `WHITELIST_FRONTMATTER_FIELDS` (line 87), `ALLOWED_ATTESTATION_PATH_PREFIXES` (lines 90-96), `REQUIRED_SECTIONS` (lines 105-130), `ALLOWED_GATES` (line 137). Replace with `from cli.vocabulary import STATUS_ENUMS, CANON_FROZEN_STATUSES, REFS_ELIGIBLE_PREFIXES, WHITELIST_FRONTMATTER_FIELDS, ALLOWED_ATTESTATION_PATH_PREFIXES, REQUIRED_SECTIONS, REVIEW_GATE_NAMES as ALLOWED_GATES`. Note: filename regex patterns at lines 99-103 are retained until slice 4 (which moves them to canon-driven).

2.3. Run full `tests/test_lint.py` suite — must remain 259 baseline + new vocab tests passing.

2.4. `pyrefly check` — must remain 0 errors.

**Commit:** `refactor(lint): source constants from cli.vocabulary canon`

Body: removes inline enum literals; canon Design Doc is now the single source. No behavior change. Refs: docs/design/controlled-vocabulary.md.

### Slice 3 — Extend `cli/lint.py § REQUIRED_SECTIONS` to STANDARDS.md form

**Files:**

- `cli/lint.py` (modify; behavior change)
- `tests/test_lint.py` (modify — add failing tests per doc-type)
- `cli/vocabulary.py` (no change — already parses canon §4.8 which has stricter list)

**Dependencies:** slices 1, 2.

**Tasks:**

3.1. **Per LLD §4.8** — write one failing test per required-section per doc-type. The full enumeration of which sections are required and which are conditional lives in LLD §4.8; do not re-state here. Test scaffolding shape:
  - For each `(doc_type, required_section)` in `cli.vocabulary.REQUIRED_SECTIONS`, write `test_lint_l2_<doc_type>_missing_<section_slug>` that creates a tmpdir doc of that type with the named section removed and asserts L2 emits a Finding.
  - For each `(doc_type, conditional_section)` (marked `(if any)` / `(where applicable)` in canon §4.8), write `test_lint_l2_<doc_type>_<section_slug>_optional` asserting L2 ACCEPTS absence.
  - Expected new test count: roughly one per row × ~6 sections average ≈ 50-60 tests (research has 5 required + 0 conditional; design has 5 required; feature has 9 required + 2 conditional; etc.).

3.2. Implementation: conditional-section handling in L2. Mark sections with `(if any)` / `(where applicable)` as conditional; L2 accepts absence. Source of truth: `cli.vocabulary.REQUIRED_SECTIONS` per LLD §4.8.

3.3. Verify canon-driven loader returns the expanded `REQUIRED_SECTIONS` correctly (slice 1 should already cover this).

**Commit:** `feat(lint): extend REQUIRED_SECTIONS to STANDARDS.md form per canon §4.8`

Body: adds API Changes, Database Changes (feature conditional); Alternatives Briefly Rejected (adr); Architecture/ER, Domain/Module/Endpoint Details, Key Decisions (design); Header, Changelog (plan); Metadata, ToC, Recommendations, Sources (research); Examples (policy conditional). Closes lint-required-sections-extension task. Refs: docs/design/controlled-vocabulary.md.

### Slice 4 — Extend filename regex (canon §4.10) — closes BUG-014

**Files:**

- `cli/lint.py` (modify; lint regex constants + `lint_doc_id_burn`)
- `tests/test_lint.py` (modify)
- `cli/vocabulary.py` (verify §4.10 parsing exposes per-type patterns)
- `docs/bugs/BUG-014-l4-bare-name-design-supersession.md` (status flip Investigating → Fix Applied after slice ships)

**Dependencies:** slices 1, 2.

**Tasks:**

4.1. Failing test: bare-name design supersession `docs/design/controlled-vocabulary-r2.md` (or any similar) — L4 must NOT reject.

4.2. Implement: add `DESIGN_BARE_NAME_RE` and `DESIGN_BARE_NAME_SUPERSESSION_RE` adjacent to the existing pattern block at `cli/lint.py:99-103` (constants range — stable until slice 2 + slice 4 land), sourced via `cli.vocabulary.FILENAME_GRAMMAR['design']`. Extend `cli/lint.py § lint_doc_id_burn` to consult the design patterns before falling through to the numeric-prefix rejection path. Executor verifies current line numbers via `grep -n "def lint_doc_id_burn\|FIRST_ITERATION_RE" cli/lint.py` at slice execution time.

4.3. Failing test: `POSTMORTEM-2026-05-06-foo.md`, `POSTMORTEM-2026-05-06-foo-r2.md`, `RUNBOOK-celery.md`, `RUNBOOK-celery-r2.md` — L1 + L4 must accept.

4.4. Implement: add `POSTMORTEM_FIRST_ITERATION_RE`, `POSTMORTEM_SUPERSESSION_RE`, `RUNBOOK_FIRST_ITERATION_RE`, `RUNBOOK_SUPERSESSION_RE` constants at `cli/lint.py:99-103` (extending the existing pattern block), sourced from `cli.vocabulary.FILENAME_GRAMMAR['postmortem' | 'runbook']`.

4.5. Update `cli/lint.py § lint_doc_id_burn` to handle these in the same pattern-match flow (each pattern tested in order; first match wins).

**Commit:** `fix(lint): accept bare-name design supersession + POSTMORTEM/RUNBOOK prefix patterns`

Body: closes BUG-014. Adds canon §4.10 filename patterns to L1 + L4. Refs: docs/bugs/BUG-014-l4-bare-name-design-supersession.md.

### Slice 5 — Add L5 strict-enum-match lint check

**Files:**

- `cli/lint.py` (modify; add `lint_strict_enum_match` function)
- `tests/test_lint_l5.py` (new)

**Dependencies:** slices 1, 2.

**Tasks:**

5.1. Failing test: a doc with `Status: Frobulating` (invalid enum value for its type) must fail L5.

5.2. Failing test: a doc with valid status + invalid `Severity:` value (e.g. `Severity: VeryHigh` on a Bug) must fail L5.

5.3. Implementation: `lint_strict_enum_match` reads every metadata field; for each (field, doc_type) pair, checks against `cli.vocabulary` canon. Skip rules per canon §4.5 Lint behavior block.

5.4. Wire into `cli.lint --pre-commit` pipeline alongside L1-L4.

5.5. Run lint against all existing docs in `docs/`; fix any drift surfaced.

**Commit:** `feat(lint): add L5 strict-enum-match check sourcing canon §4.X enums`

Body: per canon §Regression Prevention. Catches Status / Severity / verdict / gate-name drift at commit time. Refs: docs/design/controlled-vocabulary.md.

### Slice 6 — Rename existing attestations

**Files:**

- 8 files under `docs/reviews/` (rename only; content unchanged)

**Dependencies:** slice 1 (so `cli.vocabulary.REVIEW_DOC_FILENAME_REGEX` exists), independent of slices 2-5.

**Tasks:**

6.1. Capture the actual file set: `ls docs/reviews/*.review.yaml > /tmp/rename-list.txt`. Then for each `<X>.review.yaml` in that list, `git mv docs/reviews/<X>.review.yaml docs/reviews/<X>.orchestra.review.yaml`. Single commit covers all (one `git mv` per file is fine; final commit is one logical change).

6.2. Verify no doc body references the old filenames: `for f in $(cat /tmp/rename-list.txt | xargs -n1 basename); do grep -rn "$f" docs/ .claude/ CLAUDE.md skills/ 2>/dev/null; done`; fix any cross-refs in `docs/HANDOFF.md`, `docs/STANDARDS.md`, `CLAUDE.md`, `.claude/**`, `skills/**`. Git history is NOT a fix-target. Codex review files (`*.codex.md`) are not in scope.

6.3. Add test: `tests/test_review_filenames.py::test_all_attestations_match_canon` — every `docs/reviews/*.yaml` filename matches `cli.vocabulary.REVIEW_DOC_FILENAME_REGEX`. Post-slice-6 commit, this test passes for all current files.

**Commit:** `chore(reviews): rename all attestations to .orchestra.review.yaml per canon §4.11`

Body: aligns all `docs/reviews/*.review.yaml` files (~45 at execution time) with canon §4.11 review_doc_filename_convention. No content change; pure rename. Cross-refs in HANDOFF/CLAUDE/.claude updated. Refs: docs/design/controlled-vocabulary.md.

### Slice 7 — Update `cli/spec_review.py § compute_attestation_path`

**Files:**

- `cli/spec_review.py` (modify line 397-401)
- `tests/test_spec_review.py` (modify)

**Dependencies:** slices 1, 6.

**Tasks:**

7.1. Failing test: dispatch a spec-review for a fresh doc; assert the written attestation path matches `<doc-id>-rN.orchestra.review.yaml` not `<doc-id>-rN.review.yaml`.

7.2. Implementation: edit `cli/spec_review.py § compute_attestation_path` to return `Path("docs/reviews") / f"{base}-r{iteration}.orchestra.review.yaml"`. `compute_attestation_path` is the canonical builder. Delete the orchestra_path inline f-string inside `cli/spec_review.py § render_cross_judge_report` (its f-string is now redundant); the code path using `orchestra_path` calls `compute_attestation_path(canonical_path, iteration)` instead. Executor verifies current line numbers via `grep -n "def compute_attestation_path\|orchestra_path = f" cli/spec_review.py` at slice execution time.

7.3. Update any callers / golden-file tests.

**Commit:** `feat(spec-review): write attestations as .orchestra.review.yaml per canon §4.11`

Body: completes the per-judge filename convention. Codex prose reviews continue to write .codex.review.md from the codex side. Refs: docs/design/controlled-vocabulary.md.

### Slice 8 — Template generation `scripts/generate_vocab_template.py` + CI drift test

**Files:**

- `scripts/generate_vocab_template.py` (new)
- `cli/templates/vocabulary-default-1.md` (new — generated artifact, committed)
- `tests/test_template_drift.py` (new)

**Dependencies:** slice 1.

**Tasks:**

8.1. Failing test: `test_template_drift.py::test_regenerate_matches_committed` — invoke generator, write to tmp, byte-compare against committed `cli/templates/vocabulary-default-1.md`.

8.2. Implementation: generator reads canon, emits the template file body (canon-stripped of repo-specific paths like `docs/HANDOFF.md` cite in §4.11 transition rule — those become parameterised placeholders for consumer-side install).

8.3. Run generator; commit the generated artifact.

**Commit:** `feat(templates): generate vocabulary-default-1.md template from canon + CI drift test`

Body: scripts/generate_vocab_template.py is the canon → template path. CI test gates drift. Refs: docs/design/controlled-vocabulary.md.

### Slice 9 — `cli/templates/standards-default-7.md` cross-reference rewrite

**Files:**

- `cli/templates/standards-default-7.md` (modify — large rewrite of enum tables)
- `tests/test_template_drift.py` (extend if needed)

**Dependencies:** slice 1.

**Tasks:**

9.1. Failing test: test that `standards-default-7.md` contains references `See docs/design/controlled-vocabulary.md § 4.X` for each enum it previously duplicated.

9.2. Implementation: replace duplicated enum-value tables in standards-default-7.md with single-line `> **Status enums per doc type:** see `docs/design/controlled-vocabulary.md § 4.1`` (and same for severity, verdict, doc-type, required-sections, filename grammar, refs prefixes, gate names, terminal states, whitelist).

9.3. Verify no consumer relies on inline enum values in standards-default-7.md (grep `cli/templates/`).

**Commit:** `refactor(templates): cross-reference canon instead of duplicating enum tables`

Body: standards-default-7.md no longer redefines enums; defers to canon Design Doc. Drift impossible. Refs: docs/design/controlled-vocabulary.md.

### Slice 10 — `docs/STANDARDS.md` transclude rewrite

**Files:**

- `docs/STANDARDS.md` (modify — same rewrite as slice 9 but for the dogfood copy)

**Dependencies:** slice 9 (mirror).

**Tasks:**

10.1. Apply the same transclude rewrite to `docs/STANDARDS.md`.

10.2. Verify by running L2 lint on every doc in `docs/` — no regression (sections still validate via canon).

**Commit:** `docs(STANDARDS): cross-reference canon instead of duplicating enum tables`

Body: orchestra repo's own STANDARDS.md is now canon-driven, matching the shipped template. Refs: docs/design/controlled-vocabulary.md.

### Slice 11 — `skills/spec-review/` schema + prompt severity drift gate

**Files:**

- `skills/spec-review/attestation-schema-v1.0.json` (modify — add `$comment` linking to canon §4.3 + 4.4 + 4.9)
- `skills/spec-review/prompt-template.md` (modify — same comment)
- `tests/test_spec_review_canon_drift.py` (new)

**Dependencies:** slice 1.

**Tasks:**

11.1. Failing test: `test_spec_review_canon_drift.py::test_schema_severity_matches_canon` — parse `skills/spec-review/attestation-schema-v1.0.json:58`, assert enum values equal `cli.vocabulary.SEVERITY_ENUMS['finding_gravity']` (note: canon §4.3 makes clear `finding_gravity` is the axis label only — the JSON schema field name remains `severity`; this test asserts value equality, NOT field-name change).

11.2. Failing test: same for verdict (schema:40 overall_verdict + :50 per-gate verdict) against `cli.vocabulary.VERDICT_ENUM`.

11.3. Failing test: `test_schema_gate_names_match_canon` — parse the `required` array at `attestation-schema-v1.0.json:31` (gates object) plus the property keys at the gates object definition; assert match against `cli.vocabulary.REVIEW_GATE_NAMES`. (gate names are enforced via `required` + property-keys, not a single enum line; cite both.)

11.4. Failing test: same for prompt-template severity copy at `skills/spec-review/prompt-template.md:64-67`.

11.5. Implementation: no value change required (canon mirrors current schema). Add `$comment` field linking back to canon §4.3 / §4.4 / §4.9 for human readers. Tests now gate drift if anyone edits one and forgets the other.

**Commit:** `test(spec-review): gate schema + prompt drift against canon §4.3/§4.4/§4.9`

Body: CI-drift-gate add only — no value or schema-field-name change. Schema v1.0 retained. `finding_gravity` is canon §4.3's axis label for the spec-review-finding severity axis; the JSON schema field name stays `severity`. Drift tests assert value-equality across canon ↔ schema ↔ prompt-template (i.e. if anyone edits one in the future, CI fails). Refs: docs/design/controlled-vocabulary.md.

### Slice 12 — Canon Status flip + bug closures

**Files:**

- `docs/design/controlled-vocabulary.md` (Status: Draft → Approved → Current; iterate field + Changelog)
- `docs/bugs/BUG-016-scattered-vocabulary-no-canon.md` (Status: Investigating → Fix Applied → Verified after user confirm)
- `docs/bugs/BUG-014-l4-bare-name-design-supersession.md` (Status: Investigating → Fix Applied — closed by slice 4)
- `docs/HANDOFF.md` (update post-ship section)

**Dependencies:** all slices 1-11 verified green.

**Tasks:**

12.1. Run full `make check` (lint + pyrefly + pytest). Expect: 259 + new tests passing, pyrefly 0, lint 0.

12.2. Run `.venv/bin/python -m cli.lint --pre-commit` against every doc in `docs/`. Expect: no findings.

12.3. Status flip canon Design Doc: Draft → Approved (single-line metadata change per LLD-006-r4 narrow-change rule).

12.4. Wait for user verification of slice-4 fix (closes BUG-014) — explicit confirmation per `feedback_bug_iteration_loop` HARD RULE. Then status flip BUG-014 Investigating → Fix Applied (single commit).

12.5. Wait for user verification of slice-1..11 complete + acceptance criteria satisfied (BUG-016 resolved). Then status flip BUG-016 Investigating → Fix Applied (single commit).

12.6. After BUG-016 + BUG-014 are Fix Applied AND `make check` is clean AND user verifies migration end-to-end: status flip canon Design Doc Approved → Current (single commit via orchestra:commit canon-frozen-edit-narrow-change path; specifically the whitelist-edit variant — Status field is in §4.13 narrow-change whitelist, so no Addresses: line is required, distinguishing this from the tiered-finding-Addresses variant of narrow-change).

12.7. Update `docs/HANDOFF.md` — mark v1.7.2 (or whatever version this ships as) shipped; clear BUG-014, BUG-016 from open list. Single commit.

**Commits (per status flip — strict ordering 1 → 5, each requires preceding to be merged):**

1. `docs: LLD-vocab-canon Status flip Draft → Approved` (after all slice-1..11 commits land, before any Fix-Applied flip)
2. `docs: BUG-014 Status flip Investigating → Fix Applied (user-verified)` (after user confirms slice-4 closes BUG-014)
3. `docs: BUG-016 Status flip Investigating → Fix Applied (user-verified)` (after user confirms migration end-to-end)
4. `docs: LLD-vocab-canon Status flip Approved → Current` (after user confirms canon is shipped + adopted)
5. `docs: HANDOFF post-ship update — vocab canon shipped` (final cleanup)

---

## Dependencies

Plan-level dependencies (not per-slice — those live inline). Listed in canonical order.

| Dependency | Why | Where consumed |
|---|---|---|
| `docs/design/controlled-vocabulary.md` iter-6 Status: Current | LLD this plan implements | every slice references LLD §X.Y |
| Python 3.12 `.venv/bin/python3.12` | runtime | slice 1 onward |
| pytest, pyrefly, existing `cli.lint` + `cli.spec_review` | test/lint/CLI surface | every slice |
| pyrefly 0 errors baseline | regression gate | slice 12 acceptance |
| 259 pytest baseline | regression gate | slice 12 acceptance |
| `.claude-plugin/plugin.json` at repo root | `_repo_root` walk-up target | slice 1 (`cli/_shared.py`) |
| LLD §4.X canonical tables (§4.1-§4.13) | parser input | slice 1 (`cli/vocabulary.py`) |
| `cli/lint.py § repo_root_from_cwd` (git rev-parse) | NOT extracted — separate algorithm; kept for git-aware paths | slice 1.0a context only |
| Walk-up algorithm (`.claude-plugin/plugin.json` marker, max 8 levels) | NEW implementation in `cli/_shared.py` | slice 1.0a output |
| BUG-014 doc | status-flip target post slice 4 | slice 12.4 |
| BUG-016 doc | status-flip target post all slices | slice 12.5 |
| `docs/STANDARDS.md` § Required Sections Per Doc Type | content authority for slice 3 expansion | slice 3 |
| All `docs/reviews/*.review.yaml` files at slice-6 execution time (~45 at draft time) | rename targets | slice 6 |
| `cli/spec_review.py § render_cross_judge_report` (orchestra_path inline) + `§ compute_attestation_path` | consolidation targets | slice 7 |
| `cli/lint.py:99-103` filename regex constants | slice 4 input (canon-driven replacement) | slice 4 |
| `skills/spec-review/attestation-schema-v1.0.json` (lines 31, 40, 50, 58) | drift-gate targets | slice 11 |
| `skills/spec-review/prompt-template.md` (lines 64-67) | drift-gate target | slice 11 |
| `docs/HANDOFF.md` | post-ship update target | slice 12.7 |

External dependencies: none. All paths repo-internal.

---

## Sequencing summary

```
Slice 1 (vocabulary parser + cli/_shared.py) ──┬─→ Slice 2 (lint constant migration)
                                               │       │
                                               │       ├─→ Slice 3 (REQUIRED_SECTIONS extension)
                                               │       ├─→ Slice 4 (filename regex extension; closes BUG-014)
                                               │       └─→ Slice 5 (L5 lint check)
                                               ├─→ Slice 6 (rename attestations) ─→ Slice 7 (spec_review path)
                                               ├─→ Slice 8 (template generator + CI drift)
                                               ├─→ Slice 9 (standards-default-7 transclude) ─→ Slice 10 (STANDARDS.md transclude)
                                               └─→ Slice 11 (schema/prompt drift gate)
                                               
All 1-11 green → Slice 12 status-flip block (5 commits, NOT autonomous):
   12.1 LLD Draft→Approved  (autonomous; gated only on 1-11)
   12.2 [intentionally empty — slice 12.3 in body is the canon flip; 12.4 is BUG-014]
   12.3 BUG-014 Investigating→Fix Applied  (USER-CONFIRM GATE)
   12.4 BUG-016 Investigating→Fix Applied  (USER-CONFIRM GATE)
   12.5 LLD Approved→Current  (USER-CONFIRM GATE; gated on 12.3 + 12.4)
   12.6 HANDOFF post-ship update  (autonomous; gated on 12.5)
```

**Body ↔ diagram mapping** (body sub-tasks are execution steps; diagram numbers are commits):

| Diagram step | Body sub-task | Commit? | User-confirm gate? |
|---|---|---|---|
| 12.1 LLD Draft→Approved | body 12.3 | yes (1) | no |
| (no diagram step) | body 12.1 + 12.2 | no (pre-flight: make check + cli.lint --pre-commit) | no |
| 12.3 BUG-014 Fix Applied | body 12.4 | yes (2) | YES — slice-4 close verification |
| 12.4 BUG-016 Fix Applied | body 12.5 | yes (3) | YES — full migration end-to-end |
| 12.5 LLD Approved→Current | body 12.6 | yes (4) | YES — both bugs Fix Applied + make check clean |
| 12.6 HANDOFF post-ship | body 12.7 | yes (5) | no |

Diagram 12.2 is intentionally absent (no parallel commit at that slot). Body 12.1 + 12.2 are pre-flight checks, not commits — they belong to slice-12 execution but are not separately committed.

Parallelism: slices 6, 8, 9, 11 are independent post-slice-1; can be done in any order after slice 2 lands. Slices 3, 4, 5 must follow slice 2 strictly. Slice 7 must follow slice 6.

---

## Estimated time

| Slice | Effort |
|---|---|
| 1 | 2h (parser + 13 symbol tests + 5 failure modes) |
| 2 | 30m (delete literals + import) |
| 3 | 90m (conditional-section logic + 10 doc-type tests) |
| 4 | 60m (regex extension + BUG-014 close + tests) |
| 5 | 60m (L5 implementation + drift sweep on existing docs) |
| 6 | 60m (capture list + ~45 git mv + grep cross-refs across 4 paths + filename test) |
| 7 | 30m (path update + golden-file test) |
| 8 | 60m (generator + drift test) |
| 9 | 45m (template rewrite) |
| 10 | 45m (STANDARDS rewrite — mirror of slice 9) |
| 11 | 30m (drift tests) |
| 12 | 30m (status flips + HANDOFF update — gated by user verify) |
| **Total** | **~9.5h** (slice 6 rescoped 20m → 60m for 45-file rename) |

---

## Risk + rollback

- **Slice 1 risk:** parser fragility on canon edit. Mitigation: failure modes are loud (`RuntimeError`, not silent skip). Tests cover all 5.
- **Slice 3 risk:** existing docs break L2 because of newly-required sections. Mitigation: pre-flight sweep — run extended L2 dry-run before merging slice 3. Fix any doc in advance.
- **Slice 6 risk:** external references to old attestation filenames (git history, slack, HANDOFF.md). Mitigation: grep + fix HANDOFF.md; accept git-history immutability (links to old filenames in old commits are historically valid).
- **Slice 9-10 risk:** transclude rewrite weakens cross-platform readability if reader is offline. Mitigation: STANDARDS.md remains long-form prose; only enum tables become `See §X.Y` references. Reader can follow.
- **Rollback:** all slices ship as separate commits. Revert by `git revert` if any slice surfaces a regression. Slice 1 must NOT be reverted alone (slices 2-11 depend on it); revert in reverse order.

---

## Changelog

| Date | Entry |
|---|---|
| 2026-05-11 | Iter-5 fixes applied. Critical-finding fix: all `cli/spec_review.py` + `cli/lint.py § <function>` cites stripped of line numbers (function-name-only form) — driven by plan iter-4 Critical: cli/spec_review.py line numbers drifted 3 times during this session (compute_attestation_path 397→399→423; orchestra_path inline 150→152→176). New §Tasks intro adds **Cite stability rule** instructing executor to `grep -n "def <name>"` at slice-execution time. Constants ranges (`cli/lint.py:62-130, :137`) retained — slice 2 deletes them, drift bounded. LLD ref iter-6 → iter-7 in §Dependencies. |
| 2026-05-11 | Migration executed. All 12 slices shipped: 1 (cli.vocabulary parser, 36f7e43), 2 (6-enum migration, 004f111), 3 (canon-strict L2 + tolerant prefix-match, ba910d8 — REQUIRED_SECTIONS deferred from slice 2 to 3 per user-approved deviation), 4 (BUG-014 closure, b518da1), 5 (L5 strict-enum-match + postmortem narrow-change, 350f07b + 47e392e), 6 (66-file rename, b738fde + ef75694), 7 (spec_review writer path, 016b7cd), 8 (template generator + CI drift, 937a5f0), 9+10 (STANDARDS canon admonition combined, 301a40e), 11 (schema/prompt drift gates, be7cdc0), 12 (BUG-014 + BUG-016 Status flips + this Plan flip + HANDOFF update). Slices 9 + 10 took conservative-rewrite path (admonition pointing to canon, tables retained) per readability tradeoff. Status: Draft → Implemented. |
| 2026-05-11 | Iter-4 fixes applied. Critical-finding fix: rename scope expanded from 8 enumerated files to all `*.review.yaml` in `docs/reviews/` at slice-6 execution time (~45 at draft). AC + §File Structure + §Dependencies + slice 6.1/6.2/6.3 + slice-6 effort estimate (20m → 60m) + commit-msg body all updated. LLD iter-6 (§4.11 reframed rule-not-enumeration) parallel ship. Minor residue fixes: §File Structure inline comments at cli/_shared.py + cli/lint.py rows refreshed to match iter-3 reframing ("NEW walk-up", "repo-root NOT touched"). Sequencing diagram body↔diagram mapping table added (resolves iter-3 Important on diagram-12.1-12.6 vs body-12.1-12.7 mismatch). LLD ref iter-5 → iter-6 in §Dependencies. |
| 2026-05-11 | Iter-3 fixes applied. Critical-finding fix: slice 1.0a + §Dependencies rewritten to specify NEW walk-up implementation in `cli/_shared.py` (not extraction — verified `cli/lint.py` has no `_repo_root`; only `repo_root_from_cwd` at :1233 uses git rev-parse). LLD §Parse contract corrected in parallel (LLD iter-5). Line-range fixes: `compute_attestation_path` :397-401 → :399-403 (3 places); inline literal :150 → :152. §Dependencies row 1 LLD ref iter-3 → iter-5 Current. New §Dependencies row for `:99-103` filename-regex slice-4 input. Sequencing diagram annotated with user-confirm gates inside slice 12. AC test-count target updated to realistic 80-100 with per-slice breakdown. Slice 12.6 narrow-change variant specified as whitelist-edit. Slice 11 commit-msg body prepended with "CI-drift-gate add only — no value or schema-field-name change". |
| 2026-05-11 | Iter-2 spec-review fixes applied. Critical-finding fixes: rename count reconciled to 8 (+ future-proof rule); slice 2 line ranges split (REQUIRED_SECTIONS at 105-130 added to deletion list; WHITELIST at 87 alone, REFS at 81-84). Important fixes: §Header architecture inline summary added; §Dependencies top-level section added; slice 1.7 `_repo_root` reuse mechanism specified (extract to `cli/_shared.py`, slice 1.0/1.0a); slice 3.1 enumeration replaced with LLD §4.8 reference (LLD-Plan no-overlap); slice 4.2 + 4.4 regex constant location specified (cli/lint.py:99-103); slice 7.2 consolidation direction specified (compute_attestation_path canonical, line-150 helper calls it); slice 11 commit msg rephrased (finding_gravity = axis label not field rename); slice 1.4 header ref corrected to "§Parse contract"; slice 12 status-flip steps decomposed. Minor fixes: AC test count target added; slice 6.2 cross-ref fix-targets enumerated; slice 11.3 gate-name drift test added. |
| 2026-05-11 | Plan drafted. Status: Draft. 11 sequenced slices + slice 12 status-flip block. Estimated ~9h. Sequencing graph shows slices 1 + 2 are blocking; slices 6, 8, 9, 11 parallelisable after slice 2. DRI: Hassan. |
