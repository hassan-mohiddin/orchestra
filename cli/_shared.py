"""Shared helpers consumed across cli/* modules.

Currently exposes:
- `_repo_root(start: Path | None = None) -> Path`

Walk-up algorithm finds the orchestra repo root by looking for
`.claude-plugin/plugin.json` upward from `start` (defaults to this module's
own `__file__`). Distinct from `cli.lint § repo_root_from_cwd` which uses
`git rev-parse` — that path is for git-aware contexts; this one is for
parse-on-import (no git dependency).

Per `docs/design/controlled-vocabulary.md § Parse contract` (LLD iter-7).
"""

from __future__ import annotations

from pathlib import Path

_MAX_LEVELS = 8


def _repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` looking for `.claude-plugin/plugin.json`.

    If `start` is None, uses `Path(__file__)`. Raises RuntimeError if
    no plugin.json marker found within `_MAX_LEVELS` parents.
    """
    here = (start if start is not None else Path(__file__)).resolve()
    cur = here.parent if here.is_file() else here
    for _ in range(_MAX_LEVELS + 1):
        if (cur / ".claude-plugin" / "plugin.json").is_file():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    raise RuntimeError("orchestra repo root not found")
