"""cli.lint --skill-names — mechanical enforcement of ADR-002 skill naming convention.

Walks `skills/<plugin>/SKILL.md` + `skills/<plugin>/<subskill>/SKILL.md` files,
parses YAML frontmatter, validates `name:` field against ADR-002 rules:

- Bare lowercase identifier `^[a-z][a-z0-9-]*$`
- No `orchestra-` prefix (plugin namespacing is via `commands/<name>.md` shims)
- No `:` or `/` characters (illegal grammar)
- Must be present and non-empty

Implementation: `cli.lint.lint_skill_names(repo_root: Path) -> list[Finding]`.
CLI entry: `python -m cli.lint --skill-names` (exit 0 / 1).
"""

from __future__ import annotations

from pathlib import Path

from cli.lint import lint_skill_names


def _write_skill(root: Path, *segments: str, name: str | None = None,
                 description: str = "stub") -> Path:
    p = root.joinpath(*segments) / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if name is None:
        body = f"---\ndescription: {description}\n---\n# stub\n"
    else:
        body = f"---\nname: {name}\ndescription: {description}\n---\n# stub\n"
    p.write_text(body)
    return p


def test_bare_name_accepted(tmp_path):
    _write_skill(tmp_path, "skills", "init", name="init")
    _write_skill(tmp_path, "skills", "commit", name="commit")
    _write_skill(tmp_path, "skills", "spec-review", name="spec-review")
    findings = lint_skill_names(tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_orchestra_prefix_rejected(tmp_path):
    _write_skill(tmp_path, "skills", "init", name="orchestra-init")
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on orchestra- prefix"
    assert any("orchestra-" in f.message for f in findings)


def test_colon_rejected(tmp_path):
    _write_skill(tmp_path, "skills", "design-docs", name="design-docs:init")
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on colon in name"
    assert any("`:`" in f.message or "colon" in f.message.lower() for f in findings)


def test_slash_rejected(tmp_path):
    _write_skill(tmp_path, "skills", "design-docs", name="design/init")
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on slash in name"
    assert any("`/`" in f.message or "slash" in f.message.lower() for f in findings)


def test_uppercase_rejected(tmp_path):
    _write_skill(tmp_path, "skills", "init", name="Init")
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on uppercase"


def test_missing_name_field_rejected(tmp_path):
    _write_skill(tmp_path, "skills", "init", name=None)
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on missing name field"


def test_empty_name_field_rejected(tmp_path):
    _write_skill(tmp_path, "skills", "init", name="")
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on empty name field"


def test_sub_skill_bare_name_accepted(tmp_path):
    """Sub-skills at skills/<parent>/<subskill>/SKILL.md follow same rules."""
    _write_skill(tmp_path, "skills", "design-docs", name="design-docs")
    _write_skill(tmp_path, "skills", "design-docs", "init", name="init")
    findings = lint_skill_names(tmp_path)
    assert findings == [], f"expected no findings, got: {[f.message for f in findings]}"


def test_sub_skill_with_parent_prefix_rejected(tmp_path):
    """Sub-skill named `design-docs-init` rejected per ADR-002 (use bare `init`)."""
    _write_skill(tmp_path, "skills", "design-docs", name="design-docs")
    _write_skill(tmp_path, "skills", "design-docs", "init", name="design-docs-init")
    findings = lint_skill_names(tmp_path)
    assert findings, "expected rejection on parent-prefix on sub-skill"


def test_real_orchestra_skills_tree_passes(tmp_path):
    """Smoke test against the actual orchestra repo (post-v2.0.1 state).

    Skips if not run inside the orchestra repo (e.g., consumer plugin install).
    """
    import subprocess
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip())
    except subprocess.CalledProcessError:
        return
    if not (repo_root / "skills" / "init" / "SKILL.md").exists():
        return  # not orchestra repo
    findings = lint_skill_names(repo_root)
    assert findings == [], (
        f"orchestra skills/ tree must pass --skill-names; got: "
        f"{[f.message for f in findings]}"
    )
