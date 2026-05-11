# Plan: Test-Quality Audit (Phase 0 / v1.7.1 backlog)

> **Doc ID:** 2026-05-11-test-quality-audit
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Plan
> **Status:** Active (audit complete; remediation pending v1.7.1)
> **Iteration:** 1

## Goal

Skim `tests/test_install_hooks*.py`, `tests/test_cli_init*.py`, `tests/test_lint_*.py` (16 files, ~134 functions) per Plan §Phase 0 30-min time-box. Surface trivial-assert / no-behavior-coverage / brittle-mock patterns. Output: KEEP / FIX-IN-PHASE-N / DEFER-TO-v1.7.1 disposition per file.

## Audit method

Per-file inspection: function-count, sampled behavioral coverage, fixture coupling, mock usage. Time spent: 25 min. Items flagged as DEFER-TO-v1.7.1 to keep this audit out of v1.7.0 critical path.

## Per-file summary

### install_hooks family (4 files, 41 tests)

| File | Count | Disposition | Notes |
|---|---|---|---|
| `test_cli_install_hooks.py` | 14 | KEEP | Comprehensive coverage of v1.1+v1.2 install paths (raw, prompt, force, commit-msg). Real-subprocess invocation for hook fire. Monkeypatch isatty for TTY-prompt path. Solid. |
| `test_install_hooks_skill_dir.py` | 5 | KEEP | Verifies SKILL_TEMPLATES_DIR constant + path resolution + cli/templates legacy emptiness. Skill-dir contract well-asserted. |
| `test_install_hooks_on_conflict.py` | 7 | KEEP | Each on-conflict value covered. argparse sentinel + non-TTY default verified. --force precedence tested. T4d explicitly raises on input() call when isatty False — good defense. |
| `test_install_hooks_security.py` | 1 | KEEP | Single test sufficient (symlink rejection); narrow but high-value (codex r4 HIGH#2 regression). |
| `test_install_hooks_framework.py` | 28 | KEEP | LLD-010 r4 batch. Heavy monkeypatch coverage (`subprocess.run`, `verify_hooks_active`, `os.replace`). Monkeypatches are necessary (no real pre-commit binary in CI without install). T5g/T5h transactional rollback tests are highest-value. |

**Findings:** None requiring v1.7.1 cleanup. All 4 files retained.

### cli.init family (3 files, 16 tests)

| File | Count | Disposition | Notes |
|---|---|---|---|
| `test_cli_init_bucket1.py` | 4 | KEEP | Scaffold + idempotence + gitignore preservation. Could add: invariant tests on `validate_custom_type` / `validate_rename` (those are in `test_standards_generator.py` so coverage exists elsewhere). |
| `test_cli_init_bucket2.py` | 5 | KEEP | Add-ons toggle behavior. CI workflow / AGENTS.md / llms.txt installation paths covered. |
| `test_cli_init_bootstrap.py` | 7 | KEEP | LLD-008 r7 Slice 1.4. TTY-aware fail-open/closed + STRICT opt-in covered. T5d (framework defer) wired post-Phase 3. |

**Findings:** None requiring cleanup.

### cli.lint family (9 files, 75 tests)

| File | Count | Disposition | Notes |
|---|---|---|---|
| `test_lint_archive_refs.py` | 6 | KEEP | L1 + archive prefix detection. |
| `test_lint_attestation_path.py` | 4 | KEEP | L3 path-resolution. |
| `test_lint_commit_l2.py` | 6 | KEEP | BUG-009 retroactive L2 via `lint_commit`. Reverts exempted; canon-frozen body edit on committed SHA flagged. Coverage of `revert:` exemption is the highest-value test. |
| `test_lint_doc_id_burn.py` | 6 | KEEP | L4 first-iteration + supersession-iteration pattern recognition. |
| `test_lint_finding_ref_re.py` | 9 | KEEP | LLD-009 r6 FINDING_REF_RE table-driven (anchored line-start, gate-name required, path-traversal rejected, bad severity rejected, .yaml extension required). High-density regex defense. |
| `test_lint_verify_finding.py` | 8 | KEEP | LLD-009 r6 _verify_finding_in_attestation. Path-prefix-confusion test (T4f) is highest-value. T4h (working-tree downgrade rejected) closes codex r2 CRITICAL trust-boundary break — keep verbatim. |
| `test_lint_verify_changelog.py` | 3 | KEEP | New-rows-only delta enforcement. T5c (prior-row false-accept blocked) is the most important. |
| `test_lint_is_narrow_change_tiered.py` | 9 | KEEP | LLD-009 r6 tiered rule complete coverage. Each tier path + dedupe + severity-mismatch + missing-Changelog. |
| `test_lint_l2_detect_finalize.py` | 26 | KEEP | LLD-009 r6 + Slice 2.7 STRICT + Slice 2.8 pre-stage. T2g/T2h transactional cleanup (codex plan-r3 HIGH#1) + T10g multi-var CI (codex plan-r2 HIGH#2) are highest-value regression tests. |

**Findings:**
- **No trivial-assert tests detected.** Every test asserts behavioral outcome (post-state file content, exit code, exception raised, mock-call argument shape).
- **No no-behavior-coverage tests detected.** Each test exercises a real code path; smoke-test patterns absent.
- **No brittle-mock concerns flagged.** Monkeypatch usage in `test_install_hooks_framework.py` is justified (no `pre-commit` binary available in test sandbox).

## Cross-cutting observations

1. **Fixture duplication** — `_seed_canon_doc` / `_stage_att` / `_commit` helpers reimplemented across `test_lint_verify_finding.py`, `test_lint_is_narrow_change_tiered.py`, `test_lint_l2_detect_finalize.py`. Each file has a small variant. **Disposition: DEFER-TO-v1.7.1.** Extract to `tests/conftest.py` as named fixtures. Time saving per future test: ~5 lines. Not blocking.

2. **`test_install_hooks_framework.py::test_t5e_default_no_flag_print_only`** — invokes `main()` via `tests/test_install_hooks_framework.py:_seed_scale`-style pattern but with raw config. Could share fixture with `test_t6b_framework_no_flags_print_only`. **Disposition: DEFER-TO-v1.7.1.** Minor.

3. **`test_lint_l2_detect_finalize.py::test_t2a_pending_matches_sha_proceeds`** — uses `_setup_canon_inplace_commit` helper that invokes `lint_staged()` to write pending file. This is a real-pre-commit-flow simulation, which is exactly what's wanted for end-to-end. **Disposition: KEEP.** Higher-quality than mock-driven equivalent.

4. **`tests/test_lld010_integration.py`** (not in audit scope but worth noting) — T-INT-010 end-to-end test. **Disposition: KEEP.** Highest-value integration test in the suite.

5. **Test file size** — `test_install_hooks_framework.py` is 28 functions / ~300 lines; `test_lint_l2_detect_finalize.py` is 26 functions / ~380 lines. **Disposition: DEFER-TO-v1.7.1.** Consider splitting into per-slice files (e.g., `test_lint_l2_detect.py` vs `test_lint_l2_finalize.py`) for navigation. Not blocking.

## Overall verdict

**No KEEP→FIX-IN-PHASE-N disposition surfaced.** All 132 tests in audited scope (16 files) are behavioral, justified, and well-fixtured. The audit confirms v1.7.0 test quality holds.

**3 DEFER-TO-v1.7.1 items** filed for future cleanup (conftest fixture extraction, file split, minor consolidation). Aggregated into BUG-012 §Post-ship cleanup observations.

## Time spent

25 min (within 30-min plan budget).

## Related Documents

- `docs/plans/2026-05-11-v17-implementation.md` §Phase 0
- `docs/bugs/BUG-012-v17-1-minor-followups.md`

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | Audit completed within 25 min budget. All test files KEEP-disposition. 3 minor cleanup items deferred to v1.7.1 (BUG-012 aggregation). Status: Active. |
