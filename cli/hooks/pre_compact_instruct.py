"""PreCompact hook handler — emits compact_instructions preserving TLDR.

Reads `## TLDR — Nonnegotiables` sections from schema-layer files and emits
a JSON envelope with `compact_instructions` string that asks the compaction
summarizer to preserve the TLDR bullets verbatim through the summary.

Per LLD-012 SC-4 + §line 241: "emits compact_instructions string preserving
TLDR keywords verbatim".
"""

from __future__ import annotations

from pathlib import Path

from cli.hooks._common import (
    ORCHESTRA_MARKER,
    emit_json,
    read_schema_layer_tldrs,
)


def _format_compact_instructions(tldrs: list[tuple[Path, list[str]]]) -> str:
    lines: list[str] = [
        ORCHESTRA_MARKER,
        (
            "Preserve the following non-negotiable rules verbatim through "
            "any compaction summary. These rules are load-bearing — do not "
            "paraphrase, omit, or condense."
        ),
        "",
    ]
    for rel_path, bullets in tldrs:
        lines.append(f"## {rel_path.as_posix()}")
        lines.extend(f"- {b}" for b in bullets)
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    tldrs = read_schema_layer_tldrs(root)
    instructions = _format_compact_instructions(tldrs)
    emit_json({"compact_instructions": instructions})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
