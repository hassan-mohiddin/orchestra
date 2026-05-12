"""SessionStart hook handler — emits TLDR + structured violations.

Reads TLDR sections from `.claude/CLAUDE.md` + `.claude/rules/*.md` plus the
last ≤10 inject=True violation lessons, enforces a 500-token budget via the
Anthropic count_tokens API (fallback to identity index on missing API key /
timeout / over-budget), and emits the SessionStart hookSpecificOutput JSON.

LLD-012 SC-3, SC-11. Shared injection logic lives in cli/hooks/_common.py.
"""

from __future__ import annotations

from pathlib import Path

from cli.hooks._common import (
    TOKEN_BUDGET,
    build_tldr_context,
    emit_json,
)

__all__ = ["TOKEN_BUDGET", "main"]

HOOK_EVENT = "SessionStart"


def main(argv: list[str] | None = None) -> int:
    additional = build_tldr_context(Path.cwd())
    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT,
                "additionalContext": additional,
            }
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
