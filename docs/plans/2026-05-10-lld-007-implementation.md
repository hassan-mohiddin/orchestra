# Orchestra v1.6 — LLD-007 Implementation Plan

> **Doc ID:** 2026-05-10-lld-007-implementation
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Implementation Plan
> **Status:** Active
> **LLD:** `docs/features/007-spec-review-architecture.md` (Status: Draft → Implemented after this plan ships)
> **Attestations:** `docs/reviews/007-r{1,2,3}.review.yaml`

## Header

**Goal:** Implement LLD-007 — orchestra:spec-review judge-1 skill + slash command + cli.spec_review sidecar + 25 tests + 1 eval scenario. Ship as v1.6.0. Address all 10 codex findings (F1-F10) per LLD spec.

**Tech stack:** Python 3.14, pytest, jsonschema (new dep), pyyaml (existing), python-frontmatter (existing).

**LLD reference:** All design decisions in LLD-007. Plan does NOT re-state design.

**Bootstrap status:** LLD-007 is conditional_pass canon (3 codex rounds). 4 v1.6.x followups tracked in r3 attestation; addressed post-ship as observed.

## File Structure

```
orchestra/
├── skills/
│   └── spec-review/                                        # NEW directory (Task 1)
│       ├── SKILL.md                                          # NEW — frontmatter + dispatch instructions + multi-judge guidance
│       ├── prompt-template.md                                # NEW — 7-element adversarial prompt
│       ├── attestation-schema-v1.0.json                      # NEW — JSON-schema (with if/then for F3)
│       └── references/
│           └── 4-gate-rubric.md                              # NEW — pass/fail criteria per gate
├── commands/
│   └── spec-review.md                                      # NEW (Task 2) — slash-command shim
├── cli/
│   ├── spec_review.py                                      # NEW (Task 3) — sidecar (validation + write + F1-F9 enforcement)
│   └── templates/
│       └── attestation-template.yaml                       # NEW (Task 3 setup, PF3 fix) — empty fixture for tests
├── tests/
│   ├── test_spec_review_invoke.py                          # NEW (Task 4a) — T1
│   ├── test_spec_review_dispatch.py                        # NEW (Task 4a) — T2
│   ├── test_spec_review_prompt.py                          # NEW (Task 4a) — T3
│   ├── test_spec_review_schema.py                          # NEW (Task 4b) — T4-T6, T9-T12, T14, T15, T19a, T19b
│   ├── test_spec_review_path.py                            # NEW (Task 4b) — T7, T8, T24
│   ├── test_spec_review_bias.py                            # NEW (Task 4c) — T13a, T13b, T13c
│   ├── test_spec_review_iter.py                            # NEW (Task 4c) — T16
│   ├── test_spec_review_security.py                        # NEW (Task 4d) — T17a/b/c, T20, T21a/b
│   ├── test_spec_review_verdict.py                         # NEW (Task 4d) — T18
│   ├── test_spec_review_stale.py                           # NEW (Task 4d) — T22
│   └── test_spec_review_snapshot.py                        # NEW (Task 4d) — T23
├── eval/scenarios/
│   └── spec-review-yaml-schema-roundtrip.json              # NEW (Task 5)
├── docs/
│   ├── design/orchestra-philosophy.md                      # MODIFIED (Task 6) — Changelog v1.6 narrow append
│   └── features/007-spec-review-architecture.md            # MODIFIED (Task 6) — Status: Draft → Implemented (narrow change)
├── pyproject.toml                                          # MODIFIED (Task 6) — bump 1.5.1 → 1.6.0; add jsonschema>=4 dep
├── .claude-plugin/plugin.json                              # MODIFIED (Task 6) — bump 1.5.1 → 1.6.0
├── CHANGELOG.md                                            # MODIFIED (Task 6) — v1.6.0 entry
├── README.md                                               # MODIFIED (Task 6) — slash command mention
├── cli/templates/standards-default-7.md                    # MODIFIED (Task 6) — § Spec Review Rule rewrite per LLD-007
└── skills/design-docs/SKILL.md                             # MODIFIED (Task 6) — cross-reference to spec-review skill
```

