import json
from pathlib import Path

import pytest

from cli.hooks import pre_compact_instruct

_VALID_TLDR = (
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- KEYWORD_ALPHA preserved through compaction.\n"
    "- KEYWORD_BETA also preserved.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
)


def test_emits_compact_instructions_with_tldr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / ".claude/rules").mkdir(parents=True)
    (tmp_path / ".claude/CLAUDE.md").write_text(_VALID_TLDR, encoding="utf-8")
    (tmp_path / ".claude/rules/sample.md").write_text(_VALID_TLDR, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = pre_compact_instruct.main([])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "compact_instructions" in payload
    text = payload["compact_instructions"]
    assert text.startswith("[ORCHESTRA TLDR]\n")
    assert "Preserve the following non-negotiable rules verbatim" in text
    assert "KEYWORD_ALPHA preserved through compaction." in text
    assert "KEYWORD_BETA also preserved." in text
    assert ".claude/CLAUDE.md" in text
    assert ".claude/rules/sample.md" in text
