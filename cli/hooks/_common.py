"""Shared helpers for orchestra hook handlers (LLD-012 v2.1).

Used by session_start_inject, pre_compact_instruct, user_prompt_reinject.

`build_tldr_context(root)` returns the [ORCHESTRA TLDR] + <system-reminder>
additionalContext string. Centralizes:
- TLDR section reads from schema-layer files
- Recent violation lessons (kind=violation AND inject=True, ≤10)
- 500-token budget enforcement via Anthropic count_tokens (with HTTP timeout)
- Identity-index fallback on missing API key / timeout / over-budget
- Overflow logging to .claude/state/budget-overflow.log

Tests monkeypatch `cli.hooks._common._count_tokens` to mock budget decisions.
"""

from __future__ import annotations

import html
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lessons_store import read_entries
from cli.tldr_extractor import TldrSection, extract_tldr

ORCHESTRA_MARKER = "[ORCHESTRA TLDR]"
CLAUDE_FILE = Path(".claude/CLAUDE.md")
RULES_DIR = Path(".claude/rules")
STATE_DIR = Path(".claude/state")
OVERFLOW_LOG = STATE_DIR / "budget-overflow.log"
TOKEN_BUDGET = 500
FALLBACK_MODEL = "claude-opus-4-7"
HTTP_TIMEOUT_SECONDS = 2.0
LESSONS_SINCE_DAYS = 90
MAX_VIOLATIONS = 10
ALLOWLISTED_VIOLATION_FIELDS = ("rule_violated", "observed", "expected")
MAX_FIELD_CHARS = 200

_logger = logging.getLogger(__name__)


def schema_layer_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    claude_md = root / CLAUDE_FILE
    if claude_md.exists():
        paths.append(claude_md)
    rules_dir = root / RULES_DIR
    if rules_dir.is_dir():
        paths.extend(sorted(rules_dir.glob("*.md")))
    return paths


def read_schema_layer_tldrs(root: Path) -> list[tuple[Path, list[str]]]:
    """Read all valid TLDR sections from schema-layer files under `root`.

    Returns (relative_path, bullets) pairs. Files with no/invalid TLDR are
    silently skipped — hook handlers must never crash on partial state.
    """
    out: list[tuple[Path, list[str]]] = []
    for path in schema_layer_paths(root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        result = extract_tldr(text)
        if isinstance(result, TldrSection) and result.bullets:
            out.append((path.relative_to(root), result.bullets))
    return out


def _load_recent_violations() -> list[dict[str, Any]]:
    entries = read_entries(since_days=LESSONS_SINCE_DAYS)
    violations = [
        e for e in entries
        if e.get("kind") == "violation" and e.get("inject") is True
    ]
    return violations[-MAX_VIOLATIONS:]


def _format_violation_entry(entry: dict[str, Any]) -> str:
    lines: list[str] = []
    for field in ALLOWLISTED_VIOLATION_FIELDS:
        raw = entry.get(field) or ""
        encoded = html.escape(str(raw), quote=False)
        if len(encoded) > MAX_FIELD_CHARS:
            encoded = encoded[:MAX_FIELD_CHARS]
        lines.append(f"  {field}: {encoded}")
    return "\n".join(lines)


def _format_full(
    tldrs: list[tuple[Path, list[str]]],
    violations: list[dict[str, Any]],
) -> str:
    lines: list[str] = [ORCHESTRA_MARKER, "<system-reminder>"]
    for rel_path, bullets in tldrs:
        lines.append(f"## {rel_path.as_posix()}")
        lines.extend(f"- {b}" for b in bullets)
        lines.append("")
    if violations:
        lines.append("## Recent violations")
        for entry in violations:
            lines.append("- entry:")
            lines.append(_format_violation_entry(entry))
    lines.append("</system-reminder>")
    return "\n".join(lines)


def _format_fallback(tldrs: list[tuple[Path, list[str]]]) -> str:
    names = ", ".join(p.name for p, _ in tldrs) if tldrs else "(none)"
    return "\n".join(
        [
            ORCHESTRA_MARKER,
            "<system-reminder>",
            f"Rule files in effect: {names}",
            "(TLDR injection over budget — see .claude/state/budget-overflow.log)",
            "</system-reminder>",
        ]
    )


def _count_tokens(text: str) -> int | None:
    """Return Anthropic token count for `text`, or None when API unavailable.

    Returns None on: missing ANTHROPIC_API_KEY, SDK import failure, HTTP error,
    timeout. Caller treats None as "fall back to identity index" to keep
    Claude Code startup non-blocking (LLD-012 Out-of-Scope adversarial Crit #1).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=HTTP_TIMEOUT_SECONDS)
        result = client.messages.count_tokens(
            model=FALLBACK_MODEL,
            messages=[{"role": "user", "content": text}],
        )
        return int(result.input_tokens)
    except Exception:
        return None


def _log_overflow(root: Path, tokens: int) -> None:
    state_dir = root / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    line = (
        f"{datetime.now(timezone.utc).isoformat()} "
        f"tokens={tokens} budget={TOKEN_BUDGET}\n"
    )
    (root / OVERFLOW_LOG).open("a", encoding="utf-8").write(line)


def build_tldr_context(root: Path) -> str:
    """Return the additionalContext string for SessionStart / UserPromptSubmit.

    Caller wraps this in `{"hookSpecificOutput": {"hookEventName": ..., "additionalContext": ...}}`.
    """
    tldrs = read_schema_layer_tldrs(root)
    violations = _load_recent_violations()
    full = _format_full(tldrs, violations)
    tokens = _count_tokens(full)
    if tokens is None:
        return _format_fallback(tldrs)
    if tokens > TOKEN_BUDGET:
        _log_overflow(root, tokens)
        return _format_fallback(tldrs)
    return full


def emit_json(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
