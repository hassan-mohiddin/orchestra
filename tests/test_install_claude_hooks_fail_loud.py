"""Regression: codex #3 — hooks must fail loud, never silently no-op.

Slice 3.6 covers the hook-runtime side: if main() raises an unexpected
exception (e.g., upstream import error, broken state file, missing
schema-layer files combined with downstream crash), the __main__ guard
must convert the crash to a non-zero exit code + stderr diagnostic.

Phase 4 will add install-side coverage to this same file:
`test_missing_interpreter_resolution_fails_verify` etc.
"""

import pytest

from cli.hooks import pre_compact_instruct, session_start_inject, user_prompt_reinject


def _raiser(*_args: object, **_kwargs: object) -> object:
    raise RuntimeError("synthetic-hook-crash")


def test_session_start_inject_run_exits_2_on_exception(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(session_start_inject, "build_tldr_context", _raiser)
    rc = session_start_inject._run()
    err = capsys.readouterr().err
    assert rc == 2
    assert "FAIL: cli.hooks.session_start_inject crashed" in err
    assert "synthetic-hook-crash" in err


def test_pre_compact_instruct_run_exits_2_on_exception(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(pre_compact_instruct, "read_schema_layer_tldrs", _raiser)
    rc = pre_compact_instruct._run()
    err = capsys.readouterr().err
    assert rc == 2
    assert "FAIL: cli.hooks.pre_compact_instruct crashed" in err


def test_user_prompt_reinject_run_exits_2_on_exception(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(user_prompt_reinject, "_read_counter", _raiser)
    rc = user_prompt_reinject._run()
    err = capsys.readouterr().err
    assert rc == 2
    assert "FAIL: cli.hooks.user_prompt_reinject crashed" in err
