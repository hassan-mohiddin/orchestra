"""PDSA (Pre-Dispatch Self-Audit) module tests (LLD-011 Phase 2 slices 2.1-2.12).

PDSA runs deterministic checks before sub-judge dispatch. Per LLD-011 §Design PDSA:
1. cli.lint --doc <path> must pass (L1/L2/L3/L4)
2. Required sections per doc type
3. Citation validity (splitlines + bounds-check)
4. Glossary completeness (non-gating warn until BUG-016 closes)
5. Placeholder detection (TBD/TODO/FIXME without owner-suffix)
6. Cross-doc Refs: path resolution
7. Filename grammar per LLD-006-r4

PDSA emits a YAML report. Lint or any gating check fail → sub-judges do NOT dispatch.
"""

from __future__ import annotations

from pathlib import Path


def test_lint_invocation(tmp_path, monkeypatch) -> None:
    """Slice 2.1 — run_pdsa invokes cli.lint --doc and surfaces the lint exit status.

    Contract: run_pdsa(doc_path) returns a PdsaReport whose `lint` check carries
    pass/fail derived from `cli.lint --doc <path>` exit code (0 = pass, non-zero = fail).
    """
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Foo\n")

    captured_args: list[list[str]] = []

    def fake_lint_main(argv: list[str]) -> int:
        captured_args.append(list(argv))
        return 0

    monkeypatch.setattr(pdsa, "_invoke_lint", fake_lint_main)

    report = pdsa.run_pdsa(doc)

    assert captured_args == [["--doc", str(doc)]], (
        f"expected cli.lint invoked once with --doc {doc}, got {captured_args}"
    )
    assert report.checks["lint"].passed is True
    assert report.passed is True


def test_lint_invocation_surfaces_failure(tmp_path, monkeypatch) -> None:
    """Slice 2.1 — non-zero lint exit → report.checks['lint'].passed=False, report.passed=False."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 1)

    report = pdsa.run_pdsa(doc)

    assert report.checks["lint"].passed is False
    assert report.passed is False


def test_required_sections_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.3 — Feature LLD with all required sections → required_sections.passed=True."""
    from cli import pdsa

    body = """# 999 Foo

> **Status:** Draft

## Problem Statement
text
## Success Criteria
text
## Scope
text
## Design
text
## API Changes
text
## Database Changes
text
## Edge Cases & Error Handling
text
## Security Considerations
text
## Testing Strategy
text
## Related Documents
text
## Changelog
text
"""
    doc = tmp_path / "docs" / "features" / "999-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["required_sections"].passed is True


def test_required_sections_fail_missing(tmp_path, monkeypatch) -> None:
    """Slice 2.3 — Feature LLD missing required section → required_sections.passed=False, detail names section."""
    from cli import pdsa

    body = """# 999 Foo

> **Status:** Draft

## Problem Statement
text
## Success Criteria
text
"""
    doc = tmp_path / "docs" / "features" / "999-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["required_sections"].passed is False
    assert "Design" in report.checks["required_sections"].detail
    assert report.passed is False


def test_required_sections_bug_report(tmp_path, monkeypatch) -> None:
    """Slice 2.3 — Bug Report doc type uses bug-report required-sections list."""
    from cli import pdsa

    body = """# BUG-099 Foo

> **Status:** Investigating

## Observed Behavior
text
## Expected Behavior
text
## Steps to Reproduce
text
## Environment
text
## Root Cause Analysis
text
## Fix Description
text
## Iteration Log
text
## Regression Prevention
text
## Related Documents
text
## Changelog
text
"""
    doc = tmp_path / "docs" / "bugs" / "BUG-099-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["required_sections"].passed is True


