# Sonnet Judge-2 Review (LLD-008 r3)

> Reviewer: general-purpose subagent (model: sonnet) — different model than Opus author
> Date: 2026-05-11

# Adversarial Spec Review — LLD-008 (Narrowed Scope, r3)

**Reviewer:** Sonnet judge-2 (adversarial)
**Subject:** `docs/features/008-commit-skill.md` (Iteration 3, narrowed)
**Cross-references:** LLD-009 r1, LLD-010 r1, `cli/install_hooks.py`, `cli/init.py`, `cli/lint.py`

---

## Finding 1 — HIGH: `--on-conflict` argparse implementation is architecturally wrong for the stated sentinel-vs-default semantics

**Severity: High**

LLD-008 Design § `install_one_hook` pseudocode depends on this conditional:

```python
if on_conflict not in ("skip", "replace", "append"):
    if sys.stdin.isatty():
        # interactive
    else:
        on_conflict = "skip"
```

This logic assumes `on_conflict` can arrive as something *other* than `"skip"`, `"replace"`, or `"append"` — specifically as a sentinel meaning "not supplied." But argparse with `default="skip"` will **always** produce `"skip"` when the flag is absent. There is no sentinel. The TTY-detection branch (`sys.stdin.isatty()`) is unreachable: `on_conflict` will always be one of the three valid values.

To make the interactive prompt path reachable, the design must use `default=None` as the sentinel. That choice propagates through A5's acceptance text ("Non-interactive when flag passed. Existing interactive prompt path retained when flag absent + `sys.stdin.isatty()` returns True; replaced with `skip` default when non-TTY") — which is the correct user-visible behaviour — but the pseudocode default of `"skip"` kills it. The doc presents both the correct behaviour (A5 prose) and the broken mechanism (pseudocode default). The implementation spec is self-contradictory. One of them will win at code-time; the adversarial bet is the pseudocode wins and the interactive path silently dies.

Additionally, the new `--on-conflict` flag interacts with the existing `--force` flag in an undocumented way. Current `install_one_hook` already has a `force=False` parameter that bypasses conflict handling entirely (line 48: `if hook_path.exists() and not force:`). With both `--force` and `--on-conflict=skip` passed, `--force` wins and the skip is ignored. With `--force` and `--on-conflict=append`, force wins and the append never runs. This interaction is not documented in the LLD, not tested in T4a–T4d, and creates a trap for callers (including `cli.init` which might be called after `--force` was already passed by a user).

---

## Finding 2 — HIGH: `cli.init` bootstrap call passes `main()` a flat list but `main()` parses with argparse from `sys.argv` by default — the actual calling convention is untested against the real function signature

**Severity: High**

LLD-008 Design § `cli.init bootstrap call`:

```python
result = cli.install_hooks.main(["--pre-commit", "--commit-msg", "--on-conflict=skip"])
```

Looking at the actual `cli/install_hooks.py:89-108`, `main(argv: list[str] | None = None)` uses `parser.parse_args(argv)`. When `argv` is passed as a list, `argparse` parses it correctly. So far so good.

But the current argparse parser (lines 91–98) has **no `--on-conflict` flag defined**. The call `main(["--pre-commit", "--commit-msg", "--on-conflict=skip"])` would fail with `unrecognized arguments: --on-conflict=skip` on the current codebase. That is expected — it's a not-yet-implemented flag. The defect is that **A6 acceptance tests (T5a–T5c) are specified as testing `cli.init bootstrap leaves both hooks installed`** without testing that the argparse definition of `main()` actually accepts `--on-conflict`. The test matrix for T5 tests `cli.init` as a black-box but never explicitly names `cli.install_hooks` argparse coverage as part of that test. A T5c failure mode could silently be "argparse exits 2 (usage error) instead of blocking on input()" — non-TTY safe for the wrong reason.

This is a spec gap: T5c should explicitly assert that the exit is due to clean successful execution, not due to argparse error exit(2). The current spec leaves the door open for a passing test that papers over a real bug.

---

## Finding 3 — MEDIUM: Template relocation path resolution in `cli.install_hooks` uses a hardcoded `TEMPLATES_DIR` constant that LLD-008 replaces but the migration of that constant is underspecified

