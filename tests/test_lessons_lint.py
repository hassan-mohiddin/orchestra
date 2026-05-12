"""Slice 6.1 — lessons_lint scan + recurrence detection (LLD-012 SC-8)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cli.lessons_lint import (
    PROXY_DIR,
    RECURRENCE_THRESHOLD,
    draft_bullet,
    scan_recurrences,
    write_proxy_artifact,
)
from cli.lessons_store import append_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _violation(rule: str, source: str = "user", inject: bool = True) -> dict:
    return {
        "id": f"v-{rule}-{_now_iso()}",
        "ts": _now_iso(),
        "kind": "violation",
        "rule_violated": rule,
        "observed": "x",
        "expected": "y",
        "source": source,
        "inject": inject,
    }


def test_detects_threshold_recurrence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for i in range(RECURRENCE_THRESHOLD):
        e = _violation("documentation-gate")
        e["id"] = f"v-{i}"
        append_entry(e)
    result = scan_recurrences(since_days=365)
    assert "documentation-gate" in result
    assert len(result["documentation-gate"]) == RECURRENCE_THRESHOLD


def test_below_threshold_not_returned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for i in range(RECURRENCE_THRESHOLD - 1):
        e = _violation("interview-gate")
        e["id"] = f"v-{i}"
        append_entry(e)
    result = scan_recurrences(since_days=365)
    assert "interview-gate" not in result


def test_skips_source_auto_promote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LLD-012 §lessons_lint step 1 — recursion guard."""
    monkeypatch.chdir(tmp_path)
    for i in range(RECURRENCE_THRESHOLD):
        e = _violation("skills-routing", source="auto-promote")
        e["id"] = f"v-{i}"
        append_entry(e)
    result = scan_recurrences(since_days=365)
    assert "skills-routing" not in result, (
        "auto-promote entries must NOT count toward recurrence"
    )


def test_skips_non_violation_kinds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for i in range(RECURRENCE_THRESHOLD):
        e = {
            "id": f"t-{i}",
            "ts": _now_iso(),
            "kind": "teach",
            "rule_violated": None,
            "body": "free-text note",
            "source": "user",
            "inject": False,
        }
        append_entry(e)
    result = scan_recurrences(since_days=365)
    assert result == {}, "teach entries must not surface in recurrence scan"


def test_multiple_rules_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for i in range(RECURRENCE_THRESHOLD):
        e = _violation("rule-a")
        e["id"] = f"a-{i}"
        append_entry(e)
    for i in range(RECURRENCE_THRESHOLD - 1):
        e = _violation("rule-b")
        e["id"] = f"b-{i}"
        append_entry(e)
    result = scan_recurrences(since_days=365)
    assert "rule-a" in result
    assert "rule-b" not in result


_VALID_TLDR_5 = (
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- bullet 1.\n"
    "- bullet 2.\n"
    "- bullet 3.\n"
    "- bullet 4.\n"
    "- bullet 5.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
)

_VALID_TLDR_7 = (
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- bullet 1.\n"
    "- bullet 2.\n"
    "- bullet 3.\n"
    "- bullet 4.\n"
    "- bullet 5.\n"
    "- bullet 6.\n"
    "- bullet 7.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
)


def _seed_rule_file(tmp_path: Path, rule_id: str, tldr_text: str) -> None:
    rules_dir = tmp_path / ".claude/rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / f"{rule_id}.md").write_text(tldr_text, encoding="utf-8")


def test_draft_bullet_tie_break_most_recent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tie-break (a): most-recent ts wins on count-tie."""
    entries = [
        {
            "ts": "2026-05-10T00:00:00+00:00",
            "observed": "x",
            "expected": "do the older thing",
        },
        {
            "ts": "2026-05-12T00:00:00+00:00",
            "observed": "y",
            "expected": "do the newer thing",
        },
    ]
    bullet, reason = draft_bullet(entries)
    assert reason == "ok"
    assert bullet is not None
    assert "newer" in bullet
    assert bullet.startswith("MUST ")


def test_draft_bullet_overflow_emits_needs_author_rewrite_marker(
    tmp_path: Path,
) -> None:
    """Tie-break (c): drafted bullet >80 chars → needs-author-rewrite."""
    entries = [
        {
            "ts": "2026-05-12T00:00:00+00:00",
            "observed": "x",
            "expected": "x" * 100,
        }
    ] * 3
    bullet, reason = draft_bullet(entries)
    assert bullet is None
    assert reason == "needs_author_rewrite"


def test_proxy_artifact_written_with_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_rule_file(tmp_path, "documentation-gate", _VALID_TLDR_5)
    for i in range(RECURRENCE_THRESHOLD):
        e = _violation("documentation-gate")
        e["id"] = f"v-{i}"
        e["observed"] = "agent skipped spec-review"
        e["expected"] = "spec-review on every doc edit"
        append_entry(e)
    rules = scan_recurrences(since_days=365)
    path = write_proxy_artifact(
        "documentation-gate", rules["documentation-gate"], tmp_path, today="2026-05-12"
    )
    assert path == tmp_path / PROXY_DIR / "documentation-gate-2026-05-12.md"
    body = path.read_text(encoding="utf-8")
    assert "## Current TLDR" in body
    assert "## Proposed TLDR" in body
    assert "MUST Spec-review on every doc edit." in body
    assert "bullet 1." in body
    assert "## Evidence" in body
    assert "agent skipped spec-review" in body


def test_append_would_exceed_7_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_rule_file(tmp_path, "interview-gate", _VALID_TLDR_7)
    for i in range(RECURRENCE_THRESHOLD):
        e = _violation("interview-gate")
        e["id"] = f"v-{i}"
        append_entry(e)
    rules = scan_recurrences(since_days=365)
    path = write_proxy_artifact(
        "interview-gate", rules["interview-gate"], tmp_path, today="2026-05-12"
    )
    body = path.read_text(encoding="utf-8")
    assert "append-exceeds-7 refusal" in body
    assert "CONSOLIDATE" in body


def test_overflow_proxy_emits_needs_author_rewrite_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_rule_file(tmp_path, "skills-routing", _VALID_TLDR_5)
    for i in range(RECURRENCE_THRESHOLD):
        e = _violation("skills-routing")
        e["id"] = f"v-{i}"
        e["expected"] = "x" * 200
        append_entry(e)
    rules = scan_recurrences(since_days=365)
    path = write_proxy_artifact(
        "skills-routing", rules["skills-routing"], tmp_path, today="2026-05-12"
    )
    body = path.read_text(encoding="utf-8")
    assert "needs-author-rewrite marker" in body
