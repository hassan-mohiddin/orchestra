"""Phase 1 SCALE migration helper (minimal, in-tmpdir).

Encapsulates the 4 migration ops:
- DELETE .claude/rules/canon-frozen-guard.md
- DELETE .claude/rules/commit-strategy.md
- REWRITE .claude/rules/documentation-gate.md (collapse Gates 4+5)
- APPEND routing entry to .claude/skills-registry.md

Phase 4 ships transactional + multi-factor identity + symlink-safe wrapper
at `tools/migrate-scale-rules.py`; this helper is the core logic both share.
"""

from __future__ import annotations

import re
from pathlib import Path

GATE_4_5_POINTER = (
    "Gate 4 (Commit) and Gate 5 (Implementation Sync) "
    "→ see orchestra:commit skill "
    "(skills/commit/references/canon-frozen-guard.md + "
    "skills/commit/references/commit-strategy.md)."
)

QUICK_REF_GATE_4_5_POINTER = (
    "Gate 4 / Gate 5 → orchestra:commit skill "
    "(see references/canon-frozen-guard.md + references/commit-strategy.md)"
)

REGISTRY_ROW = (
    "| commit-time decision (any commit, status flip, supersession) "
    "| orchestra:commit |"
)


def _rewrite_documentation_gate(text: str) -> str:
    """Replace Gates 4 + 5 sections with pointer; collapse Quick Reference bullets."""
    # Replace Gate 4 + Gate 5 ## sections (between `## Gate 4` and `---` or end-of-section)
    pattern = re.compile(
        r"## Gate 4:[^\n]*\n.*?(?=\n## (?!Gate [45]))",
        re.DOTALL,
    )
    text = pattern.sub(f"## Gate 4 / Gate 5 — moved to orchestra:commit\n\n{GATE_4_5_POINTER}\n\n---\n\n", text)
    pattern_5 = re.compile(
        r"## Gate 5:[^\n]*\n.*?(?=\n## )",
        re.DOTALL,
    )
    text = pattern_5.sub("", text)

    # Quick Reference: replace Gate 4 + Gate 5 bullets with one pointer line
    qr_pattern = re.compile(
        r"(About to commit fix:/feat:[^\n]*\n[^\n]*\n\n[^`]*?About to run verification[^\n]*\n[^\n]*)",
        re.DOTALL,
    )
    text = qr_pattern.sub(QUICK_REF_GATE_4_5_POINTER, text)

    return text


def migrate(scale_root: Path) -> None:
    """Apply migration ops in-place. Raises if pre-state invalid.

    Caller responsible for backup/rollback in transactional contexts (Phase 4).
    """
    rules_dir = scale_root / ".claude" / "rules"
    registry = scale_root / ".claude" / "skills-registry.md"

    # Pre-flight
    canon_path = rules_dir / "canon-frozen-guard.md"
    strategy_path = rules_dir / "commit-strategy.md"
    docgate_path = rules_dir / "documentation-gate.md"

    missing = [
        p for p in (canon_path, strategy_path, docgate_path, registry)
        if not p.is_file()
    ]
    if missing:
        raise FileNotFoundError(f"pre-migration source missing: {missing}")

    # 1. DELETE canon-frozen-guard.md
    canon_path.unlink()
    # 2. DELETE commit-strategy.md
    strategy_path.unlink()
    # 3. REWRITE documentation-gate.md
    docgate_path.write_text(_rewrite_documentation_gate(docgate_path.read_text()))
    # 4. APPEND registry row
    existing = registry.read_text()
    if REGISTRY_ROW not in existing:
        if not existing.endswith("\n"):
            existing += "\n"
        registry.write_text(existing + REGISTRY_ROW + "\n")


def assert_post_state(scale_root: Path) -> None:
    """Post-flight invariant check. Raises AssertionError on any mismatch."""
    rules_dir = scale_root / ".claude" / "rules"
    registry = scale_root / ".claude" / "skills-registry.md"

    assert not (rules_dir / "canon-frozen-guard.md").exists(), "canon-frozen-guard.md should be deleted"
    assert not (rules_dir / "commit-strategy.md").exists(), "commit-strategy.md should be deleted"

    docgate = (rules_dir / "documentation-gate.md").read_text()
    assert "## Gate 1:" in docgate, "Gate 1 section missing"
    assert "## Gate 2:" in docgate, "Gate 2 section missing"
    assert "## Gate 3:" in docgate, "Gate 3 section missing"
    assert "orchestra:commit skill" in docgate, "Gate 4+5 pointer missing"

    registry_text = registry.read_text()
    assert "orchestra:commit" in registry_text, "registry routing entry missing"
