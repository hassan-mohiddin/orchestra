# BUG-004: AGENTS.md and llms.txt templates lack project-specific customization

> **Doc ID:** BUG-004-templates-not-project-aware
> **Date:** 2026-05-06
> **DRI:** Hassan Mohiddin
> **Severity:** Medium
> **Status:** Investigating

## Observed Behavior

`cli.init` (Bucket 2) writes:
- `AGENTS.md` — generic template (mentions "this repository" + orchestra by name, no project specifics)
- `llms.txt` — generic template (refs orchestra paths only)

In SCALE: AGENTS.md doesn't mention SCALE, FastAPI, Next.js, Supabase, or any tech stack. AI agents reading it learn generic orchestra discipline but nothing about the actual project they're helping with.

## Expected Behavior

Templates substitute project-aware values during install:
- Project name (from git remote OR `pyproject.toml` `[project].name` OR repo dir name)
- Repo URL (from git remote `origin`)
- Top-level tech stack (detected via file presence: `package.json` → Node/Next, `pyproject.toml` → Python/FastAPI, `Cargo.toml` → Rust, etc.)
- Optional brief description prompt during init

## Steps to Reproduce

1. `python -m cli.init` in any project
2. Open `AGENTS.md`
3. Observe: only orchestra-specific content; no project-specific information

## Environment

- orchestra v1.1.0 — v1.3.0

## Root Cause Analysis

```mermaid
graph LR
    A[cli/templates/AGENTS.md.template] -->|cp verbatim| B[project AGENTS.md]
    A -->|no substitution| B

    style A fill:#fee2e2
    style B fill:#fee2e2
```

**Root cause:** `cli/init.py` `scaffold_bucket_2()` does a plain file copy. No template engine, no placeholder substitution, no project introspection.

## Fix Description

Add project-context detection helper + template substitution:

```python
# cli/init.py

def detect_project_context(root: Path) -> dict[str, str]:
    """Best-effort project introspection."""
    ctx = {"project_name": root.name, "repo_url": "", "tech_stack": []}
    # git remote
    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=root, text=True
        ).strip()
        ctx["repo_url"] = remote
    except subprocess.CalledProcessError:
        pass
    # pyproject.toml name
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        # parse [project] name (toml stdlib)
        ...
    # tech stack heuristics
    if (root / "package.json").exists():
        ctx["tech_stack"].append("Node.js")
    if pyproject.exists():
        ctx["tech_stack"].append("Python")
    if (root / "Cargo.toml").exists():
        ctx["tech_stack"].append("Rust")
    return ctx


def _render_template(template: str, ctx: dict) -> str:
    """Simple {{var}} substitution. No external deps."""
    out = template
    for k, v in ctx.items():
        out = out.replace(f"{{{{{k}}}}}", str(v) if not isinstance(v, list) else ", ".join(v))
    return out
```

Update templates to use `{{project_name}}`, `{{repo_url}}`, `{{tech_stack}}` placeholders. `scaffold_bucket_2()` invokes detect+render.

Files:
- `cli/init.py` — add `detect_project_context()` + `_render_template()`; modify `scaffold_bucket_2()` to render
- `cli/templates/AGENTS.md.template` — add placeholder usage
- `cli/templates/llms.txt.template` — same
- `tests/test_cli_init_bucket2.py` — add `test_agents_md_substitutes_project_name` etc.

## Iteration Log

| Date | Hypothesis | Change | Result |
|---|---|---|---|
| 2026-05-06 | (none yet — bug filed for v1.4 fix) | — | — |

## Regression Prevention

Tests verify that templates with placeholders correctly substitute when `detect_project_context()` returns realistic dict; missing fields render as empty string (no `{{var}}` literals leak).

## Related Documents

- LLD-001: `docs/features/001-design-docs-init.md` Bucket 2 description
- AGENTS.md spec: https://agents.md/

## Changelog

| Date | Change |
|---|---|
| 2026-05-06 | Filed during SCALE audit. Status: Investigating. Target fix: v1.4. |
