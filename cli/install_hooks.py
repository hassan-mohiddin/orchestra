"""Install orchestra pre-commit hook into .git/hooks/.

Idempotent. Detects existing hook → diff + prompt (default skip).
With --force: replace unconditionally.

Usage:
    python -m cli.install_hooks
    python -m cli.install_hooks --force
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"
HOOK_TEMPLATE = TEMPLATES_DIR / "pre-commit.sh"


def install_hook(repo_root: Path, force: bool = False,
                 input_fn=input) -> int:
    """Install pre-commit hook. Returns 0 on success, non-zero on error."""
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        print(f"error: {repo_root} is not a git repo (no .git/ found)", file=sys.stderr)
        return 1

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    expected_content = HOOK_TEMPLATE.read_text()

    if hook_path.exists() and not force:
        existing = hook_path.read_text()
        if existing == expected_content:
            print(f"orchestra pre-commit hook already installed at {hook_path}")
            return 0
        # Different content — prompt
        print(f"existing pre-commit hook at {hook_path} differs from orchestra hook.", file=sys.stderr)
        print("Choose: [a]ppend orchestra hook, [r]eplace, [s]kip (default skip):", file=sys.stderr)
        choice = input_fn("> ").strip().lower()
        if choice == "r":
            shutil.copy(HOOK_TEMPLATE, hook_path)
            os.chmod(hook_path, 0o755)
            print(f"replaced {hook_path}")
            return 0
        if choice == "a":
            existing_no_shebang = existing
            if existing.startswith("#!"):
                existing_no_shebang = "\n".join(existing.split("\n")[1:])
            new_content = expected_content.rstrip() + "\n\n# Original hook content (preserved):\n" + existing_no_shebang
            hook_path.write_text(new_content)
            os.chmod(hook_path, 0o755)
            print(f"appended to {hook_path}")
            return 0
        print(f"skipped {hook_path}", file=sys.stderr)
        return 0

    shutil.copy(HOOK_TEMPLATE, hook_path)
    os.chmod(hook_path, 0o755)
    print(f"installed orchestra pre-commit hook at {hook_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra install-hooks")
    parser.add_argument("--force", action="store_true",
                        help="Replace existing hook unconditionally")
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    return install_hook(repo, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
