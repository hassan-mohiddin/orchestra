"""Tests for cli.init Bucket 2 scaffold + DECISIONS seeding."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cli.init import scaffold_bucket_1, scaffold_bucket_2


def _config(addons: bool = True) -> dict:
    return {
        "version": "1.1",
        "orchestra": {"mode": "solo"},
        "skills": {
            "design-docs": {
                "doc_paths": {
                    "features": "docs/features",
                    "bugs": "docs/bugs",
                    "adr": "docs/adr",
                    "design": "docs/design",
                    "postmortems": "docs/postmortems",
                    "runbooks": "docs/runbooks",
                    "plans": "docs/plans",
                },
                "doc_types": {"preset": "default-7", "renames": {}, "custom_types": []},
                "ci_workflow_installed": addons,
                "agents_md_installed": addons,
                "llms_txt_installed": addons,
            }
        },
    }


def test_bucket2_writes_all_addons(tmp_repo: Path) -> None:
    result = scaffold_bucket_2(_config(addons=True), tmp_repo)
    assert result.ok
    assert (tmp_repo / ".github" / "workflows" / "orchestra-lint.yml").exists()
    assert (tmp_repo / "AGENTS.md").exists()
    assert (tmp_repo / "llms.txt").exists()


def test_bucket2_skips_when_off(tmp_repo: Path) -> None:
    scaffold_bucket_2(_config(addons=False), tmp_repo)
    assert not (tmp_repo / "AGENTS.md").exists()
    assert not (tmp_repo / "llms.txt").exists()
    assert not (tmp_repo / ".github").exists()


def test_bucket2_idempotent(tmp_repo: Path) -> None:
    scaffold_bucket_2(_config(addons=True), tmp_repo)
    second = scaffold_bucket_2(_config(addons=True), tmp_repo)
    assert second.ok
    assert len(second.skipped) == 3


def test_decisions_seeded_on_init(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config(addons=False), tmp_repo)
    assert (tmp_repo / "docs" / "adr" / "DECISIONS.md").exists()


def test_decisions_idempotent(tmp_repo: Path) -> None:
    scaffold_bucket_1(_config(addons=False), tmp_repo)
    scaffold_bucket_1(_config(addons=False), tmp_repo)
    # Should not error; file may be regenerated or skipped
    assert (tmp_repo / "docs" / "adr" / "DECISIONS.md").exists()


# ---------------------------------------------------------------------------
# BUG-004 — project-aware template substitution
# ---------------------------------------------------------------------------


def test_detect_project_context_pyproject_name(tmp_repo: Path) -> None:
    """BUG-004 — pyproject.toml [project].name wins over dir name."""
    from cli.init import detect_project_context
    (tmp_repo / "pyproject.toml").write_text(
        '[project]\nname = "scale"\nversion = "0.1.0"\n'
    )
    ctx = detect_project_context(tmp_repo)
    assert ctx["project_name"] == "scale"
    assert "Python" in ctx["tech_stack"]


def test_detect_project_context_node_name(tmp_repo: Path) -> None:
    """BUG-004 — package.json name picked up when no pyproject; tech_stack=Node.js."""
    from cli.init import detect_project_context
    (tmp_repo / "package.json").write_text(json.dumps({"name": "myapp", "version": "1.0.0"}))
    ctx = detect_project_context(tmp_repo)
    assert ctx["project_name"] == "myapp"
    assert "Node.js" in ctx["tech_stack"]


def test_detect_project_context_fallback_to_repo_dir(tmp_repo: Path) -> None:
    """BUG-004 — no pyproject, no package.json → fall back to repo dir name."""
    from cli.init import detect_project_context
    ctx = detect_project_context(tmp_repo)
    assert ctx["project_name"] == tmp_repo.name


def test_detect_project_context_git_remote(tmp_repo: Path) -> None:
    """BUG-004 — git remote origin URL captured in repo_url."""
    from cli.init import detect_project_context
    subprocess.run(
        ["git", "-C", str(tmp_repo), "remote", "add", "origin",
         "https://github.com/hassan-mohiddin/orchestra.git"],
        check=True, capture_output=True,
    )
    ctx = detect_project_context(tmp_repo)
    assert ctx["repo_url"] == "https://github.com/hassan-mohiddin/orchestra.git"


def test_render_template_substitutes_vars(tmp_repo: Path) -> None:
    """BUG-004 — _render_template replaces {{var}} with ctx value."""
    from cli.init import _render_template
    out = _render_template(
        "Project: {{project_name}}\nRepo: {{repo_url}}\n",
        {"project_name": "scale", "repo_url": "https://x.com/scale"},
    )
    assert "Project: scale" in out
    assert "Repo: https://x.com/scale" in out
    assert "{{" not in out, "No placeholder must leak through"


def test_render_template_missing_var_emits_dash(tmp_repo: Path) -> None:
    """BUG-004 — placeholder with no matching ctx key renders as em-dash, not literal."""
    from cli.init import _render_template
    out = _render_template("Repo: {{repo_url}}\n", {})
    assert "{{repo_url}}" not in out, "Missing placeholder must not leak as literal"
    assert "—" in out, "Missing placeholder should render as em-dash (clearer than empty)"


def test_agents_md_substitutes_project_name(tmp_repo: Path) -> None:
    """BUG-004 — end-to-end: scaffold_bucket_2 writes AGENTS.md with substituted project_name."""
    (tmp_repo / "pyproject.toml").write_text('[project]\nname = "scale"\n')
    subprocess.run(
        ["git", "-C", str(tmp_repo), "remote", "add", "origin",
         "https://github.com/hassan-mohiddin/scale.git"],
        check=True, capture_output=True,
    )
    scaffold_bucket_2(_config(addons=True), tmp_repo)
    agents = (tmp_repo / "AGENTS.md").read_text()
    assert "scale" in agents, "AGENTS.md must include project_name from pyproject"
    assert "{{" not in agents, "No placeholder must leak into final AGENTS.md"


def test_llms_txt_substitutes_project_name(tmp_repo: Path) -> None:
    """BUG-004 — end-to-end: scaffold_bucket_2 writes llms.txt with substituted project_name."""
    (tmp_repo / "pyproject.toml").write_text('[project]\nname = "scale"\n')
    scaffold_bucket_2(_config(addons=True), tmp_repo)
    llms = (tmp_repo / "llms.txt").read_text()
    assert "scale" in llms, "llms.txt must include project_name"
    assert "{{" not in llms
