"""Orchestra init — scaffold docs/ + .claude/orchestra.json + add-ons.

Implements:
- Bucket 1: docs/ subdirs + STANDARDS.md + .gitignore append (always)
- Bucket 2: CI workflow + AGENTS.md + llms.txt (prompted)
- DECISIONS.md seeding (always-run)
- Custom doc-types (default-7 / subset-rename / full-custom)
- Invariants enforcement (formal vocab whitelist + custom-type rules)
- v1.0 -> v1.1 config migration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cli.config import REQUIRED_DOC_PATHS

GITKEEP = ".gitkeep"


@dataclass
class ScaffoldResult:
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def scaffold_bucket_1(config: dict, root: Path, force: bool = False) -> ScaffoldResult:
    """Create docs/ subdirs + .gitignore append. STANDARDS.md handled separately."""
    result = ScaffoldResult()

    doc_paths = config["skills"]["design-docs"]["doc_paths"]

    for key in REQUIRED_DOC_PATHS:
        rel = doc_paths[key]
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / GITKEEP
        if gitkeep.exists() and not force:
            result.skipped.append(gitkeep)
        else:
            gitkeep.touch()
            result.created.append(gitkeep)

    _append_gitignore(root, result, force)

    return result


GITIGNORE_ENTRIES = [
    "# orchestra (added by orchestra:init)",
    ".claude/orchestra.local.json",
    "docs/investigations/",
    ".eval-workspace/",
]


def _append_gitignore(root: Path, result: ScaffoldResult, force: bool) -> None:
    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    new_lines = []
    for entry in GITIGNORE_ENTRIES:
        if entry not in existing:
            new_lines.append(entry)
    if not new_lines:
        result.skipped.append(gitignore)
        return
    sep = "\n" if existing and not existing.endswith("\n") else ""
    block = sep + "\n".join(new_lines) + "\n"
    gitignore.write_text(existing + block)
    if gitignore in result.skipped:
        result.skipped.remove(gitignore)
    if gitignore not in result.created:
        result.created.append(gitignore)
