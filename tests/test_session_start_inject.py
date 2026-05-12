import json
from pathlib import Path

import pytest

from cli.hooks import session_start_inject

_VALID_TLDR = (
    "# Rule\n"
    "\n"
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- ALPHA bullet one of rule X.\n"
    "- BETA bullet two of rule X.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
    "\n"
    "Full body here.\n"
)


def _seed_schema_layer(root: Path) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude/rules").mkdir(parents=True, exist_ok=True)
    (root / ".claude/CLAUDE.md").write_text(_VALID_TLDR, encoding="utf-8")
    (root / ".claude/rules/documentation-gate.md").write_text(_VALID_TLDR, encoding="utf-8")


def test_emits_tldr_in_system_reminder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_schema_layer(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = session_start_inject.main([])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    additional = payload["hookSpecificOutput"]["additionalContext"]
    assert additional.startswith("[ORCHESTRA TLDR]\n")
    assert "<system-reminder>" in additional
    assert "</system-reminder>" in additional
    assert "ALPHA bullet one of rule X." in additional
    assert "BETA bullet two of rule X." in additional
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
