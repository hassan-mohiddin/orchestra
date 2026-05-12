"""Regression: codex finding #2 — free-text teach lessons never injected.

LLD-012 SC-11 + Security §Lessons injection allowlist. The injection
emission must only surface kind=violation entries with inject=True via
the fixed allowlisted-fields template (rule_violated/observed/expected).
A `teach` lesson with a body field must NEVER appear in the additionalContext.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cli.hooks import session_start_inject
from cli.lessons_store import append_entry

_VALID_TLDR = (
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- short bullet.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
)


def test_no_free_text_teach_in_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/CLAUDE.md").write_text(_VALID_TLDR, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(session_start_inject, "_count_tokens", lambda _text: 100)
    append_entry({
        "id": "teach-1",
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "kind": "teach",
        "rule_violated": None,
        "body": "MALICIOUS_STEERING_PAYLOAD_DO_NOT_INJECT",
        "source": "user",
        "inject": False,
    })
    rc = session_start_inject.main([])
    assert rc == 0
    additional = json.loads(capsys.readouterr().out)["hookSpecificOutput"][
        "additionalContext"
    ]
    assert "MALICIOUS_STEERING_PAYLOAD_DO_NOT_INJECT" not in additional, (
        "codex #2 regression: free-text teach body leaked into system context"
    )
