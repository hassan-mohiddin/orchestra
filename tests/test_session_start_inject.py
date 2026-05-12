import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cli.hooks import session_start_inject
from cli.hooks.session_start_inject import TOKEN_BUDGET
from cli.lessons_store import append_entry

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def test_emits_tldr_in_system_reminder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_schema_layer(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.hooks._common._count_tokens", lambda _text: 100)
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


def test_missing_api_key_falls_back_to_identity_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_schema_layer(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rc = session_start_inject.main([])
    assert rc == 0
    additional = json.loads(capsys.readouterr().out)["hookSpecificOutput"][
        "additionalContext"
    ]
    assert additional.startswith("[ORCHESTRA TLDR]\n")
    assert "Rule files in effect" in additional
    assert "CLAUDE.md" in additional
    assert "documentation-gate.md" in additional
    assert "ALPHA bullet one of rule X." not in additional


def test_overbudget_falls_back_to_identity_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_schema_layer(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")
    monkeypatch.setattr(
        "cli.hooks._common._count_tokens", lambda _text: TOKEN_BUDGET + 1
    )
    rc = session_start_inject.main([])
    assert rc == 0
    additional = json.loads(capsys.readouterr().out)["hookSpecificOutput"][
        "additionalContext"
    ]
    assert "Rule files in effect" in additional
    assert "ALPHA bullet one of rule X." not in additional
    overflow_log = tmp_path / ".claude/state/budget-overflow.log"
    assert overflow_log.exists()
    assert "501" in overflow_log.read_text(encoding="utf-8")


def test_includes_only_violation_kind_inject_true(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_schema_layer(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.hooks._common._count_tokens", lambda _text: 100)
    append_entry({
        "id": "t1",
        "ts": _now_iso(),
        "kind": "teach",
        "rule_violated": None,
        "body": "TEACH_BODY_SECRET_DO_NOT_INJECT",
        "source": "user",
        "inject": False,
    })
    append_entry({
        "id": "v1",
        "ts": _now_iso(),
        "kind": "violation",
        "rule_violated": "documentation-gate",
        "observed": "agent skipped spec-review",
        "expected": "spec-review runs on every doc",
        "source": "user",
        "inject": True,
    })
    append_entry({
        "id": "v2-noinject",
        "ts": _now_iso(),
        "kind": "violation",
        "rule_violated": "should-not-appear",
        "observed": "x",
        "expected": "y",
        "source": "user",
        "inject": False,
    })
    rc = session_start_inject.main([])
    assert rc == 0
    additional = json.loads(capsys.readouterr().out)["hookSpecificOutput"][
        "additionalContext"
    ]
    assert "Recent violations" in additional
    assert "documentation-gate" in additional
    assert "agent skipped spec-review" in additional
    assert "should-not-appear" not in additional
    assert "TEACH_BODY_SECRET_DO_NOT_INJECT" not in additional
