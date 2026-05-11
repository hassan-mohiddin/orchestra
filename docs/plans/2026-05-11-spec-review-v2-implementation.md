# Implementation Plan — spec-review v2 (LLD-011)

> **Doc ID:** 2026-05-11-spec-review-v2-implementation
> **Date:** 2026-05-11
> **Status:** Draft
> **DRI:** Hassan
> **LLD:** `docs/features/011-spec-review-v2.md`
> **Type:** Implementation Plan

---

## Header

**Goal**: Implement the v2 architecture defined in LLD-011 and ship as orchestra v2.0.0 (big-bang release covering Phase 1 + Phase 2 + Phase 3 of the LLD).

**Architecture** (from LLD-011 — this plan does not re-state design decisions):
- 6 sub-judges dispatched parallel via single-message Task tool fanout
- Schema v2.0 with provenance + integrity-hash + mandatory-map fields
- Mechanical Python aggregator (no LLM call)
- Streaming peer-judge write
- PDSA pre-dispatch self-audit
- Delta-review on iter-2 (blob-SHA provenance via `git hash-object -w` + `git cat-file -p`)
- Per-sub-judge rubric-freeze (versioned files)
- 2-iter post-commit hard cap with `--override-cap` flag
- Failure-attestation invariant (always persist, even on all-fail)

**Tech stack**: Python 3.12 (`.venv/bin/python3.12`); pytest; pyrefly; `cli.lint` for self-dogfood lint; `cli.eval` for scenario suite.

**Iteration discipline**: TDD vertical slicing. One failing test → one implementation → green → commit. NOT all-tests-then-all-impl. Horizontal slicing forbidden per `.claude/workflow.md § Step 4`.

**LLD vs Plan boundary**: this plan describes HOW + IN WHAT ORDER. It MUST NOT introduce design decisions not in LLD-011. If a slice requires a design decision not in LLD-011 → STOP, file an LLD update or interview Hassan; do not silently decide in the plan.

---

## File Structure

### Files created (new in v2)

| Path | Purpose |
|---|---|
| `skills/spec-review/attestation-schema-v2.0.json` | JSON-Schema draft-07 for v2 attestation |
| `skills/spec-review/judges/structure/prompt.md` | structure sub-judge prompt template |
| `skills/spec-review/judges/structure/rubric-v1.md` | structure rubric v1 (format / required sections / filename grammar / Mermaid) |
| `skills/spec-review/judges/semantic/prompt.md` | semantic sub-judge prompt (4-gate continuity) |
| `skills/spec-review/judges/semantic/rubric-v1.md` | semantic rubric v1 (inherits LLD-007 4-gate body) |
| `skills/spec-review/judges/gate-compliance/prompt.md` | gate-compliance prompt |
| `skills/spec-review/judges/gate-compliance/rubric-v1.md` | Gates 1-3 + canon-frozen + lifecycle rubric |
| `skills/spec-review/judges/adversarial/prompt.md` | adversarial red-team prompt |
| `skills/spec-review/judges/adversarial/rubric-v1.md` | adversarial rubric (find-what-breaks / blast-radius / invariants / edge cases) |
| `skills/spec-review/judges/repo-context/prompt.md` | repo-context prompt with Read+Grep+Glob tool scope |
| `skills/spec-review/judges/repo-context/rubric-v1.md` | citation validity / impl-doc match / test coverage rubric |
| `skills/spec-review/judges/architectural-fit/prompt.md` | architectural-fit prompt with Read+Grep scope |
| `skills/spec-review/judges/architectural-fit/rubric-v1.md` | Design Doc + ADR consistency rubric |
| `skills/spec-review/references/aggregator-algorithm.md` | mechanical merge algorithm reference |
| `skills/spec-review/references/delta-review-protocol.md` | iter-2 delta-review protocol reference |
| `skills/spec-review/references/class-vs-instance.md` | class-vs-instance fix protocol reference |
| `skills/spec-review/references/pdsa-checklist.md` | PDSA checks reference |
| `skills/spec-review/templates/attestation-template-v2.0.yaml` | v2.0 attestation template |
| `cli/pdsa.py` | Pre-Dispatch Self-Audit module |
| `cli/aggregator.py` | Mechanical merge module |
| `cli/delta_review.py` | Iter-2 delta-review module |
| `tests/test_spec_review_v2.py` | Top-level dispatch + flow integration |
| `tests/test_pdsa.py` | PDSA checks unit tests |
| `tests/test_aggregator.py` | Aggregator unit tests |
| `tests/test_delta_review.py` | Delta-review unit tests |
| `tests/test_schema_v2_validation.py` | Schema v2 validation tests |
| `tests/test_schema_v1_read_only.py` | v1 attestation read-only backward-compat |
| `tests/test_partial_failure.py` | Mandatory vs optional sub-judge failure semantics |
| `tests/test_iter_cap.py` | 2-iter cap + override-cap |
| `tests/test_class_vs_instance.py` | scope field + audit_count |
| `tests/test_rubric_freeze.py` | Rubric versioning + replay |
| `tests/test_attestation_integrity.py` | Integrity hash compute + verify |
| `tests/test_provenance.py` | iter_commit_sha + iter_blob_sha persistence + retrieval |
| `tests/test_tool_trace_rejection.py` | Output-quarantine + tool_scope_violation |
| `eval/scenarios/spec-review-v2/s1-loop-iter1-pass.yaml` | Iter-1 pass rate scenario |
| `eval/scenarios/spec-review-v2/s2-loop-iter2-pass.yaml` | Iter-2 pass rate scenario |
| `eval/scenarios/spec-review-v2/s3-depth-vs-codex.yaml` | Depth metric scenario |
| `eval/scenarios/spec-review-v2/s4-partial-failure.yaml` | Soft + hard fail scenario |
| `eval/scenarios/spec-review-v2/s5-iter-cap.yaml` | Hard cap scenario |

