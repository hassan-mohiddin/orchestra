# Implementation Plan: orchestra v1.7.0 — commit-skill consolidation (LLD-008 r7 + LLD-009 r6 + LLD-010 r4)

> **Doc ID:** 2026-05-11-v17-implementation
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Plan
> **Status:** Active (pre-impl; impl SHAs tracked per phase milestone post-merge — see § Impl-SHA tracking)
> **Iteration:** 4
> **Targets:** LLD-008 r7 + LLD-009 r6 + LLD-010 r4 (combined v1.7.0 ship)

## Goal

Ship `orchestra:commit` skill at v1.7.0 in a single atomic release covering:

- Skill structure + references migration + cli.install_hooks `--on-conflict` flag + cli.init bootstrap (LLD-008 r5)
- Commit-msg L2-finalize + tiered narrow-change rule (BUG-011 close) + `ORCHESTRA_STRICT` opt-in mode (LLD-009 r3)
- Pre-commit framework detection + `--apply` transactional rollback + `--verify` hybrid fingerprint (LLD-010 r3; BUG-006 close)
- SCALE-side migration (2 deletions + 1 partial-edit + 1 registry-append)

Pytest target: **≥252** (= 150 v1.6.2 baseline + 17 LLD-008 r7 + 53 LLD-009 r6 + 28 LLD-010 r4 + 4 Plan Phase 4 net-new). Cross-LLD audit-trail lineage: LLD-008 r7 A10 (150 → 167 = +17); LLD-009 r6 A16 (167 → 220 = +53; r5→r6 adds T2g+T2h transactional cleanup tests +0 net since prior T-counts absorbed); LLD-010 r4 A11 (220 → 248 = +28); Plan Phase 4 Slice 4.1 net-new beyond LLD-008 T6 (248 → 252 = +4 for transactional helper + multi-factor identity + symlink + atomic).

## Impl-SHA tracking (codex plan-r1 HIGH#2)

Plan filed pre-impl. Each phase milestone records its commit-SHA below post-merge to enable audit/verify of "plan claims vs reality."

| Phase | Milestone commit-SHA | Date | Test count after | Status |
|---|---|---|---|---|
| Phase 0 (test-quality audit) | TBD | TBD | 150 | pending |
| Phase 1 (LLD-008 r7 — skill structure + ORCHESTRA_INIT_STRICT + non-TTY fail-closed) | TBD | TBD | ≥167 | pending |
| Phase 2 (LLD-009 r6 — L2-finalize + tiered + ORCHESTRA_BYPASS multi-var CI-deny + transactional pending cleanup) | TBD | TBD | ≥220 | pending |
| Phase 3 (LLD-010 r4 — framework detection + repo-identity helper share) | TBD | TBD | ≥248 | pending |
| Phase 4 (SCALE migration — transactional + multi-factor repo-identity + symlink-safe) | TBD | TBD | ≥252 (Phase 4 +4 net beyond LLD-008 T6) | pending |
| Phase 5 (v1.7.0 ship) | TBD | TBD | ≥252 | pending |

Update this table after each phase's milestone-commit lands. Plan r2+ iterations sync this table for post-impl audit-trail.

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

