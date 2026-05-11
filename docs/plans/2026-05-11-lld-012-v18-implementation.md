# Implementation Plan — Rule Durability & Learning Layer (LLD-012)

> **Doc ID:** 2026-05-11-lld-012-v18-implementation
> **Date:** 2026-05-11
> **Status:** Draft
> **DRI:** Hassan
> **Iteration:** 2
> **LLD:** `docs/features/012-rule-durability-and-learning-layer.md` (Iteration 3, Status Draft, ship target v2.1.0)
> **Type:** Implementation Plan
> **Rebased against:** HEAD `a35a0f7` (post-LLD-011 v2.0.0 + BUG-012 r5 + BUG-001 Path C wip — `cli/spec_review.py` includes PDSA gate + `--aggregate-and-write` v2 dispatch + v1.0-attestation frozen-historical refuse)

---

## Header

**Goal**: Implement the durability layer (TLDR compression + hooks + compaction probe) and the learning layer (lessons skill + auto-promote pipeline via proxy artifact) defined in LLD-012, and ship as orchestra v2.1.0.

**Architecture** (from LLD-012 — this plan does not re-state design decisions):
- TLDR section format injected into 5 schema-layer files (`.claude/CLAUDE.md` + 4 rules)
- Three Claude Code hooks: SessionStart, PreCompact, UserPromptSubmit (turn-counter every Nth turn, N=5 default)
- Portable interpreter resolution via `sys.executable` at install time; fail-loud at runtime
- `cli.install_claude_hooks` writes/verifies/uninstalls `.claude/settings.json`
- `cli.hooks` package with three handler modules emitting `hookSpecificOutput.additionalContext` wrapped in `<system-reminder>` blocks
- Lessons stored at `docs/lessons/<YYYY-MM>-lessons.md` (append-only YAML entries)
- Two-tier capture (`/orchestra:teach` free-text, `/orchestra:violation` structured), single-tier injection (structured violations only)
- Recurrence detection (≥3× per `rule_violated`) emits proxy artifact to `docs/proposed-rule-mutations/<rule>-<date>.md`
- User-driven spec-review on proxy; `cli.lessons_apply` mutates schema-layer target only after passed attestation
- `source: auto-promote` marker closes recursion guard
- `cli.compaction_probe` CI gate (calls Anthropic `count_tokens` + `compact_20260112`)
- Schema-v1 attestation overwrite fail-closed on malformed existing file (codex finding #4)
- `.claude/state/` runtime-only directory (gitignored)

**Tech stack**: Python 3.12 (`.venv/bin/python3.12`); pytest; pyrefly; `cli.lint` for self-dogfood lint; `cli.eval` for scenario suite. Anthropic Python SDK (`anthropic`) for `count_tokens` + `compact_20260112` (compaction probe + token budget enforcement) — **NEW dependency in v2.1**: added to `pyproject.toml [project.dependencies]` in slice 1.0 (foundation phase). Hook runtime + compaction probe both require `ANTHROPIC_API_KEY` env var; missing-key fallbacks defined per slice (3.2 hook fallback to identity-only index; 6.6 probe exits 2 with CI-must-fail semantics).

**Iteration discipline**: TDD vertical slicing per `.claude/workflow.md § Step 4`. One failing test → one implementation → green → commit. NOT all-tests-then-all-impl. Horizontal slicing forbidden.

**LLD vs Plan boundary**: this plan describes HOW + IN WHAT ORDER. It MUST NOT introduce design decisions not in LLD-012. If a slice requires a design decision not in LLD-012 → STOP, file an LLD update (likely supersede via `-r3`) or interview Hassan; do NOT silently decide in the plan.

**LLD-011 Phase 2 state**: SHIPPED. plugin.json + marketplace.json at v2.0.0. `cli/spec_review.py` at HEAD `a35a0f7` already runs PDSA via `run_pdsa`, supports `--aggregate-and-write` v2 dispatch, and enforces v1.0-attestation frozen-historical refuse (`v1.0_attestation_frozen` branch at lines 718-728; bare-existence refuse at lines 730-735; PDSA gate at lines 737+). v2.1 ships on TOP of v2 spec-review surface. `cli.lessons_apply` reads attestation YAML by path, schema-version-agnostic — it ingests v2.0 attestations (`*.orchestra.review.yaml` per v2 file-naming) for the proxy artifact lookup, with read-only support for v1.0 historical attestations. (Line numbers verified against `cli/spec_review.py` at HEAD `a35a0f7`; will drift as parallel sessions land patches — implementer re-greps at edit time.)

---

## File Structure

### Files created (new in v2.1)

| Path | Purpose |
|---|---|
| `cli/install_claude_hooks.py` | Install/verify/uninstall `.claude/settings.json` hook entries; resolve `sys.executable` |
| `cli/compaction_probe.py` | CI gate asserting TLDR keywords survive Anthropic `compact_20260112` |
| `cli/lessons_lint.py` | Scan recurring lessons + write proxy artifacts to `docs/proposed-rule-mutations/` |
| `cli/lessons_apply.py` | User-invoked mutation step; iteration-aware attestation lookup + auto-promote marker write |
| `cli/lessons_store.py` | Append-only lesson entry writer + reader (shared helper for skill + lint) |
| `cli/tldr_extractor.py` | Pure-parsing TLDR section extractor (regex, no I/O) + 4 failure modes |
| `cli/hooks/__init__.py` | New package marker |
| `cli/hooks/session_start_inject.py` | SessionStart hook handler |
| `cli/hooks/pre_compact_instruct.py` | PreCompact hook handler |
| `cli/hooks/user_prompt_reinject.py` | UserPromptSubmit hook handler (turn-counter + Nth-turn injection) |
| `skills/lessons/SKILL.md` | Lessons skill frontmatter + body |
| `commands/teach.md` | Slash-command shim for `/orchestra:teach` |
| `commands/violation.md` | Slash-command shim for `/orchestra:violation` |
| `commands/lessons-lint.md` | Slash-command shim for `/orchestra:lessons-lint` |
| `tests/test_tldr_extractor.py` | TLDR regex + 4 failure modes |
| `tests/test_lessons_store.py` | Cross-phase: (Phase 1) append + read; YAML shape; HTML-encode + 200-char cap. (Phase 5) slash-command shim integration tests for `/orchestra:teach` and `/orchestra:violation` (rule-id allowlist, kind/inject enforcement, path-traversal block). File created in Phase 1; Phase 5 appends test cases. |
| `tests/test_install_claude_hooks.py` | Install + uninstall + verify; merge preserves non-orchestra hooks |
| `tests/test_install_claude_hooks_fail_loud.py` | Mock missing interpreter → non-zero exit + stderr (codex #3 regression) |
| `tests/test_session_start_inject.py` | TLDR + structured-violations emission; `<system-reminder>` wrap; token budget fallback |
| `tests/test_pre_compact_instruct.py` | compact_instructions text preserves TLDR verbatim |
| `tests/test_user_prompt_reinject.py` | Turn-counter increments; Nth-turn fires; non-Nth silent (SC-14) |
| `tests/test_lesson_injection_allowlist.py` | No free-text `teach` in injection output; only allowlisted structured fields (codex #2 regression) |
| `tests/test_lessons_lint.py` | ≥3× recurrence; skip `source: auto-promote`; proxy artifact written; no auto-spec-review |
| `tests/test_lessons_apply.py` | Iteration-aware attestation lookup; refuse without pass; mutate target + append auto-promote marker |
| `tests/test_compaction_probe.py` | Keyword extraction + assertion logic (Anthropic API mocked) |
| `tests/test_schema_v1_overwrite_failclosed.py` | Malformed v1 attestation → force-mode refusal + no mutation (codex #4 regression) |
| `tests/integration/__init__.py` | New package marker |
| `tests/integration/test_hook_emission.py` | Subprocess hook invocation; JSON shape + `<system-reminder>` wrap |
| `tests/integration/test_end_to_end_violation.py` | Install → violation × 3 → lint → mock review pass → apply mutation |
| `tests/test_state_dir_gitignore.py` | Assert `.claude/state/` listed in `.gitignore` (Slice 1.7 TDD anchor) |
| `tests/test_anthropic_import.py` | Assert `import anthropic` succeeds (Slice 1.0 dependency verification) |
| `docs/lessons/.gitkeep` | Directory placeholder; first real lessons file created on first `/orchestra:teach` or `/orchestra:violation` |
| `docs/proposed-rule-mutations/.gitkeep` | Directory placeholder; entries created by `cli.lessons_lint` |

### Files modified (existing files updated)

| Path | Change |
|---|---|
| `.claude/CLAUDE.md` | Add `## TLDR — Nonnegotiables` section + `## Rule Compression Convention` subsection (SC-13) |
| `.claude/rules/documentation-gate.md` | Add `## TLDR — Nonnegotiables` section |
| `.claude/rules/interview-gate.md` | Add `## TLDR — Nonnegotiables` section |
| `.claude/rules/skills-routing.md` | Add `## TLDR — Nonnegotiables` section |
| `.claude/rules/task-tracking.md` | Add `## TLDR — Nonnegotiables` section |
| `.gitignore` | Add `.claude/state/` entry |
| `cli/spec_review.py` | Force-mode overwrite path → fail-closed on malformed existing attestation (codex #4 fix) |
| `.claude-plugin/plugin.json` | Bump version `2.0.0` → `2.1.0` (minor; new feature additions: hooks + lessons skill, non-breaking) |
| `.claude-plugin/marketplace.json` | Bump `plugins[0].version` `2.0.0` → `2.1.0` (matches plugin.json after LLD-011 self-application brought both to 2.0.0) |
| `docs/design/orchestra-philosophy-r2.md` | Changelog entry citing Karpathy K1/K2/K3/K4/K8 lineage (SC-13) |
| `docs/HANDOFF.md` | Update with v2.1.0 ship state on completion |

### Files NOT touched (out of scope confirmation)

- `cli/spec_review.py` canonical-scope logic (`canonicalize_doc_path` at `../../cli/spec_review.py:416-434`) — kept unchanged per LLD-012 proxy-artifact route. (Note: citation uses `../../` prefix as a workaround for a PDSA path-resolution bug — see pending BUG-NEW for PDSA citation path resolution; PDSA resolves citations relative to doc dir instead of repo root. Line range verified at HEAD `a35a0f7`; re-grep if HEAD moves.)
- `.claude/workflow.md` + `.claude/skills-registry.md` TLDR compression — deferred to LLD-013 (v2.0 workflow skill). **Boundary-fence rule:** Phase 2 slices 2.1–2.5 enumerate the 5 schema-layer files in scope (`.claude/CLAUDE.md` + 4 rules). If a Phase 2 slice attempts to also edit `workflow.md` or `skills-registry.md`, STOP — that is silent scope-creep and out of LLD-012's Iteration-2 in-scope list. Surface for LLD-013.
- `cli/install_hooks.py` (git hooks — pre-commit / commit-msg) — `install_claude_hooks.py` is a NEW separate module; do not merge with git-hook installer
- LLD-011 Phase 2 files (`cli/pdsa.py`, `cli/aggregator.py`, `cli/delta_review.py`, schema v2.0) — separate parallel session
- Anthropic Memory tool integration — confirmed out-of-scope per LLD-012 §Out of Scope
- Skill SKILL.md compression for existing orchestra skills — deferred per LLD-012 §Out of Scope (LLD does not enumerate which skills; plan defers all)

**Six adversarial Criticals (deferred to v2.2/v2.3 hardening pass per plan r2 v2 attestation `docs/reviews/2026-05-11-lld-012-v18-implementation-r2.orchestra.review.yaml`):**

1. **SessionStart hook API hang risk** — `count_tokens` API call has no timeout; 30s hang = 30s startup delay per session. Mitigation in v2.1 implementation: add HTTP timeout (e.g., 2s) to all hook-runtime Anthropic SDK calls. **Full hardening** (LLD-014+): local tokenizer fallback so hook never blocks on network.
2. **turn-counter concurrent-session race** — two Claude Code windows on same repo race on counter file. Mitigation in v2.1 implementation: best-effort `fcntl.flock` advisory lock + atomic-write; document known-limitation under heavy concurrency. **Full hardening** (LLD-014+): per-session counter or move to claude-code-native counter API if exposed.
3. **sys.executable stale-after-venv-rebuild silent** — captured path stale once user reinstalls venv; `--verify` is CI-only. Mitigation in v2.1: implementation slice 4.1 documents this; user runbook entry. **Full hardening** (LLD-014+): runtime self-check at SessionStart that auto-emits warning when interpreter path unresolvable.
4. **lessons_apply vs user-open editor** — programmatic mutation of CLAUDE.md / .claude/rules/*.md races with editor unsaved changes. Mitigation in v2.1 implementation: add `git status --porcelain` precondition (refuse if target dirty in working tree) + atomic-write. **Full hardening** (LLD-014+): advisory file-lock + editor-process detection.
5. **rule-id allowlist symlink/file-add attack** — basename-derived allowlist trusts filesystem state. Mitigation in v2.1: implementation slice 5.3 adds symlink rejection (`Path.is_symlink()` check); only `.claude/rules/*.md` regular files admitted. **Full hardening** (LLD-014+): allowlist sourced from committed-and-signed manifest.
6. **rule_violated field content not sanitized for `</system-reminder>` escape** — only observed/expected HTML-encoded; rule_violated string interpolated verbatim. Mitigation in v2.1: implementation slice 3.3 extends HTML-encoding to rule_violated field as well (low-cost extension). **Full hardening** (LLD-016): semantic sanitization across all injected fields (per LLD-012 Out-of-Scope item #5).

The "Mitigation in v2.1 implementation" entries above are NOT new slices in this plan — they are caveats/clarifications to be applied within the existing slices when the implementer hits the relevant code path. Each is a 1-2 line addition (timeout, advisory lock, dirty-check, symlink check, HTML-encode extension) within the existing slice scope, not a new phase or slice.

---

## Open questions to resolve before / during implementation

These are flagged as plan-time questions, not silent decisions. If a slice hits one of these without an answer, STOP and interview Hassan.

| ID | Question | Where it bites | Default if no answer |
|---|---|---|---|
| Q1 | Does Claude Code's UserPromptSubmit hook accept the `hooks` array without a `matcher` field (per LLD-012 §Hook architecture)? | Slice 4.3 install + slice 3.6 handler smoke test | Add `matcher: ".*"` explicitly; interview if Claude Code rejects |
| Q2 | Is `claude --print-current-model` an available CLI surface (referenced by LLD-012 §Hook architecture for token-budget tokenizer)? No Claude Code docs URL verified — LLD-012 asserts without citation. | Slice 3.2 token budget enforcement | Fallback to hardcoded `claude-opus-4-7` per LLD-012 fallback text. **Risk:** if CLI does not exist, fallback is the only path — accept slight model/tokenizer mismatch for budget accounting purposes. |
| Q3 | Does Anthropic API expose `compact_20260112` programmatically, or is it surfaced only via Claude Code's `/compact` slash? | Slice 6.2 compaction probe | If not programmatic: probe degrades to keyword-survival assertion against a deterministic SDK summarization endpoint; interview before deciding |
| Q4 | Slash-command shim format — `commands/<name>.md` with frontmatter (per `commands/spec-review.md`) or skill-frontmatter `commands:` list? | Slices 5.1–5.3 | **RESOLVED via LLD-012 iter-3:** `commands/<name>.md` shim per existing repo pattern. LLD-012 SC-6 r3 rewritten to align (frontmatter `commands:` list dropped). No remaining ambiguity. |
| Q5 | Does `cli.lessons_apply` rewrite the proxy doc's Status (Approved → Implemented) after mutation, or leave it untouched? | Slice 6.4 | Leave untouched in v2.1; surface for LLD-013 lifecycle policy |
| Q6 | UserPromptSubmit hook turn-counter — atomic write needed for concurrent-session safety? | Slice 3.5 | Use `tempfile.NamedTemporaryFile` + `os.replace` atomic-write pattern (already canonical in `cli/spec_review.py`) |

---

## Implementation phases

Phases are **strictly sequential** at the phase boundary (Phase N+1 starts only when Phase N is committed + green). Within a phase, slices are sequential unless explicitly marked parallel-safe.

### Phase 1 — Foundation modules (pure, no I/O surface)

Goal: ship the building blocks every other phase depends on, with full test coverage, so later slices compose them.

**Slice 1.0** — Add `anthropic` to `pyproject.toml [project.dependencies]`
- Test: `tests/test_anthropic_import.py::test_anthropic_sdk_importable` — `import anthropic` does not raise.
- Impl: edit `pyproject.toml`; pin minor version (e.g., `anthropic>=0.40,<1.0`); run `.venv/bin/pip install -e .` to refresh venv.
- Commit: `feat: add anthropic SDK dependency (LLD-012 v2.1 prep for hooks + compaction_probe)`

**Slice 1.1** — TLDR extractor pure-parsing
- Test: `tests/test_tldr_extractor.py::test_extracts_valid_tldr_section`
- Impl: `cli/tldr_extractor.py::extract_tldr(text: str) -> TldrSection | TldrError`
- Behavior: regex match `^## TLDR — Nonnegotiables$` ... `^<!-- Full rule body below this section -->$`; parse bullets; return structured object.
- Commit: `feat: add TLDR extractor pure-parsing module (LLD-012 SC-1 substrate)`

**Slice 1.2** — TLDR extractor failure mode: missing close marker
- Test: `test_missing_close_marker_warns_and_extracts_to_eof`
- Impl: extend `extract_tldr` — log WARN, take content to EOF.
- Commit: `feat: TLDR extractor handles missing close marker (LLD-012 §Extractor failure modes)`

**Slice 1.3** — TLDR extractor failure mode: multiple TLDR sections
- Test: `test_multiple_tldr_sections_rejects`
- Impl: extend `extract_tldr` — return `TldrError(reason="ambiguous TLDR")`.
- Commit: `feat: TLDR extractor rejects ambiguous duplicate sections`

**Slice 1.4** — TLDR extractor failure mode: bullet-count / length overflow
- Test: `test_overflow_rejects_with_diagnostic`
- Impl: extend `extract_tldr` — reject if bullets >7 OR any bullet >80 chars; diagnostic lists offending bullets.
- Commit: `feat: TLDR extractor enforces ≤7 bullets / ≤80 chars`

**Slice 1.5** — TLDR extractor failure mode: empty section
- Test: `test_empty_tldr_rejects`
- Impl: extend `extract_tldr` — reject if header present + no bullets.
- Commit: `feat: TLDR extractor rejects empty section (fail-loud)`

**Slice 1.6** — Lessons store append + read helper
- Test: `tests/test_lessons_store.py::test_append_creates_monthly_file_with_frontmatter`
- Impl: `cli/lessons_store.py::append_entry(entry: dict) -> Path`, `::read_entries(since_days: int) -> list[dict]`
- Behavior: target `docs/lessons/<YYYY-MM>-lessons.md`; create with frontmatter on first write; append YAML entry list-item; HTML-encode `observed`/`expected`; 200-char cap; validate `kind` enum.
- Commit: `feat: add lessons store append + read helper (LLD-012 SC-7 substrate)`

**Slice 1.7** — `.claude/state/` directory + .gitignore entry
- Test: `tests/test_state_dir_gitignore.py::test_claude_state_listed_in_gitignore` — assert `.claude/state/` line present in `.gitignore`. Asserting via test (vs treating as pure mechanical edit) preserves the TDD-vertical-slicing discipline stated in §Iteration discipline: every slice has at least one failing test → green transition.
- Impl: edit `.gitignore` to add `.claude/state/`; ensure runtime modules `mkdir` on first write.
- Commit: `chore: gitignore .claude/state/ runtime directory`

Phase 1 exit: pytest green, pyrefly 0, all slice commits land sequentially.

---

### Phase 2 — TLDR authoring (data, not code)

Goal: every schema-layer file in scope carries a valid TLDR section that passes `cli/tldr_extractor.py`. No code; pure doc edits.

**Slice 2.1** — `.claude/CLAUDE.md` TLDR section + Rule Compression Convention subsection
- Impl: add `## TLDR — Nonnegotiables` (≤7 bullets) + `## Rule Compression Convention` 2–3 sentence section.
- Verify: `python -m cli.tldr_extractor .claude/CLAUDE.md` (one-shot CLI surfaced for verification).
- Commit: `docs: add TLDR section + rule-compression convention to CLAUDE.md (LLD-012 SC-1, SC-13)`

**Slice 2.2** — `.claude/rules/documentation-gate.md` TLDR
- Impl: synthesize ≤7 imperative bullets from existing body.
- Verify: extractor green.
- Commit: `docs: add TLDR section to documentation-gate.md`

**Slice 2.3** — `.claude/rules/interview-gate.md` TLDR
- Same pattern. Commit per file.

**Slice 2.4** — `.claude/rules/skills-routing.md` TLDR

**Slice 2.5** — `.claude/rules/task-tracking.md` TLDR

**Slice 2.6** — `docs/design/orchestra-philosophy-r2.md` Changelog entry — Karpathy K1/K2/K3/K4/K8 lineage
- Canon-frozen-aware edit (Status: Current). Whitelist edit = Changelog row only; no body change. Use `orchestra:commit` skill `--pre-stage-check` to validate the whitelist edit is accepted.
- **Canon-frozen-guard reference:** `skills/commit/references/canon-frozen-guard.md` (whitelist-edit definition: Status / Iteration / Superseded by + Changelog append). Reader unfamiliar with the rules should read that reference before editing canon-frozen docs.
- **Verification step:** run `python -m cli.lint --pre-stage-check docs/design/orchestra-philosophy-r2.md --commit-msg-draft "..."` before staging; on PASS, proceed to commit. On FAIL, interview Hassan (changelog-only edit should always pass; failure signals deeper issue).
- Commit: `docs: orchestra-philosophy-r2 — add Karpathy K-lineage Changelog row (LLD-012 SC-13)`

Phase 2 exit: 5 schema-layer files extractor-green; design doc Changelog row in place.

---

### Phase 3 — Hook handlers (cli/hooks/ package)

Goal: handler modules emit correct JSON + `<system-reminder>` content, exit codes, fallbacks. Subprocess-invokable.

**Slice 3.1** — `cli/hooks/__init__.py` + `session_start_inject.py` minimal happy path
- Test: `tests/test_session_start_inject.py::test_emits_tldr_in_system_reminder`
- Impl: read TLDR sections from all schema-layer files; emit JSON with `hookSpecificOutput.additionalContext` containing `<system-reminder>...[ORCHESTRA TLDR]...</system-reminder>` per LLD-012 §Edge Cases (marker = literal opening line of `additionalContext`, BEFORE the `<system-reminder>` wrap).
- Commit: `feat: add SessionStart hook handler (TLDR injection)`

**Slice 3.2** — Token budget enforcement (500 tokens) + fallback to identity + rule-name index
- Test: `test_overbudget_falls_back_to_identity_index`
- Test: `test_missing_api_key_falls_back_to_identity_index` — mock missing `ANTHROPIC_API_KEY` → hook must fall back to identity + rule-name index without crashing (hook runs synchronously on every session start; an API-call failure must not break Claude Code startup).
- Impl: call Anthropic `count_tokens` API (Q2 resolution); if over budget OR API key missing OR call fails, emit fallback shape per LLD-012 §Hook architecture; log to `.claude/state/budget-overflow.log`.
- Commit: `feat: SessionStart hook enforces 500-token budget with fallback`

**Slice 3.3** — Include last 10 structured-violation lessons via allowlisted-fields-only template
- Test: `test_includes_only_violation_kind_inject_true`
- Test: `tests/test_lesson_injection_allowlist.py::test_no_free_text_teach_in_output` (codex #2 regression)
- Impl: filter `kind == "violation" and inject == True`; emit only `rule_violated`, `observed`, `expected` via fixed template; HTML-encode; 200-char-cap.
- Commit: `feat: SessionStart hook includes structured violations only (LLD-012 SC-11, codex #2 fix)`

**Slice 3.4** — `pre_compact_instruct.py` emits compact_instructions preserving TLDR verbatim
- Test: `tests/test_pre_compact_instruct.py::test_emits_compact_instructions_with_tldr`
- Impl: read TLDR sections; emit JSON `{"compact_instructions": "...TLDR verbatim..."}` per Claude Code PreCompact contract.
- Commit: `feat: add PreCompact hook handler (TLDR preservation)`

**Slice 3.5** — `user_prompt_reinject.py` turn-counter + Nth-turn injection
- Test: `tests/test_user_prompt_reinject.py::test_counter_increments`
- Test: `test_emits_on_nth_turn_silent_otherwise` (SC-14)
- Impl: atomic read-modify-write `.claude/state/turn-counter.json`; if counter % N == 0 (N from `ORCHESTRA_REINJECT_EVERY` env, default 5), emit TLDR `<system-reminder>` (reuse session_start_inject's emit helper, same 500-token budget); else exit 0 silent.
- Commit: `feat: add UserPromptSubmit hook with Nth-turn re-injection (LLD-012 SC-14)`

**Slice 3.6** — Hook fail-loud on missing interpreter / import error
- Test: `tests/test_install_claude_hooks_fail_loud.py::test_missing_interpreter_exits_nonzero_with_stderr`
- Impl: each hook module's `__main__` guard catches `ImportError` / module-not-found and exits 2 with stderr diagnostic. (Install-side resolution in Phase 4.)
- Commit: `feat: hook handlers fail loud on missing interpreter (codex #3 fix)`

Phase 3 exit: 3 hook handlers behave correctly via subprocess; allowlist + fail-loud regressions green.

---

### Phase 4 — Installer (`cli/install_claude_hooks.py`)

Goal: write/verify/uninstall `.claude/settings.json` with `<RESOLVED_PYTHON>` from `sys.executable`; merge with other-plugin hooks; CI gate via `--verify`.

**Slice 4.1** — Install creates valid settings.json
- Test: `tests/test_install_claude_hooks.py::test_install_writes_settings_with_resolved_interpreter`
- Impl: resolve `sys.executable`, validate executable + readable; write SessionStart + PreCompact + UserPromptSubmit hook entries per LLD-012 §Hook architecture; atomic write.
- Commit: `feat: add install_claude_hooks installer (LLD-012 SC-2)`

**Slice 4.2** — `--uninstall` removes orchestra-installed lines only
- Test: `test_uninstall_removes_orchestra_preserves_others`
- Impl: identify orchestra entries by `cli.hooks.*` command prefix; remove; preserve other-plugin hook entries.
- Commit: `feat: install_claude_hooks --uninstall preserves non-orchestra hooks`

**Slice 4.3** — `--verify` fingerprint audit + non-executable detection (CI gate)
- Test: `test_verify_detects_stale_interpreter_path`
- Test: `test_verify_detects_tampering`
- Impl: compare installed command vs expected fingerprint; assert resolved interpreter is executable; exit non-zero with stderr on mismatch.
- Commit: `feat: install_claude_hooks --verify CI gate (codex #3 fix)`

**Slice 4.4** — Merge with existing settings.json (preserve non-orchestra hooks across re-install)
- Test: `test_install_merges_with_existing_settings`
- Impl: read existing settings.json; preserve non-orchestra arrays; replace orchestra entries.
- Commit: `feat: install_claude_hooks merges with existing settings.json`

**Slice 4.5** — `--force` flag for re-install on detection of stale interpreter
- Test: `test_force_reinstalls_when_interpreter_changed`
- Impl: `--force` skips "already installed" no-op and rewrites.
- Commit: `feat: install_claude_hooks --force flag`

Phase 4 exit: install + uninstall + verify + merge green; fail-loud regression green.

---

### Phase 5 — Lessons skill + slash commands

Goal: `/orchestra:teach`, `/orchestra:violation`, `/orchestra:lessons-lint` available and writing to lessons store.

**Slice 5.1** — `skills/lessons/SKILL.md` frontmatter + body
- Test: none (skill manifest is data; behavior tested via slash-command shims).
- Impl: write SKILL.md with frontmatter `name: lessons` only (NO `commands:` frontmatter list — LLD-012 iter-3 SC-6 explicitly declares slash commands via `commands/<name>.md` shim files per existing orchestra repo convention, see `commands/spec-review.md`). Body documents the three slash commands + YAML entry schemas + `[ORCHESTRA TLDR]` injection marker per LLD-012 §Edge Cases.
- Commit: `feat: add orchestra:lessons skill manifest`

**Slice 5.2** — `commands/teach.md` slash-command shim
- Test: `tests/test_lessons_store.py::test_teach_appends_kind_teach_inject_false` — **note: same file as Phase 1 Slice 1.6 store-helper tests.** The store-helper test cases (Phase 1) cover low-level append + read semantics; Phase 5 cases (5.2–5.3) cover slash-command shim integration. Reader picking up at Phase 5: the test file already exists from Phase 1; add new test cases, do not recreate.
- Impl: `commands/teach.md` frontmatter + body invokes `cli.lessons_store.append_entry(kind="teach", source="user", inject=False, body=...)`. Match `commands/spec-review.md` pattern (Q4 default).
- Commit: `feat: /orchestra:teach slash command (LLD-012 SC-6)`

**Slice 5.3** — `commands/violation.md` slash-command shim + rule-id allowlist + HTML-encode + 200-char cap
- Test: `test_violation_appends_kind_violation_inject_true`
- Test: `test_violation_rejects_unknown_rule_id`
- Test: `test_violation_path_traversal_blocked` (codex #2 / security)
- Impl: parse `--rule`, `--observed`, `--expected`; validate `rule` against allowlist (basenames of `.claude/rules/*.md` + `CLAUDE.md` + `workflow.md`); HTML-encode + 200-char cap; append entry.
- Commit: `feat: /orchestra:violation slash command (LLD-012 SC-6, SC-11)`

**Slice 5.4** — `commands/lessons-lint.md` slash-command shim
- Test: `test_lessons_lint_shim_invokes_cli`
- Impl: shim invokes `python -m cli.lessons_lint`.
- Commit: `feat: /orchestra:lessons-lint slash command (LLD-012 SC-6)`

Phase 5 exit: three slash commands available + lessons file writes work end-to-end via subprocess.

---

### Phase 6 — Lessons lint + apply + compaction probe

Goal: auto-promotion pipeline functional (lessons → proxy artifact → user spec-review → user apply → schema mutation + auto-promote marker).

**Phase-level conditional gate:** Phase 6 slices 6.5–6.6 (compaction_probe) depend on resolving **Q3** (whether `compact_20260112` is programmatically accessible from the Anthropic SDK). If Q3 unresolved when Phase 6 starts, STOP at slice 6.5 boundary and interview Hassan before proceeding to 6.6. Slices 6.1–6.4 (lint + apply pipeline) are NOT blocked by Q3 and can land independently.

**Slice 6.1** — `cli/lessons_lint.py` scan + recurrence detection
- Test: `tests/test_lessons_lint.py::test_detects_threshold_recurrence`
- Test: `test_skips_source_auto_promote` (recursion guard, LLD-012 §lessons_lint step 1)
- Impl: read `lessons_store.read_entries(since_days=90)`; filter `kind == "violation"`; group by `rule_violated`; skip `source == "auto-promote"`; detect ≥3× recurrence.
- Commit: `feat: lessons_lint detects recurring violations (LLD-012 SC-8)`

**Slice 6.2** — Proxy artifact draft (tie-break + overflow refusal)
- Test: `test_proxy_artifact_written_with_diff`
- Test: `test_overflow_emits_needs_author_rewrite_marker` (LLD-012 §lessons_lint step 3 tie-break)
- Test: `test_append_would_exceed_7_refuses` (overflow consolidate-first rule)
- Impl: draft proposed bullet per tie-break rules (a/b/c); write proxy artifact to `docs/proposed-rule-mutations/<rule>-<date>.md` with target path + current TLDR diff + proposed TLDR diff + lesson evidence + provenance; do NOT auto-trigger spec-review (Class-B reconciliation, LLD-012 SC-8).
- Commit: `feat: lessons_lint writes proxy artifact (LLD-012 SC-8)`

**Slice 6.3** — `cli/lessons_apply.py` iteration-aware attestation lookup
- Test: `tests/test_lessons_apply.py::test_refuses_without_passed_attestation`
- Test: `test_iteration_n_attestation_lookup` (per LLD-012 API table — read `> **Iteration:** N` from proxy doc, default 1 if absent)
- Impl: read proxy doc, extract `Iteration: N`, look up `docs/reviews/<proxy-stem>-rN.review.yaml`, assert verdict in `{pass, conditional_pass}`; refuse otherwise with non-zero exit.
- Commit: `feat: lessons_apply iteration-aware attestation lookup (LLD-012 §API, r2 fix)`

**Slice 6.4** — `lessons_apply` mutates schema-layer target + appends auto-promote marker
- Test: `test_mutates_target_and_appends_marker`
- Impl: on attestation pass, mutate TLDR section in target file per proxy's proposed diff; append `kind: promotion-marker, source: auto-promote, inject: false` entry to current month's lessons file per LLD-012 §Lessons skill §source: auto-promote producer.
- Commit: `feat: lessons_apply mutates target + writes auto-promote marker (LLD-012 SC-7, SC-9)`

**Slice 6.5** — `cli/compaction_probe.py` keyword extraction
- Test: `tests/test_compaction_probe.py::test_extracts_first_noun_per_bullet`
- Test: `test_orchestra_tldr_prefix_on_collision`
- Impl: parse TLDR bullets; extract first 4+ char noun per bullet; if collision-risk with common English, prefix `ORCHESTRA-TLDR-`.
- Commit: `feat: compaction_probe deterministic keyword extraction (LLD-012 SC-5)`

**Slice 6.6** — `compaction_probe` Anthropic API integration (Q3 resolution required first)
- Test: `test_compact_invocation_mocked` (Anthropic SDK mocked)
- Test: `test_missing_api_key_exits_2`
- Test: `test_allow_skip_local_dev_only`
- Impl: invoke `compact_20260112` (or fallback per Q3); assert every keyword present in compacted output; exit codes per LLD-012 §compaction_probe + §Edge Cases.
- Commit: `feat: compaction_probe CI gate against Anthropic compact API (LLD-012 SC-5)`

Phase 6 exit: lint + apply + probe modules behave correctly with mocked Anthropic calls.

---

### Phase 7 — Schema-v2 attestation overwrite fail-closed (codex #4, partial-supersession scoping)

Goal: `cli/spec_review.py` force-mode overwrite path refuses on malformed existing **v2.0** attestation, never mutates.

**Partial supersession by LLD-011 slice 1.7.** At HEAD `a35a0f7`, lines 718-728 of `cli/spec_review.py` (the `v1.0_attestation_frozen` block) ALREADY refuse all v1.0 attestation overwrites (frozen-historical) — `--force` does not apply to v1.0 files. This closes part of codex finding #4 (force-mode overwrite of v1.0 malformed file is impossible by construction). The remaining gap codex #4 addresses: when `--force` is passed AND the existing target is a **v2.0** attestation whose YAML is malformed, current code (line 730+ branch) proceeds to overwrite without inspecting the existing file. Phase 7 closes this gap.

**Edit perimeter (HEAD `a35a0f7`):** Phase 7 adds ONE new branch to `cli/spec_review.py`. After the existing v1.0-freeze check (lines 718-728) returns False (i.e., existing file is NOT v1.0), and before the "no force-passed exists refuse" branch (lines 730-735), insert a malformed-YAML detection branch that fires when `args.force is True AND out_path.exists()`. If `out_path` parses cleanly as YAML, proceed to overwrite. If parse fails, exit non-zero with stderr "force-mode overwrite refused: existing attestation malformed; hand-fix or delete first". All other functions (`canonicalize_doc_path`, `_atomic_write`, `_detect_schema_version`, PDSA invocation, aggregator wiring, delta-review wiring) are NOT touched. (Line numbers verified at HEAD `a35a0f7`; will drift — implementer re-greps at edit time. Anchor symbols: `v1.0_attestation_frozen` for the freeze branch, `if out_path.exists() and not args.force:` for the bare-exists refuse.)

**Slice 7.1** — Regression test seeded with malformed v1 attestation
- Test: `tests/test_schema_v1_overwrite_failclosed.py::test_force_mode_refuses_on_malformed_existing`
- Impl: seed `docs/reviews/<stem>-r1.review.yaml` with invalid YAML; run force-mode overwrite; assert non-zero exit + no file mutation.

**Slice 7.2** — `cli/spec_review.py` force-mode read-existing fail-closed branch
- Impl: read existing target; if YAML parse fails, abort overwrite with `OverwriteRefused(reason="malformed existing")`; exit 1.
- Commit: `fix: spec_review force-mode fail-closed on malformed existing attestation (codex #4 fix)`

Phase 7 exit: regression green; pytest baseline +1 test.

---

### Phase 8 — Integration tests

Goal: end-to-end pipeline runs in subprocess against a throwaway repo, mocked Anthropic calls.

**Slice 8.1** — `tests/integration/test_hook_emission.py`
- Test: subprocess-invoke each hook handler; assert JSON shape; assert `<system-reminder>` wrap; assert `[ORCHESTRA TLDR]` marker as opening line.
- Commit: `test: integration test for hook emission shape`

**Slice 8.2** — `tests/integration/test_end_to_end_violation.py`
- Test: create throwaway repo; run install_claude_hooks; fire SessionStart subprocess; `/orchestra:violation` × 3 same rule; run lessons_lint; assert proxy artifact written; mock spec-review attestation as `pass`; run lessons_apply; assert target file mutated + auto-promote marker appended.
- Commit: `test: end-to-end violation → lint → apply integration test`

Phase 8 exit: integration suite green.

---

### Phase 9 — Self-application + release

Goal: dogfood the durability layer in orchestra's own repo; bump version; tag release.

**Slice 9.1** — Run `python -m cli.install_claude_hooks` on this repo
- Verify: `.claude/settings.json` exists with resolved interpreter; `python -m cli.install_claude_hooks --verify` exits 0.
- Commit: `chore: self-install Claude Code hooks (orchestra dogfood)` — includes `.claude/settings.json`

**Slice 9.2** — Run `python -m cli.compaction_probe` against this repo
- Verify: every TLDR keyword survives `compact_20260112`; exit 0.
- No commit (verification only). **Rollback scope on failure:** failing keywords identify which TLDR sections under-perform under compaction. Branch behavior:
  - If 1 file fails → supersede only that file's TLDR via a Phase-2-style commit (rewrite TLDR, re-run extractor green check); no rerun of Phase 3-8 needed (compaction probe is independent of hook code paths).
  - If ≥2 files fail → STOP and interview Hassan (signals systemic TLDR-authoring drift; LLD-012 §TLDR section format may need a revision via supersession `-r3`).
  - In both cases, slice 9.3 (version bump) is BLOCKED until probe is green.

**Slice 9.3** — Bump versions
- Edit `.claude-plugin/plugin.json` `version: "2.1.0"`.
- Edit `.claude-plugin/marketplace.json` `plugins[0].version: "2.1.0"`.
- Commit: `chore: bump version to v2.1.0 (LLD-012 ship)`

**Slice 9.4** — Update `docs/HANDOFF.md` with v2.1.0 ship state
- Per `.claude/rules/documentation-gate.md` Gate 3 — run spec-review on HANDOFF update; commit after pass.
- Commit: `docs: HANDOFF — record v2.1.0 ship (LLD-012 complete)`

**Slice 9.5** — Flip LLD-012 Status `Draft` → `Approved` → `Implemented` (whitelist edit; orchestra:commit skill `--pre-stage-check`)
- Commit: `docs: LLD-012 Status → Implemented (v2.1.0 ship)`

**Slice 9.6** — Tag v2.1.0
- **Tag ordering rationale:** tag points to the slice 9.5 commit (which flips LLD-012 Status → Implemented + HANDOFF update). Status flip is the formal "this LLD ship is complete" marker. Tagging at this commit means anyone checking out `v2.1.0` lands on the post-Implemented-status state. Alternative (tag after 9.3 bump pre-status-flip) leaves the tag on a state where the LLD still says Draft/Approved — confusing. The slice 9.5 commit will be a single small whitelist edit, low risk to tag onto.
- `git tag v2.1.0` on the slice 9.5 commit.
- Push tag (interview Hassan before push per CLAUDE.md irreversible-action rule).

Phase 9 exit: tag `v2.1.0` exists; HANDOFF reflects ship; pytest baseline updated.

---

## Risk register

| Risk | Likelihood | Blast radius | Mitigation |
|---|---|---|---|
| Q3 (`compact_20260112` not programmatically accessible) | Medium | Phase 6 slice 6.6 blocked | Interview Hassan immediately on slice 6.6 attempt; possible LLD update if fallback path needed |
| Token-count drift between hook runtime model + `count_tokens` model | Low | Soft (over-budget fallback already designed) | LLD-012 §Hook architecture already specifies fallback; verify count_tokens matches running model where possible |
| Slash-command shim format diverges from `commands/spec-review.md` pattern | Low | Phase 5 cosmetic | Match canonical example; if Claude Code rejects, interview |
| Concurrent test failures from `.claude/state/turn-counter.json` | Low | Test-suite flakiness | Atomic-write via `os.replace`; tests use per-test temp dirs |
| TLDR bullet authoring drift (≤7 bullets / ≤80 chars constraint) | Medium | Phase 2 stalls | Extractor green is the gate; if hit, supersede the rule file with -r2 |
| `.claude/CLAUDE.md` TLDR drift from existing body | Medium | Future rule decay | Phase 6 compaction_probe is the long-term guard; Phase 2 authoring is one-shot |
| `cli/spec_review.py` interaction surface (post-Phase-2-ship state) | Medium | Phase 7 edit must interact correctly with v1.0-freeze + PDSA gate + v2 aggregator dispatch | **Sequencing rule (post-LLD-011 v2.0.0 ship):** Phase 7 inserts a new branch between v1.0-freeze (anchor: `v1.0_attestation_frozen` block, currently lines 718-728 at HEAD `a35a0f7`) and the no-force-exists refuse (anchor: `if out_path.exists() and not args.force:`, currently lines 730-735). PDSA gate currently at lines 737+. Reader must re-grep at edit time — line numbers shift as parallel sessions land patches. New branch is malformed-YAML-aware refuse on v2.0 attestation overwrite under `--force`. |

---

## Acceptance / exit criteria for v2.1.0 ship

All 14 SCs from LLD-012 demonstrably met:

- [ ] SC-1: 5 schema-layer files extractor-green
- [ ] SC-2: `cli.install_claude_hooks` writes `.claude/settings.json` with SessionStart + PreCompact + UserPromptSubmit (matchers per LLD; UserPromptSubmit installer behavior also covered by SC-14)
- [ ] SC-3: SessionStart hook emits TLDR + structured-violations injection wrapped in `<system-reminder>`
- [ ] SC-4: PreCompact hook emits compact_instructions preserving TLDR verbatim
- [ ] SC-5: `cli.compaction_probe` is a passing CI gate
- [ ] SC-6: `skills/lessons/SKILL.md` + 3 slash-command shims in place
- [ ] SC-7: Lessons file format conforms to `source: {user, auto-promote}` enum; auto-promote marker appended by lessons_apply
- [ ] SC-8: `cli.lessons_lint` writes proxy artifact + does NOT auto-trigger spec-review
- [ ] SC-9: `cli.lessons_apply` mutates target only after passed attestation; auto-promote marker + target + proxy committed together. **Acceptance semantics:** tooling exists + integration test asserts the end-to-end happy path (Slice 8.2). A real organic auto-promotion is NOT required during v2.1.0 ship (the pipeline is exercised by users post-ship when ≥3× recurrence accumulates). Acceptance is verified by Slice 8.2's mocked attestation pass plus Phase 6 unit tests.
- [ ] SC-10: Portable interpreter resolution via `sys.executable` at install; fail-loud at runtime; `--verify` CI gate
- [ ] SC-11: Free-text `teach` never reaches `<system-reminder>`; allowlisted structured fields only
- [ ] SC-12: All listed unit + integration tests in place and green
- [ ] SC-13: `docs/design/orchestra-philosophy-r2.md` Changelog entry + `.claude/CLAUDE.md` Rule Compression Convention subsection
- [ ] SC-14: `UserPromptSubmit` hook installed; turn-counter + Nth-turn injection green per test

Pytest baseline: **412 at HEAD `c56e85d`** (verified via `.venv/bin/python -m pytest --collect-only`) + ~25 (LLD-012 new) ≈ **~437** (estimate; final count depends on subtest granularity). The 412 figure captures all LLD-011 Phase 1 + Phase 2 + self-application work (commits `4c831c2` rubric-freeze, `ab65734` 2-iter cap, `1b438da` failure-attestation, `8f700d3` aggregate-write, `9e4b3e0` vocab canon, `c56e85d` v2.0.0 self-bump).

Pyrefly: 0 errors.

`cli.lint` self-dogfood: 0 violations across all 4 L-checks.

Tag: `v2.1.0` on main.

---

## Out-of-scope reminders

These were considered and deferred per LLD-012 §Out of Scope. Do NOT silently scope-creep:

- PreToolUse blocking on code-path edits → LLD-013
- Skill SKILL.md compression → future pass
- Anthropic Memory tool integration → confirmed dead end
- Cross-machine lesson sync → git is the sync
- Rush-mode cadence detection → v2.2+
- TLDR compression on `.claude/workflow.md` + `.claude/skills-registry.md` → LLD-013
- Maintainer ratification path (`/orchestra:ratify-lesson`) → v2.2+

If any of these surface as a blocker, file a BUG or supersede LLD-012 (`-r3`) — do NOT widen plan scope silently.

---

## Related Documents

- `docs/features/012-rule-durability-and-learning-layer.md` — source LLD (Iteration 2, ship target v2.1.0)
- `docs/reviews/012-rule-durability-and-learning-layer-r1.review.yaml` — judge-1 iter-1 attestation
- `docs/reviews/012-rule-durability-and-learning-layer-r2.review.yaml` — judge-1 iter-2 attestation
- `docs/reviews/012-rule-durability-and-learning-layer-r1.codex.md` — codex adversarial review
- `docs/investigations/2026-05-11-workflow-skill-refresh.md` — W6 + W7 brainstorm substrate
- `docs/design/orchestra-philosophy-r2.md` — Karpathy K-lineage Changelog target (SC-13)
- `docs/plans/2026-05-11-spec-review-v2-implementation.md` — LLD-011 Phase 2 parallel session (separate ship)
- `.claude/workflow.md` — Step 4 vertical-slice TDD discipline (referenced by Iteration discipline above)

---

## Changelog

| Date | Entry |
|---|---|
| 2026-05-11 | Initial draft (iter-1). Vertical slices in 9 phases. 6 open questions surfaced (Q1–Q6). Plan does not introduce design decisions beyond LLD-012 r2-final. |
| 2026-05-11 | orchestra spec-review judge-1 iter-1. Verdict: conditional_pass. 2 Critical + 13 Important + 5 Minor. Attestation NOT persisted to `docs/reviews/` due to pre-existing PDSA path-resolution bug (PDSA resolves cited file-line paths from doc-dir not repo-root → bare `cli/spec_review.py` line-N cites fail to resolve from `docs/plans/`). BUG filed as task #14 (deferred). Findings applied inline via batch-fix-by-class (per user grill): **Class A — stale facts** (C1 stale `canonicalize_doc_path` line range 376-394 → 402-422; C2 marketplace.json align-with-plugin.json rationale; pytest baseline 259 → 321 live state). **Class B — scope/perimeter** (Slice 1.7 add test for TDD discipline; risk-register row for cli/spec_review.py concurrent-mod with LLD-011 Phase 2; Phase 7 edit perimeter named explicitly; SC-2 acceptance expanded to include UserPromptSubmit; Slice 9.2 rollback scope defined; SC-9 acceptance semantics defined). **Class C — missing/duplicate info** (Phase 6 Q3 conditional promoted to phase-level gate; Phase 5 Slice 5.2 cross-phase test-file sharing noted; Phase 2 Slice 2.6 canon-frozen-guard reference + verification step added; Files-created tests/test_lessons_store.py description broadened; docs/STANDARDS.md row dropped; Q2 risk added; workflow.md/skills-registry.md boundary-fence rule). Iteration bumped 1 → 2. |
| 2026-05-11 | orchestra spec-review judge-1 iter-2 (v1 flow). Verdict: fail. 3 Critical + 10 Important + 3 Minor. Material drift discovered: LLD-011 Phase 2 fully SHIPPED (orchestra now at v2.0.0) between plan iter-1 auth and iter-2 review — line numbers shifted, parallel-session framing materially obsolete, codex finding #4 partially superseded by slice 1.7 v1.0-freeze branch. Applied per user grill (option "rebase against HEAD + supersede LLD-012 → r3"): Critical fixes — (C1) Phase 7 cite reframed against current spec_review.py; (C2) pytest baseline 321 → 412 live; (C3) Phase 7 scope narrowed to v2.0 path. Important fixes — anthropic dep slice 1.0; ANTHROPIC_API_KEY handling at hook runtime; canonicalize_doc_path 402 → 408 line cite; parallel-session note rewritten as "shipped"; risk register recast as historical; ship target v1.8.0 → v2.1.0 (semver from v2.0.0); marketplace.json row simplified; slash-command shape contradiction resolved via LLD-012 SC-6 alignment with `commands/<name>.md`; Q4 RESOLVED. Minor fixes — Files-created adds `tests/test_state_dir_gitignore.py` + `tests/test_anthropic_import.py`; SC-9 taxonomy simplified; skill enumeration de-enumerated. Iteration transiently bumped 2 → 3, then reverted to 2 to work around v2 override-cap notes-as-list schema bug (separate BUG task). |
| 2026-05-11 | orchestra spec-review v2 (6-sub-judge ensemble) iter-2 supplementary re-review. Attestation: `docs/reviews/2026-05-11-lld-012-v18-implementation-r2.orchestra.review.yaml`. Prior v1 r2 archived to `docs/archive/reviews/2026-05-11-lld-012-v18-implementation-r2.orchestra.review.v1schema-superseded.yaml`. Verdict: **fail**. 10 Critical + 28 Important + 12 Minor aggregated across 6 sub-judges. Sub-judge verdicts: structure conditional_pass (4 findings), semantic conditional_pass (11 findings), gate-compliance conditional_pass (2 findings), adversarial **fail** (21 findings), repo-context **fail** (8 findings), architectural-fit conditional_pass (4 findings). **Critical clusters**: (a) repo-context 4 Criticals — HEAD `c56e85d` cite stale (actual HEAD `a35a0f7`), `cli/spec_review.py` line cites all off by ~20 lines; (b) adversarial 6 Criticals — SessionStart API hang, turn-counter race, sys.executable stale-after-venv, lessons_apply vs editor, rule-id allowlist symlink attack, rule_violated content not sanitized. **Per user grill decision**: 6 adversarial Criticals DEFERRED to v2.2/v2.3 hardening pass per new Out-of-Scope section above (mirroring LLD-012 r2 deferral). 4 repo-context Criticals FIXED inline: line cites rebased against HEAD `a35a0f7` with anchor-symbol guidance ("re-grep at edit time"); HEAD ref updated `c56e85d` → `a35a0f7`. Plan iter stays at 2 (no iter-3 needed per disposition decision). |
