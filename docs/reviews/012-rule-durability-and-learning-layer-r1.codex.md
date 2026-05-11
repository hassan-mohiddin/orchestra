# Codex Adversarial Review — LLD-012 r1

> **Date:** 2026-05-11
> **Reviewer:** codex:adversarial-review (gpt-5-codex)
> **Doc subject:** docs/features/012-rule-durability-and-learning-layer.md
> **Iteration:** 1

Target: working tree diff
Verdict: needs-attention

No-ship: the new durability/learning design contains a core non-executable gate plus fail-open trust-boundary paths that can silently disable or subvert the control layer.

## Findings

- **[critical]** Auto-promotion requires a review path that cannot execute on the targeted files (docs/features/012-rule-durability-and-learning-layer.md:43-44)
  SC-8 requires drafting TLDR mutations for rule files and invoking spec review on those mutations, but the target artifacts are `.claude/*` rule files, not docs. Inference from current code: `cli.spec_review` canonicalizes inputs to `<repo_root>/docs/` only, so this path will reject `.claude/rules/*.md` as out-of-scope. That makes the promoted-review gate non-functional for the exact files this LLD wants to mutate, forcing either manual bypasses or dead-end automation.
  Recommendation: Before shipping, define and implement one executable review path for schema-layer files: either extend `cli.spec_review` to allow vetted `.claude/*` targets, or route promotions through a docs-scoped review artifact with deterministic mapping and provenance.

- **[high]** Untrusted repo content is elevated into system-priority prompt context (docs/features/012-rule-durability-and-learning-layer.md:199)
  The design reads lessons from git-backed files and injects them into `<system-reminder>` additional context each session. Sanitization only addresses reminder tag delimiters, not instruction payload semantics. This creates a trust-boundary break: crafted lesson text committed through normal repo workflows can become persistent system-priority steering across sessions.
  Recommendation: Treat lessons as untrusted input. Inject only strict structured summaries (allowlisted fields/format), block free-text directives from system-reminder injection, and require explicit maintainer approval/signature before any lesson-derived content is promoted into system context.

- **[high]** Hook layer is designed to fail open on environment mismatch (docs/features/012-rule-durability-and-learning-layer.md:305)
  Hooks are hardcoded to `.venv/bin/python` and the edge-case policy explicitly no-ops with exit 0 when that runtime is missing. On any host without that exact path/layout, protections silently disappear while sessions proceed as if guardrails exist. This is a high-cost observability gap for a control-plane feature.
  Recommendation: Use a portable interpreter resolution strategy (`sys.executable` or validated launcher), and make hook verification fail loudly (including CI) when required hooks are not executable. Do not silently succeed when the control layer is disabled.

- **[medium]** New tests codify permissive malformed-schema handling without a fail-closed overwrite guard (tests/test_schema_v1_read_only.py:47-53)
  The new compatibility tests assert malformed attestation YAML returns `None` and add no regression case for a malformed existing v1 attestation on overwrite attempts. Inference from current overwrite flow: treating malformed as unknown can permit bypass of v1 freeze protections under force paths unless explicitly blocked elsewhere.
  Recommendation: Add a regression test that seeds a malformed existing v1 attestation at the computed output path and asserts force-mode refusal plus no file mutation; then make overwrite logic fail closed on unreadable existing attestations.

## Next steps

- Resolve the spec-review scope mismatch for `.claude/*` artifacts before implementing SC-8 automation.
- Redesign lesson injection so untrusted free text never enters system-priority reminders directly.
- Convert hook runtime detection from silent no-op to explicit verification failure when protections are inactive.

## Resolution status (post-r1 author edits)

| # | Finding | Resolution in r1 |
|---|---|---|
| 1 | Spec-review scope mismatch | RESOLVED via proxy artifact in `docs/proposed-rule-mutations/` (Option A) |
| 2 | Untrusted lesson injection | RESOLVED via structured-fields-only injection; free-text `teach` never reaches `<system-reminder>` (Option A) |
| 3 | Hook fail-open | RESOLVED via `sys.executable` resolution at install + fail-loud at runtime + `--verify` CI gate (Option A) |
| 4 | Malformed-schema overwrite | RESOLVED via fail-closed regression test (Option A) |
