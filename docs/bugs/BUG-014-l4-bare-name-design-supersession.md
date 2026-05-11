# BUG-014: L4 doc-id-burn rejects bare-name design-doc supersession

> **Doc ID:** BUG-014-l4-bare-name-design-supersession
> **Date:** 2026-05-11
> **DRI:** Hassan Mohiddin
> **Type:** Bug Report
> **Severity:** Medium
> **Status:** Fix Applied

## Observed Behavior

Discovered 2026-05-11 during BUG-012 §6 supersession of `docs/design/orchestra-philosophy.md → orchestra-philosophy-r2.md`. Pre-commit hook L4 (`cli.lint --pre-commit` calling `lint_doc_id_burn`) rejected the supersession file with:

```
❌ docs/design/orchestra-philosophy-r2.md: filename 'orchestra-philosophy-r2.md' does not match first-iteration or supersession-iteration pattern
```

Workaround: `git commit --no-verify` (sanctioned mechanical-backstop bypass per LLD-008 Glossary). Commit landed at `<TBD-impl-sha>`.

## Expected Behavior

L4 should permit bare-name design-doc supersession (`<name>-rN.md` where `<name>` is `[a-z][a-z0-9-]*` without leading digit prefix). Design type uses bare-name convention (single-doc-per-component); numbered-prefix patterns (`NNN-name.md` / `NNN-name-rN.md`) belong to feature/bug/adr/postmortem/runbook types only.

## Steps to Reproduce

```bash
cd orchestra
git mv docs/design/orchestra-philosophy.md docs/archive/design/orchestra-philosophy.md
cp docs/archive/design/orchestra-philosophy.md docs/design/orchestra-philosophy-r2.md
# Edit r2 frontmatter + body
git add docs/design/orchestra-philosophy-r2.md docs/archive/design/orchestra-philosophy.md
git commit -m "feat: supersede orchestra-philosophy"
# → ❌ L4 rejects filename pattern
```

## Environment

- orchestra v1.7.0 (commit `<TBD>`)
- `cli/lint.py § lint_doc_id_burn` (function-anchor)

## Root Cause

`cli/lint.py § FIRST_ITERATION_RE` + `SUPERSESSION_ITERATION_RE` patterns require leading digit prefix:

```python
FIRST_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)\.md$")
SUPERSESSION_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$")
```

Design-doc convention uses bare-name (`orchestra-philosophy.md`, no leading number) because design docs are one-per-component (no enumeration needed). Supersession file (`orchestra-philosophy-r2.md`) inherits bare-name + adds `-rN` suffix.

`lint_doc_id_burn` reaches the trailing fallthrough error: `filename does not match first-iteration or supersession-iteration pattern`.

## Fix Description

**Option A (Recommended):** Add bare-name patterns for design type only.

```python
DESIGN_BARE_NAME_RE = re.compile(r"^([a-z][a-z0-9-]*)\.md$")
DESIGN_BARE_SUPERSESSION_RE = re.compile(r"^([a-z][a-z0-9-]*)-r(\d+)\.md$")
```

In `lint_doc_id_burn`, before the numbered-pattern matching:

```python
if doc_type == "design":
    if DESIGN_BARE_NAME_RE.match(name) or DESIGN_BARE_SUPERSESSION_RE.match(name):
        # bare-name; skip burn check (no enumeration to protect)
        return []
```

**Option B:** Make L4 skip design type entirely (treat design like plans/archive — not L4-eligible).

Pick A — explicit pattern matching documents the contract; B silently drops enforcement.

## Iteration Log

- r1 (2026-05-11) — filed during BUG-012 §6 supersession execution. Surfaced when L4 rejected `orchestra-philosophy-r2.md`. Severity: Medium (blocks design-doc supersession workflow until fixed; `--no-verify` works as escape hatch but is friction).

## Regression Prevention

- Add test: `tests/test_lint_doc_id_burn.py::test_design_bare_name_supersession_passes` covers bare-name `-rN.md` supersession case.
- Update LLD-006-r4 § narrow change OR § supersession workflow to call out design-doc bare-name convention.

## Related Documents

- `cli/lint.py § lint_doc_id_burn` (fix target)
- `cli/lint.py § FIRST_ITERATION_RE` / `SUPERSESSION_ITERATION_RE` (regex source)
- `docs/features/006-archive-and-supersession-conventions-r4.md` — LLD-006-r4 supersession workflow
- `docs/design/orchestra-philosophy-r2.md` — supersession that surfaced this bug
- `docs/bugs/BUG-012-v17-1-minor-followups.md` — v1.7.1 backlog (this BUG joins)

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | BUG filed during BUG-012 §6 supersession execution. L4 doc-id-burn pattern matching assumes numbered prefix; design type uses bare-name. Workaround: `--no-verify`. Target fix: v1.7.1. Severity: Medium. Status: Investigating. |
| 2026-05-11 | Fix shipped via BUG-016 slice 4 (commit b518da1). Added DESIGN_BARE_NAME_RE + DESIGN_BARE_NAME_SUPERSESSION_RE + POSTMORTEM/RUNBOOK regexes to cli/lint.py; lint_doc_id_burn dispatches by doc_type before falling through to NNN-/BUG-NNN- path. Status: Investigating → Fix Applied. User-verified 2026-05-11. |
