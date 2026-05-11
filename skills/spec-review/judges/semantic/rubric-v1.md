# Rubric — semantic sub-judge — v1

**Rubric version**: `semantic-v1`
**Model**: claude-opus-4-7
**Tools allowed**: Read (target doc only)
**Mandatory**: true

---

## What this rubric covers

The 4-gate continuity rubric from v1.0 spec-review (LLD-007). Semantic = "does the doc say what it should say, with evidence, clearly, and consistently?"

This sub-judge is the baseline depth-of-coverage that v2 preserves from v1. Failure here = `overall_verdict: fail`.

## Gate 1: Completeness

Every required section is present and filled. No empty headers. No placeholders without owner/date suffix (`TBD by <date>` or `TBD by <person>` is acceptable; bare `TBD` is not).

| Severity | Trigger |
|---|---|
| Critical | Entire required section missing |
| Important | Section present but body is one sentence, "see other doc", or only a heading |
| Minor | Section present and complete but a bullet is unfilled |

## Gate 2: Evidence

Every factual claim has backing: a file:line cite, a URL, a benchmark, a referenced doc, or a quoted source. Verbal hedges like "should work", "we believe", "presumably" are findings unless paired with concrete backing.

| Severity | Trigger |
|---|---|
| Critical | Doc cites a source that, when read, does NOT say what doc claims |
| Important | Hedge ("should", "presumably", "we believe") with no cite |
| Minor | Cite present but imprecise (file but not line) |

## Gate 3: Clarity

A fresh reader (no session history, no Slack context, no author DM access) can act on this doc. Ambiguous terms have glossary entries or inline definitions.

| Severity | Trigger |
|---|---|
| Critical | Doc cannot be acted on without external knowledge not cited |
| Important | Ambiguous term used without definition; pronoun antecedent unclear in a key paragraph |
| Minor | A paragraph reads awkwardly; minor wording |

## Gate 4: Consistency

The doc agrees with itself, with cited peer docs, and with cited code. Cross-references resolve.

| Severity | Trigger |
|---|---|
| Critical | Doc contradicts itself (e.g., Scope says A, Design says not-A) |
| Important | Doc contradicts a cited peer doc; Refs: line points to nonexistent file |
| Minor | Cross-ref to related doc is missing but obvious |

## Anti-sycophancy reminder

ZERO findings on any gate = justification required. Verdict mapping per LLD-011 §Aggregator severity rules:
- Any Critical → `fail`
- Any Important → `conditional_pass`
- Only Minor or no findings → `pass`

## Output discipline reminder

Output the YAML in `sub_judges[]` entry shape (see prompt). Each finding cites a location matching `^(.+\s+§\s+.+|line\s+\d+)$`. Findings without parsable location are auto-rejected by `cli.spec_review` validation.