### Files modified (existing files updated)

| Path | Change |
|---|---|
| `cli/spec_review.py` | Rewritten — v2 dispatch + aggregator wiring + PDSA invocation + iter-cap + provenance + integrity hash + failure-attestation invariant |
| `skills/spec-review/SKILL.md` | Rewritten — v2 dispatch protocol (parallel Task fanout) + report + interview-gate |
| `skills/spec-review/attestation-schema-v1.0.json` | UNCHANGED — kept frozen for v1.0 historical reads |
| `commands/spec-review.md` | Add `--override-cap` flag pass-through |
| `.claude/workflow.md` | Add 1-paragraph v2 reference in Step 2 |
| `.claude/skills-registry.md` | Update orchestra:spec-review note to reflect v2 multi-judge |
| `.claude-plugin/plugin.json` | Bump version to 2.0.0 |
| `.claude-plugin/marketplace.json` | Bump version to 2.0.0 |
| `docs/STANDARDS.md` | Update "Spec Review Rule" section to reflect v2 (4 → 6 sub-judges + cross-judge report + interview-gate) |
| `docs/HANDOFF.md` | Update with v2.0.0 ship state when complete |

### Files NOT touched (out of scope confirmation)

- `docs/reviews/*.review.yaml` v1.0 attestations — frozen, read-only
- `cli/lint.py` STATUS_ENUMS / CANON_FROZEN_STATUSES — owned by BUG-016 vocab canon effort
- `cli/templates/*` — owned by separate effort

---

## Sequencing Rules

1. **Phase boundaries are non-overlapping**: complete Phase 1 acceptance before any Phase 2 slice. Complete Phase 2 acceptance before any Phase 3 slice. This is for verifiable incremental green state.
2. **Within a phase, slices are ordered**: each slice references the previous one's output. Skipping ahead invalidates the TDD chain.
3. **Each slice = one failing test, one implementation, one green run, one commit**. No "while I'm here" cleanup. Slice-and-commit discipline.
4. **Commit prefix**: `test:` for the failing test addition; `feat:` for the implementation that makes the test pass; `refactor:` for any restructuring during green. ONE commit per slice is preferred; two (test then feat) acceptable if test alone is meaningful checkpoint.
5. **No `wip:` commits unless explicitly bug-iteration loop**. v2 is not a bug fix; it is a feature.
6. **After every 5 slices, run full `.venv/bin/python -m pytest` + `pyrefly check` + `.venv/bin/python -m cli.lint`**. Verify no drift.
7. **At each phase acceptance boundary (end of Phase 1, Phase 2, Phase 3), run the FULL suite — not filtered `pytest -k`**. The filtered `pytest -k` runs noted in per-phase acceptance sections are convenience checks during development; phase transitions require: `.venv/bin/python -m pytest` (entire suite, green), `pyrefly check` (0 errors), `.venv/bin/python -m cli.lint --pre-commit` (no errors), `.venv/bin/python -m cli.eval` (all scenarios pass). Slice counts (33 / 29 / 22) are not multiples of 5 and a tail-slice regression in a critical invariant (stale-state / atomic-write / security / canon-frozen) could slip past every-5 checkpoints if we relied only on filtered runs. Phase-boundary full-suite is the invariant gate.
7. **Refs: line required** for `feat:` commits per orchestra L2 rule. Format: `Refs: docs/features/011-spec-review-v2.md`.

