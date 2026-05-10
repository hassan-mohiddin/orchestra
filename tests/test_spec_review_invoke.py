"""Slash command invocation test (S25 slice)."""

import pytest


def test_slash_command_arg_parsing(tmp_path, capsys, monkeypatch):
    """T1 / S25 — A2: slash cmd accepts single positional doc-path arg.

    No-arg invocation must error. Two-arg (positional) invocation must error.
    """
    from cli import spec_review

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    # No args → argparse exits 2
    with pytest.raises(SystemExit) as exc:
        spec_review.main([])
    assert exc.value.code == 2

    # Two positional args → argparse exits 2
    with pytest.raises(SystemExit) as exc:
        spec_review.main(["docs/a.md", "docs/b.md"])
    assert exc.value.code == 2
