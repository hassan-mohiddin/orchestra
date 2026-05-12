import json
import sys
from pathlib import Path

import pytest

from cli.install_claude_hooks import install


def test_install_writes_settings_with_resolved_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    path = install(tmp_path)
    assert path == tmp_path / ".claude/settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    hooks = data["hooks"]

    assert "SessionStart" in hooks
    ss = hooks["SessionStart"][0]
    assert ss["matcher"] == "startup|resume|clear|compact"
    ss_cmd = ss["hooks"][0]["command"]
    assert sys.executable in ss_cmd
    assert "cli.hooks.session_start_inject" in ss_cmd

    assert "PreCompact" in hooks
    pc_cmd = hooks["PreCompact"][0]["hooks"][0]["command"]
    assert "cli.hooks.pre_compact_instruct" in pc_cmd

    assert "UserPromptSubmit" in hooks
    ups_cmd = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "cli.hooks.user_prompt_reinject" in ups_cmd
