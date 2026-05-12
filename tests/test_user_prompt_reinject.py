import json
from pathlib import Path

import pytest

from cli.hooks import user_prompt_reinject

_VALID_TLDR = (
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- KEEP THIS BULLET ALIVE.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
)


def _seed(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".claude/CLAUDE.md").write_text(_VALID_TLDR, encoding="utf-8")


def test_counter_increments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.hooks._common._count_tokens", lambda _text: 100)
    monkeypatch.delenv("ORCHESTRA_REINJECT_EVERY", raising=False)
    for _ in range(3):
        user_prompt_reinject.main([])
        capsys.readouterr()
    counter_file = tmp_path / ".claude/state/turn-counter.json"
    assert counter_file.exists()
    assert json.loads(counter_file.read_text(encoding="utf-8"))["count"] == 3


def test_emits_on_nth_turn_silent_otherwise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.hooks._common._count_tokens", lambda _text: 100)
    monkeypatch.delenv("ORCHESTRA_REINJECT_EVERY", raising=False)
    silent_outputs: list[str] = []
    emit_outputs: list[str] = []
    for turn in range(1, 11):
        user_prompt_reinject.main([])
        out = capsys.readouterr().out
        if turn % 5 == 0:
            emit_outputs.append(out)
        else:
            silent_outputs.append(out)
    assert all(o == "" for o in silent_outputs), (
        f"non-Nth turns must be silent, got: {silent_outputs!r}"
    )
    assert len(emit_outputs) == 2, "expected emit on turns 5 + 10"
    for raw in emit_outputs:
        payload = json.loads(raw)
        assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        additional = payload["hookSpecificOutput"]["additionalContext"]
        assert additional.startswith("[ORCHESTRA TLDR]\n")
        assert "KEEP THIS BULLET ALIVE." in additional


def test_reinject_every_env_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.hooks._common._count_tokens", lambda _text: 100)
    monkeypatch.setenv("ORCHESTRA_REINJECT_EVERY", "2")
    fires = 0
    for _ in range(6):
        user_prompt_reinject.main([])
        if capsys.readouterr().out:
            fires += 1
    assert fires == 3, "ORCHESTRA_REINJECT_EVERY=2 should fire on turns 2, 4, 6"