## Tasks (TDD vertical slice — one test → one impl → repeat)

### Task 1: skills/spec-review/ scaffold (4 files)

- **Files:** SKILL.md, prompt-template.md, attestation-schema-v1.0.json, references/4-gate-rubric.md (all NEW)
- **What:** Per LLD-007 § Skill body structure + § 7-element adversarial prompt + § Attestation schema v1.0
- **Acceptance:** A1 (skill registered manual), A4 (7 prompt elements), A10 (schema v1.0)
- **Tests:** Tests come in Task 4a (test_spec_review_prompt.py reads files written here)
- **Sequencing:** Foundation. Must precede Task 3 + Task 4.
- **Commit:** Bundle with Task 2-3 (single feat: commit per LLD-007 ship)

### Task 2: commands/spec-review.md slash-command shim

- **Files:** commands/spec-review.md (NEW)
- **What:** Per LLD-007 § Slash command. Frontmatter + body referring user to skill.
- **Acceptance:** A2 (slash cmd accepts single positional arg)
- **Sequencing:** Independent of Task 1 + 3; can run parallel.
- **Commit:** bundled

### Task 3 — Vertical-slice TDD loop (cli/spec_review.py + tests grow together)

**PF2 fix** — replaces "write all impl, then write all tests" with true RED→GREEN per slice. Each slice = one failing test → minimum impl in cli/spec_review.py → green → next slice. NEVER write impl ahead of test.

**Setup (one-time, before slice 1):**
- Create empty `cli/spec_review.py` with import skeleton + `main(argv)` raising `NotImplementedError`
- Create `cli/templates/attestation-template.yaml` (PF3 fix — was missing in original plan; LLD-007 § cli.spec_review module references it as a fixture for tests)

**Slice ordering** (dependency-respecting; lowest-deps first to bootstrap module shape):

