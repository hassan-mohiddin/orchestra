"""Lessons recurrence scanner + proxy-artifact drafter (LLD-012 SC-8).

`scan_recurrences()` returns rules with ≥3 recurrences. `write_proxy_artifact()`
drafts a proposed TLDR mutation per LLD-012 §lessons_lint step 3 tie-break:
  (a) highest-frequency (observed, expected) pair wins
  (b) most-recent ts on count-tie
  (c) lex-min observed on recency-tie
  (d) if drafted bullet >80 chars → emit needs-author-rewrite marker
  (e) if append would push existing TLDR count >7 → refuse (consolidate first)

Class-B reconciliation (SC-8): emits proxy artifacts only. Does NOT
auto-trigger spec-review. User runs `/orchestra:spec-review <proxy-path>`
when ready, then `python -m cli.lessons_apply <proxy-path>` after a passed
attestation.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lessons_store import read_entries
from cli.tldr_extractor import MAX_BULLET_LENGTH, MAX_BULLETS, TldrSection, extract_tldr

DEFAULT_SINCE_DAYS = 90
RECURRENCE_THRESHOLD = 3
PROXY_DIR = Path("docs/proposed-rule-mutations")
TARGET_SPECIAL_RULES = {
    "CLAUDE": Path(".claude/CLAUDE.md"),
    "workflow": Path(".claude/workflow.md"),
}


def scan_recurrences(
    since_days: int = DEFAULT_SINCE_DAYS,
    threshold: int = RECURRENCE_THRESHOLD,
) -> dict[str, list[dict[str, Any]]]:
    """Group violation lessons by rule_violated; return rules with ≥threshold entries.

    Filters: kind==violation, source!=auto-promote (recursion guard),
    truthy rule_violated.
    """
    entries = read_entries(since_days=since_days)
    by_rule: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        if entry.get("kind") != "violation":
            continue
        if entry.get("source") == "auto-promote":
            continue
        rule = entry.get("rule_violated")
        if not rule:
            continue
        by_rule[rule].append(entry)
    return {rule: items for rule, items in by_rule.items() if len(items) >= threshold}


def _rule_target_path(rule_id: str, root: Path) -> Path:
    if rule_id in TARGET_SPECIAL_RULES:
        return root / TARGET_SPECIAL_RULES[rule_id]
    return root / ".claude/rules" / f"{rule_id}.md"


def _read_current_tldr(target: Path) -> list[str]:
    if not target.exists():
        return []
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return []
    result = extract_tldr(text)
    if isinstance(result, TldrSection):
        return result.bullets
    return []


def _select_top_pair(entries: list[dict[str, Any]]) -> tuple[str, str]:
    """Apply tie-break a/b/c → return winning (observed, expected) pair."""
    counts: Counter[tuple[str, str]] = Counter()
    latest_ts: dict[tuple[str, str], str] = {}
    for e in entries:
        pair = (str(e.get("observed") or ""), str(e.get("expected") or ""))
        counts[pair] += 1
        ts = str(e.get("ts") or "")
        if pair not in latest_ts or ts > latest_ts[pair]:
            latest_ts[pair] = ts
    top_count = max(counts.values())
    top = [p for p, c in counts.items() if c == top_count]
    if len(top) > 1:
        top_ts = max(latest_ts[p] for p in top)
        top = [p for p in top if latest_ts[p] == top_ts]
    if len(top) > 1:
        top.sort(key=lambda p: p[0])
    return top[0]


def _draft_bullet_text(expected: str) -> str:
    """Build deterministic imperative bullet from the winning `expected` text."""
    trimmed = expected.strip().rstrip(".")
    if not trimmed:
        return ""
    first = trimmed[0].upper() + trimmed[1:]
    return f"MUST {first}."


def draft_bullet(entries: list[dict[str, Any]]) -> tuple[str | None, str]:
    """Return (drafted_bullet, reason). drafted_bullet=None signals needs-author-rewrite."""
    if not entries:
        return None, "no_entries"
    _, expected = _select_top_pair(entries)
    bullet = _draft_bullet_text(expected)
    if not bullet:
        return None, "empty_expected"
    if len(bullet) > MAX_BULLET_LENGTH:
        return None, "needs_author_rewrite"
    return bullet, "ok"


def _format_proxy_artifact(
    rule_id: str,
    target: Path,
    current_bullets: list[str],
    entries: list[dict[str, Any]],
    drafted: str | None,
    reason: str,
    today: str,
) -> str:
    target_str = target.as_posix()
    rows = "\n".join(
        f"| {e.get('ts', '?')} | {e.get('observed', '')} | {e.get('expected', '')} |"
        for e in entries
    )
    current_block = (
        "\n".join(f" - {b}" for b in current_bullets)
        if current_bullets
        else " (no current TLDR found)"
    )
    if reason == "ok" and drafted is not None:
        proposed_block = (
            "\n".join(f" - {b}" for b in current_bullets) + f"\n+- {drafted}"
        )
        proposed_note = ""
    elif reason == "needs_author_rewrite":
        proposed_block = " (auto-draft exceeded 80 chars — author must compose manually)"
        proposed_note = (
            "\n\n**needs-author-rewrite marker** — `cli.lessons_lint` could not "
            "synthesize a bullet within the 80-char cap from the recurring lesson "
            "pair. Author must compose the bullet manually before applying."
        )
    elif reason == "append_would_exceed_7":
        proposed_block = " (REFUSED: existing TLDR already has 7 bullets)"
        proposed_note = (
            "\n\n**append-exceeds-7 refusal** — existing TLDR cap reached. "
            "Author must CONSOLIDATE existing bullets first before this proxy "
            "can be applied. lessons_lint will retry on the next scan."
        )
    else:
        proposed_block = f" (no bullet drafted; reason={reason})"
        proposed_note = ""
    body = f"""# Proposed Rule Mutation: {rule_id}

