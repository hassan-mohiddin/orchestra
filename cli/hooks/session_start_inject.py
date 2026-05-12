"""SessionStart hook handler — emits TLDR sections from schema-layer files.

Reads `## TLDR — Nonnegotiables` sections from `.claude/CLAUDE.md` and
`.claude/rules/*.md`, formats them under an `[ORCHESTRA TLDR]` marker +
`<system-reminder>` wrap, and emits the JSON envelope Claude Code expects
on stdout.

Slice 3.1: minimal happy path — no token budget, no lessons inclusion.
Subsequent slices add budget enforcement (3.2) and structured violations (3.3).
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
HOOK_EVENT = "SessionStart"
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


def _schema_layer_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    claude_md = root / CLAUDE_FILE
    if claude_md.exists():
        paths.append(claude_md)
    rules_dir = root / RULES_DIR
    if rules_dir.is_dir():
        paths.extend(sorted(rules_dir.glob("*.md")))
    return paths


def _read_tldrs(root: Path) -> list[tuple[Path, list[str]]]:
    out: list[tuple[Path, list[str]]] = []
    for path in _schema_layer_paths(root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        result = extract_tldr(text)
        if isinstance(result, TldrSection) and result.bullets:
            out.append((path.relative_to(root), result.bullets))
    return out


def _load_recent_violations() -> list[dict[str, Any]]:
    """Return ≤MAX_VIOLATIONS most-recent kind=violation, inject=True lessons.

    LLD-012 SC-11 + Security §Lessons injection allowlist: free-text `teach`
    entries are NEVER surfaced; only structured violations may flow into
    system-priority context.
    """
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


def _format_additional_context(
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
    Claude Code startup non-blocking.
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


def _emit(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    tldrs = _read_tldrs(root)
    violations = _load_recent_violations()
    full = _format_additional_context(tldrs, violations)
    tokens = _count_tokens(full)
    if tokens is None:
        additional = _format_fallback(tldrs)
    elif tokens > TOKEN_BUDGET:
        _log_overflow(root, tokens)
        additional = _format_fallback(tldrs)
    else:
        additional = full
    payload: dict[str, object] = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": additional,
        },
    }
    _emit(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
