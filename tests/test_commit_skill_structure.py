"""Tests for orchestra:commit skill directory structure (LLD-008 r7 T1)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "skills" / "commit"

EXPECTED_FILES = (
    "SKILL.md",
    "templates/pre-commit.sh",
    "templates/commit-msg.sh",
    "references/commit-strategy.md",
    "references/canon-frozen-guard.md",
    "references/refs-line-rules.md",
    "references/doc-vs-code-commit.md",
    "references/supersession-decision.md",
)


def test_skill_dir_has_expected_files() -> None:
    missing = [rel for rel in EXPECTED_FILES if not (SKILL_ROOT / rel).is_file()]
    assert not missing, f"missing skill files: {missing}"


def test_skill_dir_file_count_exactly_eight() -> None:
    found = sorted(p.relative_to(SKILL_ROOT).as_posix()
                   for p in SKILL_ROOT.rglob("*") if p.is_file())
    assert found == sorted(EXPECTED_FILES), (
        f"skill dir contents drift; expected {sorted(EXPECTED_FILES)}, got {found}"
    )
