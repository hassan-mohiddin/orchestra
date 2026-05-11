"""Mechanical aggregator for spec-review v2 (LLD-011 Phase 1 slices 1.11-1.18).

Pure Python dict-merge. No LLM call. Deterministic.

Algorithm:
    1. For each sub-judge with status=='completed', iterate its findings.
    2. For each finding, compute key = (normalize_location(location), fuzzy_hash(problem)).
    3. Group findings by key. Take max severity. Union raised_by. Pick canonical
       finding text from the sub-judge whose id sorts first (deterministic).
    4. Emit deduped list ordered by normalize_location.

LLD reference: docs/features/011-spec-review-v2.md §Design Aggregator.
"""

from __future__ import annotations

import hashlib
import re

SEVERITY_RANK: dict[str, int] = {"Minor": 0, "Important": 1, "Critical": 2}

# English stopwords for fuzzy_hash tokenization. Compact list — covers most
# common spec-review noise words. Not exhaustive; ambiguity-tolerant by design.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "do",
        "does",
        "for",
        "from",
        "has",
        "have",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "too",
        "was",
        "will",
        "with",
    }
)


def normalize_location(loc: str) -> str:
    """Normalize a finding location string for dedup.

    Lowercases, collapses whitespace, normalizes the section separator `§` so
    "Body § Intro", "body§intro", and "  Body  §  Intro  " all hash to the
    same canonical form.
    """
    s = loc.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*§\s*", " § ", s)
    return s


def fuzzy_hash(problem: str) -> str:
    """Stable hash of a finding's problem text after tokenization.

    Tokenization: lowercase, alphanumeric-only tokens, stopwords removed, sorted
    alphabetically. SHA-256 prefix (16 hex chars).

    Two findings with the same significant tokens — regardless of order, case,
    or stopword presence — hash to the same key.
    """
    tokens = re.findall(r"[a-z0-9]+", problem.lower())
    significant = sorted(t for t in tokens if t not in _STOPWORDS)
    joined = " ".join(significant)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def aggregate_findings(sub_judges: list[dict]) -> list[dict]:
    """Merge findings across sub-judges, dedup, union raised_by, max severity.

    Args:
        sub_judges: list of sub_judge dicts per LLD-011 §Schema v2.0. Each must
            have 'id', 'status', 'findings' fields. Only sub-judges with
            status=='completed' contribute findings; others are skipped per
            partial-failure soft-fail semantics.

    Returns:
        Deduped findings list. Each entry:
            {severity, location, problem, scope (if set on source), raised_by}
        raised_by is a sorted unique list of sub-judge ids that raised the
        merged finding. Output is ordered by normalize_location for stability.
    """
    bucket: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    for sj in sub_judges:
        if sj.get("status") != "completed":
            continue
        for f in sj.get("findings", []):
            key = (normalize_location(f["location"]), fuzzy_hash(f["problem"]))
            bucket.setdefault(key, []).append((sj["id"], f))

    aggregated: list[dict] = []
    for entries in bucket.values():
        max_sev = max(
            (e[1]["severity"] for e in entries),
            key=lambda s: SEVERITY_RANK.get(s, -1),
        )
        canonical = sorted(entries, key=lambda e: e[0])[0][1]
        merged: dict = {
            "severity": max_sev,
            "location": canonical["location"],
            "problem": canonical["problem"],
            "raised_by": sorted({e[0] for e in entries}),
        }
        if "scope" in canonical:
            merged["scope"] = canonical["scope"]
        aggregated.append(merged)

    aggregated.sort(key=lambda f: normalize_location(f["location"]))
    return aggregated