---

## Phase 1 — Depth Fix (schema v2 + dispatch + aggregator + streaming + report + gate)

**Acceptance**: 6 sub-judges dispatch in parallel; aggregator produces deduped findings_aggregated; streaming write per peer-judge works; cross-judge comparison report renders; interview-gate auto-fires on Critical/Important. End-to-end fixture-based validation (NOT pass/fail on a real doc, since real docs have outcomes that should NOT be reverse-engineered for verification):
- **Fixture A** — known-clean synthetic LLD at `tests/fixtures/spec-review-v2/clean-lld.md` (a hand-crafted minimal Feature LLD with no seeded defects). Expectation: v2 dispatch produces `overall_verdict: pass`, all 6 sub-judges complete, findings_aggregated empty, attestation written.
- **Fixture B** — known-defective synthetic LLD at `tests/fixtures/spec-review-v2/defective-lld.md` (hand-crafted with seeded defects: missing citation, contradictory section, stale Refs link). Expectation: v2 dispatch produces `overall_verdict: conditional_pass` or `fail`; findings_aggregated contains the seeded defects (assert by specific location/problem pattern, not by count); each defect raised by the expected sub-judge per its rubric slice.
- **Real-doc dry-run** — invoke `/orchestra:spec-review docs/features/008-commit-skill-r8.md` to confirm end-to-end pipeline runs without errors. Verdict is **observed-not-asserted** — we record what v2 surfaces and compare to the v1 attestation in `docs/reviews/008-commit-skill-r8.review.yaml`; informational only for cross-judge calibration. Do NOT use real-doc verdict as a phase-acceptance gate.

### Slices

