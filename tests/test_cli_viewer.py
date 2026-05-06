"""Tests for cli.viewer — Tier 2 mermaid export."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.viewer import (
    GITIGNORE_RENDERED_ENTRY,
    RenderResult,
    ViewerError,
    _ensure_gitignore_rendered,
    render_all,
    render_doc,
)

VALID_DOC = """# Test

```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: hi
```

```mermaid
graph TD
    X --> Y
```
"""

NO_MERMAID_DOC = "# Just markdown\n\nNo diagrams.\n"


def test_render_doc_extracts_blocks(tmp_path: Path) -> None:
    doc = tmp_path / "valid.md"
    doc.write_text(VALID_DOC)
    output = tmp_path / "out"

    fake_proc = MagicMock(returncode=0, stdout="", stderr="")

    with patch("cli.viewer.shutil.which", return_value="/usr/bin/npx"), \
         patch("cli.viewer.subprocess.run", return_value=fake_proc) as run_mock:
        result = render_doc(doc, output)

    assert result.ok
    assert run_mock.call_count == 2  # 2 mermaid blocks
    # Verify subprocess invocation shape
    call_args = run_mock.call_args_list[0][0][0]
    assert call_args[0] == "npx"
    assert "@mermaid-js/mermaid-cli" in call_args


def test_render_no_blocks_no_op(tmp_path: Path) -> None:
    doc = tmp_path / "no_mermaid.md"
    doc.write_text(NO_MERMAID_DOC)
    output = tmp_path / "out"

    with patch("cli.viewer.shutil.which", return_value="/usr/bin/npx"):
        result = render_doc(doc, output)

    assert result.ok
    assert result.skipped == "no mermaid blocks"
    assert not output.exists()


def test_render_npx_absent_raises(tmp_path: Path) -> None:
    doc = tmp_path / "valid.md"
    doc.write_text(VALID_DOC)
    output = tmp_path / "out"

    with patch("cli.viewer.shutil.which", return_value=None):
        with pytest.raises(ViewerError):
            render_doc(doc, output)


def test_render_all_walks_docs(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "a.md").write_text(VALID_DOC)
    (docs / "b.md").write_text(NO_MERMAID_DOC)
    output = tmp_path / "rendered"

    fake_proc = MagicMock(returncode=0, stdout="", stderr="")
    with patch("cli.viewer.shutil.which", return_value="/usr/bin/npx"), \
         patch("cli.viewer.subprocess.run", return_value=fake_proc):
        results = render_all(tmp_path, output)

    assert len(results) == 2
    rendered_total = sum(len(r.rendered) for r in results)
    assert rendered_total == 2  # only a.md has 2 blocks; b.md has 0


def test_render_continues_on_parse_error(tmp_path: Path) -> None:
    doc = tmp_path / "valid.md"
    doc.write_text(VALID_DOC)
    output = tmp_path / "out"

    # First call succeeds, second fails
    proc_ok = MagicMock(returncode=0, stdout="", stderr="")
    proc_fail = MagicMock(returncode=1, stdout="", stderr="parse error\nbad token")

    with patch("cli.viewer.shutil.which", return_value="/usr/bin/npx"), \
         patch("cli.viewer.subprocess.run", side_effect=[proc_ok, proc_fail]):
        result = render_doc(doc, output)

    assert len(result.rendered) == 1
    assert len(result.failed) == 1


def test_gitignore_append_first_run(tmp_path: Path) -> None:
    appended = _ensure_gitignore_rendered(tmp_path)
    assert appended
    content = (tmp_path / ".gitignore").read_text()
    assert GITIGNORE_RENDERED_ENTRY in content


def test_gitignore_no_double_append(tmp_path: Path) -> None:
    _ensure_gitignore_rendered(tmp_path)
    appended = _ensure_gitignore_rendered(tmp_path)
    assert not appended
    content = (tmp_path / ".gitignore").read_text()
    assert content.count(GITIGNORE_RENDERED_ENTRY) == 1


def test_gitignore_preserves_existing(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    _ensure_gitignore_rendered(tmp_path)
    content = (tmp_path / ".gitignore").read_text()
    assert "node_modules/" in content
    assert GITIGNORE_RENDERED_ENTRY in content


def test_render_doc_timeout(tmp_path: Path) -> None:
    import subprocess
    doc = tmp_path / "valid.md"
    doc.write_text(VALID_DOC)
    output = tmp_path / "out"

    with patch("cli.viewer.shutil.which", return_value="/usr/bin/npx"), \
         patch("cli.viewer.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="npx", timeout=60)):
        result = render_doc(doc, output)

    assert not result.ok
    assert any("timeout" in err.lower() for _, err in result.failed)