| # | Test ID | Test file | What this slice builds in `cli/spec_review.py` | Acceptance |
|---|---|---|---|---|
| S1 | T7 | test_spec_review_path.py | `compute_attestation_path()` no-suffix case | A6 |
| S2 | T8 | test_spec_review_path.py | `compute_attestation_path()` -rN suffix strip | A6 |
| S3 | T24 | test_spec_review_path.py | repo_root anchoring (F9) — caller side | A23 |
| S4 | T17a | test_spec_review_security.py | `canonicalize_doc_path()` rejects absolute paths | A16 |
| S5 | T17b | test_spec_review_security.py | `canonicalize_doc_path()` rejects `..` escape | A16 |
| S6 | T17c | test_spec_review_security.py | `canonicalize_doc_path()` rejects symlink escape | A16 |
| S7 | T21a | test_spec_review_security.py | F5 `FileNotFoundError` mapped to path_traversal_blocked | A20 |
| S8 | T21b | test_spec_review_security.py | F5 broken-symlink mapped to path_traversal_blocked | A20 |
| S9 | T16 | test_spec_review_iter.py | `parse_iteration_from_text()` + iteration-mismatch error | A11 |
| S10 | T15 | test_spec_review_schema.py | schema_version="1.1" → schema-fail (load schema, basic validate) | A10 |
| S11 | T9 | test_spec_review_schema.py | missing required field rejected | A7 |
| S12 | T10 | test_spec_review_schema.py | unknown gate name rejected | A7 |
| S13 | T11 | test_spec_review_schema.py | severity=Info rejected | A7 |
| S14 | T12 | test_spec_review_schema.py | overall_verdict=invalid rejected | A7 |
| S15 | T14 | test_spec_review_schema.py | location-field regex enforced | A9 |
| S16 | T19a | test_spec_review_schema.py | findings=[] missing justification → fail (if/then F3) | A18 |
| S17 | T19b | test_spec_review_schema.py | findings=[] short justification (<10 chars) → fail | A18 |
| S18 | T20 | test_spec_review_security.py | F4 path-mismatch hard-fail | A19 |
| S19 | T18 | test_spec_review_verdict.py | `compute_overall_verdict()` worst-case + F2 mismatch | A17 |
| S20 | T4 | test_spec_review_schema.py | valid YAML → exit 0 + file written (full happy path) | A5 |
| S21 | T5 | test_spec_review_schema.py | invalid first attempt + valid second → exit 0 (retry) | A5 |
| S22 | T6 | test_spec_review_schema.py | invalid twice → exit 1 | A5 |
| S23 | T22 | test_spec_review_stale.py | F6 stale-state byte-compare exit 1 | A21 |
| S24 | T23 | test_spec_review_snapshot.py | F8 single-read assertion (mock read_bytes called ≤2x) | A22 |
| S25 | T1 | test_spec_review_invoke.py | slash cmd argparse — single positional arg | A2 |
| S26 | T2 | test_spec_review_dispatch.py | structural — SKILL.md prose contains `subagent_type: general-purpose` | A3 |
| S27 | T3 | test_spec_review_prompt.py | render_prompt has 7 element headings | A4 |
| S28 | T13a | test_spec_review_bias.py | prompt template contains "ordering" instruction | A8 |
| S29 | T13b | test_spec_review_bias.py | duplicate-judge-id detection | A8 |
| S30 | T13c | test_spec_review_bias.py | SKILL.md prose contains `max_tokens: 4000` | A8 |
| S31 | T25 | test_spec_review_atomicity.py | atomic-write — pre-write fail (schema-fail-twice) → no file at out_path, no .tmp.* leftovers | A24 |
| S31b | T25b | test_spec_review_atomicity.py | atomic-write fault injection — mock open/fsync IOError mid-write → no file at out_path, temp cleaned (PF10) | A24 |
| S32 | T26 | test_spec_review_path.py | `docs/plans/...` accepted by schema regex | A25 |

**Per-slice loop:**

```
for slice in S1..S30:
    1. Write the failing test (commit not required mid-loop; commits at end)
    2. Run pytest -k <test_name> → MUST FAIL (red proves test catches the gap)
    3. Add minimum code to cli/spec_review.py (or skill files for S26-S30) to pass
    4. Run pytest -k <test_name> → MUST PASS (green)
    5. Run full pytest tests/ → no regression
    6. Move to next slice
```

If slice 5 (full pytest regression) fails → STOP, root-cause, fix before next slice. Never paper over with `@pytest.mark.skip`.

**Files touched across all slices:**
- `cli/spec_review.py` (grows incrementally — one function per slice batch)
- `cli/templates/attestation-template.yaml` (one-time at setup)
- 11 test files (grow incrementally as slices land)

**Acceptance covered:** A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A16-A23 (all code-checkable). A1, A12, A13 in Task 6 (manual + version). A14 in Task 7 (count gate). A15 in Task 5 (eval).

**Sequencing:** Foundation = Task 1 + 2 + setup-step above. Slices then run sequentially S1..S30 within Task 3.

**Commit:** Bundle all into single feat: commit (atomic-ship). Slice commits NOT required mid-loop (would inflate git history; per `.claude/rules/commit-strategy.md` mid-feature commits are OK but not required if final state is one logical unit).

### Task 5: eval/scenarios/spec-review-yaml-schema-roundtrip.json

- **Files:** eval/scenarios/spec-review-yaml-schema-roundtrip.json (NEW)
- **What:** Per LLD-007 § New eval scenario. Pipe canned valid YAML to `python -m cli.spec_review`; verify exit 0, file written, hash recomputed, path canonical.
- **Acceptance:** A15
- **Sequencing:** After Task 3 (eval invokes cli.spec_review).

