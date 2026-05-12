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
