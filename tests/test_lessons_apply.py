"""Slice 6.3-6.4 tests — cli.lessons_apply attestation lookup + mutation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cli.lessons_apply import ApplyError, assert_passed_attestation, main


def _seed_proxy(
    tmp_path: Path,
    rule_id: str = "documentation-gate",
    iteration: int = 1,
    target: str = ".claude/rules/documentation-gate.md",
) -> Path:
    proxy_dir = tmp_path / "docs/proposed-rule-mutations"
    proxy_dir.mkdir(parents=True, exist_ok=True)
    proxy = proxy_dir / f"{rule_id}-2026-05-12.md"
    proxy.write_text(
        textwrap.dedent(
            f"""\
            # Proposed Rule Mutation: {rule_id}

            > **Iteration:** {iteration}
            > **Target:** {target}

            ## Proposed TLDR

            ```diff
             - existing
            +- MUST do new thing.
            ```
            """
        ),
        encoding="utf-8",
    )
    return proxy


def _seed_attestation(
    tmp_path: Path,
    proxy_stem: str,
    iteration: int,
    verdict: str,
    variant: str = ".orchestra.review.yaml",
) -> Path:
    reviews = tmp_path / "docs/reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    att = reviews / f"{proxy_stem}-r{iteration}{variant}"
    att.write_text(f"overall_verdict: {verdict}\n", encoding="utf-8")
    return att


def test_refuses_without_passed_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    proxy = _seed_proxy(tmp_path)
    with pytest.raises(ApplyError, match="no attestation found"):
        assert_passed_attestation(proxy, tmp_path)


def test_iteration_n_attestation_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    proxy = _seed_proxy(tmp_path, iteration=2)
    att = _seed_attestation(
        tmp_path, "documentation-gate-2026-05-12", iteration=2, verdict="pass"
    )
    found = assert_passed_attestation(proxy, tmp_path)
    assert found == att


def test_default_iteration_1_when_field_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    proxy_dir = tmp_path / "docs/proposed-rule-mutations"
    proxy_dir.mkdir(parents=True)
    proxy = proxy_dir / "rule-x-2026-05-12.md"
    proxy.write_text("# Proposed Rule Mutation: rule-x\n", encoding="utf-8")
    _seed_attestation(
        tmp_path, "rule-x-2026-05-12", iteration=1, verdict="pass"
    )
    found = assert_passed_attestation(proxy, tmp_path)
    assert found.name == "rule-x-2026-05-12-r1.orchestra.review.yaml"


def test_refuses_on_fail_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    proxy = _seed_proxy(tmp_path, iteration=1)
    _seed_attestation(
        tmp_path, "documentation-gate-2026-05-12", iteration=1, verdict="fail"
    )
    with pytest.raises(ApplyError, match="verdict 'fail'"):
        assert_passed_attestation(proxy, tmp_path)


def test_accepts_conditional_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    proxy = _seed_proxy(tmp_path, iteration=1)
    _seed_attestation(
        tmp_path,
        "documentation-gate-2026-05-12",
        iteration=1,
        verdict="conditional_pass",
    )
    att = assert_passed_attestation(proxy, tmp_path)
    assert att.exists()


def test_v1_attestation_variant_also_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Legacy `.review.yaml` (pre-v2 naming) still resolves."""
    monkeypatch.chdir(tmp_path)
    proxy = _seed_proxy(tmp_path, iteration=1)
    att = _seed_attestation(
        tmp_path,
        "documentation-gate-2026-05-12",
        iteration=1,
        verdict="pass",
        variant=".review.yaml",
    )
    found = assert_passed_attestation(proxy, tmp_path)
    assert found == att


def test_main_returns_2_when_attestation_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    proxy = _seed_proxy(tmp_path)
    rc = main([str(proxy)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "no attestation found" in err


def _seed_realistic_proxy(
    tmp_path: Path, rule_id: str = "documentation-gate"
) -> Path:
    proxy_dir = tmp_path / "docs/proposed-rule-mutations"
    proxy_dir.mkdir(parents=True, exist_ok=True)
    proxy = proxy_dir / f"{rule_id}-2026-05-12.md"
    proxy.write_text(
        textwrap.dedent(
            f"""\
            # Proposed Rule Mutation: {rule_id}

            > **Doc ID:** {rule_id}-2026-05-12
            > **Iteration:** 1
            > **Target:** .claude/rules/{rule_id}.md

            ## Proposed TLDR

            ```diff
             - existing 1.
             - existing 2.
            +- MUST do the new thing.
            ```

            ## Evidence (3 entries)

            | id | ts | observed | expected |
            |---|---|---|---|
            | aaa-111 | 2026-05-12T01:00:00+00:00 | x | y |
            | bbb-222 | 2026-05-12T02:00:00+00:00 | x | y |
            | ccc-333 | 2026-05-12T03:00:00+00:00 | x | y |
            """
        ),
        encoding="utf-8",
    )
    return proxy


def _seed_target_with_tldr(tmp_path: Path, rule_id: str) -> Path:
    rules_dir = tmp_path / ".claude/rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    target = rules_dir / f"{rule_id}.md"
    target.write_text(
        "# Doc\n"
        "\n"
        "## TLDR — Nonnegotiables\n"
        "\n"
        "- existing 1.\n"
        "- existing 2.\n"
        "\n"
        "<!-- Full rule body below this section -->\n"
        "\n"
        "body.\n",
        encoding="utf-8",
    )
    return target


def test_mutates_target_and_appends_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from cli.lessons_apply import apply_proxy
    from cli.lessons_store import read_entries

    monkeypatch.chdir(tmp_path)
    rule_id = "documentation-gate"
    proxy = _seed_realistic_proxy(tmp_path, rule_id)
    target = _seed_target_with_tldr(tmp_path, rule_id)
    _seed_attestation(
        tmp_path, f"{rule_id}-2026-05-12", iteration=1, verdict="pass"
    )

    result = apply_proxy(proxy, tmp_path)

    mutated = target.read_text(encoding="utf-8")
    assert "- existing 1." in mutated
    assert "- existing 2." in mutated
    assert "- MUST do the new thing." in mutated
    assert result["added_bullet"] == "MUST do the new thing."

    markers = [e for e in read_entries(since_days=1) if e["kind"] == "promotion-marker"]
    assert len(markers) == 1
    marker = markers[0]
    assert marker["rule_violated"] == rule_id
    assert marker["source"] == "auto-promote"
    assert marker["inject"] is False
    assert "proposed-rule-mutations" in marker["proxy_artifact"]
    assert marker["source_lesson_ids"] == ["aaa-111", "bbb-222", "ccc-333"]


def test_apply_refuses_when_target_missing_tldr_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from cli.lessons_apply import apply_proxy

    monkeypatch.chdir(tmp_path)
    rule_id = "documentation-gate"
    proxy = _seed_realistic_proxy(tmp_path, rule_id)
    rules_dir = tmp_path / ".claude/rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / f"{rule_id}.md").write_text("# Doc\n\nno tldr here.\n", encoding="utf-8")
    _seed_attestation(
        tmp_path, f"{rule_id}-2026-05-12", iteration=1, verdict="pass"
    )
    with pytest.raises(ApplyError, match="TLDR"):
        apply_proxy(proxy, tmp_path)
