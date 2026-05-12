"""Slice 5.4 — /orchestra:lessons-lint shim structural test.

The actual cli.lessons_lint scan implementation lands in Phase 6 (Slice 6.1).
This test asserts the shim file exists with valid frontmatter + body that
references `cli.lessons_lint`.
"""

from pathlib import Path

import frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIM_PATH = REPO_ROOT / "commands" / "lessons-lint.md"


def test_lessons_lint_shim_exists() -> None:
    assert SHIM_PATH.exists(), f"shim missing at {SHIM_PATH}"


def test_lessons_lint_shim_invokes_cli() -> None:
    post = frontmatter.load(str(SHIM_PATH))
    assert post.metadata.get("description"), "shim must have description frontmatter"
    body = post.content
    assert "cli.lessons_lint" in body, "shim body must reference cli.lessons_lint"
    assert "python -m cli.lessons_lint" in body, (
        "shim body must show the canonical invocation"
    )


def test_lessons_lint_shim_no_auto_spec_review() -> None:
    """LLD-012 SC-8 Class-B: shim must NOT promise auto-spec-review."""
    post = frontmatter.load(str(SHIM_PATH))
    body = post.content
    assert "does NOT auto-trigger" in body or "Class-B" in body, (
        "shim must document that lessons_lint emits proxy artifacts only"
    )
