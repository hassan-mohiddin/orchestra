"""Tests for cli._shared — walk-up _repo_root() helper (BUG-016 slice 1.0).

Per LLD `docs/design/controlled-vocabulary.md § Parse contract`:
- Walk up from `__file__` looking for `.claude-plugin/plugin.json`
- Raise `RuntimeError("orchestra repo root not found")` after 8 levels.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_repo_root_walks_up_to_plugin_json(tmp_path: Path, monkeypatch):
    root = tmp_path / "fakerepo"
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(json.dumps({"name": "fake"}))

    nested = root / "a" / "b" / "c"
    nested.mkdir(parents=True)
    fake_file = nested / "caller.py"
    fake_file.write_text("# fake")

    from cli import _shared

    assert _shared._repo_root(start=fake_file) == root


def test_repo_root_finds_at_start_dir(tmp_path: Path):
    root = tmp_path / "repo"
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text("{}")

    caller = root / "caller.py"
    caller.write_text("")

    from cli import _shared

    assert _shared._repo_root(start=caller) == root


def test_repo_root_raises_after_max_levels(tmp_path: Path):
    deep = tmp_path
    for i in range(12):
        deep = deep / f"level{i}"
    deep.mkdir(parents=True)
    caller = deep / "caller.py"
    caller.write_text("")

    from cli import _shared

    with pytest.raises(RuntimeError, match="orchestra repo root not found"):
        _shared._repo_root(start=caller)


def test_repo_root_default_uses_module_file():
    """Called with no args from inside the orchestra repo, resolves to repo root."""
    from cli import _shared

    root = _shared._repo_root()
    assert (root / ".claude-plugin" / "plugin.json").is_file()
