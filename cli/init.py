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

import subprocess
import sys

from cli.config import REQUIRED_DOC_PATHS

GITKEEP = ".gitkeep"
TEMPLATES_DIR = Path(__file__).parent / "templates"


class InvariantViolation(Exception):
    """Raised when a custom doc-type or rename violates orchestra invariants."""


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

    # Generate STANDARDS.md
    standards_md = root / "docs" / "STANDARDS.md"
    if standards_md.exists() and not force:
        result.skipped.append(standards_md)
    else:
        content = generate_standards_md(config)
        standards_md.write_text(content)
        result.created.append(standards_md)

    # Always-run: seed DECISIONS.md
    seed_decisions_index(root, result, force)

    return result


def scaffold_bucket_2(config: dict, root: Path, force: bool = False) -> ScaffoldResult:
    """Create CI workflow + AGENTS.md + llms.txt."""
    result = ScaffoldResult()
    dd = config["skills"]["design-docs"]

    if dd.get("ci_workflow_installed"):
        ci_path = root / ".github" / "workflows" / "orchestra-lint.yml"
        ci_path.parent.mkdir(parents=True, exist_ok=True)
        if ci_path.exists() and not force:
            result.skipped.append(ci_path)
        else:
            ci_path.write_text((TEMPLATES_DIR / "orchestra-lint.yml").read_text())
            result.created.append(ci_path)

    if dd.get("agents_md_installed"):
        agents_path = root / "AGENTS.md"
        if agents_path.exists() and not force:
            result.skipped.append(agents_path)
        else:
            agents_path.write_text((TEMPLATES_DIR / "AGENTS.md.template").read_text())
            result.created.append(agents_path)

    if dd.get("llms_txt_installed"):
        llms_path = root / "llms.txt"
        if llms_path.exists() and not force:
            result.skipped.append(llms_path)
        else:
            llms_path.write_text((TEMPLATES_DIR / "llms.txt.template").read_text())
            result.created.append(llms_path)

    return result


def seed_decisions_index(root: Path, result: ScaffoldResult, force: bool) -> None:
    """Run cli.decisions_index to seed docs/adr/DECISIONS.md (always-run)."""
    adr_dir = root / "docs" / "adr"
    output = adr_dir / "DECISIONS.md"

    if output.exists() and not force:
        result.skipped.append(output)
        return

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "cli.decisions_index",
             "--adr-dir", str(adr_dir),
             "--output", str(output)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        combined = (proc.stdout + proc.stderr).lower()
        if proc.returncode != 0 and "no adrs found" not in combined:
            result.errors.append(f"decisions_index failed: {proc.stderr}")
            return
    except Exception as e:
        result.errors.append(f"decisions_index error: {e}")
        return

    if output.exists():
        result.created.append(output)
    else:
        # No ADRs yet — seed empty index manually
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("# Decision Records Index\n\n_No ADRs yet. This index regenerates on each commit._\n")
        result.created.append(output)


def generate_standards_md(config: dict) -> str:
    """Emit STANDARDS.md content per doc_types preset."""
    doc_types = config["skills"]["design-docs"]["doc_types"]
    preset = doc_types["preset"]

    template = (TEMPLATES_DIR / "standards-default-7.md").read_text()

    if preset == "default-7":
        return template

    if preset == "subset-rename":
        return _apply_renames(template, doc_types.get("renames", {}))

    if preset == "full-custom":
        return _generate_full_custom(template, doc_types.get("custom_types", []))

    raise InvariantViolation(f"Unknown preset: {preset!r}")


def _apply_renames(template: str, renames: dict[str, str]) -> str:
    """Validate and apply rename map to STANDARDS.md template."""
    for original, new_name in renames.items():
        validate_rename(new_name)
        template = template.replace(original, new_name)
    return template


def _generate_full_custom(template: str, custom_types: list[dict]) -> str:
    """Append full-custom doc-type sections to template."""
    for ct in custom_types:
        validate_custom_type(ct)
    out = template + "\n\n## Custom Doc Types\n\n"
    for ct in custom_types:
        out += f"### {ct['name']}\n\n"
        out += f"- **Path:** `docs/{ct['path']}/`\n"
        out += f"- **Naming:** `{ct['naming_pattern']}`\n"
        out += f"- **Status enum:** {' | '.join(ct['status_enum'])}\n"
        out += f"- **Required sections:** {', '.join(ct['required_sections'])}\n"
        if ct.get("mermaid_required"):
            out += f"- **Mermaid:** ≥{ct.get('mermaid_min_count', 1)}\n"
        out += "\n"
    return out


# Formal vocabulary whitelist — sourced from industry literature.
# RFC explicitly excluded per orchestra-philosophy "Formal Vocabulary" stance.
FORMAL_VOCAB_WHITELIST = {
    "Tech Spec", "Engineering Design", "Spec", "Design Brief",
    "Decision Record", "Architecture Decision", "Incident Report",
    "Operations Runbook", "Implementation Plan", "Engineering Plan",
    "Postmortem", "Retrospective",
    # Original canonical names also acceptable (no-op rename):
    "Feature LLD", "Bug Report", "ADR", "Design Doc", "Runbook", "Plan",
}


def validate_rename(new_name: str) -> None:
    """Enforce formal-vocab whitelist for subset-rename mode."""
    if new_name not in FORMAL_VOCAB_WHITELIST:
        allowed = sorted(FORMAL_VOCAB_WHITELIST)
        raise InvariantViolation(
            f"Rename target {new_name!r} not in formal-vocab whitelist. "
            f"Allowed: {allowed}. Note: 'RFC' explicitly excluded per orchestra philosophy."
        )


def validate_custom_type(ct: dict) -> None:
    """Enforce orchestra invariants on full-custom doc types."""
    if "Changelog" not in ct.get("required_sections", []):
        raise InvariantViolation(
            f"Custom type {ct.get('name')!r} missing 'Changelog' in required_sections."
        )
    if len(ct.get("status_enum", [])) < 3:
        raise InvariantViolation(
            f"Custom type {ct.get('name')!r} status_enum must have ≥3 states."
        )
    if ct.get("naming_pattern") not in {"NNN-kebab.md", "YYYY-MM-DD-kebab.md", "kebab.md"}:
        raise InvariantViolation(
            f"Custom type {ct.get('name')!r} naming_pattern invalid."
        )
    import re
    path = ct.get("path", "")
    if not re.match(r"^[a-z][a-z0-9-]*$", path):
        raise InvariantViolation(
            f"Custom type {ct.get('name')!r} path {path!r} invalid (no traversal)."
        )


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
