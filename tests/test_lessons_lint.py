"""Slice 6.1 — lessons_lint scan + recurrence detection (LLD-012 SC-8)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cli.lessons_lint import RECURRENCE_THRESHOLD, scan_recurrences
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
