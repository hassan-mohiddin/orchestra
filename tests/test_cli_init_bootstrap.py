"""Tests for cli.init hook bootstrap (LLD-008 r7 T5a-g; BUG-010 Part 3).

T5d (framework-present defer to print-only) requires LLD-010 framework detection
shipped in Phase 3 — marked xfail until then.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from cli import init as cli_init


def _run_init_cli(repo: Path, *extra, env=None) -> subprocess.CompletedProcess:
    """Invoke `python -m cli.init --repo <repo>` as subprocess to honor argparse + bootstrap."""
    cmd = [sys.executable, "-m", "cli.init", "--repo", str(repo), *extra]
    return subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
        env=env,
    )


def test_cli_init_bootstrap_installs_both_hooks(tmp_repo: Path) -> None:
    """T5a — cli.init bootstrap leaves both hooks installed when no framework."""
    rc = cli_init.main(["--repo", str(tmp_repo)])
    assert rc == 0
    assert (tmp_repo / ".git" / "hooks" / "pre-commit").exists()
    assert (tmp_repo / ".git" / "hooks" / "commit-msg").exists()


def test_cli_init_bootstrap_idempotent(tmp_repo: Path) -> None:
    """T5b — second cli.init invocation does not error."""
    rc1 = cli_init.main(["--repo", str(tmp_repo)])
    assert rc1 == 0
    rc2 = cli_init.main(["--repo", str(tmp_repo)])
    assert rc2 == 0
    assert (tmp_repo / ".git" / "hooks" / "pre-commit").exists()
    assert (tmp_repo / ".git" / "hooks" / "commit-msg").exists()


def test_cli_init_non_tty_no_input_blocking(tmp_repo: Path, monkeypatch) -> None:
    """T5c — non-TTY environment: no input() blocking; clean rc=0."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    rc = cli_init.main(["--repo", str(tmp_repo)])
    assert rc == 0


@pytest.mark.xfail(reason="LLD-010 framework detection deferred to Phase 3", strict=False)
def test_cli_init_framework_present_no_apply_defers_to_print_only(tmp_repo: Path) -> None:
    """T5d — `.pre-commit-config.yaml` present + no --apply → framework branch print-only."""
    (tmp_repo / ".pre-commit-config.yaml").write_text("repos: []\n")
    rc = cli_init.main(["--repo", str(tmp_repo)])
    assert rc == 0
    # Phase 3: bootstrap should detect framework and NOT raw-overwrite hooks
    assert not (tmp_repo / ".git" / "hooks" / "pre-commit").exists()


def test_cli_init_tty_bootstrap_non_zero_rc_emits_warning_fail_open(
    tmp_repo: Path, monkeypatch, capsys
) -> None:
    """T5e — TTY default fail-open: rc!=0 from bootstrap → WARNING + cli.init returns 0."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(
        "cli.install_hooks.main",
        lambda argv=None: 1,
    )
    monkeypatch.delenv("ORCHESTRA_INIT_STRICT", raising=False)
    rc = cli_init.main(["--repo", str(tmp_repo)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "WARNING" in captured.err
    assert "bootstrap returned rc=1" in captured.err


def test_cli_init_orchestra_init_strict_propagates_non_zero_rc(
    tmp_repo: Path, monkeypatch, capsys
) -> None:
    """T5f — ORCHESTRA_INIT_STRICT=1 + rc!=0 → cli.init returns non-zero regardless of TTY."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)  # TTY default would fail-open
    monkeypatch.setattr("cli.install_hooks.main", lambda argv=None: 1)
    monkeypatch.setenv("ORCHESTRA_INIT_STRICT", "1")
    rc = cli_init.main(["--repo", str(tmp_repo)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "WARNING" in captured.err


def test_cli_init_non_tty_bootstrap_non_zero_rc_fails_closed(
    tmp_repo: Path, monkeypatch, capsys
) -> None:
    """T5g — non-TTY + rc!=0 + env unset → cli.init returns non-zero (TTY-aware fail-closed).

    Closes plan-r2 codex HIGH#1: CI/automation observes bootstrap failure via exit code.
    """
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("cli.install_hooks.main", lambda argv=None: 1)
    monkeypatch.delenv("ORCHESTRA_INIT_STRICT", raising=False)
    rc = cli_init.main(["--repo", str(tmp_repo)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "WARNING" in captured.err
