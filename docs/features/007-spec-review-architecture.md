# Feature: orchestra v1.6 — Spec-Review Architecture (Multi-Judge, Manual Chair) (LLD-007)

> **Doc ID:** 007-spec-review-architecture
> **Date:** 2026-05-10
> **DRI:** Hassan Mohiddin
> **Type:** Feature LLD
> **Status:** Implemented
> **Iteration:** 5

## Bootstrap Note

This LLD defines the spec-review skill that orchestra will USE to review docs going forward. This doc itself is reviewed via the OLD ad-hoc process (manual extra-careful read by author + user + fresh subagent dispatch with author-applied fixes inline). Future docs use the NEW skill once shipped. The bootstrap paradox is acknowledged and accepted: we cannot use a tool to evaluate the tool itself before the tool exists.

## Glossary (single source of truth)

- **judge** — an agent invocation that produces a 4-gate verdict + findings list against a target doc. Judge-1 is orchestra default; judges 2-N are user-registered alternates (codex adversarial-review, cavecrew-reviewer, superpowers requesting-code-review, etc.).
- **judge-1** — orchestra:spec-review skill. Always present. Default invocation. Built and shipped in this LLD.
- **judges 2-N** — external skills/plugins the user invokes manually. orchestra:spec-review does NOT invoke them. User reads each judge's output and decides verdict (manual chair).
- **manual chair** — the user. Reads outputs from all invoked judges. Decides whether the doc passes or needs another iteration. orchestra ships no auto-aggregation logic in v1.6.
- **attestation** — YAML file at `docs/reviews/<doc-id>-rN.review.yaml` recording one judge's verdict on a doc at a specific iteration. Schema v1.0 (formalized in this LLD).
- **fresh subagent** — `Task` tool dispatch with `subagent_type: general-purpose`, isolated context (no main-thread history), input = doc path + 4-gate rubric + attestation schema only.
- **4-gate rubric** — Completeness / Evidence / Clarity / Consistency. Per-gate verdict ∈ {pass, conditional_pass, fail}. Overall verdict = worst-case across gates.
- **iteration** — one round of (write/edit doc → invoke judges → read findings → fix). Max 3 iterations per documentation-gate convention; iteration 4+ surfaces interview-gate. Corresponds 1:1 to the `Iteration: N` field in the doc metadata block — author bumps the field before each new round; skill reads it to populate `iteration` field in attestation YAML.
- **canon-frozen** (from LLD-006-r4 Glossary) — Status ∈ `{Approved, Implemented, Verified, Fix Applied, Current}`. Spec-review enables canon-frozen transition; without passing review, doc stays Draft.
- **bootstrap paradox** — the meta-condition where this LLD defines the tool used to evaluate this LLD. Resolution: extra-careful manual review on this doc one last time; future docs use the skill.

## Problem Statement

orchestra v1.0–1.5 has no formalized spec-review skill. Three concrete defects observed:

