"""UserPromptSubmit hook handler — Nth-turn TLDR re-injection (LLD-012 SC-14).

Increments a per-repo turn counter at `.claude/state/turn-counter.json` on
every user prompt. On every Nth turn (default N=5, configurable via
`ORCHESTRA_REINJECT_EVERY`), emits the same TLDR + structured-violation
additionalContext SessionStart uses. Non-Nth turns exit 0 with no stdout.

Atomic counter write (tempfile + os.replace) per Q6 default. Best-effort
under concurrent sessions — Out-of-Scope adversarial Crit #2 documents
the unresolved race under heavy concurrency; v2.2 hardening pass moves
to per-session counters or claude-code-native counter API.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from cli.hooks._common import build_tldr_context, emit_json

STATE_DIR = Path(".claude/state")
COUNTER_FILE = STATE_DIR / "turn-counter.json"
DEFAULT_REINJECT_EVERY = 5
HOOK_EVENT = "UserPromptSubmit"


def _resolve_every() -> int:
    raw = os.environ.get("ORCHESTRA_REINJECT_EVERY")
    if raw is None:
        return DEFAULT_REINJECT_EVERY
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_REINJECT_EVERY
    return value if value >= 1 else DEFAULT_REINJECT_EVERY


def _read_counter(root: Path) -> int:
    path = root / COUNTER_FILE
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("count", 0))
    except (json.JSONDecodeError, ValueError, TypeError, OSError):
        return 0


def _write_counter_atomic(root: Path, count: int) -> None:
    state_dir = root / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    target = root / COUNTER_FILE
    fd, tmp_path = tempfile.mkstemp(
        prefix=".turn-counter-", suffix=".json.tmp", dir=str(state_dir)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"count": count}, f)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    every = _resolve_every()
    counter = _read_counter(root) + 1
    _write_counter_atomic(root, counter)
    if counter % every != 0:
        return 0
    additional = build_tldr_context(root)
    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT,
                "additionalContext": additional,
            }
        }
    )
    return 0


def _run() -> int:
    try:
        return main()
    except Exception as exc:
        sys.stderr.write(
            f"FAIL: cli.hooks.user_prompt_reinject crashed: {exc}\n"
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(_run())
