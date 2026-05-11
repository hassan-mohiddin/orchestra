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
    """Slice 2.4 — citation `<path>:<N>` with N in range → citations.passed=True."""
    from cli import pdsa

    target = tmp_path / "src" / "foo.py"
    target.parent.mkdir(parents=True)
    target.write_text("line1\nline2\nline3\nline4\nline5\n")

    body = f"## Body\nReference: `{target}:3` — see line 3.\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    report = pdsa.run_pdsa(doc)

    assert report.checks["citations"].passed is True


def test_citation_validity_range_pass(tmp_path, monkeypatch) -> None:
    """Slice 2.4 — range citation `<path>:<N>-<M>` validates both endpoints."""
    from cli import pdsa

    target = tmp_path / "src" / "foo.py"
    target.parent.mkdir(parents=True)
    target.write_text("\n".join(f"l{i}" for i in range(1, 21)) + "\n")

    body = f"Reference: `{target}:5-10`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
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

    body = f"Reference: `{target}:99`\n"
    doc = tmp_path / "random.md"
    doc.write_text(body)

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
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