def test_citation_validity_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.4 — citation `<path>:<N>` with N in range → citations.passed=True.

    Note: post-fix #2, only repo-relative cites resolve. Tests chdir into the
    fixture root so `src/foo.py` is a valid repo-relative cite.
    """
    from cli import pdsa

    target = tmp_path / "src" / "foo.py"
    target.parent.mkdir(parents=True)
    target.write_text("line1\nline2\nline3\nline4\nline5\n")

    body = "## Body\nReference: `src/foo.py:3` — see line 3.\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is True


def test_citation_validity_range_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.4 — range citation `<path>:<N>-<M>` validates both endpoints."""
    from cli import pdsa

    target = tmp_path / "src" / "foo.py"
    target.parent.mkdir(parents=True)
    target.write_text("\n".join(f"l{i}" for i in range(1, 21)) + "\n")

    body = "Reference: `src/foo.py:5-10`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is True


def test_citation_validity_nonexistent_path(tmp_path, monkeypatch) -> None:
    """Slice 2.5 — citation points at nonexistent path → citations.passed=False."""
    from cli import pdsa

    body = "Reference: `nonexistent/path.py:5`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is False
    assert "nonexistent" in report.checks["citations"].detail


def test_citation_validity_out_of_range(tmp_path, monkeypatch) -> None:
    """Slice 2.5 — citation line N > len(lines) → citations.passed=False."""
    from cli import pdsa

    target = tmp_path / "src" / "small.py"
    target.parent.mkdir(parents=True)
    target.write_text("only one line\n")

    body = "Reference: `src/small.py:99`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is False
    assert "99" in report.checks["citations"].detail or "out of range" in report.checks["citations"].detail.lower()


def test_citation_range_inverted_fails(tmp_path, monkeypatch) -> None:
    """Slice 2.5 — range citation with M < N → citations.passed=False."""
    from cli import pdsa

    target = tmp_path / "src" / "f.py"
    target.parent.mkdir(parents=True)
    target.write_text("\n".join(f"l{i}" for i in range(1, 21)) + "\n")

    body = f"Reference: `{target}:10-5`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is False


def test_citation_absolute_path_rejected(tmp_path, monkeypatch) -> None:
    """Fix #2 — absolute paths (`/etc/passwd:1`) are rejected even if file exists.

    Defends against adversarial finding: PDSA executes read_text on every
    cited file; an absolute path lets a doc trigger reads outside the repo.
    """
    from cli import pdsa

    body = "Reference: `/etc/hosts.txt:1`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    monkeypatch.chdir(tmp_path)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is False
    assert "out-of-repo" in report.checks["citations"].detail or \
        "unresolvable" in report.checks["citations"].detail


