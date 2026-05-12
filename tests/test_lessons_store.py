from pathlib import Path

import pytest

from cli.lessons_store import LessonsStoreError, append_entry, read_entries


def _valid_teach_entry() -> dict:
    return {
        "id": "abc-123",
        "ts": "2026-05-11T15:32:00Z",
        "kind": "teach",
        "rule_violated": None,
        "body": "remember to ask before editing canon-frozen docs",
        "source": "user",
        "inject": False,
    }


def _valid_violation_entry() -> dict:
    return {
        "id": "v-1",
        "ts": "2026-05-11T15:33:00Z",
        "kind": "violation",
        "rule_violated": "documentation-gate",
        "observed": "agent skipped spec-review",
        "expected": "agent runs spec-review on every doc edit",
        "source": "user",
        "inject": True,
    }


def test_append_creates_monthly_file_with_frontmatter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    path = append_entry(_valid_teach_entry())
    assert path == tmp_path / "docs" / "lessons" / "2026-05-lessons.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "file_type: lessons" in text
    assert "month: 2026-05" in text


def test_append_then_read_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    append_entry(_valid_teach_entry())
    append_entry(_valid_violation_entry())
    entries = read_entries(since_days=365)
    assert len(entries) == 2
    assert entries[0]["id"] == "abc-123"
    assert entries[1]["id"] == "v-1"


def test_html_encodes_observed_and_expected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    entry = _valid_violation_entry()
    entry["observed"] = "<script>alert(1)</script>"
    entry["expected"] = "safe & sound"
    append_entry(entry)
    entries = read_entries(since_days=365)
    assert "<script>" not in entries[0]["observed"]
    assert "&lt;script&gt;" in entries[0]["observed"]
    assert "&amp;" in entries[0]["expected"]


def test_observed_expected_capped_at_200_chars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    entry = _valid_violation_entry()
    entry["observed"] = "x" * 500
    entry["expected"] = "y" * 500
    append_entry(entry)
    entries = read_entries(since_days=365)
    assert len(entries[0]["observed"]) <= 200
    assert len(entries[0]["expected"]) <= 200


def test_rejects_invalid_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    entry = _valid_teach_entry()
    entry["kind"] = "bogus"
    with pytest.raises(LessonsStoreError, match="kind"):
        append_entry(entry)


def test_rejects_missing_ts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    entry = _valid_teach_entry()
    del entry["ts"]
    with pytest.raises(LessonsStoreError, match="ts"):
        append_entry(entry)


def test_teach_cli_appends_kind_teach_inject_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Slice 5.2 — /orchestra:teach shim → cli.lessons_teach → append_entry."""
    monkeypatch.chdir(tmp_path)
    from cli.lessons_teach import main

    rc = main(["remember", "to", "check", "things"])
    assert rc == 0
    entries = read_entries(since_days=1)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["kind"] == "teach"
    assert entry["body"] == "remember to check things"
    assert entry["inject"] is False
    assert entry["source"] == "user"
    assert entry["rule_violated"] is None
    assert entry["id"]
    assert entry["ts"]


def test_teach_cli_rejects_empty_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    from cli.lessons_teach import main

    rc = main(["   "])
    assert rc == 2