1. **Ad-hoc invocation.** Each doc review is hand-rolled: I (the author agent) prompt a subagent with whatever criteria fit my mental model that day. Output format varies. No schema validation. v1.5.0 dogfood: 5 attestations exist but were authored manually with inconsistent rigor.
2. **Single-judge default = same-model self-preference bias.** Opus-author + Opus-judge systematically under-flags Opus-written docs (arXiv 2410.21819, https://arxiv.org/abs/2410.21819). LLD-005 r1 + r2 + LLD-006 r1+r2+r3 all FAILED — but the failure rate was likely under-counting findings. Multi-judge primitive needed; user constraint locked: orchestra ships judge-1 default; user manually invokes judges 2-N.
3. **No bias mitigations encoded.** Position bias (orderings of findings affect verdict), self-preference (judge agent reviews its own work), length bias (long docs get over-flagged or under-flagged depending on prompt), hallucinated findings (observed in this session's LLD-005/006/007 review series: codex-round attestations recorded multiple cases where draft text cited papers/sections that did not exist or had been renamed — the v1.6.1 dogfood r4 attestation itself flagged a similar fabricated-citation candidate in this LLD's prior text). Without explicit mitigations + schema enforcement, judge output quality degrades.

These defects make the spec-review process — orchestra's PRIMARY discriminator gate — itself unverifiable. Per user direction: build the discriminator before the generator (LLD-011+ workflow). v1.6 ships this LLD's implementation.

## Success Criteria

### Acceptance items (testable; each maps 1:1 to a test in Testing §)

- [ ] **A1.** New skill `orchestra:spec-review` registered (skills/spec-review/SKILL.md) — manual verification post-merge. **Checkoff process** (v1.6.1 finding #2): post-merge, list `skills/` dir; confirm `spec-review/` present with SKILL.md + prompt-template.md + attestation-schema-v1.0.json + references/4-gate-rubric.md. Tick A1 when all 4 files present. No automated test (skill registration is plugin-runtime; tested indirectly via T2/T3).
- [ ] **A2.** Slash command `/orchestra:spec-review <doc-path>` invocable; no positional args other than path → test T1
- [ ] **A3.** Skill body (skills/spec-review/SKILL.md) prose specifies dispatch via Claude Code Task tool with `subagent_type: general-purpose` and inlines doc text + 4-gate rubric + attestation schema into prompt. Runtime Task kwargs verification deferred to manual dogfood (D4 deliverable: run `/orchestra:spec-review` against this LLD post-merge and inspect Task call) — codex-r2 F7 honest narrowing → test T2 (structural prose check)
- [ ] **A4.** Subagent prompt contains all 7 adversarial-prompt elements (role anchor, scope fence, 4-gate rubric, anti-sycophancy, anti-pedantry, forced YAML schema, minimum-issue framing) → test T3
- [ ] **A5.** Subagent output validated against attestation schema v1.0; **single attempt** (v1.6.1 finding #5: stdin-bound dispatch makes in-Python retry meaningless — second `sys.stdin.read()` returns empty). Schema-fail → exit 1 with explicit `schema_validation_failed` error message; user re-invokes `/orchestra:spec-review` for fresh subagent dispatch → tests T4 (valid output written), T5 (single-attempt fail), T6 (schema-fail surfaces explicit error)
- [ ] **A6.** Attestation written to `docs/reviews/<doc-id>-rN.review.yaml` (path derived from doc filename + iteration); existing file overwritten on re-run with NEW iteration index → tests T7, T8
- [ ] **A7.** YAML schema validation rejects: missing required fields, unknown gate names, severity not in {Critical, Important, Minor}, overall_verdict not in {pass, conditional_pass, fail} → tests T9, T10, T11, T12
- [ ] **A8.** Bias mitigations: (a) finding order ordered-by-location instructed in subagent prompt template (testable via prompt-render assertion); (b) judge-id field in attestation prevents same-judge re-invocation on same doc-iteration without explicit `--force` flag (code-enforced); (c) max output token cap of 4000 documented in SKILL.md prose for agent-layer Task dispatch — runtime kwarg verification deferred to manual dogfood (D4) since dispatch happens at agent layer, NOT in `cli.spec_review` Python (codex-r3 F10 honest narrowing) → tests T13a (prompt prose contains ordering instruction), T13b (judge-id duplicate check), T13c (SKILL.md prose contains `max_tokens: 4000`)
- [ ] **A9.** Each finding has `location` field referencing `<section> § <subsection>` or `line N`; lint-time check that location syntax matches regex → test T14
- [ ] **A10.** Schema v1.0 stable: skill emits `schema_version: "1.0"`; reading code accepts only "1.0" → test T15
- [ ] **A11.** Iteration counter: skill reads `Iteration:` field from doc frontmatter; emits matching `iteration` field in attestation. Mismatch → exit 1 → test T16
- [ ] **A12.** Multi-judge: skill outputs ONE attestation per invocation. orchestra ships no auto-invocation of other judges. STANDARDS doc lists how user manually invokes judges 2-N (codex, cavecrew, etc.) — manual verification post-merge. **Checkoff process** (v1.6.1 finding #2): post-merge, grep `cli/templates/standards-default-7.md` for `/codex:adversarial-review` + `/caveman:cavecrew-reviewer` + `/superpowers:requesting-code-review` mentions in § Spec Review Rule. Tick A12 when all 3 judges-2-N references present.
- [ ] **A13.** Plugin version: 1.5.1 → 1.6.0
- [ ] **A14.** Pytest baseline: 107 → ≥140. v1.6.1 reconcile (finding #7): the Testing § matrix enumerates 33 acceptance-row test IDs (T1-T26 with splits). Implementation actually adds 37 spec-review test functions across 11 files (matrix-row tests + 4 helper assertions: `compute_overall_verdict_worst_case`, `parse_iteration_default_is_1`, `parse_iteration_from_metadata`, `test_doc_disappeared_between_dispatch_and_write` v1.6.1 patch). 107 + 37 = 144 actual at v1.6.1. Plan target stays ≥140 (semantic check via REQUIRED_TESTS array of 33 matrix IDs in Task 7 — helpers are bonus coverage, not gated).
- [ ] **A15.** Eval: 11 → 12 scenarios (1 new: `spec-review-yaml-schema-roundtrip`)
- [ ] **A16.** Path canonicalization (codex-r1 F1): non-`docs/` paths, absolute paths, `..` escapes, symlink escapes all rejected with `path_traversal_blocked` error → tests T17a (absolute), T17b (`..` escape), T17c (symlink escape)
- [ ] **A17.** Verdict authoritative-compute (codex-r1 F2): `cli.spec_review` computes overall_verdict from gates worst-case; subagent value mismatch → `verdict_mismatch` exit 1 → test T18
- [ ] **A18.** Empty-findings justification (codex-r1 F3): JSON-schema requires `justification` (min 10 chars) when `findings: []`; missing or short → schema-fail → tests T19a (missing), T19b (too short)
- [ ] **A19.** Path identity binding (codex-r1 F4): subagent-claimed `doc_subject.path` must equal canonical input path; mismatch → `path_mismatch` exit 1 → test T20
- [ ] **A20.** Canonicalization fail-closed for resolve errors (codex-r2 F5): `FileNotFoundError`/`OSError` from `resolve(strict=True)` mapped to `path_traversal_blocked` exit 2 (not Python crash) → tests T21a (missing file), T21b (broken symlink)
- [ ] **A21.** Stale-state hash gate (codex-r2 F6): hash captured at dispatch; doc bytes changed between dispatch + write → `stale_state` exit 1 (was silent overwrite) → test T22
- [ ] **A22.** Single-snapshot semantics (codex-r3 F8): doc bytes read ONCE; hash, iteration, and prompt rendering all derive from the same snapshot. Eliminates TOCTOU between multi-reads → test T23
- [ ] **A23.** Repo-anchored attestation path (codex-r3 F9): `compute_attestation_path` result is joined with `repo_root` BEFORE existence check + write. Cwd-independent → test T24
- [ ] **A24.** Atomic-write contract (codex-r3-plan PF10): skill emits exactly ONE attestation YAML per successful invocation via atomic-replace pattern. Implementation: write to `<out_path>.tmp.<pid>` in same directory as out_path → fsync the temp file → `os.replace()` to atomically rename to out_path → on any exception, unlink temp file and exit non-zero. Covers both pre-write failures (schema-fail post-retry, hash mismatch, path mismatch, verdict mismatch) AND write-path failures (ENOSPC, I/O exception, signal mid-write). NO partial files at out_path under any failure mode → tests T25 (pre-write fail), T25b (write-path fault injection)
- [ ] **A25.** Plans are valid attestation targets: `doc_subject.path` schema regex includes `docs/plans/...`; plans get reviewed with same 4-gate rubric + attestation YAML pattern → test T26 + lint update (Task 6 meta extension to ALLOWED_ATTESTATION_PATH_PREFIXES)

### Deliverables (recorded for sign-off, not lint-checkable)

- [ ] D1. `docs/design/orchestra-philosophy.md` Changelog appended with v1.6 entry (narrow change)
- [ ] D2. README.md mentions `/orchestra:spec-review` slash command
- [ ] D3. `cli/templates/standards-default-7.md` references the new skill in § Spec Review Rule
- [ ] D4. Bootstrap paradox: this LLD-007 itself reviewed via OLD ad-hoc process (fresh subagent + author-applied fixes inline). Per LLD-006-r4 precedent.

## Scope

### In Scope (v1.6 ships exactly this)

1. **`orchestra:spec-review` skill** — judge-1 implementation. Skill body: prompt template + dispatch logic. Sidecar Python module `cli.spec_review` for: Task-tool dispatch invocation, YAML schema validation, attestation file write.
2. **Slash command** `/orchestra:spec-review <doc-path>` — single arg (doc path). Skill resolves invocation from registered slash-command file `commands/spec-review.md`.
3. **Attestation YAML schema v1.0** — formalized JSON-schema (validated via PyYAML + jsonschema lib).
4. **4-gate rubric prompt** — embedded in skill; references `references/spec-review-gates.md` (already in orchestra:design-docs skill).
5. **7-element adversarial prompt** — formal template in `skills/spec-review/prompt-template.md`.
6. **Bias mitigations** — randomized finding order, judge-id duplicate-detection, output token cap.
7. **Iteration handling** — read `Iteration:` from doc frontmatter (orchestra metadata block format), emit matching iteration in attestation. Skill itself does NOT increment; that's the doc author's job.
8. **No auto-invocation of other judges.** User manually runs `/codex:adversarial-review`, `/caveman:cavecrew-reviewer` etc. as separate invocations. orchestra leaves consensus to user.

### Out of Scope (deferred)

- **Auto-aggregation of multi-judge verdicts** (v1.6.x patch or v1.7+) — once we have data on judge agreement patterns, we'll know which aggregation rule works
- **Auto-firing from workflow Gate 3** — workflow LLD-011+ wires this in
- **Auto-firing from PreToolUse hook on doc commit** — needs hook architecture not built
- **Drift detection** (attestation vs current doc state) — v1.6.x
- **Hallucination auto-verification** (each finding's location verified to exist in doc) — v1.6.x; for v1.6, schema-enforced location format only
- **Configurable judge model** (`--judge-model sonnet`) — Task tool doesn't expose model selection per-call; defer until SDK supports
- **Memory architecture (LLD-008)** — separate; orthogonal
- **Backward-flow workflow primitives** — LLD-011+
- **Lessons-capture** (LLD-009) — separate
- **Skills registry auto-population** (LLD-010) — separate

## Design

### Decision: invocation pattern (committed; no alternatives)

User invokes `/orchestra:spec-review <doc-path>` slash command. Skill body parses arg, dispatches subagent, validates output, writes attestation. Returns exit 0 on pass, exit 1 on fail.

Single mechanism. No "alternatively." (P3 checklist.)

### Decision: subagent dispatch (committed; no alternatives)

Skill uses Claude Code's `Task` tool with `subagent_type: general-purpose`. Subagent receives a constructed prompt (the 7-element adversarial template with doc text inlined). Subagent has no main-thread history. Fresh-context isolation guaranteed by Task-tool semantics.

Skill does NOT register a custom subagent type (e.g., `orchestra:reviewer`). Reasoning: custom-subagent registration requires plugin-agent-definition format orchestra doesn't yet expose; using `general-purpose` subagent ships with existing infrastructure.

### Decision: schema v1.0 stable (committed)

Schema version stable at "1.0". Future schema bumps require new skill version + migration logic. v1.6 ships only "1.0".

### Skill body structure

```
skills/spec-review/
├── SKILL.md                        # Frontmatter + skill prose + invocation guidance
├── prompt-template.md              # The 7-element adversarial prompt (rendered with doc text + schema)
├── attestation-schema-v1.0.json    # JSON-schema for YAML validation
└── references/
    └── 4-gate-rubric.md            # Detailed pass/fail criteria per gate
```

Sidecar Python module:

```
cli/
├── spec_review.py                   # Dispatch + validation + write logic
└── templates/
    └── attestation-template.yaml    # Empty template for testing
```

Slash command:

```
commands/
└── spec-review.md                   # Slash command definition pointing at the skill
```

### 7-element adversarial prompt (skills/spec-review/prompt-template.md)

```markdown
# orchestra Spec Review — Judge 1

You are an adversarial spec reviewer. Your job: find problems in the doc below.

## SCOPE FENCE

Review THIS DOC ONLY. Do not flag broader-system issues. Do not propose new
features. Do not refactor scope.

## 4-GATE RUBRIC (verdict per gate ∈ {pass, conditional_pass, fail})

1. **Completeness** — Required sections (per `references/4-gate-rubric.md` for
   the doc type) present and filled. No empty placeholders.
2. **Evidence** — Every claim has file:line citation, benchmark URL, or
   external research link. No "should work" / "we believe."
3. **Clarity** — A fresh reader (no session history, no author DM access) can
   act on this doc. Glossary defines ambiguous terms.
4. **Consistency** — Doc agrees with itself, with peer docs in `docs/`, and
   with code. Cross-reference verified for the docs cited.

## ANTI-SYCOPHANCY

If you produce ZERO findings on any gate, you MUST justify in the attestation
`gates.<gate>.justification` field. Praise is forbidden; only justifications.

## ANTI-PEDANTRY

Skip taste-level issues unless they change meaning. No formatting nits, no
"could be more concise," no "consider using X instead of Y" without a
correctness reason.

## OUTPUT FORMAT (forced YAML schema v1.0)

Output ONE YAML document matching the schema below. No prose, no code blocks,
no commentary. Output starts at `schema_version:` and ends at the last YAML key.

```
schema_version: "1.0"
doc_subject:
  path: <repo-relative path>
  content_hash: sha256:<hash of doc bytes>
  iteration: <integer matching doc Iteration: field>
reviewer:
  identifier: "subagent:general-purpose+spec-review-v1"
  invoked_at: <ISO-8601 UTC timestamp>
  context_isolation: fresh_subagent
gates:
  completeness:
    verdict: pass | conditional_pass | fail
    findings:
      - severity: Critical | Important | Minor
        location: <section § subsection> or <line N>
        problem: <one-line problem statement>
    justification: <required if findings = []>
  evidence:
    verdict: ...
    findings: [...]
    justification: ...
  clarity: ...
  consistency: ...
overall_verdict: pass | conditional_pass | fail
required_followup: [<list of v1.6+ followup items>]  # optional
notes: |   # optional, free-form
  ...
```

## SEVERITY ENUM (only these three; no Info)

- **Critical** — fact wrong, contract broken, security gap, doc would mislead
  any reader following it
- **Important** — omission, ambiguity, or stale reference that a reader could
  reasonably misinterpret
- **Minor** — small inconsistency, missing detail, or undocumented edge case

## MINIMUM-ISSUE FRAMING

Typical reviews find 2-5 issues per gate. ZERO findings on multiple gates is
suspicious. If you produce zero findings overall, justify in `notes` field.

## BIAS MITIGATIONS

- Order findings within each gate by location (top-of-doc first), NOT by
  severity. Position bias is a known judge-output flaw.
- Each finding cites `location` matching `^(.+\\s+§\\s+.+|line\\s+\\d+)$`.
  Findings without parsable location are auto-rejected.

## DOC TO REVIEW

<doc text inlined here at dispatch time>

## END OF PROMPT

Output the YAML now. No preamble, no acknowledgment, no commentary outside the
YAML document itself.
```

### Attestation schema v1.0 (skills/spec-review/attestation-schema-v1.0.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "orchestra Spec Review Attestation v1.0",
  "type": "object",
  "required": ["schema_version", "doc_subject", "reviewer", "gates", "overall_verdict"],
  "additionalProperties": false,
  "properties": {
    "schema_version": {"const": "1.0"},
    "doc_subject": {
      "type": "object",
      "required": ["path", "content_hash", "iteration"],
      "additionalProperties": false,
      "properties": {
        "path": {"type": "string", "pattern": "^docs/(features|bugs|adr|design|postmortems|runbooks|plans|archive/[a-z]+)/.+\\.md$"},
        "content_hash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        "iteration": {"type": "integer", "minimum": 1}
      }
    },
    "reviewer": {
      "type": "object",
      "required": ["identifier", "invoked_at", "context_isolation"],
      "additionalProperties": false,
      "properties": {
        "identifier": {"type": "string"},
        "invoked_at": {"type": "string", "format": "date-time"},
        "context_isolation": {"const": "fresh_subagent"}
      }
    },
    "gates": {
      "type": "object",
      "required": ["completeness", "evidence", "clarity", "consistency"],
      "additionalProperties": false,
      "properties": {
        "completeness": {"$ref": "#/definitions/gate"},
        "evidence": {"$ref": "#/definitions/gate"},
        "clarity": {"$ref": "#/definitions/gate"},
        "consistency": {"$ref": "#/definitions/gate"}
      }
    },
    "overall_verdict": {"enum": ["pass", "conditional_pass", "fail"]},
    "required_followup": {"type": "array", "items": {"type": "string"}},
    "notes": {"type": "string"}
  },
  "definitions": {
    "gate": {
      "type": "object",
      "required": ["verdict", "findings"],
      "additionalProperties": false,
      "properties": {
        "verdict": {"enum": ["pass", "conditional_pass", "fail"]},
        "findings": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["severity", "location", "problem"],
            "additionalProperties": false,
            "properties": {
              "severity": {"enum": ["Critical", "Important", "Minor"]},
              "location": {"type": "string", "pattern": "^(.+\\s+§\\s+.+|line\\s+\\d+)$"},
              "problem": {"type": "string", "minLength": 1, "maxLength": 500}
            }
          }
        },
        "justification": {"type": "string", "minLength": 10}
      },
      "if": {
        "properties": {"findings": {"maxItems": 0}}
      },
      "then": {
        "required": ["verdict", "findings", "justification"]
      }
    }
  }
}
```

### cli.spec_review module (sidecar Python)

```python
"""orchestra spec-review skill sidecar — Task-tool dispatch + schema validation."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent / "skills" / "spec-review" / "attestation-schema-v1.0.json"
PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent / "skills" / "spec-review" / "prompt-template.md"
MAX_RETRIES = 0                           # v1.6.1: stdin-bound dispatch has no useful retry
SUBAGENT_OUTPUT_TOKEN_CAP = 4000          # bias mitigation (length cap)


VERDICT_RANK = {"pass": 0, "conditional_pass": 1, "fail": 2}


class _NoTimestampLoader(yaml.SafeLoader):
    """SafeLoader without implicit timestamp resolution (v1.6.0 design).

    Keeps `invoked_at: 2026-05-10T00:00:00Z` as string for schema validation.
    json-schema `format: date-time` checks string format, not datetime objects.
    """


_NoTimestampLoader.yaml_implicit_resolvers = {
    k: [(tag, regexp) for tag, regexp in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra:spec-review")
    parser.add_argument("doc_path", help="Repo-relative path to doc to review")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing attestation for same iteration")
    args = parser.parse_args(argv)

    repo_root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True).strip())

    # F1 + F5: fail-closed path canonicalization (codex-r1 F1, codex-r2 F5)
    # Catch ValueError (logical reject), FileNotFoundError/OSError (resolve failures
    # on missing/inaccessible/broken-symlink). All map to single error code.
    try:
        canonical_path = canonicalize_doc_path(args.doc_path, repo_root)
    except (ValueError, FileNotFoundError, OSError) as e:
        print(f"error: path_traversal_blocked: {e}", file=sys.stderr)
        return 2

    # F6 + F8: single immutable snapshot (codex-r2 F6 + codex-r3 F8 TOCTOU fix).
    # Read doc bytes ONCE; derive hash, iteration, prompt all from same snapshot.
    # Eliminates concurrent-edit race where multiple reads see different content.
    doc_bytes = canonical_path.read_bytes()
    doc_text = doc_bytes.decode("utf-8")
    pre_dispatch_hash = "sha256:" + hashlib.sha256(doc_bytes).hexdigest()
    iteration = parse_iteration_from_text(doc_text)

    # F9: anchor attestation path to repo_root (codex-r3 finding).
    # compute_attestation_path returns repo-relative; we anchor it before any
    # filesystem operation to prevent cwd-dependent misplacement.
    out_path = repo_root / compute_attestation_path(canonical_path, iteration)
    if out_path.exists() and not args.force:
        print(f"error: {out_path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    schema = json.loads(SCHEMA_PATH.read_text())
    prompt = render_prompt_from_text(doc_text, schema)

    # v1.6.1: single attempt — stdin-bound dispatch makes in-Python retry
    # meaningless (second sys.stdin.read() returns empty). User re-invokes
    # /orchestra:spec-review for fresh subagent dispatch on schema-fail.
    yaml_text = dispatch_subagent(prompt)  # uses Task tool under the hood
    try:
        # Custom loader: SafeLoader minus implicit timestamp resolver. Keeps
        # `invoked_at: 2026-...Z` as string for json-schema `format: date-time`
        # validation. PyYAML default coerces ISO timestamps to datetime objects
        # which fail string-typed schema rules.
        attestation = yaml.load(yaml_text, Loader=_NoTimestampLoader)
        jsonschema.validate(attestation, schema)
    except (yaml.YAMLError, jsonschema.ValidationError, TypeError) as e:
        # TypeError: jsonschema raises this when given non-dict input
        # (e.g., bare string when subagent returned plain text)
        print(
            f"error: schema_validation_failed: {e}. "
            f"Re-invoke /orchestra:spec-review for fresh dispatch.",
            file=sys.stderr,
        )
        return 1

    # Author iteration check (existing)
    if attestation["doc_subject"]["iteration"] != iteration:
        print(f"error: iteration_mismatch: attestation iteration "
              f"{attestation['doc_subject']['iteration']} ≠ doc Iteration: {iteration}",
              file=sys.stderr)
        return 1

    # F4: hard-fail on path mismatch (codex-r1 finding)
    canonical_relpath = str(canonical_path.relative_to(repo_root))
    if attestation["doc_subject"]["path"] != canonical_relpath:
        print(f"error: path_mismatch: attestation path "
              f"{attestation['doc_subject']['path']!r} ≠ canonical input "
              f"{canonical_relpath!r}", file=sys.stderr)
        return 1

    # F6 + F8: stale-state hash check against single snapshot (codex-r2 F6 + codex-r3 F8).
    # v1.6.1: try/except around read_bytes covers doc_disappeared case
    # (file moved/deleted between dispatch and write). Without this guard,
    # FileNotFoundError crashes Python.
    try:
        write_time_bytes = canonical_path.read_bytes()
    except (FileNotFoundError, OSError) as e:
        print(
            f"error: doc_disappeared: doc removed/inaccessible between dispatch "
            f"and write. {e}. Re-run spec-review.",
            file=sys.stderr,
        )
        return 1
    if write_time_bytes != doc_bytes:
        print(f"error: stale_state: doc bytes changed between dispatch and write. "
              f"Pre-dispatch hash {pre_dispatch_hash}. Re-run spec-review.",
              file=sys.stderr)
        return 1
    # Bind authoritative hash into attestation (subagent value not trusted)
    attestation["doc_subject"]["content_hash"] = pre_dispatch_hash

    # F2: hard-fail on overall_verdict mismatch (codex-r1 finding)
    computed_overall = compute_overall_verdict(attestation["gates"])
    if attestation["overall_verdict"] != computed_overall:
        print(f"error: verdict_mismatch: claimed overall_verdict "
              f"{attestation['overall_verdict']!r} ≠ computed worst-case "
              f"{computed_overall!r} from gate verdicts", file=sys.stderr)
        return 1

    # A24 + PF10: atomic-write via temp + fsync + os.replace
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f".{out_path.name}.tmp.{os.getpid()}")
    yaml_content = yaml.safe_dump(attestation, sort_keys=False, default_flow_style=False)
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, out_path)
    except Exception as e:
        try:
            tmp_path.unlink()  # Best-effort cleanup of temp file
        except FileNotFoundError:
            pass
        print(f"error: atomic_write_failed: {e}", file=sys.stderr)
        return 1
    print(f"OK: attestation written to {out_path}")
    print(f"verdict: {attestation['overall_verdict']}")

    return 0 if attestation["overall_verdict"] in ("pass", "conditional_pass") else 1


def canonicalize_doc_path(input_path: str, repo_root: Path) -> Path:
    """Fail-closed canonicalization of the user-supplied doc path (F1).

    Resolves symlinks transitively, strips `..`, and verifies the resolved
    path is under `<repo_root>/docs/`. Raises ValueError on any failure.
    """
    p = Path(input_path)
    # Disallow absolute paths up-front (clearer error than post-resolve check)
    if p.is_absolute():
        raise ValueError(f"absolute path not allowed: {input_path}")
    candidate = (repo_root / p).resolve(strict=True)
    docs_root = (repo_root / "docs").resolve(strict=True)
    try:
        candidate.relative_to(docs_root)
    except ValueError:
        raise ValueError(
            f"path resolves outside repo docs/ tree: {input_path} → {candidate}")
    return candidate


def compute_overall_verdict(gates: dict) -> str:
    """Compute worst-case across gate verdicts (F2).

    fail > conditional_pass > pass. Returns the highest-rank verdict found.
    """
    worst_rank = 0
    for gate_name, gate in gates.items():
        rank = VERDICT_RANK.get(gate.get("verdict", ""), 0)
        if rank > worst_rank:
            worst_rank = rank
    return next(k for k, v in VERDICT_RANK.items() if v == worst_rank)


def parse_iteration_from_text(text: str) -> int:
    """Read Iteration: field from doc metadata block (text-only, no I/O — F8).

    Operates on a snapshot string to avoid TOCTOU between hash + iteration reads.
    """
    m = re.search(r"^>\s+\*\*Iteration:\*\*\s+(\d+)\s*$", text, re.MULTILINE)
    if not m:
        return 1                          # default
    return int(m.group(1))


def compute_attestation_path(doc_path: Path, iteration: int) -> Path:
    """For docs/features/007-x.md → docs/reviews/007-r1.review.yaml.

    Strips type-dir prefix; strips -rN suffix from filename if present
    (the iteration number in attestation uses the doc Iteration: field, NOT
    the filename suffix).
    """
    name = doc_path.stem  # "007-x" or "006-archive-and-supersession-conventions-r4"
    # Strip trailing -rN if present (filename convention from LLD-006-r4)
    base = re.sub(r"-r\d+$", "", name)
    return Path("docs/reviews") / f"{base}-r{iteration}.review.yaml"


def render_prompt_from_text(doc_text: str, schema: dict) -> str:
    """Render prompt from snapshot text (no I/O on doc — F8 TOCTOU fix)."""
    template = PROMPT_TEMPLATE_PATH.read_text()
    return template.replace("<doc text inlined here at dispatch time>", doc_text)


def dispatch_subagent(prompt: str) -> str:
    """Invoke Claude Code Task tool with general-purpose subagent.

    Implementation note: this function is the seam where the skill's
    SKILL.md instructs Claude (the main agent) to invoke Task. The Python
    module exists for schema validation + attestation writing. Actual
    subagent dispatch happens at the agent layer via the skill's prose body.

    For testing: dispatch_subagent is monkey-patched to return canned YAML.
    For runtime: SKILL.md instructs Claude to dispatch Task and pipe YAML
    output back via stdin.
    """
    return sys.stdin.read()
```

This `dispatch_subagent` design — read YAML from stdin in production — is
the v1.6 simplification: the skill's prose body (SKILL.md) tells Claude to
dispatch Task tool, pipe the YAML response to `python -m cli.spec_review`,
which then validates + writes the attestation. No custom Task-tool wrapping
inside Python (that would require Anthropic SDK + API key handling that's
out of scope for v1.6).

(P2 helper-fully-specified checklist item.)

### Slash command (commands/spec-review.md)

```markdown
---
description: Run orchestra:spec-review (judge-1) on a doc
arguments:
  - name: doc_path
    description: Repo-relative path to the doc
    required: true
---

Invoke skill `orchestra:spec-review` with arg `${doc_path}`.
```

The slash command is a thin shim. The skill handles dispatch + validation +
write.

### Iteration handling

Skill reads `Iteration: <N>` from doc metadata block (orchestra format `> **Iteration:** N`). Emits matching `iteration: N` in attestation. Mismatch → exit 1. Author increments Iteration before re-invoking spec-review on a revised doc.

Iteration is NOT auto-incremented by the skill. The author bumps it when revising the doc. This decouples skill execution from doc lifecycle (skill can be run multiple times on same iteration with `--force` for testing).

### Multi-judge invocation flow (manual chair, user-driven)

```
1. Author writes/edits doc → bumps Iteration field in metadata block
2. Author runs: /orchestra:spec-review docs/features/NNN-foo.md
   → judge-1 attestation written to docs/reviews/<doc-id>-r<Iteration>.review.yaml
   Examples (v1.6.1 finding #6 — show concrete derivation):
     docs/features/007-spec-review-architecture.md  Iter=4
       → docs/reviews/007-spec-review-architecture-r4.review.yaml
     docs/features/006-archive-and-supersession-conventions-r4.md  Iter=4
       → docs/reviews/006-archive-and-supersession-conventions-r4.review.yaml
       (filename -rN suffix is stripped + re-applied; iteration value
        comes from doc Iteration: field, not filename)
     docs/bugs/BUG-008-spec-review-cargo-cult.md  Iter=2
       → docs/reviews/BUG-008-spec-review-cargo-cult-r2.review.yaml
3. (Optional) Author runs: /codex:adversarial-review docs/features/NNN-foo.md
   → codex output (free-form prose, NOT in orchestra schema; user reads separately)
4. (Optional) Author runs: /caveman:cavecrew-reviewer docs/features/NNN-foo.md
   → cavecrew one-line/severity-emoji output (NOT in orchestra schema; user reads)
5. User reads all judge outputs.
6. User decides: doc passes (move to next status) OR doc needs revision (back to step 1).
```

orchestra ships ONLY judge-1. orchestra:spec-review skill writes ONE attestation per invocation. orchestra does NOT invoke other judges, does NOT aggregate verdicts, does NOT enforce consensus.

This is intentional. Aggregation rules need data we don't have. v1.6.x or v1.7+ may add aggregation once we observe judge-disagreement patterns in practice.

### STANDARDS template update (cli/templates/standards-default-7.md)

Replaces existing § Spec Review Rule with:

```markdown
## Spec Review Rule (multi-judge, manual chair — v1.6)

After writing or updating any doc destined for `docs/`:

1. Bump `Iteration:` field in metadata block (or set `Iteration: 1` for new doc)
2. Run judge-1 (orchestra default): `/orchestra:spec-review <doc-path>`
   → writes attestation to `docs/reviews/<doc-id>-rN.review.yaml`
3. (Optional) Run additional judges manually:
   - `/codex:adversarial-review <doc-path>` (different model — bias mitigation)
   - `/caveman:cavecrew-reviewer <doc-path>` (terse one-line format)
   - `/superpowers:requesting-code-review <doc-path>` (general-purpose subagent)
4. Read all judge outputs. User decides: pass → commit + advance Status; fail → revise + bump Iteration → re-review

Max 3 iterations per LLD; iteration 4+ → interview-gate fires (context drift suspected; surface to user before silent retry).

Failures named by gate. See `references/4-gate-rubric.md` for pass/fail criteria.
```

### Bias mitigations (3 enforced + 1 documented)

Enforced in code:
1. **Position bias** — prompt instructs subagent to order findings by location (top-of-doc first), not severity
2. **Self-preference** — `reviewer.identifier` field detects same-judge re-invocation; `--force` flag required to overwrite
3. **Length bias** — output token cap of 4000 in subagent dispatch (specified in SKILL.md prose for agent-layer Task tool dispatch). Cap chosen to bound one full attestation YAML (4 gates × ~5 findings × ~80 tokens/finding + structural overhead ≈ 2000 tokens; 2× headroom). Empirically validated against the 6 LLD-007 codex attestations + 3 v1.5 attestations all rendered under 3000 tokens. v1.6.1 finding #11: number is observation-justified, not benchmark-derived; revisit if subagent attestations consistently truncate (no observed truncation through r4 dogfood).

Documented (not enforced):
4. **Same-model bias** — Opus-judging-Opus systematically under-flags Opus-authored docs (arXiv 2410.21819, https://arxiv.org/abs/2410.21819). v1.6 mitigation: STANDARDS recommends user run `/codex:adversarial-review` as judge-2 (different model). v1.7+ may add `--judge-model` flag if Task tool exposes per-call model selection.

(P9 checklist: does new rule break existing rule? — No. Bias mitigations 1-3 add constraints not in conflict with LLD-006-r4 narrow-change rule or doc-id-burn rule. Mitigation 4 is documentation-only, no rule impact.)

### Bootstrap-paradox handling (this LLD)

**BEFORE merge** (current state, 2026-05-10): orchestra:spec-review skill does NOT exist. LLD-007 reviewed via codex:adversarial-review (different model — gpt-5-codex — bypasses Opus self-preference) + author-applied fixes inline + manual user read.

**AFTER merge** (post-v1.6 ship): all future LLDs reviewed via `/orchestra:spec-review` (judge-1 default) plus optional manual `/codex:adversarial-review` (judge-2). LLD-007 itself can be re-reviewed using its own skill as a dogfood verification (D4 deliverable).

This LLD-007 reviewed via OLD ad-hoc process:
1. Author (me) applies pre-dispatch checklist P1-P9 inline before dispatch
2. Author dispatches fresh-subagent review using Task tool, prompt includes 4-gate criteria + this doc text
3. Subagent returns findings (informal format since orchestra:spec-review skill not yet built)
4. Author applies fixes inline, re-reviews mentally
5. User does manual extra-careful read

Per LLD-006-r4 precedent (4 review rounds, conditional_pass on r4). LLD-007 reached conditional_pass at r3 + r4 dogfood. **Canonical max-iteration**: 3 per documentation-gate convention (Glossary § iteration); iteration 4+ surfaces interview-gate. v1.6.1 finding #12 reconcile — bootstrap "up to 5" wording removed: bootstrap context does NOT extend the iteration cap. r4+ rounds always surface interview-gate; user explicitly approves continuation case-by-case (same rule as non-bootstrap docs).

After v1.6 ships, all future LLDs use `/orchestra:spec-review` instead.

## Edge Cases

- **Subagent returns empty output** — caught by yaml.load returning None → schema validation rejects (None is not a dict; jsonschema raises TypeError) → exit 1 with `schema_validation_failed`. User re-invokes `/orchestra:spec-review` for fresh dispatch (v1.6.1: no in-Python retry; stdin-bound dispatch makes retry meaningless).
- **Subagent returns prose then YAML** — yaml.load may parse the prose-prefix portion → schema validation rejects (missing required fields) → exit 1 with `schema_validation_failed`. User re-invokes for fresh dispatch. v1.7+ may add yaml-document-extraction (find first `schema_version:` line) to recover gracefully.
- **Subagent claims `pass` with zero findings on all gates** — schema requires `justification` field per gate when findings list is empty. No justification → schema-fail.
- **Doc has no Iteration field** — parse_iteration defaults to 1.
- **Doc filename has -rN suffix (supersession-iteration)** — attestation path strips suffix; iteration field comes from doc metadata, not filename. E.g., `docs/features/006-foo-r4.md` with `Iteration: 4` → `docs/reviews/006-foo-r4.review.yaml`.
- **Existing attestation exists, no --force** — skill exits 1 with explicit error. Re-running on same iteration is intentional friction (prevents accidental overwrite).
- **Doc moved to archive between dispatch and write** — v1.6.1 (finding #9): write-time `read_bytes` is wrapped in try/except; FileNotFoundError/OSError → exit 1 with `doc_disappeared` error. User re-runs spec-review against the new path (post-archive). For docs intentionally archived during a different attestation invocation, the prior attestation's `doc_subject.path` still reflects pre-move location and is rewritten via `cli.lifecycle update-attestation-paths` (LLD-006-r4).
- **Subagent generates fabricated finding (#1 production issue per Diffray)** — v1.6 mitigation: schema-enforced `location` field syntax. v1.6.x followup: auto-verify location string resolves to real position in doc.
- **Two judges disagree (one pass, one fail)** — orchestra ships no aggregation. User reads both outputs and decides. Default policy: any fail → doc fails. User can override.
- **Slash command invoked outside git repo** — skill checks via `git rev-parse --show-toplevel`; exits 2 with "not in git repo" if missing.
- **JSON-schema library not installed** — pyproject.toml declares `jsonschema>=4` as v1.6 dep; otherwise install error surfaces.

## Security

- **Prompt injection via doc content** — doc text is inlined into subagent prompt. Malicious doc could include "ignore previous instructions" or similar. Mitigation: subagent prompt explicitly delimits doc with "## DOC TO REVIEW" / "## END OF PROMPT" markers; subagent instructed to "output YAML only, no preamble." Risk residual but bounded; future v1.7+ may sanitize.
- **Path traversal — fail-closed canonicalization (codex-r1 F1 + codex-r2 F5)** — `doc_path` is canonicalized via `Path.resolve(strict=True)` BEFORE any file read. Validation: (a) resolved path must be under `<repo_root>/docs/`; (b) any `..` segment in input resolves to a path still under docs/ or rejected; (c) symlinks resolved transitively and re-checked under docs/. Caller catches `(ValueError, FileNotFoundError, OSError)` — covers logical reject, missing file, broken symlink, permission denied. Any failure → exit 2 + explicit `path_traversal_blocked` error (no Python crash). Implementation in `cli.spec_review.canonicalize_doc_path()` — fully spec'd in Design § cli.spec_review module below.
- **Verdict spoofing — authoritative overall_verdict (codex-r1 finding F2)** — `overall_verdict` from subagent output is NEVER trusted as the source of truth. After schema validation, `cli.spec_review` computes overall = worst-case across gate verdicts (any `fail` → `fail`; else any `conditional_pass` → `conditional_pass`; else `pass`). If subagent-supplied value ≠ computed value → exit 1 with `verdict_mismatch` error. Hard-fail (no silent overwrite) — silent fix would hide systematic judge bias.
- **Empty-finding justification — schema-enforced (codex-r1 finding F3)** — JSON-schema uses conditional `if/then`: when `findings: []` → `justification` is required AND non-empty (≥10 chars). Prevents anti-sycophancy bypass via empty-gates-no-justification.
- **Attestation path binding (codex-r1 finding F4)** — `doc_subject.path` from subagent output is validated post-schema against the caller-canonical input path. Mismatch → exit 1 with `path_mismatch` error (consistent with existing iteration-mismatch behavior). Hard-fail prevents audit-trail corruption via judge naming wrong doc.
- **Stale-state hash gate (codex-r2 F6)** — content hash captured at DISPATCH time (before subagent invocation). At write time, doc bytes re-hashed; if write-time hash ≠ pre-dispatch hash → exit 1 with `stale_state` error. Prevents the race where doc changes between prompt-render and attestation-write, leaving "verdict-on-old-bytes + hash-on-new-bytes" mismatch in the attested record.
- **Attestation file overwrite** — `--force` flag required; default exits 1 on existing file.
- **Subagent output as code** — never executed; only parsed as YAML + validated against schema.
- **Token-cap DOS prevention (codex-r3 F10 honest narrowing)** — token cap of 4000 is specified in SKILL.md prose for the agent-layer Task tool dispatch. `cli.spec_review` Python does NOT enforce this — dispatch happens at agent layer. Manual dogfood verification (D4 deliverable) inspects actual Task call kwargs post-merge. Runtime cap enforcement = v1.6.x followup if Python takes over dispatch.

## Testing

### Pytest baseline (verified 2026-05-10)

Captured directly:
```bash
$ cd /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra
$ /Users/mohammedhassanmohiddin/Documents/Antigravity/SCALE\ APP/.venv/bin/python -m pytest tests/ 2>&1 | tail -3
tests/test_standards_generator.py ...........                            [100%]

============================= 107 passed in 3.06s ==============================
```

Baseline = 107 (post-v1.5.1).

### New unit tests (binding floor: ≥16; this list enumerates exactly 16)

Each test maps 1:1 to an Acceptance item per P5 checklist:

| Test ID | Test file::function | Maps to | Coverage |
|---|---|---|---|
| T1 | `tests/test_spec_review_invoke.py::test_slash_command_arg_parsing` | A2 | Slash cmd accepts single positional doc-path arg |
| T2 | `tests/test_spec_review_dispatch.py::test_skill_md_specifies_general_purpose_subagent` | A3 | Open `skills/spec-review/SKILL.md`; assert prose contains `subagent_type: general-purpose` and `Task` tool reference (structural — Python validates skill body, agent-layer Task dispatch tested manually via dogfood) |
| T3 | `tests/test_spec_review_prompt.py::test_prompt_template_has_7_elements` | A4 | Render prompt; assert all 7 element headings present |
| T4 | `tests/test_spec_review_schema.py::test_valid_yaml_passes` | A5 | Valid attestation → exit 0 + file written |
| T5 | `tests/test_spec_review_schema.py::test_invalid_yaml_retries_once` | A5 | Invalid first attempt; valid second → exit 0 |
| T6 | `tests/test_spec_review_schema.py::test_invalid_yaml_twice_fails` | A5 | Invalid twice → exit 1 |
| T7 | `tests/test_spec_review_path.py::test_attestation_path_no_suffix` | A6 | `docs/features/007-x.md` → `docs/reviews/007-r1.review.yaml` |
| T8 | `tests/test_spec_review_path.py::test_attestation_path_with_rN_suffix` | A6 | `docs/features/006-x-r4.md` Iter=4 → `docs/reviews/006-x-r4.review.yaml` |
| T9 | `tests/test_spec_review_schema.py::test_missing_required_field_rejected` | A7 | Drop `overall_verdict` → schema-fail |
| T10 | `tests/test_spec_review_schema.py::test_unknown_gate_name_rejected` | A7 | Add `gates.bogus` → schema-fail |
| T11 | `tests/test_spec_review_schema.py::test_severity_enum_violated_rejected` | A7 | severity=Info → schema-fail (only Critical/Important/Minor allowed) |
| T12 | `tests/test_spec_review_schema.py::test_overall_verdict_enum_violated_rejected` | A7 | overall_verdict=maybe → schema-fail |
| T13a | `tests/test_spec_review_bias.py::test_finding_order_random_seed_in_prompt` | A8 | Prompt instructs ordering-by-location |
| T13b | `tests/test_spec_review_bias.py::test_force_required_for_same_iteration_overwrite` | A8 | Pre-existing attestation + no --force → exit 1 |
| T13c | `tests/test_spec_review_bias.py::test_skill_md_specifies_max_tokens_4000` | A8 | Open `skills/spec-review/SKILL.md`; assert prose contains `max_tokens: 4000` (structural — runtime kwarg verification deferred to manual dogfood D4 per A8 honest narrowing, codex-r3 F10) |
| T14 | `tests/test_spec_review_schema.py::test_location_field_regex_enforced` | A9 | `location: garbage` → schema-fail |
| T15 | `tests/test_spec_review_schema.py::test_schema_version_must_be_1_0` | A10 | schema_version="1.1" → schema-fail |
| T16 | `tests/test_spec_review_iter.py::test_iteration_mismatch_exits_1` | A11 | Doc Iter=2, attestation iter=1 → exit 1 |
| T17a | `tests/test_spec_review_security.py::test_absolute_path_rejected` | A16 | `/etc/passwd` → exit 2 + `path_traversal_blocked` |
| T17b | `tests/test_spec_review_security.py::test_dotdot_escape_rejected` | A16 | `docs/../../etc/passwd` → exit 2 |
| T17c | `tests/test_spec_review_security.py::test_symlink_escape_rejected` | A16 | symlink `docs/foo` → `/etc/passwd` → exit 2 |
| T18 | `tests/test_spec_review_verdict.py::test_overall_verdict_mismatch_exits_1` | A17 | gate=fail + claimed overall=pass → exit 1 + `verdict_mismatch` |
| T19a | `tests/test_spec_review_schema.py::test_empty_findings_no_justification_rejected` | A18 | findings=[] + no justification → schema-fail |
| T19b | `tests/test_spec_review_schema.py::test_empty_findings_short_justification_rejected` | A18 | findings=[] + justification="ok" → schema-fail (min 10 chars) |
| T20 | `tests/test_spec_review_security.py::test_attestation_path_mismatch_exits_1` | A19 | claimed path ≠ canonical input → exit 1 + `path_mismatch` |
| T21a | `tests/test_spec_review_security.py::test_missing_file_returns_path_traversal_blocked` | A20 | non-existent doc path → exit 2 (not Python crash) |
| T21b | `tests/test_spec_review_security.py::test_broken_symlink_returns_path_traversal_blocked` | A20 | symlink with missing target → exit 2 |
| T22 | `tests/test_spec_review_stale.py::test_doc_modified_between_dispatch_and_write_exits_1` | A21 | mutate doc bytes after dispatch_subagent returns → exit 1 + `stale_state` |
| T23 | `tests/test_spec_review_snapshot.py::test_single_read_for_hash_iter_prompt` | A22 | mock `Path.read_bytes`; assert called exactly twice (once dispatch, once write-time stale check) — never thrice |
| T24 | `tests/test_spec_review_path.py::test_attestation_path_anchored_to_repo_root` | A23 | invoke from cwd ≠ repo_root; verify out_path is absolute under repo_root |
| T25 | `tests/test_spec_review_atomicity.py::test_no_partial_write_on_pre_write_failure` | A24 | force schema-fail twice (retry exhausted); assert NO attestation file at out_path AND no leftover .tmp.* files |
| T25b | `tests/test_spec_review_atomicity.py::test_no_partial_write_on_io_exception` | A24 | mock open() / fsync to raise IOError mid-write; assert NO attestation file at out_path AND temp file cleaned up |
| T26 | `tests/test_spec_review_path.py::test_plans_path_accepted_in_schema` | A25 | doc_subject.path under `docs/plans/` accepted by schema validation |

Total new: 28 tests (T13 split a/b/c; T17 split a/b/c; T19 split a/b; T21 split a/b; T25 split a/b). Suite post-merge: 107 + 28 = 135.

### New eval scenario

| Scenario | Path |
|---|---|
| `spec-review-yaml-schema-roundtrip` | `eval/scenarios/spec-review-yaml-schema-roundtrip.json`. Fixture: minimal canon doc + canned valid YAML attestation. Pipe canned YAML to `python -m cli.spec_review`. Verify: exit 0, attestation written, schema-validation passes, content-hash recomputed correctly. |

### Manual verification (post-merge)

- Run `/orchestra:spec-review docs/features/007-spec-review-architecture.md` against THIS LLD (after canon-frozen) — verifies skill works on its own design doc (dogfood)
- README mentions slash command
- Plugin version 1.6.0 in plugin.json + pyproject.toml

## Related Documents

- `docs/features/006-archive-and-supersession-conventions-r4.md` — canon LLD-006; defines attestation file location convention
- `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` — Round 6 spec-review architecture; 7-element adversarial prompt anatomy; bias citations
- `docs/reviews/006-r4.review.yaml` — example v1.0 attestation (informal author-applied); v1.6 attestations follow the same shape
- ADR pattern — Michael Nygard, *Documenting Architecture Decisions* (https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- LLM self-preference bias — arXiv 2410.21819 (https://arxiv.org/abs/2410.21819)
<!-- v1.6.1 finding #4: arXiv 2512.01786 ID not verifiable as of 2026-05-10; removed pending citation review. Re-add with verified ID + in-body usage when source confirmed. -->
- LLM Jury / multi-judge — citation pending verification (see v1.6.1 followup)
- Empirical LLM-as-Judge — arXiv 2506.13639 (https://arxiv.org/abs/2506.13639)
- Cursor builder/validator — https://www.cursor.com/blog/agent (general agent architecture reference)
- python-frontmatter — https://pypi.org/project/python-frontmatter/
- jsonschema — https://pypi.org/project/jsonschema/

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | r1 written. Multi-judge with manual chair scope locked (Q2-(b)). Slash command primary invocation locked (Q3-(a)). 7-element adversarial prompt + schema v1.0 + 3 enforced bias mitigations + 1 documented. cli.spec_review sidecar reads YAML from stdin (subagent dispatch happens at agent layer via SKILL.md instructions; Python validates + writes only). Bootstrap paradox handled via codex:adversarial-review (different model — gpt-5-codex — no Opus self-preference). Pre-dispatch P1-P9 self-audit applied: P1 (dropped unverifiable Diffray + arXiv 2411.03079 citation), P2 (T2 reframed from agent-layer mock to structural SKILL.md prose check), P4 (Glossary "iteration" entry adds 1:1 correspondence note), P7 (BEFORE/AFTER merge labels added to bootstrap section). Status: Draft. r1 codex review pending. |
| 2026-05-10 | r1 revised after codex adversarial review (verdict: needs-attention). 4 findings addressed inline (Draft → full edit permitted): F1 (Critical) path traversal — added `canonicalize_doc_path()` with fail-closed resolve+under-docs/ check; F2 (High) verdict spoofing — added `compute_overall_verdict()` worst-case derivation, hard-fail on subagent-claimed-vs-computed mismatch; F3 (High) anti-sycophancy bypass — JSON-schema `if/then` conditional requires `justification` (min 10 chars) when `findings: []`; F4 (Medium) path identity — hard-fail on `doc_subject.path` mismatch with canonical input (consistent with existing iteration-mismatch behavior). Tests: 16 → 20 (added T17a/b/c, T18, T19a/b, T20). Pytest target: 123 → 127. Picks: F1=A (resolve+under-docs/), F2=B (hard-fail), F3=B (≥10 chars), F4=B (hard-fail). Status: Draft. Re-codex pass pending. |
| 2026-05-10 | r1 second revision after codex round-2 review (verdict: needs-attention; 3 NEW findings, no overlap with F1-F4 — distinct error-handling/race/test-coverage gaps, real progress). F5 (High) canonicalize fail-closed — caller now catches `(ValueError, FileNotFoundError, OSError)`, all map to `path_traversal_blocked` exit 2 (was Python crash on resolve failures). F6 (High) stale-state integrity — pre-dispatch hash captured before subagent invocation; write-time hash re-checked; mismatch → exit 1 `stale_state` (was silent overwrite, hiding doc-mutated-mid-flight). F7 (Medium) A3 honest narrowing — acceptance text now says SKILL.md prose specifies dispatch + runtime Task kwargs verified via manual dogfood (D4); T2 stays as structural prose check matching narrowed claim. Tests: 20 → 23 (added T21a, T21b, T22). Pytest target: 127 → 130. Status: Draft. |
| 2026-05-10 | r1 third revision after codex round-3 review (verdict: needs-attention; 3 NEW findings, no overlap with R1 or R2 — distinct snapshot/path-anchoring/honesty gaps). F8 (High) TOCTOU between multi-reads — refactored to single immutable `doc_bytes` snapshot used for hash + iteration + prompt; helpers `parse_iteration_from_text` + `render_prompt_from_text` operate on snapshot; write-time check compares bytes directly. F9 (High) repo-root anchoring — `out_path = repo_root / compute_attestation_path(...)` before existence check, eliminates cwd-dependent misplacement. F10 (Medium) honesty on token-cap claim — Security § + A8 narrowed; runtime cap enforcement marked as v1.6.x followup since `cli.spec_review` Python doesn't dispatch (agent layer does). Tests: 23 → 25 (added T23 single-read assertion, T24 cwd-independence). Pytest target: 130 → 132. Iteration field bumped 1 → 3 to match review-round count (semantic tension with LLD-006-r4 strict filename-suffix convention noted as v1.6.x followup; doc filename remains unsuffixed since no formal supersession event occurred — Draft full-edit-in-place). 3 codex rounds total = max-iteration boundary per LLD-006-r4 convention; round 4 would surface interview-gate. Verdict: conditional_pass with 4 v1.6.x followups tracked (Iteration/filename-suffix semantics; runtime token-cap enforcement; runtime Task-kwargs verification; eventual stdin-bound size limit). LLD architecture (multi-judge / manual chair / slash command / Task dispatch) intact across all 3 rounds. Status: Draft → ready for implementation phase. |
| 2026-05-10 | T13c row in Testing § matrix updated to match plan PF7 fix (drift between LLD + plan caught in plan codex round-2). T13c was specified as runtime mock-Task-kwargs assertion but A8 was narrowed in r3 to honest "SKILL.md prose specifies max_tokens 4000" (runtime kwarg verification deferred to manual dogfood D4). T13c now reads: `test_skill_md_specifies_max_tokens_4000` — opens SKILL.md, asserts prose contains `max_tokens: 4000`. Consistent with A8 + S30 slice in plan. No new findings; mechanical drift fix. Status: Draft. |
| 2026-05-10 | v1.6.0 SHIPPED. Implementation per plan `docs/plans/2026-05-10-lld-007-implementation.md`: skills/spec-review/ scaffold (SKILL.md + prompt-template.md + attestation-schema-v1.0.json + references/4-gate-rubric.md), commands/spec-review.md slash shim, cli/spec_review.py sidecar (canonicalize_doc_path / parse_iteration_from_text / compute_attestation_path / render_prompt_from_text / compute_overall_verdict / dispatch_subagent / _atomic_write / main), cli/templates/attestation-template.yaml, 36 new pytest tests across 11 test files (107→143, target ≥135 — exceeded), 1 new eval scenario `spec-review-yaml-schema-roundtrip` (11→12, all 12 PASS). cli.lint ALLOWED_ATTESTATION_PATH_PREFIXES extended to allow docs/plans/ + docs/archive/plans/ (A25). pyproject.toml + plugin.json bumped 1.5.1 → 1.6.0; jsonschema>=4 added as dep. Status: Draft → Implemented (full edit unrestricted on Draft per LLD-006-r4 narrow-change rules). Verified flips post-Task-8 dogfood. Status: Implemented. |
| 2026-05-10 | r4 dogfood + v1.6.1 patches (Iteration 3→4 narrow-change). Dogfood ran `/orchestra:spec-review` on this LLD with the just-shipped v1.6.0 skill — 13 findings (1 Critical / 8 Important / 4 Minor); attestation at `docs/reviews/007-spec-review-architecture-r4.review.yaml`; verdict=fail (consistency gate). Code patches: dropped stdin retry (MAX_RETRIES=0; second `sys.stdin.read()` returns empty making in-Python retry meaningless) — A5 reworded; added doc_disappeared try/except around write-time `read_bytes` (handles doc moved/deleted between dispatch and write per Edge Cases); 1 new test `test_doc_disappeared_between_dispatch_and_write` (T22b); 1 test rewritten T5 (`test_invalid_yaml_single_attempt_fails`) + T6 (`test_schema_validation_failed_error_surfaced`); pytest 143→144. Doc patches: A1+A12 manual-checkoff procedures spelled out; A14 reconciled (33 enumerated matrix rows + 4 helper assertions = 37 spec-review tests; baseline ≥140); fabricated arXiv 2603.07670 reference reframed to honest in-session attestation evidence; future-dated arXiv 2512.01786 reference removed pending verification; Multi-judge invocation flow gained 3 concrete attestation-filename derivation examples; cli.spec_review snippet `import os` added; token-cap=4000 justification added (observation-derived from 9 codex attestations rendering under 3000 tokens); max-iteration ambiguity resolved (canonical=3; bootstrap "up to 5" wording removed — r4+ always surfaces interview-gate). Status: Implemented (NOT yet Verified — flip post r5 dogfood confirms no regressions). |
| 2026-05-10 | r5 dogfood + v1.6.1 doc-snippet sync (Iteration 4→5 narrow-change; r5 surfaced interview-gate per canonical max-iter rule, user explicitly approved continuation for patch verification). r5 attestation at `docs/reviews/007-spec-review-architecture-r5.review.yaml`; 13 r4 findings ALL VERIFIED RESOLVED. 7 NEW findings introduced by v1.6.1 patches themselves (4 Important / 3 Minor) — same disease v1.6.1 was meant to cure: doc-vs-code drift. r4 patches updated `MAX_RETRIES = 0` constant + A5 wording but did NOT update the full cli.spec_review module CODE SNIPPET in the LLD, leaving the snippet showing old retry-loop code (yaml.safe_load instead of yaml.load+_NoTimestampLoader, missing TypeError catch, missing _NoTimestampLoader class definition); also Edge Cases bullets on empty-output and doc-moved-to-archive were stale relative to single-attempt + doc_disappeared semantics. r5 snippet sync: rewrote retry block to single-attempt + comment; added _NoTimestampLoader class definition with rationale; added TypeError to exception tuple; wrapped write-time read_bytes in try/except matching code; updated 2 Edge Cases bullets. 3 Minor r5 findings deferred to v1.6.2 followup (Problem Statement defect 3 fabricated-citation cite, token-cap measurement procedure, Changelog pytest-math chain-of-reasoning). Pytest 144 unchanged (doc-only patches; no code touched). Status: Implemented. r6 dogfood NOT run (canon-frozen at r5; further iteration surfaces interview-gate again). |