| # | Slice | Test added | Implementation | Files |
|---|---|---|---|---|
| 1.1 | Schema v2.0 JSON file accepts conforming minimal attestation | `test_schema_v2_validation.py::test_minimal_conforming` | Write `attestation-schema-v2.0.json` draft-07 with required + optional fields per LLD §Schema v2.0 | `skills/spec-review/attestation-schema-v2.0.json`, `tests/test_schema_v2_validation.py` |
| 1.2 | Schema v2.0 rejects missing required `sub_judges` | `test_schema_v2_validation.py::test_rejects_missing_sub_judges` | Schema `required` array enforcement | same |
| 1.3 | Schema v2.0 rejects invalid severity enum | `test_schema_v2_validation.py::test_rejects_invalid_severity` | Schema `enum` for severity | same |
| 1.4 | Schema v2.0 rejects invalid verdict enum | `test_schema_v2_validation.py::test_rejects_invalid_verdict` | Schema `enum` for verdict | same |
| 1.5 | Schema v2.0 accepts schema_version 2.0; rejects others | `test_schema_v2_validation.py::test_version_pinning` | Schema `const` for schema_version | same |
| 1.6 | cli.spec_review reads schema_version and routes v1.0 to read-only | `test_schema_v1_read_only.py::test_v1_attestation_readable` | Add schema-version-dispatcher in `cli.spec_review` main | `cli/spec_review.py`, `tests/test_schema_v1_read_only.py` |
| 1.7 | cli.spec_review v1.0 attestation overwrite refused | `test_schema_v1_read_only.py::test_v1_overwrite_refused` | Read-only path emits error | same |
| 1.8 | Mandatory map in cli.spec_review module-level constant | `test_spec_review_v2.py::test_mandatory_map` | `MANDATORY_SUBJUDGES = frozenset({"semantic", "adversarial"})` | `cli/spec_review.py`, `tests/test_spec_review_v2.py` |
| 1.9 | Sub-judge prompt files exist for all 6 sub-judges | `test_spec_review_v2.py::test_judge_prompt_files_present` | Write 6 prompt.md files in `skills/spec-review/judges/<id>/` | `skills/spec-review/judges/*/prompt.md` |
| 1.10 | Sub-judge rubric-v1.md files exist for all 6 sub-judges | `test_spec_review_v2.py::test_judge_rubric_files_present` | Write 6 rubric-v1.md files | `skills/spec-review/judges/*/rubric-v1.md` |
| 1.11 | Aggregator empty input → empty output | `test_aggregator.py::test_empty_input` | `cli/aggregator.py::aggregate_findings` with empty list | `cli/aggregator.py`, `tests/test_aggregator.py` |
| 1.12 | Aggregator single sub-judge → findings pass-through | `test_aggregator.py::test_single_subjudge` | normalize_location + fuzzy_hash key building | same |
| 1.13 | Aggregator dedup on same key | `test_aggregator.py::test_dedup_same_key` | Bucket merge logic | same |
| 1.14 | Aggregator severity union (max) | `test_aggregator.py::test_severity_union_max` | `SEVERITY_RANK` + max | same |
| 1.15 | Aggregator raised_by union (sorted unique) | `test_aggregator.py::test_raised_by_union` | Set-then-sort | same |
| 1.16 | Aggregator output ordered by location | `test_aggregator.py::test_output_ordered_by_location` | Final sort | same |
| 1.17 | normalize_location handles `§` / `section` / `line N` consistently | `test_aggregator.py::test_normalize_location` | Regex normalization | same |
| 1.18 | fuzzy_hash collision-resistant on common synonyms | `test_aggregator.py::test_fuzzy_hash_stable` | Stopword strip + stem + SHA-256 prefix | same |
| 1.19 | Provenance: cli.spec_review writes iter_commit_sha via `git rev-parse HEAD` | `test_provenance.py::test_iter_commit_sha_written` | Add to attestation builder | `cli/spec_review.py`, `tests/test_provenance.py` |
| 1.20 | Provenance: cli.spec_review writes iter_blob_sha via `git hash-object -w` | `test_provenance.py::test_iter_blob_sha_persisted` | shell out to `git hash-object -w <path>` | same |
| 1.21 | Provenance: `git cat-file -p <iter_blob_sha>` retrieves doc bytes | `test_provenance.py::test_blob_retrievable` | Verify after write | same |
| 1.22 | Provenance: works for uncommitted docs | `test_provenance.py::test_uncommitted_doc_provenance` | Sanity test — no commit required | same |
| 1.23 | Integrity hash: computed at write over canonical payload (excluding the field itself) | `test_attestation_integrity.py::test_hash_computation` | Zero-field-then-hash | `cli/spec_review.py`, `tests/test_attestation_integrity.py` |
| 1.24 | Integrity hash: re-verified at iter-2 load | `test_attestation_integrity.py::test_hash_verification` | `verify_attestation_integrity_hash` | same |
| 1.25 | Integrity hash: tamper detected | `test_attestation_integrity.py::test_tamper_detected` | Edit findings post-write → verify fails | same |
| 1.26 | Dispatch: skill body emits N parallel Task calls (mock layer) | `test_spec_review_v2.py::test_parallel_dispatch_count` | Update `skills/spec-review/SKILL.md` body with dispatch sequence; test the harness | `skills/spec-review/SKILL.md`, `cli/spec_review.py` |
| 1.27 | Failure-attestation invariant: write attestation even on all-fail | `test_partial_failure.py::test_all_fail_writes_attestation` | `--aggregate-and-write` always emits YAML | `cli/spec_review.py`, `tests/test_partial_failure.py` |
| 1.28 | Mandatory fail → overall_verdict=fail with reason=mandatory_subjudge_failed | `test_partial_failure.py::test_mandatory_fail_hard_block` | Tiered policy in `compute_overall_verdict` | same |
| 1.29 | Optional fail → overall_verdict from completed sub-judges; excluded_sub_judges populated | `test_partial_failure.py::test_optional_fail_soft_pass` | Same module | same |
| 1.30 | Cross-judge report: counts table renders correctly | `test_spec_review_v2.py::test_report_table_format` | Report-rendering helper in `cli/spec_review.py` or skill body | same |
| 1.31 | Cross-judge report: tolerant codex .md parser extracts severity counts | `test_spec_review_v2.py::test_codex_md_parser` | Regex-based parse helper | same |
| 1.32 | Interview-gate auto-fire when aggregate has Critical | `test_spec_review_v2.py::test_gate_fires_critical` | Wire AskUserQuestion (mocked) in skill body OR in cli.spec_review subcommand | same |
| 1.33 | Interview-gate skip when only Minor findings | `test_spec_review_v2.py::test_gate_skips_minor_only` | Same | same |

**Phase 1 verification — full-suite gate per Sequencing Rule 7**:
- Filtered sanity check (during development): `.venv/bin/python -m pytest -k "v2 or aggregator or partial_failure or schema_v2 or schema_v1 or provenance or attestation_integrity"` returns green
- **Phase-boundary gate (required before Phase 2 begins)**: full `.venv/bin/python -m pytest` returns green, `pyrefly check` returns 0 errors, `.venv/bin/python -m cli.lint --pre-commit` clean, `.venv/bin/python -m cli.eval` passes
- Pytest baseline grows from 259 to ≥ 288 (29 new tests above)

