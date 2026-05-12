"""Slice 6.5 — compaction_probe keyword extraction (LLD-012 SC-5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.compaction_probe import (
    KEYWORD_PREFIX,
    extract_keyword,
    extract_keywords_from_tldrs,
    gather_keywords,
)


def test_extracts_first_non_stopword_per_bullet() -> None:
    bullet = "READ docs/HANDOFF.md + run TaskList before any work on first turn."
    kw = extract_keyword(bullet)
    assert kw == "docs/HANDOFF.md", kw


def test_extracts_distinctive_path_token() -> None:
    bullet = "ROUTE every code change through .claude/workflow.md (no exceptions)."
    kw = extract_keyword(bullet)
    assert kw.startswith(".claude") or kw == "change" or "workflow" in kw, kw


def test_orchestra_tldr_prefix_on_collision() -> None:
    """All tokens are stopwords → fallback to ORCHESTRA-TLDR-<first-token>."""
    bullet = "Do see the work for any code."
    kw = extract_keyword(bullet)
    assert kw.startswith(KEYWORD_PREFIX), (
        f"expected ORCHESTRA-TLDR- prefix on all-stopword bullet, got {kw!r}"
    )


def test_empty_bullet_returns_prefix_empty() -> None:
    assert extract_keyword("") == f"{KEYWORD_PREFIX}empty"
    assert extract_keyword("   ") == f"{KEYWORD_PREFIX}empty"


def test_short_token_skipped() -> None:
    """Tokens shorter than MIN_TOKEN_LENGTH (4) are skipped."""
    bullet = "fix io to fs by op."
    kw = extract_keyword(bullet)
    assert kw.startswith(KEYWORD_PREFIX), kw


def test_extract_keywords_from_tldrs_preserves_order() -> None:
    tldrs = [
        (Path("a.md"), ["First bullet about HANDOFF.md content.", "Second TaskList one."]),
        (Path("b.md"), ["Single .claude/workflow.md bullet."]),
    ]
    out = extract_keywords_from_tldrs(tldrs)
    assert len(out) == 2
    assert out[0][0] == Path("a.md")
    assert out[1][0] == Path("b.md")
    assert len(out[0][1]) == 2
    assert len(out[1][1]) == 1


def test_gather_keywords_from_seeded_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".claude/rules").mkdir(parents=True)
    (tmp_path / ".claude/CLAUDE.md").write_text(
        "## TLDR — Nonnegotiables\n\n- HANDOFF.md keyword anchor here.\n\n<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )
    (tmp_path / ".claude/rules/docs.md").write_text(
        "## TLDR — Nonnegotiables\n\n- Use TaskList anchor for second rule.\n\n<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    keywords = gather_keywords()
    assert len(keywords) == 2
    assert "HANDOFF.md" in keywords[0]
    assert "TaskList" in keywords[1]


def test_probe_keyword_survival_all_survived(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cli import compaction_probe

    monkeypatch.setattr(
        compaction_probe,
        "_run_compaction_summary",
        lambda _payload: "The summary preserves HANDOFF.md and TaskList verbatim.",
    )
    result = compaction_probe.probe_keyword_survival(
        "payload", ["HANDOFF.md", "TaskList"]
    )
    assert result["all_survived"] is True
    assert result["error"] is None
    assert result["survived"] == {"HANDOFF.md": True, "TaskList": True}


def test_probe_keyword_survival_some_lost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cli import compaction_probe

    monkeypatch.setattr(
        compaction_probe,
        "_run_compaction_summary",
        lambda _payload: "Only HANDOFF.md survives this summary.",
    )
    result = compaction_probe.probe_keyword_survival(
        "payload", ["HANDOFF.md", "TaskList"]
    )
    assert result["all_survived"] is False
    assert result["survived"] == {"HANDOFF.md": True, "TaskList": False}


def test_compact_invocation_mocked_exits_zero_when_all_survive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from cli import compaction_probe

    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/CLAUDE.md").write_text(
        "## TLDR — Nonnegotiables\n\n- READ HANDOFF.md anchor.\n\n<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        compaction_probe,
        "_run_compaction_summary",
        lambda _payload: "summary contains HANDOFF.md verbatim",
    )
    rc = compaction_probe.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "PASS" in out


def test_compact_invocation_mocked_exits_1_when_keyword_lost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from cli import compaction_probe

    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/CLAUDE.md").write_text(
        "## TLDR — Nonnegotiables\n\n- READ HANDOFF.md anchor.\n\n<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        compaction_probe,
        "_run_compaction_summary",
        lambda _payload: "the summary paraphrased everything away",
    )
    rc = compaction_probe.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "FAIL" in err
    assert "HANDOFF.md" in err


def test_missing_api_key_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from cli import compaction_probe

    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/CLAUDE.md").write_text(
        "## TLDR — Nonnegotiables\n\n- One HANDOFF.md bullet.\n\n<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        compaction_probe, "_run_compaction_summary", lambda _payload: None
    )
    rc = compaction_probe.main([])
    err = capsys.readouterr().err
    assert rc == 2
    assert "ANTHROPIC_API_KEY" in err


def test_allow_skip_local_dev_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from cli import compaction_probe

    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/CLAUDE.md").write_text(
        "## TLDR — Nonnegotiables\n\n- One bullet HANDOFF.md.\n\n<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        compaction_probe, "_run_compaction_summary", lambda _payload: None
    )
    rc = compaction_probe.main(["--allow-skip"])
    err = capsys.readouterr().err
    assert rc == 0
    assert "WARN" in err
    assert "skipped" in err