### Task 6: docs + version + meta (single commit "feat: ship v1.6.0")

- **Files:**
  - LLD-007 Status: Draft → Implemented. **Allowed because Draft is NOT canon-frozen** (LLD-006-r4 Glossary § canon-frozen statuses = `{Approved, Implemented, Verified, Fix Applied, Current}`). Per LLD-006-r4 § narrow change: "modification permitted in-place to a canon-frozen doc" — narrow-change rules apply ONLY to canon-frozen. Draft → Implemented is a Status flip on a not-yet-canon-frozen doc; full edit unrestricted (PF5 fix — replaces prior non-authoritative "symmetric rejection-finalization-edit" rationale).
  - philosophy Changelog (narrow append): v1.6.0 entry
  - pyproject.toml: 1.5.1 → 1.6.0 + jsonschema>=4 dep
  - plugin.json: 1.5.1 → 1.6.0
  - CHANGELOG.md: v1.6.0 entry
  - README.md: slash command mention
  - cli/templates/standards-default-7.md: § Spec Review Rule rewrite (D3); add Plans-as-attestation-target note
  - skills/design-docs/SKILL.md: cross-reference to spec-review skill
  - **`cli/lint.py` ALLOWED_ATTESTATION_PATH_PREFIXES extension** (A25 enabling change): add `"docs/plans/"` to the tuple. Without this, current v1.5.0 L3 lint rejects plan attestations. Small surgical addition to existing v1.5.0 code.
  - **STANDARDS.md doc-type table** (A25 disclosure): note that `docs/reviews/<doc-id>-rN.review.yaml` is a tracked doc TYPE (machine-validated YAML attestation). Reviews are docs but follow schema, not free-form prose; no recursive spec-review on attestations themselves (would create infinite regress).
- **What:** Bundle all metadata + version + doc updates. Final commit.
- **Acceptance:** A12, A13
- **Sequencing:** Last. After all code + tests green (Task 7 gate).

### Task 7: Verification (fail-closed; no commit)