**Severity: Medium**

Current `cli/install_hooks.py:21`: `TEMPLATES_DIR = Path(__file__).parent / "templates"`. A4 says `cli.install_hooks reads templates from skills/commit/templates/`. This requires changing this line.

The LLD references `cli/lint.py:36-52 _load_extract_mermaid` as the precedent — that function uses `importlib.util.spec_from_file_location` to load a Python module from a path with a hyphenated directory. But template loading is simpler: it's just `path.read_text()`. The precedent is slightly misleading — the template case doesn't need `importlib`, it needs a path constant change.

The risk: the new `SKILL_TEMPLATES_DIR` constant (referenced in LLD-010 `_parse_user_config` code as `SKILL_TEMPLATES_DIR / "precommit-framework-snippet.yaml"`) is never defined in LLD-008. LLD-008 A4 says "reads from `skills/commit/templates/`" but specifies no constant name, no relative-path anchor, no fallback if the skills directory is missing (e.g., orchestra not installed as a plugin, only used as a local checkout). LLD-010 assumes this constant exists (it uses it directly in pseudocode) but LLD-008 — the LLD that is supposed to introduce it — never names it.

This is a cross-LLD contract gap: LLD-010 builds on an undefined symbol from LLD-008.

---

## Finding 4 — MEDIUM: SCALE migration "atomic single commit" invariant is weakened by the partial-edit requirement on `documentation-gate.md`

**Severity: Medium**

A8 and the Migration § define: "atomic single SCALE-side commit applies all 4 changes (2 deletions + 1 partial-edit + 1 registry-append)."

The partial-edit of `documentation-gate.md` (retaining Gates 1–3 verbatim, replacing Gates 4+5 with a one-line pointer) is an in-place body edit of a canon-frozen document. `documentation-gate.md` is in `.claude/rules/` — NOT under `docs/{features,bugs,adr,...}` — so it is not subject to `cli.lint` L2. But it IS subject to the `canon-frozen-guard.md` rule that LLD-008 is migrating. The rule (loaded in every session) says: any non-whitelist body change on a canon-frozen doc fires the interview gate.

