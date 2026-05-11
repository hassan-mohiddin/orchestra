"""SCALE migration post-state test (LLD-008 r7 T6).

Phase 1 ships a minimal in-tmpdir test; Phase 4 (transactional helper) adds
expanded test coverage in `test_scale_migration_transactional.py`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from tools.scale_migration_core import assert_post_state, migrate

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "scale-pre-migration"


def _replicate_fixture(dest: Path) -> Path:
    shutil.copytree(FIXTURE, dest / "scale", dirs_exist_ok=False)
    return dest / "scale"


def test_scale_migration_post_state(tmp_path: Path) -> None:
    scale_root = _replicate_fixture(tmp_path)
    migrate(scale_root)
    assert_post_state(scale_root)
