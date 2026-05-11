# Implementation Plan: orchestra v1.7.0 — commit-skill consolidation (LLD-008 r5 + LLD-009 r3 + LLD-010 r3)

> **Doc ID:** 2026-05-11-v17-implementation
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Plan
> **Status:** Active
> **Targets:** LLD-008 r5 + LLD-009 r3 + LLD-010 r3 (combined v1.7.0 ship)

## Goal

Ship `orchestra:commit` skill at v1.7.0 in a single atomic release covering:

- Skill structure + references migration + cli.install_hooks `--on-conflict` flag + cli.init bootstrap (LLD-008 r5)
- Commit-msg L2-finalize + tiered narrow-change rule (BUG-011 close) + `ORCHESTRA_STRICT` opt-in mode (LLD-009 r3)
- Pre-commit framework detection + `--apply` transactional rollback + `--verify` hybrid fingerprint (LLD-010 r3; BUG-006 close)
- SCALE-side migration (2 deletions + 1 partial-edit + 1 registry-append)

Pytest target: **≥240** (= 150 baseline + 15 LLD-008 + 48 LLD-009 + 27 LLD-010).

## Cross-LLD dependencies

```
LLD-008 (skill structure)
  ↳ provides SKILL_TEMPLATES_DIR constant
  ↳ provides skills/commit/templates/{pre-commit.sh, commit-msg.sh} files (empty content fingerprint)
  ↳ provides cli.install_hooks --on-conflict flag

LLD-009 (L2-finalize)
  ↳ consumes SKILL_TEMPLATES_DIR (commit-msg.sh template content owned here)
  ↳ adds is_narrow_change tiered extension + helpers
  ↳ adds cli.lint --commit-msg-finalize / --pre-stage-check entrypoints

LLD-010 (framework-detection)
  ↳ consumes SKILL_TEMPLATES_DIR (precommit-framework-snippet.yaml)
  ↳ adds --apply + --verify + framework detection branches to cli.install_hooks

SCALE migration: applies AFTER all 3 LLDs land (deletes SCALE/.claude/rules/canon-frozen-guard.md + commit-strategy.md; partial-edits documentation-gate.md; appends registry).
```

## Implementation strategy: TDD vertical slices

Per `mattpocock-skills:tdd` + LLD-007 precedent: one failing test → one implementation → green → next slice. Vertical means feature-thin slices (test + impl + doc-deviation entry if any), NOT horizontal (all tests then all impl).

## Phase 0: Pre-impl test-quality audit (one-time)

