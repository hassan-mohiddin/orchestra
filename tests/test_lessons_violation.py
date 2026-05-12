"""Slice 5.3 tests — /orchestra:violation shim + allowlist + path-traversal."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.lessons_store import read_entries
from cli.lessons_violation import main


def _seed_rules(root: Path) -> None:
    (root / ".claude/rules").mkdir(parents=True, exist_ok=True)
    (root / ".claude/rules/documentation-gate.md").write_text("# x\n", encoding="utf-8")
    (root / ".claude/rules/interview-gate.md").write_text("# x\n", encoding="utf-8")


def test_violation_appends_kind_violation_inject_true(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = main(
        [
            "--rule=documentation-gate",
            "--observed=agent skipped spec-review",
            "--expected=spec-review fires on every doc",
        ]
    )
    assert rc == 0
    entries = read_entries(since_days=1)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["kind"] == "violation"
    assert entry["rule_violated"] == "documentation-gate"
    assert entry["inject"] is True
    assert entry["source"] == "user"
    assert "agent skipped spec-review" in entry["observed"]
    assert "spec-review fires" in entry["expected"]


def test_violation_rejects_unknown_rule_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = main(
        [
            "--rule=nonexistent-rule",
            "--observed=x",
            "--expected=y",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "unknown rule" in err
    assert "nonexistent-rule" in err
    assert read_entries(since_days=1) == []


def test_violation_path_traversal_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    for malicious in (
        "../../../etc/passwd",
        "../something",
        ".claude/rules/documentation-gate",
        "rules/documentation-gate",
        "..",
    ):
        rc = main([f"--rule={malicious}", "--observed=x", "--expected=y"])
        err = capsys.readouterr().err
        assert rc == 2, f"path traversal {malicious!r} must be rejected"
        assert "path components" in err or "unknown rule" in err
    assert read_entries(since_days=1) == []


def test_violation_symlinked_rule_file_not_in_allowlist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_rules(tmp_path)
    target = tmp_path / "outside-rule.md"
    target.write_text("# x\n", encoding="utf-8")
    symlink = tmp_path / ".claude/rules/sneaky-symlink.md"
    symlink.symlink_to(target)
    monkeypatch.chdir(tmp_path)
    rc = main(
        [
            "--rule=sneaky-symlink",
            "--observed=x",
            "--expected=y",
        ]
    )
    assert rc == 2, "symlinked rule file must not widen the allowlist"
    err = capsys.readouterr().err
    assert "unknown rule" in err


def test_violation_html_encodes_observed_expected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = main(
        [
            "--rule=documentation-gate",
            "--observed=<script>alert(1)</script>",
            "--expected=safe & sound",
        ]
    )
    assert rc == 0
    entry = read_entries(since_days=1)[0]
    assert "<script>" not in entry["observed"]
    assert "&lt;script&gt;" in entry["observed"]
    assert "&amp;" in entry["expected"]
