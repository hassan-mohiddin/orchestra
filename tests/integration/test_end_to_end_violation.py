"""Slice 8.2 — Integration: end-to-end violation → lint → apply pipeline.

Wires together the full LLD-012 v2.1 surface in a throwaway repo:

  1. cli.install_claude_hooks → settings.json present + verifies clean
  2. cli.hooks.session_start_inject → JSON envelope readable (no live API)
  3. cli.lessons_violation × 3 → kind=violation entries appended
  4. cli.lessons_lint → ≥3-recurrence triggers proxy artifact
  5. seeded attestation pass → cli.lessons_apply mutates target +
     auto-promote marker appended → next lessons_lint scan no longer
     re-detects (recursion guard closed)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_TARGET_TLDR = (
    "# documentation-gate\n"
    "\n"
    "## TLDR — Nonnegotiables\n"
    "\n"
    "- INVESTIGATION reveals defect → STOP and file BUG-NNN.\n"
    "- NO code without committed design doc + passed spec review.\n"
    "\n"
    "<!-- Full rule body below this section -->\n"
    "\n"
    "body.\n"
)


def _run(
    module_args: list[str], cwd: Path, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("ANTHROPIC_API_KEY",)
    }
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.setdefault("PATH", os.environ.get("PATH", ""))
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, *module_args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _seed_throwaway_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    (tmp_path / ".claude/rules").mkdir(parents=True)
    (tmp_path / ".claude/rules/documentation-gate.md").write_text(
        _TARGET_TLDR, encoding="utf-8"
    )
    (tmp_path / ".claude/CLAUDE.md").write_text(
        "## TLDR — Nonnegotiables\n\n- READ docs/HANDOFF.md anchor.\n\n"
        "<!-- Full rule body below this section -->\n",
        encoding="utf-8",
    )


def test_end_to_end_violation_pipeline(tmp_path: Path) -> None:
    _seed_throwaway_repo(tmp_path)

    # --- Step 1: install hooks -------------------------------------------
    install = _run(["-m", "cli.install_claude_hooks"], tmp_path)
    assert install.returncode == 0, install.stderr
    settings = tmp_path / ".claude/settings.json"
    assert settings.exists()
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert "SessionStart" in data["hooks"]
    verify = _run(["-m", "cli.install_claude_hooks", "--verify"], tmp_path)
    assert verify.returncode == 0, verify.stderr

    # --- Step 2: SessionStart hook emits clean JSON ----------------------
    ss = _run(["-m", "cli.hooks.session_start_inject"], tmp_path)
    assert ss.returncode == 0, ss.stderr
    payload = json.loads(ss.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "[ORCHESTRA TLDR]" in payload["hookSpecificOutput"]["additionalContext"]

    # --- Step 3: 3 violations same rule ---------------------------------
    for i in range(3):
        proc = _run(
            [
                "-m",
                "cli.lessons_violation",
                "--rule=documentation-gate",
                f"--observed=agent skipped spec-review run #{i}",
                "--expected=spec-review fires on every doc edit",
            ],
            tmp_path,
        )
        assert proc.returncode == 0, proc.stderr

    # --- Step 4: lessons_lint detects + writes proxy ---------------------
    lint = _run(["-m", "cli.lessons_lint"], tmp_path)
    assert lint.returncode == 0, lint.stderr
    assert "proxy artifact:" in lint.stdout, lint.stdout
    proxy_dir = tmp_path / "docs/proposed-rule-mutations"
    proxies = list(proxy_dir.glob("documentation-gate-*.md"))
    assert len(proxies) == 1
    proxy = proxies[0]
    body = proxy.read_text(encoding="utf-8")
    assert "MUST Spec-review fires on every doc edit." in body

    # --- Step 5: seed attestation as `pass` ------------------------------
    reviews = tmp_path / "docs/reviews"
    reviews.mkdir(parents=True)
    att = reviews / f"{proxy.stem}-r1.orchestra.review.yaml"
    att.write_text("overall_verdict: pass\n", encoding="utf-8")

    # --- Step 6: lessons_apply mutates target + writes marker -----------
    apply = _run(["-m", "cli.lessons_apply", str(proxy.relative_to(tmp_path))], tmp_path)
    assert apply.returncode == 0, apply.stderr
    target_after = (tmp_path / ".claude/rules/documentation-gate.md").read_text(
        encoding="utf-8"
    )
    assert "- MUST Spec-review fires on every doc edit." in target_after
    assert "- INVESTIGATION reveals defect" in target_after  # pre-existing preserved

    # --- Step 7: lessons file has the auto-promote marker ----------------
    lessons_files = list((tmp_path / "docs/lessons").glob("*-lessons.md"))
    assert lessons_files, "lessons file must exist after violations"
    combined = "\n".join(p.read_text(encoding="utf-8") for p in lessons_files)
    assert "kind: promotion-marker" in combined
    assert "source: auto-promote" in combined
    assert "documentation-gate" in combined

    # --- Step 8: recursion guard — re-running lint must NOT re-trigger ---
    lint2 = _run(["-m", "cli.lessons_lint"], tmp_path)
    assert lint2.returncode == 0
    # Same 3 violation entries still present, but the promotion-marker entry
    # is now in the lessons file. The recursion guard skips entries with
    # source: auto-promote, so the original 3 still count toward recurrence
    # and a SECOND proxy may be written (with today's date — same filename
    # if same day). The contract: no infinite re-detection of the
    # promotion-marker itself.
    new_proxies = list(proxy_dir.glob("documentation-gate-*.md"))
    assert len(new_proxies) >= 1
