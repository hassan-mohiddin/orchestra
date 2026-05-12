"""Slice 8.1 — Integration: subprocess-invoke each hook handler.

Asserts JSON envelope shape + [ORCHESTRA TLDR] marker + <system-reminder>
wrap end-to-end via `python -m cli.hooks.<module>`.

Tests skip the Anthropic token-budget API by monkeypatching the env var
out and relying on the identity-index fallback branch (Slice 3.2).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_TLDR_FIXTURE = (
    "# Fixture\n"
    "\n"
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- INTEGRATION_KEYWORD survives end-to-end test.\n"
    "- SECOND_ANCHOR also present.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
    "\n"
    "body.\n"
)


@pytest.fixture
def hook_workspace(tmp_path: Path) -> Path:
    (tmp_path / ".claude/rules").mkdir(parents=True)
    (tmp_path / ".claude/CLAUDE.md").write_text(_TLDR_FIXTURE, encoding="utf-8")
    (tmp_path / ".claude/rules/sample.md").write_text(_TLDR_FIXTURE, encoding="utf-8")
    return tmp_path


def _run_hook(module: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("ANTHROPIC_API_KEY",)
    }
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.setdefault("PATH", os.environ.get("PATH", ""))
    return subprocess.run(
        [sys.executable, "-m", module],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_session_start_hook_emits_json_with_marker(hook_workspace: Path) -> None:
    proc = _run_hook("cli.hooks.session_start_inject", hook_workspace)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    additional = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert additional.startswith("[ORCHESTRA TLDR]\n")


def test_pre_compact_hook_emits_compact_instructions(hook_workspace: Path) -> None:
    proc = _run_hook("cli.hooks.pre_compact_instruct", hook_workspace)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    text = payload["compact_instructions"]
    assert text.startswith("[ORCHESTRA TLDR]\n")
    assert "INTEGRATION_KEYWORD" in text


def test_user_prompt_reinject_silent_on_non_nth_turn(hook_workspace: Path) -> None:
    """First invocation increments counter to 1 — non-Nth → silent (no stdout)."""
    proc = _run_hook("cli.hooks.user_prompt_reinject", hook_workspace)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "", f"non-Nth turn must be silent, got: {proc.stdout!r}"


def test_user_prompt_reinject_fires_on_fifth_turn(hook_workspace: Path) -> None:
    """5 invocations → 5th fires the injection JSON."""
    for _ in range(4):
        proc = _run_hook("cli.hooks.user_prompt_reinject", hook_workspace)
        assert proc.returncode == 0
        assert proc.stdout == ""
    proc = _run_hook("cli.hooks.user_prompt_reinject", hook_workspace)
    assert proc.returncode == 0
    assert proc.stdout != ""
    payload = json.loads(proc.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert payload["hookSpecificOutput"]["additionalContext"].startswith(
        "[ORCHESTRA TLDR]\n"
    )
