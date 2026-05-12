"""SessionStart hook handler — emits TLDR sections from schema-layer files.

Reads `## TLDR — Nonnegotiables` sections from `.claude/CLAUDE.md` and
`.claude/rules/*.md`, formats them under an `[ORCHESTRA TLDR]` marker +
`<system-reminder>` wrap, and emits the JSON envelope Claude Code expects
on stdout.

Slice 3.1: minimal happy path — no token budget, no lessons inclusion.
Subsequent slices add budget enforcement (3.2) and structured violations (3.3).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cli.tldr_extractor import TldrSection, extract_tldr

ORCHESTRA_MARKER = "[ORCHESTRA TLDR]"
HOOK_EVENT = "SessionStart"
CLAUDE_FILE = Path(".claude/CLAUDE.md")
RULES_DIR = Path(".claude/rules")


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


def _format_additional_context(tldrs: list[tuple[Path, list[str]]]) -> str:
    lines: list[str] = [ORCHESTRA_MARKER, "<system-reminder>"]
    for rel_path, bullets in tldrs:
        lines.append(f"## {rel_path.as_posix()}")
        lines.extend(f"- {b}" for b in bullets)
        lines.append("")
    lines.append("</system-reminder>")
    return "\n".join(lines)


def _emit(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    tldrs = _read_tldrs(root)
    additional = _format_additional_context(tldrs)
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
