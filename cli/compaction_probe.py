"""Compaction probe: assert TLDR keywords survive Anthropic compact_20260112 (LLD-012 SC-5).

Slice 6.5: deterministic keyword extraction (pre-API). One canonical
keyword per TLDR bullet is selected via a 4+char first-non-stopword
rule. If every token in a bullet is a common imperative/connector, the
keyword falls back to `ORCHESTRA-TLDR-<first-token>` for collision-resistance.

Slice 6.6 (Q3-gated): wire `anthropic.compact_20260112` (or fallback
endpoint) + assert each keyword survives the compacted summary.

Out-of-Scope adversarial Crit #4 (compaction non-determinism) — v2.2
hardening: n-trial sampling + statistical confidence + seed-pinning.
"""

from __future__ import annotations

import re
from pathlib import Path

from cli.hooks._common import read_schema_layer_tldrs

KEYWORD_PREFIX = "ORCHESTRA-TLDR-"
MIN_TOKEN_LENGTH = 4
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*[A-Za-z0-9]|[A-Za-z0-9]")

# Bullet-leading imperatives + connectors that are too generic to anchor on.
STOPWORDS: frozenset[str] = frozenset(
    word.lower()
    for word in (
        # imperatives we use in bullets
        "STOP", "ASK", "RUN", "USE", "DO", "MUST", "READ", "VERIFY", "SAVE",
        "SEE", "ROUTE", "DOGFOOD", "NAMESPACE", "BATCH", "OVERRIDE",
        "INVESTIGATE", "INVESTIGATION", "PROMOTE", "ADR", "BYPASS",
        "RESOLVE", "NEVER", "FROM", "TASKCREATE", "TASK", "TLDR",
        "MARK", "TEST", "TESTS", "FIX", "FIXES", "DESIGN", "WORKFLOW",
        # connectors
        "FOR", "BY", "THE", "AND", "OR", "ON", "IN", "AT", "TO", "OF",
        "WITH", "WITHOUT", "INTO", "EVERY", "ALL", "ANY", "EACH",
        "BEFORE", "AFTER", "ALWAYS", "MORE", "LESS", "AGAIN",
        # generic content
        "CODE", "DOC", "DOCS", "WORK", "STEP", "TURN", "FIRST",
        "ITEM", "ITEMS", "THING", "THINGS", "STUFF",
    )
)


def _is_stopword(token: str) -> bool:
    return token.lower() in STOPWORDS


def extract_keyword(bullet: str) -> str:
    """Pick a deterministic, collision-resistant keyword for one TLDR bullet.

    Algorithm:
      1. Tokenize on word boundaries (allow . _ - / inside tokens for paths).
      2. Take first token that is ≥MIN_TOKEN_LENGTH chars AND not a stopword.
      3. Return token verbatim (case preserved — `HANDOFF.md` stays distinctive).
      4. If every token is filtered out, return `ORCHESTRA-TLDR-<first-token>`
         to keep the keyword maximally distinctive for the compaction probe.
    """
    tokens = TOKEN_RE.findall(bullet)
    if not tokens:
        return f"{KEYWORD_PREFIX}empty"
    for token in tokens:
        if len(token) >= MIN_TOKEN_LENGTH and not _is_stopword(token):
            return token
    return f"{KEYWORD_PREFIX}{tokens[0]}"


def extract_keywords_from_tldrs(
    tldrs: list[tuple[Path, list[str]]]
) -> list[tuple[Path, list[str]]]:
    """Return (path, [keywords]) for each schema-layer TLDR section."""
    return [(path, [extract_keyword(b) for b in bullets]) for path, bullets in tldrs]


def gather_keywords(root: Path | None = None) -> list[str]:
    """Read all schema-layer TLDR sections and emit one keyword per bullet."""
    if root is None:
        root = Path.cwd()
    tldrs = read_schema_layer_tldrs(root)
    return [kw for _path, kws in extract_keywords_from_tldrs(tldrs) for kw in kws]
