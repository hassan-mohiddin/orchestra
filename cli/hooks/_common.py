"""Shared helpers for orchestra hook handlers (LLD-012 v2.1).

Used by session_start_inject, pre_compact_instruct, user_prompt_reinject.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cli.tldr_extractor import TldrSection, extract_tldr

ORCHESTRA_MARKER = "[ORCHESTRA TLDR]"
CLAUDE_FILE = Path(".claude/CLAUDE.md")
RULES_DIR = Path(".claude/rules")


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


def emit_json(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
