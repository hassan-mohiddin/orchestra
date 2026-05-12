"""Slice 7 — codex #4 regression: --force overwrite fail-closed on malformed existing v2.0 attestation.

LLD-011 slice 1.7 already refuses overwrite of v1.0 attestations
(frozen-historical) regardless of --force. The remaining codex #4 gap:
when --force is passed AND the existing target is a v2.0 attestation
whose YAML is malformed, the spec_review main path used to proceed to
overwrite without inspecting the existing file. Phase 7 inserts a parse
check that fails non-zero with an informative stderr message.

File name preserved as `test_schema_v1_overwrite_failclosed.py` per plan
slice 7.1 even though the impl targets v2.0 — the regression label
tracks the codex finding #4 lineage.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_spec_review(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli.spec_review", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(REPO_ROOT), "PATH": ""},
    )


def test_force_mode_refuses_on_malformed_existing(
    tmp_path: Path,
) -> None:
    """codex #4: --force on a malformed existing v2.0 attestation must refuse."""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    docs_features = tmp_path / "docs/features"
    docs_features.mkdir(parents=True)
    doc = docs_features / "999-foo.md"
    doc.write_text("# 999 Foo\n\n> **Iteration:** 1\n\nbody.\n", encoding="utf-8")

    reviews = tmp_path / "docs/reviews"
    reviews.mkdir(parents=True)
    malformed = reviews / "999-foo-r1.orchestra.review.yaml"
    malformed.write_text(
        "schema_version: 2.0\n"
        "findings_aggregated:\n"
        "  - severity: Critical\n"
        "    location: 'unclosed quote\n"
        "    problem: malformed line",
        encoding="utf-8",
    )
    original_bytes = malformed.read_bytes()

    from cli.spec_review import _detect_schema_version

    assert _detect_schema_version(malformed) != "1.0", (
        "test fixture must be non-v1.0 — v1.0 branch handled separately"
    )

    from cli import spec_review
    import io
    import contextlib

    err_buf = io.StringIO()
    argv = [
        "--aggregate-and-write",
        "--force",
        str(doc.relative_to(tmp_path)),
    ]
    import os

    cwd_original = os.getcwd()
    try:
        os.chdir(tmp_path)
        with contextlib.redirect_stderr(err_buf):
            rc = spec_review.main(argv)
    finally:
        os.chdir(cwd_original)

    err = err_buf.getvalue()
    assert rc != 0, f"force-mode overwrite of malformed file must refuse, got rc={rc}"
    assert "force-mode overwrite refused" in err or "malformed YAML" in err, (
        f"expected refusal message in stderr, got: {err!r}"
    )
    assert malformed.read_bytes() == original_bytes, (
        "malformed file must not be mutated by refused overwrite"
    )