def test_citation_parent_escape_rejected(tmp_path, monkeypatch) -> None:
    """Fix #2 — `..`-escapes outside repo root are rejected post-resolve."""
    from cli import pdsa

    # Create a real file outside the would-be repo root
    outside = tmp_path / "outside.txt"
    outside.write_text("secrets\n")

    repo = tmp_path / "repo"
    repo.mkdir()
    doc = repo / "random.md"
    doc.write_text("Reference: `../outside.txt:1`\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    monkeypatch.chdir(repo)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is False


def test_refs_absolute_rejected(tmp_path, monkeypatch) -> None:
    """Fix #2 — absolute Refs: paths are rejected (same defense as citations)."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("Refs: /etc/hosts\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    monkeypatch.chdir(tmp_path)
    report = pdsa.run_pdsa(doc)

    assert report.checks["refs"].passed is False


def test_refs_parent_escape_rejected(tmp_path, monkeypatch) -> None:
    """Fix #2 — Refs: with `..`-escape outside repo root rejected."""
    from cli import pdsa

    outside = tmp_path / "outside.md"
    outside.write_text("# outside\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    doc = repo / "random.md"
    doc.write_text("Refs: ../outside.md\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    monkeypatch.chdir(repo)
    report = pdsa.run_pdsa(doc)

    assert report.checks["refs"].passed is False


def test_citation_no_citations(tmp_path, monkeypatch) -> None:
    """Slice 2.4 — doc with no citations → citations.passed=True (nothing to validate)."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Foo\n\nNo references here.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is True


def test_bare_placeholder_fails(tmp_path, monkeypatch) -> None:
    """Slice 2.6 — bare TBD/TODO/FIXME → placeholders.passed=False."""
    from cli import pdsa

    body = "## Body\n\nThis is TBD.\n\nFIXME later.\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["placeholders"].passed is False


def test_owned_placeholder_passes(tmp_path, monkeypatch) -> None:
    """Slice 2.7 — TBD by <date> or TBD by <person> → placeholders.passed=True."""
    from cli import pdsa

    body = "## Body\n\nTBD by 2026-05-15.\n\nTODO by Hassan: integrate.\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["placeholders"].passed is True


def test_no_placeholders(tmp_path, monkeypatch) -> None:
    """Slice 2.6 — doc without placeholders → placeholders.passed=True."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Title\n\nAll content is final.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["placeholders"].passed is True


def test_mixed_placeholders(tmp_path, monkeypatch) -> None:
    """Slice 2.7 — one owned + one bare → fails (any bare hit fails)."""
    from cli import pdsa

    body = "TBD by 2026-05-15.\n\nbare FIXME here.\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["placeholders"].passed is False
    assert "FIXME" in report.checks["placeholders"].detail


def test_refs_resolve_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.8 — Refs: line pointing at existing file → refs.passed=True.

    Post-fix #2: only repo-relative Refs values resolve. Tests chdir.
    """
    from cli import pdsa

    target = tmp_path / "docs" / "features" / "100-bar.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Bar\n")

    body = "## Body\n\nRefs: docs/features/100-bar.md\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)
    report = pdsa.run_pdsa(doc)

    assert report.checks["refs"].passed is True


def test_refs_resolve_fail(tmp_path, monkeypatch) -> None:
    """Slice 2.8 — Refs: line points at nonexistent file → refs.passed=False."""
    from cli import pdsa

    body = "Refs: docs/features/does-not-exist.md\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["refs"].passed is False


def test_refs_no_refs_line(tmp_path, monkeypatch) -> None:
    """Slice 2.8 — no Refs: lines → refs.passed=True (nothing to validate)."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# foo\n\nbody.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["refs"].passed is True


def test_filename_grammar_feature_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.9 — feature doc `NNN-name.md` matches LLD-006-r4 grammar."""
    from cli import pdsa

    doc = tmp_path / "docs" / "features" / "008-commit-skill.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["filename_grammar"].passed is True


def test_filename_grammar_feature_rev_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.9 — feature `NNN-name-rN.md` supersession variant passes."""
    from cli import pdsa

    doc = tmp_path / "docs" / "features" / "008-commit-skill-r8.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["filename_grammar"].passed is True


def test_filename_grammar_feature_fail(tmp_path, monkeypatch) -> None:
    """Slice 2.9 — feature `name.md` without NNN prefix fails."""
    from cli import pdsa

    doc = tmp_path / "docs" / "features" / "no-prefix.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["filename_grammar"].passed is False


def test_filename_grammar_bug_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.9 — bug `BUG-NNN-name.md` matches grammar."""
    from cli import pdsa

    doc = tmp_path / "docs" / "bugs" / "BUG-014-l4-bare-name.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["filename_grammar"].passed is True


def test_filename_grammar_design_bare_name_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.9 — design doc bare-name with -rN supersession passes (BUG-014 gap)."""
    from cli import pdsa

    doc = tmp_path / "docs" / "design" / "orchestra-philosophy-r2.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["filename_grammar"].passed is True


def test_glossary_non_gating(tmp_path, monkeypatch) -> None:
    """Slice 2.10 — glossary check exists, marked non-gating; report.passed unaffected by glossary fail.

    Per LLD-011 §PDSA item 4: glossary check warns but does NOT block dispatch
    until BUG-016 controlled-vocabulary canon ships.
    """
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Title\n\nbody.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)

    # Force the glossary check to "fail" by monkeypatching a fail-returning replacement.
    def fake_glossary(_p: Path) -> pdsa.CheckResult:
        return pdsa.CheckResult(passed=False, detail="missing term: foo", gating=False)

    monkeypatch.setattr(pdsa, "_check_glossary", fake_glossary)
    report = pdsa.run_pdsa(doc)

    assert "glossary" in report.checks
    assert report.checks["glossary"].passed is False
    assert report.checks["glossary"].gating is False
    # Non-gating fail must NOT make report.passed False
    assert report.passed is True


def test_glossary_default_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.10 — default glossary impl passes (placeholder until BUG-016)."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Title\n\nbody.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert "glossary" in report.checks
    assert report.checks["glossary"].gating is False


def test_pdsa_report_yaml_format(tmp_path, monkeypatch) -> None:
    """Slice 2.11 — PdsaReport.to_yaml() emits per-check pass/fail YAML."""
    import yaml as yaml_mod

    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("# Title\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    yaml_text = report.to_yaml()
    parsed = yaml_mod.safe_load(yaml_text)

    assert parsed["doc_path"] == str(doc)
    assert parsed["passed"] is True
    assert "checks" in parsed
    # All 7 named checks present
    for check_id in [
        "lint",
        "required_sections",
        "citations",
        "placeholders",
        "refs",
        "filename_grammar",
        "glossary",
    ]:
        assert check_id in parsed["checks"], f"missing {check_id} in YAML report"
        assert "passed" in parsed["checks"][check_id]
        assert "gating" in parsed["checks"][check_id]


def test_pdsa_report_yaml_fail_surfaces_detail(tmp_path, monkeypatch) -> None:
    """Slice 2.11 — failing check's detail is in YAML."""
    from cli import pdsa
    import yaml as yaml_mod

    doc = tmp_path / "random.md"
    doc.write_text("Reference: `nope/x.py:5`\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    yaml_text = report.to_yaml()
    parsed = yaml_mod.safe_load(yaml_text)

    assert parsed["passed"] is False
    assert parsed["checks"]["citations"]["passed"] is False
    assert "nope" in parsed["checks"]["citations"]["detail"]


def test_citation_validity_repo_root_resolution(tmp_path, monkeypatch) -> None:
    """Citation `cli/lint.py:42` resolves against cwd (repo root), not just doc parent.

    Real-doc dogfood on LLD-011 surfaced this — citations canonically use
    repo-root-relative paths; resolving only against doc.parent gave false
    positives. Fix: try cwd first, then doc.parent.
    """
    from cli import pdsa

    target = tmp_path / "src" / "module.py"
    target.parent.mkdir(parents=True)
    target.write_text("\n".join(f"l{i}" for i in range(1, 51)) + "\n")

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    doc = docs / "999-foo.md"
    doc.write_text("Reference: `src/module.py:5`\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)

    report = pdsa.run_pdsa(doc)
    assert report.checks["citations"].passed is True, report.checks["citations"].detail


def test_placeholders_skip_backtick_inline_code(tmp_path, monkeypatch) -> None:
    """Backtick-quoted `TBD` is a meta-reference, not a bare placeholder.

    Real-doc dogfood on LLD-011 surfaced this — the doc references the
    literal placeholder canon as `TBD` / `TODO` / `FIXME` tokens. Stripping
    code spans before scanning eliminates the false positive.
    """
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text(
        "## Section\n\nThe canon uses `TBD`, `TODO`, and `FIXME` markers.\n"
    )

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)
    assert report.checks["placeholders"].passed is True, report.checks["placeholders"].detail


def test_placeholders_skip_fenced_code_block(tmp_path, monkeypatch) -> None:
    """Fenced code blocks containing TBD/TODO/FIXME are meta-references."""
    from cli import pdsa

    doc = tmp_path / "random.md"
    doc.write_text("## Body\n\n```\nTBD\nTODO: foo\n```\n\nReal body.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)
    assert report.checks["placeholders"].passed is True


def test_required_sections_unknown_doc_type(tmp_path, monkeypatch) -> None:
    """Slice 2.3 — unknown doc type → required_sections.passed=True (skip check, no spec to enforce)."""
    from cli import pdsa

    doc = tmp_path / "docs" / "scratch" / "random.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# random\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    # Unknown type — check passes (informational only)
    assert report.checks["required_sections"].passed is True
    assert "unknown" in report.checks["required_sections"].detail.lower() or \
        "skipped" in report.checks["required_sections"].detail.lower()