Before slicing: skim `tests/test_install_hooks.py`, `tests/test_cli_install_hooks.py`, `tests/test_cli_init_*.py`, `tests/test_lint_*.py` for low-quality tests (asserts trivial; tests path that doesn't exercise behavior). Fix or note for cleanup post-ship. Time-box: 30min.

**Output contract (per orchestra plan-r1 Minor #1):** `docs/plans/2026-05-11-test-quality-audit.md`. Required sections:
- One-line summary per audited test file (file path + test count + KEEP/FIX-IN-PHASE-N/DEFER-TO-v1.7.1 disposition).
- Per-file findings list with low-quality category (trivial-assert / no-behavior-coverage / brittle-mock / etc.).
- Total time spent.

**Phase 1 gating relation:** Phase 1 does NOT gate on Phase 0 completion. Phase 0 may run parallel with Phase 1 Slice 1.1. Time-box 30min: drop unfinished after 30min, defer rest to v1.7.1 BUG.

## Phase 1: LLD-008 r7 (skill structure + bootstrap + ORCHESTRA_INIT_STRICT + non-TTY fail-closed; 17 tests)

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
  - **Fingerprint `# orchestra` in line 2 of both shell templates — required by LLD-010 r3 A4 `RAW_FINGERPRINT` substring floor; works with `EXPECTED_ENTRYPOINTS` hybrid pattern check** (orchestra plan-r1 evidence Minor #1).
- **Verify:** `pytest tests/test_install_hooks.py -v` → green; `python3 -m cli.install_hooks --commit-msg` writes commit-msg hook with `# orchestra` (case-insensitive substring) somewhere in file content.

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

### Slice 1.4 — cli.init bootstrap: TTY-aware fail-open/closed + ORCHESTRA_INIT_STRICT opt-in (T5a-g)
- **Test first:** 7 test functions in `tests/test_cli_init_bootstrap.py`:
  - `test_cli_init_bootstrap_installs_both_hooks` (no framework)
  - `test_cli_init_bootstrap_idempotent`
  - `test_cli_init_non_tty_no_input_blocking`
  - `test_cli_init_framework_present_no_apply_defers_to_print_only`
  - `test_cli_init_tty_bootstrap_non_zero_rc_emits_warning_fail_open` (TTY default)
  - `test_cli_init_orchestra_init_strict_propagates_non_zero_rc` (opt-in fail-closed regardless of TTY)
  - `test_cli_init_non_tty_bootstrap_non_zero_rc_fails_closed` (NEW per codex plan-r2 HIGH#1 — non-TTY default fail-closed)
- **Impl:**
  - Bootstrap call at end of `cli.init.main()`: `cli.install_hooks.main(["--all", "--on-conflict=skip"])`.
  - **TTY-aware default (per LLD-008 r7 A14 — codex plan-r2 HIGH#1 compromise):** capture rc; emit WARNING on non-zero. If `sys.stdin.isatty()` (interactive shell): `cli.init` returns 0 (fail-open WARNING — user sees, can react). If non-TTY (CI / script / piped): `cli.init` returns the non-zero rc (fail-closed — automation observes via exit code).
  - **`ORCHESTRA_INIT_STRICT=1` opt-in:** when env-var set + bootstrap rc != 0: `cli.init` propagates non-zero rc REGARDLESS of TTY (overrides TTY-aware default for users who want fail-closed even interactively). Mirrors LLD-009 ORCHESTRA_STRICT pattern.
- **Verify:** all 7 tests green.

### Slice 1.5 — SCALE migration test (T6)
- **Test first:** `tests/test_scale_migration.py::test_scale_migration_post_state` — in-tmpdir fixture replicating pre-migration SCALE `.claude/rules/`; runs migration helper; asserts post-state. Initially fails.
- **Impl:** Write `tests/fixtures/scale-pre-migration/` + `tests/scale_migration_helper.py` (encapsulates migration steps); assert files absent + documentation-gate.md retains Gates 1-3 + Quick Reference Gates 1-3 + skill pointer + registry append.
- **Verify:** test green.

### Slice 1.6 — Symlink rejection (T8)
- **Test first:** `tests/test_install_hooks_security.py::test_symlink_destination_rejected` — creates `.git/hooks/pre-commit` as symlink to `/tmp/xxx`; asserts `install_one_hook` raises `SecurityError`. Initially fails.
- **Impl:** Add `hook_path.is_symlink()` lstat check + parent-dir `.resolve()` containment verification before any write.
- **Verify:** test green.

### Slice 1.7 — Pytest baseline assertion (T7)
- **Test first:** `tests/test_pytest_baseline.py::test_baseline_at_least_167` — collects all tests; asserts count ≥167 (was 166 in plan r2; bumped to 167 in plan r3 for LLD-008 r7 T5g non-TTY fail-closed test). Passes deterministically after slices 1.1-1.6 land.
- **Impl:** N/A; sanity check only.
- **Verify:** `pytest --collect-only -q | wc -l` ≥167.

**Phase 1 milestone:** all 17 LLD-008 r7 tests green + baseline ≥167. Bump SKILL.md `version: 1.7.0-pre`. Commit: `feat: LLD-008 r7 skill structure + bootstrap + TTY-aware fail-closed + ORCHESTRA_INIT_STRICT opt-in (BUG-010 Part 3 closed). Refs: docs/features/008-commit-skill.md`.

## Phase 2: LLD-009 r6 (L2-finalize + tiered + ORCHESTRA_STRICT + ORCHESTRA_BYPASS multi-var CI-deny + transactional pending cleanup; 53 tests)

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

### Slice 2.6 — `lint_commit_msg_finalize` entrypoint + ORCHESTRA_BYPASS multi-var CI-deny + Bypass: mandatory + transactional pending cleanup (T2a-h, T10a-g, T11)
- **Test first:** 8 + 7 + 1 = 16 sub-tests (added T2g + T2h r4 per codex plan-r3 HIGH#1 transactional cleanup).
- **Impl:** New CLI subcommand `cli.lint --commit-msg-finalize <msg-file>`. Reads pending, msg, runs tiered rule per pending entry.
  - **Transactional pending cleanup (r4; per codex plan-r3 HIGH#1):** cleanup pending file ONLY after L2-finalize validation completes successfully (rc=0 return). If validation raises exception OR rejects (rc=1): pending file PRESERVED for retry. Retried commit re-runs pre-commit hook (which truncates pending fresh anyway) OR if invoked with --no-verify on retry: pending entries from prior fire remain → L2-finalize re-validates on next commit-msg fire. Eliminates lost-state window where mid-validation crash skipped enforcement on retried commit. Implementation: replace `finally: unlink(missing_ok=True)` with success-only cleanup at end of normal return path; exception/reject paths leave pending in place.
  - Per LLD-009 r6 A2 update + new T2g (crash-during-validation: inject exception → pending preserved → retry sees pending → L2-finalize re-runs successfully) + T2h (reject-then-retry-with-fix: rc=1 leaves pending; retry with valid msg cleans up successfully).
  - **ORCHESTRA_BYPASS handling (per LLD-009 r5 A10 + codex plan-r2 HIGH#2 + user direction):**
    - **Multi-var CI detection** via helper `_is_ci_environment()`: returns True if ANY of these env vars non-empty: `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `BUILDKITE`, `CIRCLECI`, `TRAVIS`, `JENKINS_URL`. Closes codex plan-r2 HIGH#2 brittle-CI-detection gap.
    - When `ORCHESTRA_BYPASS=1` AND `_is_ci_environment()` returns True: REJECT bypass with explicit error `error: ORCHESTRA_BYPASS=1 cannot be used in CI environment (detected via: <list-of-set-vars>). Fix the underlying issue or run locally.`. Exit non-zero.
    - When `ORCHESTRA_BYPASS=1` AND non-CI (local dev): REQUIRE `Bypass: <reason>` line in commit message body. If absent: REJECT. Exit non-zero. Audit log entry written.
    - When `ORCHESTRA_BYPASS=1` + non-CI + valid `Bypass:` annotation: skip-and-log.
  - Fail-closed when no msg-file arg.
- **Verify:** 14 sub-tests green incl. T10e (CI-deny via `CI` var) + T10f (Bypass: missing → fail) + **T10g (CI-deny via provider-specific var without `CI`: e.g., `GITHUB_ACTIONS=true` alone → reject — codex plan-r2 HIGH#2 regression test)**.

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

**Phase 2 milestone:** all 53 LLD-009 r6 tests green + baseline ≥220. BUG-011 frontmatter `Status: Investigating → Fix Applied` via whitelist edit. Commit: `feat: LLD-009 r6 L2-detect/L2-finalize + tiered narrow-change + ORCHESTRA_BYPASS multi-var CI-deny + transactional pending cleanup (BUG-011 closed). Refs: docs/features/009-commit-msg-l2-finalize.md`.

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

**Phase 3 milestone:** all 28 LLD-010 r4 tests green + baseline ≥248 (LLD-010 portion; Plan Phase 4 adds further 4 net = 252 final). BUG-006 `Status: Investigating → Fix Applied`. Commit: `feat: LLD-010 r4 framework detection + transactional apply + hybrid verify (BUG-006 closed). Refs: docs/features/010-framework-detection-determinism.md`.

## Phase 4: SCALE migration (transactional per codex plan-r1 CRITICAL)

### Slice 4.1 — Transactional + repo-identity + symlink-safe migration helper (closes codex plan-r1 CRITICAL + codex plan-r2 MEDIUM)
- **Test first:** `tests/test_scale_migration_transactional.py` — 7 test functions covering:
  - `test_migration_dry_run_changes_nothing` — `--dry-run` flag prints planned ops; modifies nothing on disk
  - `test_migration_pre_check_invariants` — refuses to start if SCALE state doesn't match pre-migration expectations
  - `test_migration_idempotent_rerun` — rerun on already-migrated state: detects + exits 0 with `already-migrated` message; modifies nothing
  - `test_migration_rollback_on_mid_run_failure` — inject failure between deletion + registry-append; assert all changes reverted from snapshot; SCALE state restored byte-for-byte
  - `test_migration_post_check_invariants` — after successful migration: assert 2 files absent + documentation-gate.md correct + registry has orchestra:commit row
  - `test_migration_rejects_wrong_git_toplevel` (NEW codex plan-r3 HIGH#2) — pass `--scale-root` pointing to subdir of a git repo → git rev-parse mismatch → refuse; no mutation
  - `test_migration_rejects_bad_remote` (NEW codex plan-r3 HIGH#2) — pass `--expected-remote` mismatching actual `remote.origin.url` → refuse; no mutation
  - `test_migration_rejects_missing_claude_md_sentinel` (NEW) — CLAUDE.md absent or missing SCALE marker → refuse; no mutation
  - `test_migration_rejects_missing_apps_web_sentinel` (NEW) — apps/web/package.json absent or missing scale name → refuse; no mutation
  - `test_migration_rejects_symlinked_targets` (codex plan-r2 MEDIUM) — create any of the touched paths as a symlink → refuse; no mutation
- **Impl:** `tools/migrate-scale-rules.py` with:
  - **`--dry-run` flag:** print planned ops; modify nothing.
  - **`--scale-root` arg:** explicit SCALE repo path (no implicit cwd or path traversal).
  - **NEW: Multi-factor repo-identity verification (codex plan-r2 MEDIUM + plan-r3 HIGH#2 strengthening):** before any mutation, ALL of the following must pass; ANY failure → refuse with explicit error listing the failed check:
    - **(a) Git toplevel match:** `git rev-parse --show-toplevel` (run with cwd=`<scale-root>`) must resolve to the same path as `Path(scale_root).resolve()`. Rejects accidental sub-directory targeting.
    - **(b) Expected remote match:** `git config --get remote.origin.url` must match `--expected-remote` arg (required; no default — user MUST pass it). Rejects wrong-repo-with-similar-structure forgery.
    - **(c) SCALE CLAUDE.md sentinel:** `<scale-root>/.claude/CLAUDE.md` exists AND contains `SCALE — Claude Code` in first 100 lines.
    - **(d) Second sentinel:** `<scale-root>/apps/web/package.json` exists AND contains `"name": "scale"` (or substring `scale`).
    - Rejects accidental wrong-root execution (typo, copy-paste, partial-replicate-of-SCALE-tree).
  - Tests T-migration-rejects-wrong-toplevel (cwd is subdir) + T-migration-rejects-bad-remote (git remote mismatch) + T-migration-rejects-missing-sentinel-a + T-migration-rejects-missing-sentinel-b → 4 new tests covering each of the 4 factors fail-closed-individually.
  - **NEW: Symlink-safe path mutation (codex plan-r2 MEDIUM):** for EVERY path the helper touches (read/write/delete/copy/restore): perform `path.lstat()` + `path.is_symlink()` check. If symlink: refuse with `error: refusing to mutate symlinked path: <path> -> <readlink>`. Applies to all 4 source files + .scale-migration-backup dir creation + parent-dir traversal. Mirrors LLD-008 r6 Security § symlink defense extended to migration script.
  - **Pre-flight invariant checks:** assert all 3 source files present at expected paths + frontmatter check on documentation-gate.md + skills-registry.md exists + ALL paths pass symlink check. Refuse to start otherwise.
  - **Pre-flight snapshot:** copy `SCALE/.claude/rules/{canon-frozen-guard.md,commit-strategy.md,documentation-gate.md}` + `SCALE/.claude/skills-registry.md` → `SCALE/.scale-migration-backup/<timestamp>/`. If backup dir exists with same timestamp: refuse.
  - **Idempotent rerun:** if 2 deletion-target files absent + registry contains orchestra:commit row + documentation-gate.md contains skill pointer: exit 0 `already-migrated`; do nothing.
  - **Atomic-where-possible execution:** sequence: rewrite documentation-gate.md (via `tempfile.NamedTemporaryFile` + `os.replace`) → append registry (via same pattern) → delete canon-frozen-guard.md → delete commit-strategy.md. If ANY step raises: restore all 4 files from snapshot via `shutil.copy` reverse; exit non-zero with rollback notice.
  - **Post-flight invariant checks:** all 4 post-state assertions; on failure: rollback from snapshot.
  - **Cleanup:** on success leave `.scale-migration-backup/<timestamp>/` for 1 week (user manual cleanup) — gives recovery window if SCALE-side problem surfaces post-migration.

### Slice 4.2 — Run migration in SCALE repo (dry-run first)
- **Run dry-run first:** `python3 ~/Documents/Antigravity/orchestra/tools/migrate-scale-rules.py --scale-root ~/Documents/Antigravity/SCALE\ APP --expected-remote <SCALE-repo-url> --dry-run`. Inspect planned ops.
- **Run real:** drop `--dry-run`. Migration helper executes transactional sequence with all 4 identity checks + symlink-safe + atomic.
- **Verify state:** post-flight invariants from Slice 4.1 (already enforced); manual `git status` + `git diff` confirms.
- **Commit in SCALE repo:** `chore: migrate canon-frozen-guard + commit-strategy to orchestra:commit skill (orchestra v1.7.0). Refs: orchestra/docs/features/008-commit-skill.md`.

## Phase 5: v1.7.0 release ship

### Slice 5.1 — Plugin version bump
- Update `manifest.json` or `plugin.json`: `version: 1.6.2 → 1.7.0`.
- Update README.md mentions of `/orchestra:commit`.

### Slice 5.2 — CHANGELOG.md v1.7.0 entry
- Combined entry covering LLD-008/009/010 portions + BUG-006 + BUG-010 Part 3 + BUG-011 closes.
- Pytest baseline: 150 → 252.

### Slice 5.3 — Flip Status: Draft → Implemented (3 LLDs)
- Each LLD currently `Status: Draft` (full edit permitted on Draft per LLD-006-r4). Flip to `Implemented` — this is the transition INTO canon-frozen state. After flip: subsequent body edits subject to narrow-change rule (whitelist or tiered).
- Append closing Changelog row per LLD with impl commit-sha — append-only Changelog is whitelist-eligible post-flip; safe to do in same commit as Status flip (or immediately after).

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
| TDD slice depends on cross-LLD primitive (e.g., Slice 2.6 depends on Slice 1.2 SKILL_TEMPLATES_DIR) | High | Phase ordering: Phase 1 must complete first (LLD-008 provides SKILL_TEMPLATES_DIR + skill dir + hook templates). **Phase 2 and Phase 3 can run in parallel after Phase 1** (Phase 3 LLD-010 only consumes SKILL_TEMPLATES_DIR + framework-snippet; does NOT depend on Phase 2 LLD-009 L2-finalize). Plan executes sequentially by default for simplicity but parallelization permitted if useful. Phase 4 + 5 must follow Phases 2 + 3 |
| Test for symlink rejection (T8) hard to write portably | Medium | Use `os.symlink` in tmpdir; skip on Windows (we don't support Windows for orchestra) |
| Transactional rollback test (T5g/T5h) requires real `pre-commit` binary | Medium | Mock `subprocess.run` to return rc=1; verify backup-restore logic; supplement with integration test using real binary |
| ORCHESTRA_STRICT path requires staged-content scanning at commit-msg time | Medium | Implement as separate helper `_recompute_canon_inplace_candidates_from_index`; testable in isolation |
| Plateau heuristic risk: r5/r3/r3 are 5/3/3 iterations | Acknowledged | User explicit direction "ship without 4th review"; Minor findings deferred to v1.7.1 |

## Acceptance gate

v1.7.0 ships when ALL of:
- All 102 new tests green (17 LLD-008 + 53 LLD-009 + 28 LLD-010 + 4 Phase 4 net-new beyond LLD-008 T6)
- Pytest baseline ≥252 confirmed
- 3 LLDs Status: Implemented (LLD-008 r7 + LLD-009 r5 + LLD-010 r4)
- BUG-006 Status: Investigating → Fix Applied (state flip)
- BUG-010 Part 3: Changelog row appended (BUG-010 already canon-frozen Fix Applied; whitelist append only — NOT a Status flip)
- BUG-011 Status: Investigating → Fix Applied (state flip)
- SCALE migration committed (transactional helper + post-flight invariants verified)
- CHANGELOG.md v1.7.0 entry present (orchestra repo)
- Plugin version 1.7.0
- Tag v1.7.0 created

## v1.7.1 deferred items (per interview-gate direction)

Minor orchestra findings explicitly deferred:

- LLD-008: pseudocode `input_fn=input` clarification; prompt UX preservation note; T2 11-file enumeration assertion; A8 section-header cite (replace fragile line range); Skill-Status value-collision documentation.
- LLD-009: D1-D3 verifiability classification; mixed line-anchor vs function-anchor citations; 3a/3b sub-numbering convention note; pre-commit.sh canonical content inlined (currently referenced not inlined); A16 third-place CHANGELOG cite verification post-impl.

Track as `BUG-012-v17.1-minor-followups.md` post-ship.

## Related Documents

- `docs/features/008-commit-skill.md` — LLD-008 r7
- `docs/features/009-commit-msg-l2-finalize.md` — LLD-009 r6
- `docs/features/010-framework-detection-determinism.md` — LLD-010 r4
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
| 2026-05-11 | r1 drafted per user direction. Covers 5 phases / 33 slices / 90 new tests / target ≥240 pytest baseline. Status: Active. Filed without spec-review (Gate 3 violation — caught + fixed in r2). |
| 2026-05-11 | r3 spec-review verdicts: orchestra conditional_pass (3 Minor paperwork: doc title r5/r3/r3 stale; Phase 3 header LLD-010 r3 stale; Slice 5.2 baseline 240 stale + Related Documents iter tags); codex needs-attention (2 HIGH + 1 MEDIUM convergent with orchestra Minor #1 on Slice 5.2 baseline). r3 → r4 per user-delegated decisions (all Recommended): (1) codex HIGH#1 transactional pending cleanup — Slice 2.6 + LLD-009 r5→r6 A2 update: cleanup pending ONLY after L2-finalize rc=0; exception/reject paths preserve pending for retry-safety. New T2g (crash-during-validation) + T2h (reject-then-retry). (2) codex HIGH#2 multi-factor repo-identity — Slice 4.1 upgraded from single CLAUDE.md sentinel to 4-factor verification: (a) git rev-parse --show-toplevel match `--scale-root`, (b) `--expected-remote` arg required + matches `git config --get remote.origin.url`, (c) CLAUDE.md SCALE sentinel, (d) apps/web/package.json scale-name marker. 4 new tests (one per factor fail-closed). (3) codex MEDIUM + orchestra Minor #1 + #2 + #3 (paperwork stale-text) — fixed: doc title r7/r6/r4; Phase 3 header LLD-010 r4 / 28 tests; Slice 5.2 baseline 150→252; Related Documents iter tags r7/r6/r4. Combined v1.7.0 target 248 → 252 (Plan Phase 4 +4 net beyond LLD-008 T6 placeholder). Status: Active iter 4. **NO further spec-review per user direction "no more spec reviews, we can proceed to fix and then prepare for compaction"**. |
| 2026-05-11 | r2 spec-review verdicts: orchestra PASS (2 Minor paperwork: LLD-010 A11 stale 240→243; LLD-008 A10 prose stale 15/165→16/166); codex needs-attention (2 HIGH + 1 MEDIUM — fresh substantive surface, zero orchestra↔codex overlap; codex r1↔r2 OVERLAP on cli.init fail-open — plateau signal). r2 → r3 per user-delegated decisions (Hassan deferred to my technical judgment on all 4 questions): (1) codex HIGH#1 fail-open compromise — Slice 1.4 + LLD-008 r7 A14 now TTY-aware: interactive → fail-open WARNING; non-TTY → fail-closed (returns non-zero rc). ORCHESTRA_INIT_STRICT=1 opt-in overrides TTY-aware default for fail-closed always. New T5g test. (2) codex HIGH#2 CI detection refinement — Slice 2.6 + LLD-009 r5 A10 multi-var detection via `_is_ci_environment()` helper checking ANY of {CI, GITHUB_ACTIONS, GITLAB_CI, BUILDKITE, CIRCLECI, TRAVIS, JENKINS_URL}. New T10g regression test. (3) codex MEDIUM SCALE migration safety — Slice 4.1 + 2 new tests: repo-identity sentinel check (`<scale-root>/.claude/CLAUDE.md` contains `SCALE — Claude Code`); symlink-safe mutation via `path.is_symlink()` lstat check on every touched path; atomic-replace via `tempfile.NamedTemporaryFile` + `os.replace` for rewrites. (4) orchestra paperwork — LLD-010 r3→r4 bump (A11 baseline 240→248 cascade); LLD-008 r6 A10 prose stale 15→17 / 165→167. Combined v1.7.0 pytest target: 243 → 248 (= 150 + 17 + 53 + 28). Test count delta: +1 LLD-008 (T5g) + +3 LLD-009 (T10g + 2 symlink helpers shared with migration) + +1 LLD-010 (T-INT-010 repo-identity check). Status: Active iter 3. Re-spec-review of r3 pending per user direction. |
| 2026-05-11 | r1 spec-review verdicts: orchestra conditional_pass (7 Minor); codex needs-attention (1 CRITICAL + 3 HIGH — fresh substantive surface, zero cross-judge overlap). r1 → r2 fixes inline per user interview-gate direction: Phase 4 SCALE migration redesigned as transactional helper with snapshot/dry-run/idempotent/pre-+post-invariants/rollback + 5 tests (codex CRITICAL); impl-SHA tracking table added at top (codex HIGH#2); Slice 1.4 cli.init bootstrap adds ORCHESTRA_INIT_STRICT=1 opt-in mirror-of-LLD-009-pattern (codex HIGH#3 partial — user picked Recommended); Slice 2.6 ORCHESTRA_BYPASS gains CI-deny + mandatory Bypass: annotation (codex HIGH#4 — user picked Recommended); Phase 0 output contract specified (orchestra Minor #1); Slice 1.7 deterministic wording (orchestra Minor #2); Slice 1.2 LLD-010 A4 cross-cite added (orchestra Minor #3); Acceptance gate BUG-006/010/011 distinguished (orchestra Minor #4); Slice count enumeration honest (33 not 22; orchestra Minor #5); Risks table Phase 2/3 parallel-eligible noted (orchestra Minor #6); Slice 5.3 Draft→Implemented framing fixed + baseline lineage surfaced (orchestra Minor #7). LLD-008 r5 → r6 (add A14 ORCHESTRA_INIT_STRICT + T5f); LLD-009 r3 → r4 (A10 ORCHESTRA_BYPASS CI-deny + mandatory Bypass: + T10e + T10f). Test counts updated (+1 LLD-008 / +2 LLD-009 / 0 LLD-010 = +3); pytest target 240 → 243. Status: Active iter 2. Re-spec-review of r2 dispatched per user direction "re-run spec review on plan doc to see if all issues were fixed or any overlapping errors, if new issues weren't created etc." |
