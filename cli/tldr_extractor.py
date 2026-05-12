"""TLDR section extractor for orchestra schema-layer files (LLD-012 SC-1 substrate).

`extract_tldr` is pure parsing — no I/O. A thin __main__ CLI reads a single
file path and exits 0 (OK) / 1 (TldrError) / 2 (bad args) for use as a
verification step during TLDR authoring.

Format spec: docs/features/012-rule-durability-and-learning-layer.md § TLDR section format.
"""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_logger = logging.getLogger(__name__)

TLDR_HEADER_RE = re.compile(r"^## TLDR — Nonnegotiables\s*$", re.MULTILINE)
TLDR_CLOSE_MARKER = "<!-- Full rule body below this section -->"
BULLET_RE = re.compile(r"^-\s+(.+?)\s*$")
MAX_BULLETS = 7
MAX_BULLET_LENGTH = 80


@dataclass
class TldrSection:
    bullets: list[str] = field(default_factory=list)


@dataclass
class TldrError:
    reason: str
    detail: str = ""


def extract_tldr(text: str) -> TldrSection | TldrError:
    matches = list(TLDR_HEADER_RE.finditer(text))
    if not matches:
        return TldrError(reason="no_tldr_section")
    if len(matches) > 1:
        return TldrError(
            reason="ambiguous_tldr",
            detail=f"found {len(matches)} TLDR sections; expected exactly 1",
        )
    header_end = matches[0].end()
    close_idx = text.find(TLDR_CLOSE_MARKER, header_end)
    if close_idx == -1:
        _logger.warning(
            "TLDR close marker %r missing; extracting bullets to EOF",
            TLDR_CLOSE_MARKER,
        )
        body = text[header_end:]
    else:
        body = text[header_end:close_idx]
    bullets = [m.group(1) for line in body.splitlines() if (m := BULLET_RE.match(line))]
    if not bullets:
        return TldrError(
            reason="empty_tldr",
            detail="header found but no bullets",
        )
    if len(bullets) > MAX_BULLETS:
        return TldrError(
            reason="overflow",
            detail=f"bullet count {len(bullets)} exceeds max {MAX_BULLETS}",
        )
    over_length = [b for b in bullets if len(b) > MAX_BULLET_LENGTH]
    if over_length:
        sample = "; ".join(f"{b[:40]}…" for b in over_length[:3])
        return TldrError(
            reason="overflow",
            detail=f"bullet length exceeds {MAX_BULLET_LENGTH} chars: {sample}",
        )
    return TldrSection(bullets=bullets)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m cli.tldr_extractor <file>", file=sys.stderr)
        return 2
    text = Path(args[0]).read_text(encoding="utf-8")
    result = extract_tldr(text)
    if isinstance(result, TldrError):
        print(f"FAIL: {result.reason}: {result.detail}", file=sys.stderr)
        return 1
    print(f"OK: {len(result.bullets)} bullets")
    for bullet in result.bullets:
        print(f"  - {bullet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
