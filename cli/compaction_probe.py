"""Compaction probe: assert TLDR keywords survive Anthropic compact_20260112 (LLD-012 SC-5).

Slice 6.5: deterministic keyword extraction (pre-API). One canonical
keyword per TLDR bullet is selected via a 4+char first-non-stopword
rule. If every token in a bullet is a common imperative/connector, the
keyword falls back to `ORCHESTRA-TLDR-<first-token>` for collision-resistance.

Slice 6.6 (Q3 resolved): `compact_20260112` is NOT exposed via the
Anthropic Python SDK 0.101.0 (verified at slice-6.6 prep time). Per the
plan §Q3 default — degrade the probe to a `messages.create` summarization
endpoint asking the model to produce a compaction-style summary while
preserving TLDR keywords verbatim. CI gate fails if any keyword is lost.

Out-of-Scope adversarial Crit #4 (compaction non-determinism) — v2.2
hardening: n-trial sampling + statistical confidence + seed-pinning.
The current single-run probe is best-effort; the ORCHESTRA-TLDR- prefix
fallback (slice 6.5) gives keywords maximum collision-resistance against
paraphrase loss.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

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


ANTHROPIC_MODEL = "claude-opus-4-7"
PROBE_MAX_TOKENS = 1024
PROBE_TIMEOUT_SECONDS = 30.0
PROBE_SYSTEM_PROMPT = (
    "You are simulating a context-compaction summarizer. Summarize the user "
    "message in <=200 words, preserving any rule keywords verbatim. Do NOT "
    "paraphrase identifier-style tokens (`HANDOFF.md`, `TaskList`, "
    "`.claude/workflow.md`, `ORCHESTRA-TLDR-*`, etc.); keep them as-is."
)


def _run_compaction_summary(text_to_summarize: str) -> str | None:
    """Q3-fallback path: invoke messages.create as a compaction-summary proxy.

    Returns the summary text, or None when:
    - ANTHROPIC_API_KEY env var missing
    - anthropic SDK import fails
    - HTTP error / timeout / non-text response
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=PROBE_TIMEOUT_SECONDS)
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=PROBE_MAX_TOKENS,
            system=PROBE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text_to_summarize}],
        )
    except Exception:
        return None
    parts: list[str] = []
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", "") == "text":
            parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts) if parts else None


def probe_keyword_survival(
    text_to_summarize: str, keywords: list[str]
) -> dict[str, Any]:
    """Run the summary + return per-keyword survival map.

    Result schema:
      {"summary": str|None, "survived": {kw: bool}, "all_survived": bool, "error": str|None}
    """
    summary = _run_compaction_summary(text_to_summarize)
    if summary is None:
        return {
            "summary": None,
            "survived": {},
            "all_survived": False,
            "error": "api_unavailable",
        }
    survived = {kw: kw in summary for kw in keywords}
    return {
        "summary": summary,
        "survived": survived,
        "all_survived": all(survived.values()) if survived else False,
        "error": None,
    }


def _build_probe_input(root: Path) -> str:
    """Concatenate all schema-layer TLDR sections into a representative payload."""
    tldrs = read_schema_layer_tldrs(root)
    parts: list[str] = []
    for path, bullets in tldrs:
        parts.append(f"## {path.as_posix()}")
        parts.extend(f"- {b}" for b in bullets)
        parts.append("")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli.compaction_probe",
        description="Assert TLDR keywords survive a compaction summary (LLD-012 SC-5).",
    )
    parser.add_argument(
        "--allow-skip",
        action="store_true",
        help="Exit 0 (skip) when Anthropic API is unavailable. Local-dev only — "
        "CI must NOT pass this flag.",
    )
    args = parser.parse_args(argv)
    root = Path.cwd()
    keywords = gather_keywords(root)
    if not keywords:
        sys.stderr.write("FAIL: no TLDR keywords found in schema-layer files\n")
        return 2
    payload = _build_probe_input(root)
    result = probe_keyword_survival(payload, keywords)
    if result["error"] == "api_unavailable":
        if args.allow_skip:
            sys.stderr.write(
                "WARN: compaction probe skipped — Anthropic API unavailable "
                "(missing ANTHROPIC_API_KEY or SDK call failure)\n"
            )
            return 0
        sys.stderr.write(
            "FAIL: compaction probe requires ANTHROPIC_API_KEY (or pass "
            "--allow-skip for local dev only — CI MUST NOT skip)\n"
        )
        return 2
    if result["all_survived"]:
        print(f"PASS: {len(keywords)} keywords survived compaction")
        return 0
    missing = [kw for kw, ok in result["survived"].items() if not ok]
    sys.stderr.write(
        f"FAIL: {len(missing)}/{len(keywords)} keywords lost in compaction: "
        f"{missing}\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