**Phase 1 commit cadence**: ~33 slices = ~33 commits (or merged to ~20 if test+impl bundled). Estimated 4-7 working days.

---

## Phase 2 — Loop Fix Part A (PDSA + class/instance + delta-review)

**Acceptance**: PDSA blocks dispatch on mechanical fails; class-vs-instance scope tags propagate through aggregator; delta-review on iter-2 loads iter-1 attestation, verifies integrity, retrieves blob, computes diff, prompts sub-judges with diff + iter-1 findings; fail-closed on missing provenance.

### Slices

| # | Slice | Test added | Implementation | Files |
|---|---|---|---|---|
| 2.1 | PDSA: invokes `cli.lint --doc <path>` | `test_pdsa.py::test_lint_invocation` | `cli/pdsa.py::run_pdsa` | `cli/pdsa.py`, `tests/test_pdsa.py` |
| 2.2 | PDSA: lint fail blocks dispatch | `test_pdsa.py::test_lint_fail_blocks` | Return non-zero exit if lint fails | same |
| 2.3 | PDSA: required-sections check per doc type | `test_pdsa.py::test_required_sections` | Heuristic match against STANDARDS.md per-type lists | same |
| 2.4 | PDSA: citation validity via splitlines bounds-check | `test_pdsa.py::test_citation_validity` | Per LLD §PDSA item 3 pseudocode | same |
| 2.5 | PDSA: citation out-of-range fails | `test_pdsa.py::test_citation_out_of_range` | Same | same |
| 2.6 | PDSA: placeholder detection — bare TBD fails | `test_pdsa.py::test_bare_placeholder_fails` | grep + owner-suffix check | same |
| 2.7 | PDSA: placeholder with `by <date>` passes | `test_pdsa.py::test_owned_placeholder_passes` | Same | same |
| 2.8 | PDSA: cross-doc Refs: resolution | `test_pdsa.py::test_refs_resolve` | Path.exists() per `Refs:` line | same |
| 2.9 | PDSA: filename grammar per LLD-006-r4 | `test_pdsa.py::test_filename_grammar` | Regex per doc type | same |
| 2.10 | PDSA: glossary check is non-gating warn | `test_pdsa.py::test_glossary_non_gating` | Emit warning, do not fail | same |
| 2.11 | PDSA YAML report format | `test_pdsa.py::test_pdsa_report_format` | Per-check pass/fail YAML output | same |
| 2.12 | cli.spec_review invokes PDSA before sub-judge dispatch | `test_spec_review_v2.py::test_pdsa_blocks_dispatch` | Wire PDSA call into entry point | `cli/spec_review.py`, `tests/test_spec_review_v2.py` |
| 2.13 | Schema v2.0: `scope: instance|class` field in findings | `test_schema_v2_validation.py::test_scope_field` | Update schema enum + required | `skills/spec-review/attestation-schema-v2.0.json`, `tests/test_schema_v2_validation.py` |
| 2.14 | Aggregator preserves scope through merge | `test_class_vs_instance.py::test_scope_preserved` | First-finding scope wins; raised_by all merge | `cli/aggregator.py`, `tests/test_class_vs_instance.py` |
| 2.15 | Class finding requires audit_attestation in iter-2 doc | `test_class_vs_instance.py::test_class_audit_required` | PDSA or sub-judge enforces presence | same |
| 2.16 | Instance finding requires no audit attestation | `test_class_vs_instance.py::test_instance_no_audit` | Same | same |
| 2.17 | Delta-review: locate iter-1 attestation path | `test_delta_review.py::test_locate_iter1_attestation` | `compute_attestation_path` helper | `cli/delta_review.py`, `tests/test_delta_review.py` |
| 2.18 | Delta-review: verify attestation_integrity_hash | `test_delta_review.py::test_integrity_verification` | `verify_attestation_integrity_hash` call | same |
| 2.19 | Delta-review: read iter_blob_sha from iter-1 attestation | `test_delta_review.py::test_read_blob_sha` | dict lookup with fail-closed | same |
| 2.20 | Delta-review: fail-closed on missing iter_blob_sha | `test_delta_review.py::test_missing_provenance_fails` | Raise `SpecReviewError(iter1_provenance_missing)` | same |
| 2.21 | Delta-review: fail-closed on missing iter-1 attestation file | `test_delta_review.py::test_missing_attestation_fails` | Raise `SpecReviewError(iter1_attestation_missing)` | same |
| 2.22 | Delta-review: `git cat-file -p` retrieves iter-1 bytes | `test_delta_review.py::test_cat_file_retrieval` | subprocess call | same |
| 2.23 | Delta-review: blob SHA cross-check (retrieved bytes hash to stored SHA) | `test_delta_review.py::test_blob_sha_cross_check` | git_hash_object helper | same |
| 2.24 | Delta-review: pruned-blob fails closed | `test_delta_review.py::test_pruned_blob_fails` | Catch CalledProcessError → SpecReviewError | same |
| 2.25 | Delta-review: diff section extraction | `test_delta_review.py::test_diff_sections` | unified-diff parse → section range list | same |
| 2.26 | Delta-review: empty diff → no-op iteration | `test_delta_review.py::test_empty_diff_noop` | Skip dispatch, write attestation referencing iter-1 verdict | same |
| 2.27 | Delta-review: sub-judge prompt includes diff + iter-1 findings | `test_delta_review.py::test_subjudge_prompt_context` | Skill body / dispatch context builder | `skills/spec-review/SKILL.md`, `cli/delta_review.py` |
| 2.28 | E13: iteration missing + prior attestation exists → fail-closed | `test_iter_cap.py::test_iteration_missing_with_prior` | Scan `docs/reviews/<doc-id>-r*.review.yaml` | `cli/spec_review.py`, `tests/test_iter_cap.py` |
| 2.29 | E13: iteration missing + no prior attestation → default to 1 | `test_iter_cap.py::test_iteration_missing_no_prior` | Same | same |