Before slicing: skim `tests/test_install_hooks.py`, `tests/test_cli_install_hooks.py`, `tests/test_cli_init_*.py`, `tests/test_lint_*.py` for low-quality tests (e.g., asserts trivial; tests path that doesn't exercise behavior). Fix or note for cleanup post-ship. Time-box: 30min. Output: `docs/plans/2026-05-11-test-quality-audit.md` (one-line summary per test file).

## Phase 1: LLD-008 r5 (skill structure + bootstrap; 15 tests)

### Slice 1.1 — Skill directory scaffolding (T1, T2)
- **Test first:** `tests/test_commit_skill_structure.py::test_skill_dir_has_expected_files` — asserts 8 files at expected paths under `skills/commit/`. Initially fails (no skill).
- **Impl:** Create directory + 8 files (with minimal placeholder content; full content filled in slice 1.2):
  - `skills/commit/SKILL.md`
  - `skills/commit/templates/pre-commit.sh` (moved from `cli/templates/pre-commit.sh`)
  - `skills/commit/templates/commit-msg.sh` (moved from `cli/templates/commit-msg.sh`)
  - `skills/commit/references/{commit-strategy,canon-frozen-guard,refs-line-rules,doc-vs-code-commit,supersession-decision}.md`
- **Verify:** `pytest tests/test_commit_skill_structure.py -v` → green
- **Doc-deviation entry:** none if matches spec.

### Slice 1.2 — Hook template relocation + SKILL_TEMPLATES_DIR (T3)
- **Test first:** `tests/test_install_hooks.py::test_install_hooks_reads_from_skill_dir` — asserts new SKILL_TEMPLATES_DIR constant resolves correctly; pre-commit hook installs with skill-dir template content. Initially fails.
- **Impl:**
  - Add `SKILL_TEMPLATES_DIR` constant to `cli/install_hooks.py` (top-level, after `from pathlib import Path`).
  - Update template-loading to read from `SKILL_TEMPLATES_DIR / "pre-commit.sh"` etc.
  - Delete `cli/templates/pre-commit.sh` + `cli/templates/commit-msg.sh`.
  - Fingerprint comment `# orchestra` in line 2 of both shell templates.
- **Verify:** `pytest tests/test_install_hooks.py -v` → green; `python3 -m cli.install_hooks --commit-msg` writes commit-msg hook with `# orchestra` in line 2.

### Slice 1.3 — `--on-conflict` flag with argparse sentinel (T4a-e)
- **Test first:** 5 test functions in `tests/test_cli_install_hooks.py`:
  - `test_on_conflict_skip_leaves_untouched`
  - `test_on_conflict_replace_overwrites`
  - `test_on_conflict_append_concatenates`
  - `test_non_tty_no_flag_defaults_to_skip` — pty fakery for stdin
  - `test_force_takes_precedence_over_on_conflict`
- **Impl:**
  - Add `--on-conflict` flag with `default=None` (sentinel) + `choices=["skip", "replace", "append"]`.
  - Update `install_one_hook` to handle sentinel via TTY check + `--force` precedence.
  - Preserve existing `input_fn=input` parameter for test injection.
- **Verify:** all 5 tests green.

### Slice 1.4 — cli.init bootstrap with WARNING on non-zero rc (T5a-e)
- **Test first:** 5 test functions in `tests/test_cli_init_bootstrap.py`:
  - `test_cli_init_bootstrap_installs_both_hooks` (no framework)
  - `test_cli_init_bootstrap_idempotent`
  - `test_cli_init_non_tty_clean_exit`
  - `test_cli_init_framework_present_no_apply_defers_to_print_only`
  - `test_cli_init_bootstrap_non_zero_rc_emits_warning`
- **Impl:** Add bootstrap call to end of `cli.init.main()` invoking `cli.install_hooks.main(["--all", "--on-conflict=skip"])`; capture rc; emit WARNING on non-zero; cli.init returns 0 unconditionally (non-blocking).
- **Verify:** all 5 tests green.

### Slice 1.5 — SCALE migration test (T6)
- **Test first:** `tests/test_scale_migration.py::test_scale_migration_post_state` — in-tmpdir fixture replicating pre-migration SCALE `.claude/rules/`; runs migration helper; asserts post-state. Initially fails.
- **Impl:** Write `tests/fixtures/scale-pre-migration/` + `tests/scale_migration_helper.py` (encapsulates migration steps); assert files absent + documentation-gate.md retains Gates 1-3 + Quick Reference Gates 1-3 + skill pointer + registry append.
- **Verify:** test green.

### Slice 1.6 — Symlink rejection (T8)
- **Test first:** `tests/test_install_hooks_security.py::test_symlink_destination_rejected` — creates `.git/hooks/pre-commit` as symlink to `/tmp/xxx`; asserts `install_one_hook` raises `SecurityError`. Initially fails.
- **Impl:** Add `hook_path.is_symlink()` lstat check + parent-dir `.resolve()` containment verification before any write.
- **Verify:** test green.

### Slice 1.7 — Pytest baseline assertion (T7)
- **Test first:** `tests/test_pytest_baseline.py::test_baseline_at_least_165` — collects all tests; asserts count ≥165. Initially might fail.
- **Impl:** N/A; just sanity check.
- **Verify:** `pytest --collect-only -q | wc -l` ≥165.

**Phase 1 milestone:** all 15 LLD-008 tests green + baseline ≥165. Bump SKILL.md `version: 1.7.0-pre`. Commit: `feat: LLD-008 r5 skill structure + bootstrap (BUG-010 Part 3 closed). Refs: docs/features/008-commit-skill.md`.

## Phase 2: LLD-009 r3 (L2-finalize + tiered + ORCHESTRA_STRICT; 48 tests)

### Slice 2.1 — FINDING_REF_RE constant + ALLOWED_GATES (T6)
- **Test first:** `tests/test_lint_finding_ref_re.py` — 8 sub-cases: valid line passes; embedded mid-prose fails; `..`-traversal fails; unknown gate fails; etc.
- **Impl:** Add regex + tuple constant to `cli/lint.py`.

### Slice 2.2 — `_verify_finding_in_attestation` helper with staged-content read (T4a-h)
- **Test first:** 8 sub-tests including the staged-content trust source check (T4h: working-tree-only attestation with downgraded severity → rejected via `attestation_not_staged`).
- **Impl:** Helper reads via `git show :0:<path>`; uses `Path.is_relative_to` for containment; navigates `gates[<gate>].findings[finding_n-1]` directly.

### Slice 2.3 — `_verify_changelog_row_per_finding` helper with new-rows-only delta (T5a-c)
- **Test first:** 3 sub-tests: all-present matches new-row; missing new row rejects; prior Changelog row alone insufficient (false-accept blocked).
- **Impl:** Helper takes `new_body` + `prior_body`; computes delta; regex-matches `att_basename + gate + finding_n` in new rows only.

### Slice 2.4 — `is_narrow_change` tiered extension (T3a-h)
- **Test first:** 8 sub-tests covering tier paths: Minor pass, Critical reject, Important ≤3 pass, Important ≥4 reject, Minor without Changelog reject, severity mismatch, no Addresses+canon-inplace reject (fallback), dedupe.
- **Impl:** Extend signature; add tiered logic (Step 2 of pseudocode); accumulate findings (no early-return); dedupe by `(path, gate, finding_n)`.

### Slice 2.5 — `lint_staged` L2-detect path (T1a-e)
- **Test first:** 5 sub-tests including worktree subdir gitdir resolution (T1e).
- **Impl:** Modify `lint_staged` to call `is_narrow_change(prior, new, commit_msg=None, repo_root=None)` for canon-frozen candidates; on False return, append `<sha>\t<path>` to pending file (resolved via `git rev-parse --git-path`); does NOT block.

### Slice 2.6 — `lint_commit_msg_finalize` entrypoint + ORCHESTRA_BYPASS (T2a-f, T10a-d, T11)
- **Test first:** 6 + 4 + 1 = 11 sub-tests.
- **Impl:** New CLI subcommand `cli.lint --commit-msg-finalize <msg-file>`. Reads pending, msg, runs tiered rule per pending entry; cleans up via `unlink(missing_ok=True)`. ORCHESTRA_BYPASS handling with audit log (HEAD-or-INITIAL sha). Fail-closed when no msg-file arg.

### Slice 2.7 — ORCHESTRA_STRICT opt-in mode (T10b-strict-a/b/c)
- **Test first:** 3 sub-tests: strict + no pending + staged canon-inplace + Addresses → pass; strict + missing Addresses → reject; non-strict + no pending → fail-open pass.
- **Impl:** At start of `lint_commit_msg_finalize`, check `os.environ.get("ORCHESTRA_STRICT") == "1"` + pending absent → invoke recompute helper that scans staged docs via `git diff --cached --name-only` + canon-frozen status + tiered rule on each.

### Slice 2.8 — `lint_pre_stage_check` author entrypoint (T9a-c)
- **Test first:** 3 sub-tests.
- **Impl:** New CLI subcommand `cli.lint --pre-stage-check <doc-path> --commit-msg-draft <text>`. Runs L2-finalize logic against working-tree (since not yet staged).

### Slice 2.9 — commit-msg.sh shell wrapper with python3-pin (T12)
- **Test first:** template content assertions (shebang + `# orchestra` line 2 + Refs:-line check + L2-finalize invocation + python3-pin fallback).
- **Impl:** Update `skills/commit/templates/commit-msg.sh` to inlined LLD-009 content.

### Slice 2.10 — pre-commit.sh template content (T13-pre)
- **Test first:** template content (shebang + `# orchestra` line 2 + `python3 -m cli.lint --pre-commit`).
- **Impl:** Update `skills/commit/templates/pre-commit.sh`.

### Slice 2.11 — SKILL.md pre-stage checklist (T8)
- **Test first:** `tests/test_skill_md_content.py::test_skill_md_pre_stage_checklist_present` — assert SKILL.md contains the pre-stage checklist + attestation-commit-first note.
- **Impl:** Write SKILL.md prose per LLD-009 Author UX section.

**Phase 2 milestone:** all 48 LLD-009 tests green + baseline ≥213. BUG-011 frontmatter `Status: Investigating → Fix Applied` via whitelist edit. Commit: `feat: LLD-009 r3 L2-detect/L2-finalize + tiered narrow-change (BUG-011 closed). Refs: docs/features/009-commit-msg-l2-finalize.md`.

## Phase 3: LLD-010 r3 (framework detection + verify + transactional --apply; 27 tests)

### Slice 3.1 — `precommit-framework-snippet.yaml` template (T1 + T2)
- **Test first:** snippet content assertions (2 hook ids; both `pass_filenames: false`; active `default_install_hook_types` directive).
- **Impl:** Write `skills/commit/templates/precommit-framework-snippet.yaml` per LLD-010 r3 content.

### Slice 3.2 — Framework detection helpers (T3a-d)
- **Test first:** 4 sub-tests: full config → already-configured + verify; no orchestra ids → snippet emitted; malformed config → UserConfigParseError → exit non-zero; partial XOR → hard-fail.
- **Impl:** Add `_is_precommit_framework`, `_parse_user_config` (raises `UserConfigParseError`), `_detect_orchestra_ids`, `_orchestra_ids_state`.

### Slice 3.3 — `--verify` hybrid fingerprint (T4a-g)
- **Test first:** 7 sub-tests incl. T4g stale-script false-PASS regression (substring present, entrypoint absent → FAIL).
- **Impl:** Add `verify_hooks_active` with `RAW_FINGERPRINT` + `FRAMEWORK_FINGERPRINT` substring floor + `EXPECTED_ENTRYPOINTS` per-stage pattern dict.

### Slice 3.4 — `--apply` with transactional rollback (T5a-h)
- **Test first:** 8 sub-tests incl. T5g (rollback on subprocess fail) + T5h (rollback on verify-fail).
- **Impl:** Wrap `install_via_framework_apply` in `install_via_framework_apply_with_rollback`; snapshot to `.orchestra-backup`; restore on any failure; cleanup on success.

### Slice 3.5 — Framework branch integration in `cli.install_hooks` (T6a-d)
- **Test first:** 4 sub-tests: no framework → raw; framework + no flags → print-only; framework + `--apply` → auto-merge; framework + `--force-raw` → raw bypassing detection.
- **Impl:** Branch logic in `main()` based on `_is_precommit_framework` + flag combinations.

### Slice 3.6 — Hard-fail invariant (T7a-b)
- **Test first:** 2 sub-tests: verify-fail post-install → install_hooks exits non-zero; remediation message includes pre-commit install command.
- **Impl:** Ensure `--apply` propagates verify rc.

### Slice 3.7 — Template-ownership invariant (T8)
- **Test first:** both `precommit-yaml-patch.txt` (cli/templates/) and `precommit-framework-snippet.yaml` (skills/commit/templates/) exist with header ownership comments.
- **Impl:** Write header comments to both files documenting placement rule.

### Slice 3.8 — Integration test T-INT-010
- **Test first:** end-to-end tmpdir + framework + canon-frozen fixture + violation → commit rejected.
- **Impl:** Fixture file at `tests/fixtures/test-canon-frozen.md` + end-to-end test driver (uses real `pre-commit` binary in tmpdir).

**Phase 3 milestone:** all 27 LLD-010 tests green + baseline ≥240. BUG-006 `Status: Investigating → Fix Applied`. Commit: `feat: LLD-010 r3 framework detection + transactional apply + hybrid verify (BUG-006 closed). Refs: docs/features/010-framework-detection-determinism.md`.

## Phase 4: SCALE migration

### Slice 4.1 — Migration helper script
- **Impl:** Write `tools/migrate-scale-rules.py` (one-shot script) that performs migration steps. Run manually from SCALE repo root.

### Slice 4.2 — Run migration in SCALE repo
- Run `python3 ~/Documents/Antigravity/orchestra/tools/migrate-scale-rules.py` in SCALE.
- Verify state: 2 files absent + `documentation-gate.md` Gates 1-3 retained + Quick Reference Gates 1-3 + skill pointer + registry entry appended.
- Commit in SCALE repo: `chore: migrate canon-frozen-guard + commit-strategy to orchestra:commit skill (orchestra v1.7.0). Refs: orchestra/docs/features/008-commit-skill.md`.

## Phase 5: v1.7.0 release ship

### Slice 5.1 — Plugin version bump
- Update `manifest.json` or `plugin.json`: `version: 1.6.2 → 1.7.0`.
- Update README.md mentions of `/orchestra:commit`.

### Slice 5.2 — CHANGELOG.md v1.7.0 entry
- Combined entry covering LLD-008/009/010 portions + BUG-006 + BUG-010 Part 3 + BUG-011 closes.
- Pytest baseline: 150 → 240.

### Slice 5.3 — Flip Status: Draft → Implemented (3 LLDs)
- Whitelist edit on canon-frozen-eligible `Status` field for each LLD (currently Draft, no canon-frozen restriction).
- Append closing Changelog row per LLD with impl commit-sha.

### Slice 5.4 — Bump BUG status fields
- BUG-006: Investigating → Fix Applied (Changelog row with impl-commit).
- BUG-010 Part 3: append Changelog row to BUG-010 (canon-frozen; whitelist-eligible).
- BUG-011: Investigating → Fix Applied (Changelog row).

### Slice 5.5 — Final commit + tag
- Commit: `chore: bump orchestra to v1.7.0 (commit-skill consolidation). Refs: docs/plans/2026-05-11-v17-implementation.md`.
- Tag: `git tag -a v1.7.0 -m "orchestra v1.7.0 — commit-skill consolidation"`.

## Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| TDD slice depends on cross-LLD primitive (e.g., Slice 2.6 depends on Slice 1.2 SKILL_TEMPLATES_DIR) | High | Strict phase ordering; Phase 2/3 cannot start until Phase 1 milestone green |
| Test for symlink rejection (T8) hard to write portably | Medium | Use `os.symlink` in tmpdir; skip on Windows (we don't support Windows for orchestra) |
| Transactional rollback test (T5g/T5h) requires real `pre-commit` binary | Medium | Mock `subprocess.run` to return rc=1; verify backup-restore logic; supplement with integration test using real binary |
| ORCHESTRA_STRICT path requires staged-content scanning at commit-msg time | Medium | Implement as separate helper `_recompute_canon_inplace_candidates_from_index`; testable in isolation |
| Plateau heuristic risk: r5/r3/r3 are 5/3/3 iterations | Acknowledged | User explicit direction "ship without 4th review"; Minor findings deferred to v1.7.1 |

## Acceptance gate

v1.7.0 ships when ALL of:
- All 90 new tests green (15 + 48 + 27)
- Pytest baseline ≥240 confirmed
- 3 LLDs Status: Implemented
- BUG-006 + BUG-010 + BUG-011 Status: Fix Applied
- SCALE migration committed
- CHANGELOG.md v1.7.0 entry present
- Plugin version 1.7.0
- Tag v1.7.0 created

## v1.7.1 deferred items (per interview-gate direction)

Minor orchestra findings explicitly deferred:

- LLD-008: pseudocode `input_fn=input` clarification; prompt UX preservation note; T2 11-file enumeration assertion; A8 section-header cite (replace fragile line range); Skill-Status value-collision documentation.
- LLD-009: D1-D3 verifiability classification; mixed line-anchor vs function-anchor citations; 3a/3b sub-numbering convention note; pre-commit.sh canonical content inlined (currently referenced not inlined); A16 third-place CHANGELOG cite verification post-impl.

Track as `BUG-012-v17.1-minor-followups.md` post-ship.

## Related Documents

- `docs/features/008-commit-skill.md` — LLD-008 r5
- `docs/features/009-commit-msg-l2-finalize.md` — LLD-009 r3
- `docs/features/010-framework-detection-determinism.md` — LLD-010 r3
- `docs/reviews/008-commit-skill-r4.review.yaml` + `.codex.md` — r4 attestations (drove r5)
- `docs/reviews/009-commit-msg-l2-finalize-r2.review.yaml` + `.codex.md` — r2 attestations (drove r3)
- `docs/reviews/010-framework-detection-determinism-r2.review.yaml` + `.codex.md` — r2 attestations (drove r3)
- `docs/bugs/BUG-006-install-hooks-precommit-framework.md` — closes via Phase 3
- `docs/bugs/BUG-010-orchestra-self-install-precommit-hook.md` — Part 3 closes via Phase 1
- `docs/bugs/BUG-011-supersession-tier-refinement.md` — closes via Phase 2 (precursor reconciliation committed `0bd866d`)
- `docs/plans/2026-05-10-v17-followups-checklist.md` — § E0 commit-skill proposal entry point

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | Plan drafted per user direction "create a plan doc and execute to ship the whole skill". Covers 5 phases / 22 vertical slices / 90 new tests / target ≥240 pytest baseline. Status: Active. |
