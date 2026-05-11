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

    doc = tmp_path / "docs" / "features" / "999-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n\n> **Status:** Draft\n\n## Body\n")

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

    doc = tmp_path / "docs" / "features" / "999-foo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Foo\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 1)

    report = pdsa.run_pdsa(doc)

    assert report.checks["lint"].passed is False
    assert report.passed is False