What is the `Status` of `documentation-gate.md`? The SCALE-side file has no standard metadata block (it's a `.claude/rules/` file, not a `docs/` LLD). So the canon-frozen guard's Status-based trigger doesn't apply. But the partial-edit semantics are still a semantic canon violation: agents have loaded `documentation-gate.md` into prior sessions' context with Gates 4+5 in full. The one-line pointer eliminates that content. If SCALE's canon-frozen-guard.md is already being deleted in the same atomic commit, there's no enforcement mechanism — but there is a philosophical gap: the doc says "2 deletions + 1 partial-edit" without ever defending why the partial-edit is a safe narrowing rather than requiring supersession of `documentation-gate.md` itself to `documentation-gate-r2.md`.

The ADR for this decision doesn't exist. The atomic-commit invariant papers over the question without answering it.

---

## Finding 5 — MEDIUM: `--on-conflict=append` semantics in the pseudocode preserve user content in the wrong order

**Severity: Medium**

The append logic in the Design pseudocode:

```python
if on_conflict == "append":
    # ... existing append logic (preserve user content)
```

This defers to "existing append logic." Looking at the actual implementation in `cli/install_hooks.py:63-73`:

```python
if choice == "a":
    existing_no_shebang = existing
    if existing.startswith("#!"):
        existing_no_shebang = "\n".join(existing.split("\n")[1:])
    new_content = (expected_content.rstrip() +
                   "\n\n# Original hook content (preserved):\n" +
                   existing_no_shebang)
```

The orchestra hook comes FIRST, then the existing user hook is appended after a `# Original hook content (preserved):` comment. This ordering makes the orchestra hook the primary hook and silently demotes the user's existing hook. For a pre-commit framework user (LLD-010 context), if the user's existing hook is the framework's `pre-commit hook-impl` invocation, appending orchestra's raw `cli.lint --pre-commit` call BEFORE the framework call means: the framework hook still runs (it's after orchestra), but the framework's own lint checks run in a second pass after orchestra's. Worse: if the framework's hook is a commit-msg hook that sets `$MSG_FILE` via args and orchestra's hook runs `$1` — the `$1` in orchestra's template references the commit-msg file, but because `set -euo pipefail` is set and `$1` is missing when the hook fires standalone, this would fail. These cross-mode ordering hazards for the append case are unaddressed.

The LLD says LLD-010 handles framework detection, but LLD-008 ships `--on-conflict=append` and the implementation-level ordering semantics affect the framework case too.

---

## Finding 6 — MEDIUM: `references/` governance introduces a `Status: Current` on skill-internal files that collides with `CANON_FROZEN_STATUSES`

**Severity: Medium**

Design § `references/` governance: "Each reference file has metadata block: `Doc ID`, `Date`, `Status` (skill-internal enum: `Current` / `Deprecated`), `Skill version`."

`"Current"` appears in `CANON_FROZEN_STATUSES` at `cli/lint.py:71-73`. These files live under `skills/commit/references/`, which is NOT under `REFS_ELIGIBLE_PREFIXES` (`docs/{features,bugs,...}`), so L2 will not fire on them. That part is correct.

However, `cli.lint --doc <path>` can be invoked on any path. If a developer or CI pipeline runs `python -m cli.lint --doc skills/commit/references/canon-frozen-guard.md`, `detect_doc_type()` (lint.py:154-168) will return `None` (no `features/bugs/adr/...` in the path) and emit a warning, not an error. That's benign. But if someone adds `skills/` to `REFS_ELIGIBLE_PREFIXES` later (a plausible future extension), the skill-internal `Status: Current` files would immediately become canon-frozen under L2 and block their own updates.

More concretely: the LLD defines two parallel governance systems with the same Status vocabulary. Future maintainers will be confused about which governance applies to a `Status: Current` file. The LLD should explicitly state that skill-internal `Status` is NOT the same enum as doc-lifecycle `Status`, and that the metadata block on reference files intentionally uses a subset of the same tokens for different semantics. This is a documentation debt that will cause errors.

---

## Finding 7 — LOW: Test T6 (SCALE migration assertions) runs in SCALE repo but no CI path is defined for cross-repo tests

**Severity: Low**

A10 says T6 is "SCALE migration: 2 absent files, doc-gate.md retains Gates 1-3 sections + skill pointer for Gates 4+5, registry entry present" and the test matrix notes "Tests T6 (post-migration SCALE state assertions; runs in SCALE repo)."

There is no description of HOW T6 runs against the SCALE repo during orchestra's CI pipeline. Orchestra's pytest suite runs in the orchestra repo. The SCALE repo is a consumer. If T6 is an orchestra test that imports from SCALE's filesystem, it depends on SCALE being at a known path relative to orchestra — a brittle coupling. If T6 is a SCALE-side test, it needs to be shipped to SCALE as part of the migration commit, but the migration deliverable list (A8) doesn't mention any test files.

The LLD counts T6 toward the `150 + 11 = 161` pytest target, implying it runs in orchestra's test suite. But it asserts state in the SCALE repo. This is an unresolved test architecture question. If T6 is skipped when SCALE is not found, the test count math is wrong and A10's assertion of 161 minimum is not guaranteed.

---

## Finding 8 — LOW: LLD-009 A13 references `pre-commit.sh` template as "unchanged from LLD-008 ship" but LLD-008's template is not yet canonically defined

**Severity: Low**

LLD-009 A13 / T13: "pre-commit.sh template unchanged from LLD-008 ship." LLD-008 A2 says the template is "moved from cli/templates/" — it's a relocation, not a new file. The content is whatever is currently in `cli/templates/pre-commit.sh`.

Cross-checking against the LLD-009 spec: LLD-009 A1 modifies `cli.lint --pre-commit` to add L2-detect (the pending-file write). This is a Python-side change, not a shell template change — the template still runs `python -m cli.lint --pre-commit` and the new behaviour is inside that call. So T13's assertion that "the shell template is unchanged" is testable and probably true. But LLD-008 does not include the actual content of the template being relocated, so there is no canonical reference for LLD-009 T13 to diff against. If the relocation involves any content change (e.g., adding the `# orchestra` fingerprint header that LLD-010's `--verify` check depends on), LLD-009 T13 would fail silently.

This is a latent consistency risk between LLD-008 (ships template) and LLD-010 (verifies fingerprint in first 5 lines of template). LLD-008 must explicitly state whether the relocated template includes `# orchestra` in its header. Currently it does not.

---

## Finding 9 — LOW: `cli.init` bootstrap integration is non-reversible and lacks a `--no-hooks` escape hatch

**Severity: Low**

A6 adds `cli.install_hooks.main(["--pre-commit", "--commit-msg", "--on-conflict=skip"])` unconditionally to the end of `cli.init.main()`. `--on-conflict=skip` means if hooks already exist, they are left alone — idempotent, non-destructive. Fine.

But `cli.init --force` (which already exists in `cli/init.py:356`) will run the hook bootstrap unconditionally too, since `--on-conflict=skip` is hardcoded in the bootstrap call regardless of whether `--force` was passed to init. An operator running `cli.init --force` to reset scaffold files expects `--force` semantics on ALL init operations; getting `--on-conflict=skip` hook behavior while `--force` overwrites docs is inconsistent.

There is also no `--no-hooks` flag on `cli.init` to suppress the bootstrap for environments where hooks are undesirable (e.g., ephemeral CI that runs `cli.init` to set up a test scaffold but does not want hooks installed). The current design of `--on-conflict=skip` makes this mostly harmless, but the absence of an escape hatch is a design completeness gap.

---

## Cross-LLD Consistency Findings

**LLD-008 / LLD-009 boundary — commit-msg.sh ownership:**
LLD-008 A2 ships `skills/commit/templates/commit-msg.sh` (moved from `cli/templates/`). LLD-009 A12 updates `commit-msg.sh` to add the `--commit-msg-finalize "$1"` call. Both LLDs claim to define the content of this file. Since they ship together as v1.7.0, the final state is deterministic — but the intermediate state (LLD-008 merged, LLD-009 not yet merged) would leave a `commit-msg.sh` that runs only the Refs:-line check without L2-finalize. No doc says this intermediate state is acceptable. If the three LLDs are merged in order, commit-discipline has a regression window.

**LLD-008 / LLD-010 boundary — `SKILL_TEMPLATES_DIR` constant:**
As noted in Finding 3, LLD-010 pseudocode assumes a `SKILL_TEMPLATES_DIR` constant defined in LLD-008. LLD-008 never names it. This is a contract gap between two co-dependent specs.

**LLD-010 `--apply` writes YAML via `yaml.safe_dump` which strips comments:**
This is acknowledged as a documented limitation in LLD-010 § Out-of-Scope. The cross-LLD gap is that LLD-008's `cli.init` bootstrap uses `--on-conflict=skip` which means framework users who ran `--apply` and then re-run `cli.init` will get skip behavior (hooks already there). But if the framework user's config had comments stripped by the prior `--apply`, and they re-run `--apply` manually, they lose comments again. Not a LLD-008 defect per se, but the compounding effect across the three LLDs is nowhere documented as a known user-visible degradation.

---

## Verdict: **needs-attention**

The narrowed scope is much cleaner than r2. The split into three LLDs was the right call. The core design — skill structure, references governance, migration invariant — is architecturally sound. However, Finding 1 (argparse sentinel defect) and Finding 2 (T5 test coverage gap for argparse error vs. clean exit) are implementation-time traps that the narrowed spec still ships into production. Finding 3 (undefined `SKILL_TEMPLATES_DIR` constant needed by LLD-010) is a cross-LLD contract gap that must be closed before implementation starts on LLD-010. These three findings together are sufficient to block implementation approval.

The medium-severity findings (4, 5, 6) are design debt that will create confusion or bugs under specific conditions; they should be addressed in-place (LLD-008 is still Draft) rather than deferred. The low-severity findings (7, 8, 9) can be addressed as DEVIATION entries or follow-up items if implementation reveals them to be non-issues in practice.

Recommended: fix Finding 1 (use `default=None` sentinel, specify interaction with `--force`), Finding 2 (T5c explicitly asserts non-zero exit for wrong reason vs. zero exit for right reason), and Finding 3 (name the `SKILL_TEMPLATES_DIR` constant in LLD-008 A4) before progressing to implementation.