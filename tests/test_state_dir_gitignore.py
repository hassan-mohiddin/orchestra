from pathlib import Path


def test_claude_state_listed_in_gitignore() -> None:
    """LLD-012 SC: runtime state dir excluded from version control."""
    gitignore = Path(__file__).resolve().parent.parent / ".gitignore"
    lines = {ln.strip() for ln in gitignore.read_text(encoding="utf-8").splitlines()}
    assert ".claude/state/" in lines, (
        f"Expected '.claude/state/' in .gitignore, got entries: {sorted(lines)}"
    )