**Phase 2 verification — full-suite gate per Sequencing Rule 7**:
- Filtered sanity check: `.venv/bin/python -m pytest -k "pdsa or class_vs_instance or delta_review"` green
- **Phase-boundary gate (required before Phase 3 begins)**: full `.venv/bin/python -m pytest` green, `pyrefly check` 0 errors, `.venv/bin/python -m cli.lint --pre-commit` clean, `.venv/bin/python -m cli.eval` passes
- Pytest baseline ≥ 317

**Phase 2 commit cadence**: ~29 slices. ~5 working days.

---

## Phase 3 — Loop Fix Part B (rubric-freeze + 2-iter cap + override + always-persist)

**Acceptance**: rubric_version recorded per sub-judge at iter-1; replayed at iter-2; rubric file missing at iter-2 hard-fails; iter-3+ blocked; `--override-cap` fires interview-gate + logs degraded mode; E11/E18/E20/E21 produce failure attestations.

### Slices

| # | Slice | Test added | Implementation | Files |
|---|---|---|---|---|
| 3.1 | Rubric-v1.md content for all 6 sub-judges | `test_rubric_freeze.py::test_rubric_v1_content` | Write rubric body per sub-judge (per LLD §Sub-judge cast) | `skills/spec-review/judges/*/rubric-v1.md` |
| 3.2 | cli.spec_review reads latest rubric version at iter-1 | `test_rubric_freeze.py::test_iter1_uses_latest_rubric` | `find_latest_rubric_version(judge_id)` helper | `cli/spec_review.py`, `tests/test_rubric_freeze.py` |
| 3.3 | cli.spec_review records rubric_version in attestation | `test_rubric_freeze.py::test_rubric_version_recorded` | Build attestation with field | same |
| 3.4 | cli.spec_review reads rubric_version at iter-2 (frozen) | `test_rubric_freeze.py::test_iter2_uses_iter1_rubric` | Read from iter-1 attestation | same |
| 3.5 | Iter-2 rubric file missing → hard fail | `test_rubric_freeze.py::test_iter2_missing_rubric_fails` | Raise `SpecReviewError(rubric_version_not_found)` | same |
| 3.6 | Iter-2 newer rubric version exists but NOT used | `test_rubric_freeze.py::test_iter2_ignores_newer_rubric` | Verify v2 file uses v1 file content | same |
| 3.7 | 2-iter cap: iter-1 dispatches normally | `test_iter_cap.py::test_iter1_dispatches` | Wire iteration check at entry | `cli/spec_review.py`, `tests/test_iter_cap.py` |
| 3.8 | 2-iter cap: iter-2 dispatches via delta-review | `test_iter_cap.py::test_iter2_dispatches_delta` | Branch to delta-review module | same |
| 3.9 | 2-iter cap: iter-3 refuses without override | `test_iter_cap.py::test_iter3_blocked` | Exit with explicit error | same |
| 3.10 | --override-cap flag parsed in argparse | `test_iter_cap.py::test_override_flag_parsed` | Add to argparse | same |
| 3.11 | --override-cap fires interview-gate before dispatch | `test_iter_cap.py::test_override_fires_gate` | Mock AskUserQuestion | same |
| 3.12 | --override-cap with iter-3 + user-confirms proceeds | `test_iter_cap.py::test_override_confirmed_proceeds` | Mock yes-response | same |
| 3.13 | --override-cap logs degraded mode in attestation notes | `test_iter_cap.py::test_override_logged` | Append to notes field | same |
| 3.14 | --override-cap composes with normal iter (no-op) | `test_iter_cap.py::test_override_iter1_noop` | Flag ignored if not iter-3+ | same |
| 3.15 | E11: sub-judge prompt missing → failure attestation persisted | `test_partial_failure.py::test_e11_failure_attestation` | Catch FileNotFoundError → emit failure attestation | `cli/spec_review.py`, `tests/test_partial_failure.py` |
| 3.16 | E17: model unavailable for optional sub-judge → soft-fail | `test_partial_failure.py::test_e17_optional_soft_fail` | Catch provider error → status=error | same |
| 3.17 | E17b: model unavailable for mandatory sub-judge → hard-fail | `test_partial_failure.py::test_e17b_mandatory_hard_fail` | Same with mandatory check | same |
| 3.18 | E18: doc disappeared → failure attestation written | `test_partial_failure.py::test_e18_doc_disappeared` | F8 inherited check writes failure attestation now (was no-attestation in v1) | same |
| 3.19 | E20: tampered attestation → failure attestation at iter-2 load | `test_attestation_integrity.py::test_e20_tamper_failure` | Re-verify at load + write failure if mismatch | `cli/spec_review.py`, `tests/test_attestation_integrity.py` |
| 3.20 | E21: tool_scope_violation → output-quarantine | `test_tool_trace_rejection.py::test_e21_quarantine` | Regex-scan sub-judge output for out-of-rubric paths / credential patterns; replace problem with redacted; mark status=error | `cli/spec_review.py`, `tests/test_tool_trace_rejection.py` |
| 3.21 | E21: optional sub-judge quarantine = soft-fail | `test_tool_trace_rejection.py::test_e21_optional_soft` | Map to E1 semantics | same |
| 3.22 | E21: mandatory sub-judge quarantine = hard-fail | `test_tool_trace_rejection.py::test_e21_mandatory_hard` | Map to E1b semantics | same |

