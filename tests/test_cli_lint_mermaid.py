"""Tests for cli.lint --mermaid mermaid block validation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from cli.lint import _load_extract_mermaid, lint_mermaid

VALID_DOC = """# Test Doc

```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Hello
```

End.
"""

BROKEN_DOC = """# Test Doc

```mermaid
this is not valid mermaid syntax at all
nor does it declare a diagram type
```
"""

UNBALANCED_DOC = """# Test Doc

```mermaid
graph TD
    A[Start
    B[End]
```
"""


def test_lint_passes_valid_mermaid(tmp_path: Path) -> None:
    doc = tmp_path / "valid.md"
    doc.write_text(VALID_DOC)
    with patch("cli.lint.shutil.which", return_value=None):
        # Force fallback to basic_syntax_check
        findings = lint_mermaid(doc)
    assert not findings


def test_lint_falls_back_when_npx_absent(tmp_path: Path) -> None:
    doc = tmp_path / "broken.md"
    doc.write_text(BROKEN_DOC)
    with patch("cli.lint.shutil.which", return_value=None):
        findings = lint_mermaid(doc)
    # basic_syntax_check should flag missing diagram type
    assert any("syntax" in f.message for f in findings)


def test_basic_syntax_check_catches_unbalanced_braces(tmp_path: Path) -> None:
    doc = tmp_path / "unbalanced.md"
    doc.write_text(UNBALANCED_DOC)
    with patch("cli.lint.shutil.which", return_value=None):
        findings = lint_mermaid(doc)
    assert any("unbalanced" in f.message for f in findings)


def test_extract_diagrams_from_file_helper(tmp_path: Path) -> None:
    doc = tmp_path / "valid.md"
    doc.write_text(VALID_DOC)
    em = _load_extract_mermaid()
    diagrams = em.extract_diagrams_from_file(doc)
    assert len(diagrams) == 1


def test_lint_no_mermaid_blocks_returns_empty(tmp_path: Path) -> None:
    doc = tmp_path / "no_mermaid.md"
    doc.write_text("# Just markdown\n\nNo mermaid here.\n")
    findings = lint_mermaid(doc)
    assert not findings