> **Doc ID:** {rule_id}-{today}
> **Date:** {today}
> **DRI:** Hassan Mohiddin
> **Type:** Proposed Rule Mutation
> **Status:** Draft
> **Iteration:** 1
> **Target:** {target_str}

## Trigger

≥{RECURRENCE_THRESHOLD} violations of `{rule_id}` observed in last
{DEFAULT_SINCE_DAYS} days. Auto-drafted by `cli.lessons_lint`. Per LLD-012
SC-8 (Class-B reconciliation), this artifact does NOT auto-trigger
spec-review. Run `/orchestra:spec-review docs/proposed-rule-mutations/{rule_id}-{today}.md`
when ready.

## Current TLDR (`{target_str}`)

```diff
{current_block}
```

## Proposed TLDR

```diff
{proposed_block}
```
{proposed_note}

## Evidence ({len(entries)} entries)

| ts | observed | expected |
|---|---|---|
{rows}

## Provenance

- Drafter: `cli.lessons_lint` (LLD-012 SC-8)
- Date: {today}
- Reason: {reason}

## Changelog

| Date | Change |
|---|---|
| {today} | Auto-drafted proxy artifact from {len(entries)} recurring violations of `{rule_id}`. |
"""
    return body


def write_proxy_artifact(
    rule_id: str,
    entries: list[dict[str, Any]],
    root: Path,
    today: str | None = None,
) -> Path:
    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    target = _rule_target_path(rule_id, root)
    current_bullets = _read_current_tldr(target)
    if len(current_bullets) >= MAX_BULLETS:
        drafted, reason = None, "append_would_exceed_7"
    else:
        drafted, reason = draft_bullet(entries)
    body = _format_proxy_artifact(
        rule_id, target, current_bullets, entries, drafted, reason, today
    )
    out_dir = root / PROXY_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{rule_id}-{today}.md"
    out_path.write_text(body, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    rules = scan_recurrences()
    if not rules:
        print("No recurring violations detected.")
        return 0
    for rule_id, entries in rules.items():
        path = write_proxy_artifact(rule_id, entries, root)
        print(f"proxy artifact: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
