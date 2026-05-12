"""Lessons recurrence scanner (LLD-012 SC-8).

Reads `docs/lessons/<YYYY-MM>-lessons.md` entries from the last 90 days,
filters `kind == "violation"` and `source != "auto-promote"` (recursion
guard), groups by `rule_violated`, and surfaces rule IDs with ≥3
recurrences as candidates for TLDR mutation.

Phase 6.1: scan + recurrence detection only. Phase 6.2 adds proxy-artifact
write (target path + current TLDR diff + proposed TLDR diff). Phase 6.3+4
add lessons_apply (user-invoked mutation step).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from cli.lessons_store import read_entries

DEFAULT_SINCE_DAYS = 90
RECURRENCE_THRESHOLD = 3


def scan_recurrences(
    since_days: int = DEFAULT_SINCE_DAYS,
    threshold: int = RECURRENCE_THRESHOLD,
) -> dict[str, list[dict[str, Any]]]:
    """Group violation lessons by rule_violated; return rules with ≥threshold entries.

    Filters:
    - kind == "violation"
    - source != "auto-promote" (LLD-012 recursion guard — promote-marker
      entries must NOT count toward recurrence or we get an infinite loop:
      promote → inject → re-detect → promote)
    - rule_violated is truthy (None / "" entries dropped)

    Returns {rule_id: [entry, ...]} for rules at or above threshold.
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