**PF1 fix** — verification gate must be fail-closed on exit status. Pipe to `tail` masks failures (pipeline exit = `tail`'s exit). Use `set -o pipefail` OR run gate commands without pipe.

Run before final commit:
```bash
set -e                                             # fail-fast on any non-zero
set -o pipefail                                    # PF1: pipe exit = first non-zero in pipeline
cd orchestra

# Full pytest run — every test green
.venv/bin/python -m pytest tests/ -q               # exit 0 required; 132+ collected

# PF4 + PF8: assert specific test IDs collected (not just total count).
# Count-only gate could pass with unrelated growth or skipped tests — semantically false.
REQUIRED_TESTS=(
  "test_spec_review_path.py::test_attestation_path_no_suffix"          # T7 / S1
  "test_spec_review_path.py::test_attestation_path_with_rN_suffix"     # T8 / S2
  "test_spec_review_path.py::test_attestation_path_anchored_to_repo_root" # T24 / S3
  "test_spec_review_security.py::test_absolute_path_rejected"          # T17a / S4
  "test_spec_review_security.py::test_dotdot_escape_rejected"          # T17b / S5
  "test_spec_review_security.py::test_symlink_escape_rejected"         # T17c / S6
  "test_spec_review_security.py::test_missing_file_returns_path_traversal_blocked" # T21a / S7
  "test_spec_review_security.py::test_broken_symlink_returns_path_traversal_blocked" # T21b / S8
  "test_spec_review_iter.py::test_iteration_mismatch_exits_1"          # T16 / S9
  "test_spec_review_schema.py::test_schema_version_must_be_1_0"        # T15 / S10
  "test_spec_review_schema.py::test_missing_required_field_rejected"   # T9 / S11
  "test_spec_review_schema.py::test_unknown_gate_name_rejected"        # T10 / S12
  "test_spec_review_schema.py::test_severity_enum_violated_rejected"   # T11 / S13
  "test_spec_review_schema.py::test_overall_verdict_enum_violated_rejected" # T12 / S14
  "test_spec_review_schema.py::test_location_field_regex_enforced"     # T14 / S15
  "test_spec_review_schema.py::test_empty_findings_no_justification_rejected" # T19a / S16
  "test_spec_review_schema.py::test_empty_findings_short_justification_rejected" # T19b / S17
  "test_spec_review_security.py::test_attestation_path_mismatch_exits_1" # T20 / S18
  "test_spec_review_verdict.py::test_overall_verdict_mismatch_exits_1" # T18 / S19
  "test_spec_review_schema.py::test_valid_yaml_passes"                 # T4 / S20
  "test_spec_review_schema.py::test_invalid_yaml_retries_once"         # T5 / S21
  "test_spec_review_schema.py::test_invalid_yaml_twice_fails"          # T6 / S22
  "test_spec_review_stale.py::test_doc_modified_between_dispatch_and_write_exits_1" # T22 / S23
  "test_spec_review_snapshot.py::test_single_read_for_hash_iter_prompt" # T23 / S24
  "test_spec_review_invoke.py::test_slash_command_arg_parsing"         # T1 / S25
  "test_spec_review_dispatch.py::test_skill_md_specifies_general_purpose_subagent" # T2 / S26
  "test_spec_review_prompt.py::test_prompt_template_has_7_elements"    # T3 / S27
  "test_spec_review_bias.py::test_finding_order_random_seed_in_prompt" # T13a / S28
  "test_spec_review_bias.py::test_force_required_for_same_iteration_overwrite" # T13b / S29
  "test_spec_review_bias.py::test_skill_md_specifies_max_tokens_4000"  # T13c / S30
  "test_spec_review_atomicity.py::test_no_partial_write_on_pre_write_failure"  # T25 / S31
  "test_spec_review_atomicity.py::test_no_partial_write_on_io_exception"       # T25b / S31b
  "test_spec_review_path.py::test_plans_path_accepted_in_schema"       # T26 / S32
)
COLLECTED=$(.venv/bin/python -m pytest tests/ --collect-only -q)
for t in "${REQUIRED_TESTS[@]}"; do
  echo "$COLLECTED" | grep -qF "$t" || { echo "A14 FAIL: required test missing: $t"; exit 1; }
done
# PF9 fix — pytest exit 0 does NOT detect skips; need explicit skipped count from JUnit output.
# Run spec-review tests with junit-xml; assert zero skips on required tests.
.venv/bin/python -m pytest tests/test_spec_review_*.py --junitxml=/tmp/specrev-junit.xml -q
SKIPPED=$(.venv/bin/python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('/tmp/specrev-junit.xml')
root = tree.getroot()
skipped = root.attrib.get('skipped', '0')
print(skipped)
")
[ "$SKIPPED" = "0" ] || { echo "A14 FAIL: $SKIPPED required spec-review test(s) skipped"; exit 1; }

.venv/bin/python -m eval.run --all                 # exit 0 required; 12/12 PASS

.venv/bin/python -m cli.lint --doc docs/features/007-spec-review-architecture.md
.venv/bin/python -m cli.lint --attestations        # all attestations valid
```

If any command exits non-zero → STOP. Fix root cause. Never skip to commit on red.

**A14 owned by Task 7** (PF4 + PF8 fixes): Task 7 verifies (a) full pytest exits 0 with no skips on spec-review tests, (b) all 30 required test IDs are collected (semantic check, not just count), (c) `eval.run --all` 12/12, (d) lint clean. Any failure blocks Task 6 commit.

### Task 8: Post-commit dogfood (manual D4 deliverable — BLOCKING)

**PF4 fix** — runtime Task-kwargs verification (A3/A8 manual claim) is BLOCKING for v1.6 ship completion. Not just an "if differs, file bug" — this is the test that A3 + A8 actually hold in practice.

After commit lands locally:

```bash
/orchestra:spec-review docs/features/007-spec-review-architecture.md
```

**Required pass criteria (all must hold):**

1. Skill produces an attestation YAML at `docs/reviews/007-r4.review.yaml` (next iteration)
2. Attestation passes `cli.lint --attestations` (schema valid, paths valid)
3. **Runtime Task kwarg inspection (not prose)** — capture the actual Task tool invocation when the skill runs (e.g., via Claude Code's tool-call log / transcript). Assert: `subagent_type == "general-purpose"` AND prompt content includes 7-element template. NOT SKILL.md prose check (PF7/PF11 lessons learned — recurring drift).
4. **Runtime token-cap inspection (not prose, PF11 fix)** — same captured Task invocation must show `max_tokens == 4000`. Inspecting SKILL.md prose for "max_tokens: 4000" string is INSUFFICIENT — it doesn't prove runtime kwargs match prose. If Task invocation log shows different/missing max_tokens → criterion 4 FAILS.
5. overall_verdict ∈ {pass, conditional_pass}; if `fail` → record findings + iterate

**Failure handling (PF6 fix — no conditional-ship escape hatches on trust-boundary controls):**

- **Schema-fail or path-fail (criteria 1-2)** → BUG-NNN-spec-review-bootstrap-{schema|path}-mismatch filed; v1.6 ship REVERTED via `git revert`; address in v1.6.1 patch
- **Task-kwargs mismatch (A3/A8 fail, criteria 3-4)** → BUG-NNN-spec-review-runtime-dispatch-drift filed; v1.6 ship REVERTED via `git revert`. NO conditional-ship path. Criteria 3 + 4 are trust-boundary controls (subagent isolation, output cap); ship cannot proceed with known runtime gaps. Address in v1.6.1 patch + re-attempt ship.
- **Verdict=fail with new findings on LLD-007 (criterion 5)** → expected (reviewer is doing its job); apply per LLD-006-r4 narrow-change rules + bump LLD-007 Iteration → 4 + add r4 attestation. Not a ship-blocker on its own; LLD already conditional_pass with v1.6.x followups tracked.

Until all 5 criteria pass → v1.6 not considered Verified. LLD-007 Status stays Implemented until Task 8 green; flips to Verified post-dogfood (separate small commit).

## Dependencies

```
Task 1 (skill scaffold)  ──┐
                            ├──► Task 3 (cli.spec_review) ──► Task 4 (tests) ──► Task 5 (eval)
Task 2 (slash command)   ──┘                                                          │
                                                                                       ▼
                                                                         Task 7 (verification — green?)
                                                                                       │
                                                                                       ▼
                                                                          Task 6 (docs + commit)
                                                                                       │
                                                                                       ▼
                                                                          Task 8 (manual dogfood)
```

## Sequencing rule

TDD vertical slice: for each task in 4a/b/c/d, write ONE failing test → minimum impl in cli.spec_review.py → green → next test. NOT all-tests-then-all-impl (horizontal).

## Estimated time

- Task 1 (skill scaffold): 30 min
- Task 2 (slash cmd): 5 min
- Task 3 (TDD vertical slice S1-S30, ~5min/slice avg): 150 min
- Task 5 (eval): 15 min
- Task 6 (meta + commit): 20 min
- Task 7 (verification gate, fail-closed): 10 min
- Task 8 (dogfood — BLOCKING): 15 min (incl. inspecting Task kwargs)

**Total: ~4 hours**

(Increase from prior 3.5h driven by TDD vertical-slice discipline + dogfood Task-kwargs runtime verification — both PF2 and PF4 fixes trade speed for correctness assurance.)

## v1.6.x followups (NOT this plan; track post-ship)

Per LLD-007 r3 attestation `required_followup`:

1. Iteration vs `-rN` filename suffix semantic disambiguation (LLD-006-r4 strict reading vs in-draft pragmatic)
2. Runtime token-cap enforcement (move dispatch into Python OR add stdin guards)
3. Runtime Task-kwargs verification (post-dogfood)
4. Stdin-bound size limit in cli.spec_review (DoS bound)

Each → small BUG-NNN or v1.6.x patch as observed.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Plan written immediately after LLD-007 conditional_pass canon. 8 tasks, ~3.5h. TDD vertical slice. Status: Active. |
| 2026-05-10 | Codex round-1 review of plan (verdict: needs-attention; 5 findings). All 5 addressed: PF1 (High) verification fail-open — added `set -o pipefail`, removed result-masking pipes, A14 explicit pytest-count check; PF2 (High) Task 3+4 horizontal — restructured into 30 explicit RED→GREEN slices S1-S30 in dependency order; PF3 (Medium) missing `cli/templates/attestation-template.yaml` — added to file structure + Task 3 setup step; PF4 (Medium) A14 ownership + Task 8 not blocking — A14 owned by Task 7 with explicit count gate, Task 8 dogfood marked BLOCKING with 5 pass criteria including runtime Task-kwargs verification; PF5 (Low) Task 6 rationale — replaced "symmetric rejection-finalization-edit" with authoritative LLD-006-r4 language (Draft is NOT canon-frozen → narrow-change rules don't apply → full edit unrestricted). Estimated time: 3.5h → 4h (TDD vertical-slice + blocking dogfood adds rigor cost). Status: Active. |
| 2026-05-10 | Codex round-2 review of plan (verdict: needs-attention; 3 NEW findings, no overlap with PF1-PF5). All 3 addressed: PF6 (High) conditional-ship escape hatch — Task 8 failure handling for A3/A8 mismatch now mandates revert + v1.6.1 patch, no conditional-ship path; PF7 (High) T13c drift between plan + LLD — LLD-007 testing matrix updated to match plan structural-prose-check claim (consistent with A8 honest narrowing); PF8 (Medium) A14 count-only gate — Task 7 now has explicit REQUIRED_TESTS array verifying T1-T26 (now T1-T32 with S31+S32 additions) collected + non-skipped, not just total count. Plan attestations created retroactively at `docs/reviews/2026-05-10-lld-007-implementation-r{1,2}.review.yaml` per user request (every review gets attestation doc). LLD-007 schema regex extended to allow `docs/plans/` as valid doc_subject.path. Two new acceptance items A24 (atomic-write contract; no partial files on failure) + A25 (plans as valid attestation targets) → S31 + S32 slices added. Tests: 25 → 27. Pytest target: 132 → 134. Status: Active. |
| 2026-05-10 | Codex round-3 review of plan (verdict: needs-attention; 3 NEW findings, no overlap with PF1-PF8). All 3 addressed: PF9 (High) skipped-tests gate broken — pytest exit 0 doesn't catch skips; replaced with junit-xml parse + assert `skipped == 0`; PF10 (High) atomic-write only covered pre-write failure — A24 redefined with temp+fsync+os.replace pattern + new fault-injection test T25b for I/O-exception case; LLD-007 cli.spec_review module updated with concrete atomic-write code; PF11 (Medium) Task 8 criterion 4 prose-only — replaced with runtime Task-kwargs inspection (capture actual invocation, assert max_tokens == 4000); same lesson as F10/F7 recurring (prose-vs-runtime drift kills trust-boundary controls if not enforced at runtime). T25 split into T25 (pre-write fail) + T25b (write-path fault injection); slice S31 split into S31 + S31b. Tests: 27 → 28. Pytest target: 134 → 135. 3 codex rounds total = max-iteration boundary per LLD-006-r4 convention. Plan accepted as conditional_pass canon-equivalent — implementation can proceed; remaining residual issues addressed in v1.6.x followups if observed. Status: Active → ready for implementation. |
