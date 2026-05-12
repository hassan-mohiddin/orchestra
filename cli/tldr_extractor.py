"""TLDR section extractor for orchestra schema-layer files (LLD-012 SC-1 substrate).

Parses `## TLDR — Nonnegotiables` ... `<!-- Full rule body below this section -->`
sections. Pure parsing — no I/O. Caller is responsible for reading file contents.

Format spec: docs/features/012-rule-durability-and-learning-layer.md § TLDR section format.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

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