**Phase 3 verification — full-suite gate per Sequencing Rule 7**:
- Filtered sanity check: `.venv/bin/python -m pytest -k "rubric or iter_cap or partial_failure or tool_trace or attestation_integrity"` green
- **Phase-boundary gate (required before Self-Application begins)**: full `.venv/bin/python -m pytest` green, `pyrefly check` 0 errors, `.venv/bin/python -m cli.lint --pre-commit` clean, `.venv/bin/python -m cli.eval` passes
- Pytest baseline ≥ 339

**Phase 3 commit cadence**: ~22 slices. ~3-4 working days.

---

## Self-Application (post-Phase-3)

After Phase 3 acceptance:

1. **Update plugin version**: `.claude-plugin/plugin.json` + `marketplace.json` bump to `2.0.0`.
2. **Update SKILL.md + STANDARDS.md + workflow.md references** to v2 (already partially updated in Phase 1 slices; final sweep here).
3. **Run `/orchestra:spec-review docs/features/011-spec-review-v2.md`** — dogfood: v2 reviews its own LLD. Expected: pass / conditional_pass. If fail, file BUG and iterate per v2 protocol itself.
4. **Run depth-metric validation** on 5-doc sample:
   - LLD-008-r8 (Feature LLD)
   - BUG-014 (Bug Report)
   - one ADR (pick from `docs/adr/`)
   - orchestra-philosophy-r2 (Design Doc)
   - LLD-011 (self)
   For each: run v2 ensemble + `/codex:adversarial-review`. Compute overlap on (severity ≥ Important, location_normalized). Verify ≥ 80%.
