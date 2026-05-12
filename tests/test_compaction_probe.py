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
