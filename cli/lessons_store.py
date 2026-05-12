"""Append-only lessons store for orchestra (LLD-012 SC-7 substrate).

Writes lesson entries to `docs/lessons/<YYYY-MM>-lessons.md` relative to cwd.
File format: frontmatter (file_type + month) + YAML-list body.

Public surface:
- `append_entry(entry)` — validate + HTML-encode + 200-char cap + append.
- `read_entries(since_days)` — read all lessons across last N days.
- `LessonsStoreError` — raised on invalid input.

Schema per LLD-012 § Lessons skill (lines 261–301).
"""

from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import frontmatter
import yaml

VALID_KINDS = frozenset({"teach", "violation", "promotion-marker"})
ENCODED_FIELDS = ("observed", "expected")
MAX_FIELD_LENGTH = 200
LESSONS_DIR = Path("docs/lessons")


class LessonsStoreError(ValueError):
    """Raised on invalid lesson entry input."""


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _validate_and_normalize(entry: dict[str, Any]) -> dict[str, Any]:
    if "ts" not in entry:
        raise LessonsStoreError("entry missing required field: ts")
    try:
        _parse_ts(entry["ts"])
    except (ValueError, TypeError) as exc:
        raise LessonsStoreError(f"invalid ts: {entry['ts']!r}") from exc
    kind = entry.get("kind")
    if kind not in VALID_KINDS:
        raise LessonsStoreError(
            f"invalid kind {kind!r}; expected one of {sorted(VALID_KINDS)}"
        )
    normalized = dict(entry)
    for field in ENCODED_FIELDS:
        raw = normalized.get(field)
        if raw is None:
            continue
        if not isinstance(raw, str):
            raise LessonsStoreError(f"{field} must be str, got {type(raw).__name__}")
        encoded = html.escape(raw, quote=False)
        if len(encoded) > MAX_FIELD_LENGTH:
            encoded = encoded[:MAX_FIELD_LENGTH]
        normalized[field] = encoded
    return normalized


def _monthly_path(entry: dict[str, Any]) -> Path:
    ts = _parse_ts(entry["ts"])
    return LESSONS_DIR / f"{ts.year:04d}-{ts.month:02d}-lessons.md"


def _load_post(path: Path) -> tuple[frontmatter.Post, list[dict[str, Any]]]:
    if path.exists():
        post = frontmatter.load(str(path))
        body = post.content.strip()
        existing = yaml.safe_load(body) if body else []
        if existing is None:
            existing = []
        return post, list(existing)
    month = path.stem.replace("-lessons", "")
    post = frontmatter.Post("", file_type="lessons", month=month)
    return post, []


def append_entry(entry: dict[str, Any]) -> Path:
    normalized = _validate_and_normalize(entry)
    path = _monthly_path(normalized)
    path.parent.mkdir(parents=True, exist_ok=True)
    post, entries = _load_post(path)
    entries.append(normalized)
    post.content = yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return path.resolve()


def read_entries(since_days: int) -> list[dict[str, Any]]:
    if not LESSONS_DIR.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    out: list[dict[str, Any]] = []
    for path in sorted(LESSONS_DIR.glob("*-lessons.md")):
        post = frontmatter.load(str(path))
        body = post.content.strip()
        if not body:
            continue
        entries = yaml.safe_load(body) or []
        for entry in entries:
            try:
                ts = _parse_ts(entry["ts"])
            except (KeyError, ValueError, TypeError):
                continue
            if ts >= cutoff:
                out.append(entry)
    return out
