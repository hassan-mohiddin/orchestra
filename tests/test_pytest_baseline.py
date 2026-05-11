"""Pytest baseline assertion (LLD-008 r7 T7).

Lower-bound only — asserts ≥167 after Phase 1 ships. Higher counts permitted
as later phases land (Phase 2 → ≥220, Phase 3 → ≥248, Phase 4 → ≥252).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ORCHESTRA_ROOT = Path(__file__).resolve().parent.parent


def test_baseline_at_least_167() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        capture_output=True, text=True, cwd=str(ORCHESTRA_ROOT),
    )
    last = [ln for ln in proc.stdout.splitlines() if "test" in ln and "collected" in ln]
    assert last, f"could not parse pytest summary: {proc.stdout!r}"
    count = int(last[-1].split()[0])
    assert count >= 167, f"pytest baseline regressed: {count} < 167"