5. **Tag v2.0.0** + push.
6. **Status flips**:
   - LLD-011 Status: Approved → Implemented (this plan's completion)
   - Plan Status: In Progress → Implemented
   - After validation runs: → Verified

---

## Risk Register + Mitigation

| Risk | Likelihood | Mitigation |
|---|---|---|
| Task tool parallel dispatch returns out of order — aggregator assumptions break | Medium | Aggregator is order-agnostic (sorts by location); test 1.16 covers |
| `git hash-object -w` permission denied (bare repo, shallow clone, read-only `.git/`) | Low | Detect at dispatch + emit clear error: `git_object_write_failed: cannot persist iter-1 blob. Recovery: ensure the working repo has writable .git/objects/, OR pass --override-cap for a fresh full-doc iter-2 review (degraded mode, no delta-review provenance).` Fail-closed per LLD-011 contract. NO inline-bytes fallback (that would contradict LLD-011 §Scope item 16 and weaken tamper/replay guarantees). The plan does not introduce new degraded modes — recovery is one of the two paths LLD-011 already defines |
| Sub-judge prompt > Task tool context limit | Medium | Per-sub-judge prompts kept terse; eval scenarios sized appropriately |
| Aggregator fuzzy_hash collides on unrelated findings | Low | Test 1.18 covers known synonyms; acceptable risk per LLD §E14 |
| Output-quarantine regex false positives reject valid findings | Medium | Test broad sample; tunable regex per `references/pdsa-checklist.md` |
| Mandatory sub-judge (Opus) provider outage blocks all reviews | High during outage | Documented E17b; user retries when Opus back. No mitigation in v2 — acceptable per LLD |
| Self-application iter-1 fails on LLD-011 itself (dogfood loop) | Medium | Acceptable — file BUG and iterate per v2's own protocol; this validates the design end-to-end |
| Depth-metric ≥ 80% not hit on 5-doc sample | Medium | Tune sub-judge prompts before tagging v2.0.0; do not ship without metric passing per Success Criteria |

---

## Out of Plan Scope

These are referenced by LLD-011 but explicitly NOT in this plan:
- BUG-016 vocab canon (parallel session) — PDSA upgrades to strict-enum-match when that lands
- Workflow state-machine + phase return (future LLD)
- HMAC / cryptographic signature on attestation (deferred per LLD §Out of scope)
- Per-doc cost ceiling (deferred to v2.1 measurement)
- Codex output normalization to v2.0 YAML (rejected per session decision)

---

## Total scope summary

| | Slices | New files | Modified files | Estimated days |
|---|---|---|---|---|
| Phase 1 | 33 | ~30 | ~3 | 4-7 |
| Phase 2 | 29 | ~5 | ~3 | 5 |
| Phase 3 | 22 | ~0 | ~3 | 3-4 |
| Self-Application | — | — | ~5 | 1-2 |
| **Total** | **84** | **~35** | **~14** | **13-18** |

Pytest baseline grows: 259 → ~339 (≥ 80 new tests).

---

## Changelog

| Date | Entry |
|---|---|
| 2026-05-11 | Plan v1 drafted by Claude per Hassan request immediately after LLD-011 Status flip Draft → Approved. 84 slices across 3 phases + self-application. Pending: Hassan approval (Status → Approved) before Phase 1 slice 1.1 begins. Plan describes HOW + IN WHAT ORDER only; design decisions live in LLD-011. No design content duplicated. If a slice requires a design decision not in LLD-011, slice is BLOCKED on LLD update or interview — do not silently decide in this plan. |
| 2026-05-11 | Plan iter-1 spec-review by `/codex:adversarial-review` — found 3 findings (1 Critical, 2 High); all applied: (1) Critical L118 Phase-1 acceptance used `008-commit-skill-r8.md` as clean-pass fixture but its v1 attestation = `conditional_pass`; reframed Phase-1 acceptance to use known-clean + known-defective synthetic fixtures at `tests/fixtures/spec-review-v2/{clean-lld,defective-lld}.md` with specific-finding-recall assertion; real-doc invocation kept as observed-not-asserted dry-run; (2) High L272 Risk register introduced `inline-bytes-only` fallback contradicting LLD-011 fail-closed contract + plan's own "no design decisions" rule; removed fallback; restated recovery as fail-closed error + LLD-defined paths (restart iter-1, or `--override-cap` degraded mode); (3) High L111 Phase verification used filtered `pytest -k` only; slice counts (33/29/22) not multiples of 5 → tail-slice invariant regressions could slip past every-5-slice checkpoints; added Sequencing Rule 7 mandating full `pytest` + `pyrefly` + `cli.lint --pre-commit` + `cli.eval` at each phase-boundary acceptance gate; per-phase verification sections updated to distinguish filtered sanity-check (dev) from phase-boundary full-suite (required). |
