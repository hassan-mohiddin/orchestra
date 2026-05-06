"""Install orchestra git hooks into .git/hooks/.

Idempotent. Detects existing hook → diff + prompt (default skip).
With --force: replace unconditionally.

Usage:
    python -m cli.install_hooks                  # pre-commit only (v1.1 default)
    python -m cli.install_hooks --commit-msg     # commit-msg only (v1.2)
    python -m cli.install_hooks --all            # both pre-commit + commit-msg
    python -m cli.install_hooks --force          # replace existing
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

HOOK_TEMPLATES = {
    "pre-commit": TEMPLATES_DIR / "pre-commit.sh",
    "commit-msg": TEMPLATES_DIR / "commit-msg.sh",
}


def install_one_hook(repo_root: Path, hook_name: str, force: bool = False,
                     input_fn=input) -> int:
    """Install a single git hook. Returns 0 on success, non-zero on error."""
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        print(f"error: {repo_root} is not a git repo (no .git/ found)", file=sys.stderr)
        return 1

    template_path = HOOK_TEMPLATES.get(hook_name)
    if template_path is None:
        print(f"error: unknown hook {hook_name!r}", file=sys.stderr)
        return 1

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / hook_name

    expected_content = template_path.read_text()

    if hook_path.exists() and not force:
        existing = hook_path.read_text()
        if existing == expected_content:
            print(f"orchestra {hook_name} hook already installed at {hook_path}")
            return 0
        print(f"existing {hook_name} hook at {hook_path} differs from orchestra hook.",
              file=sys.stderr)
        print("Choose: [a]ppend orchestra hook, [r]eplace, [s]kip (default skip):",
              file=sys.stderr)
        choice = input_fn("> ").strip().lower()
        if choice == "r":
            shutil.copy(template_path, hook_path)
            os.chmod(hook_path, 0o755)
            print(f"replaced {hook_path}")
            return 0
        if choice == "a":
            existing_no_shebang = existing
            if existing.startswith("#!"):
                existing_no_shebang = "\n".join(existing.split("\n")[1:])
            new_content = (expected_content.rstrip() +
                           "\n\n# Original hook content (preserved):\n" +
                           existing_no_shebang)
            hook_path.write_text(new_content)
            os.chmod(hook_path, 0o755)
            print(f"appended to {hook_path}")
            return 0
        print(f"skipped {hook_path}", file=sys.stderr)
        return 0

    shutil.copy(template_path, hook_path)
    os.chmod(hook_path, 0o755)
    print(f"installed orchestra {hook_name} hook at {hook_path}")
    return 0


# Backward-compat alias for v1.1 callers + tests
def install_hook(repo_root: Path, force: bool = False, input_fn=input) -> int:
    """v1.1 entry point — installs pre-commit only. Preserved for compatibility."""
    return install_one_hook(repo_root, "pre-commit", force=force, input_fn=input_fn)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra install-hooks")
    parser.add_argument("--commit-msg", action="store_true",
                        help="Install commit-msg hook (Refs: line check at message author time)")
    parser.add_argument("--all", action="store_true",
                        help="Install both pre-commit and commit-msg hooks")
    parser.add_argument("--force", action="store_true",
                        help="Replace existing hook unconditionally")
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()

    if args.all:
        rc1 = install_one_hook(repo, "pre-commit", force=args.force)
        rc2 = install_one_hook(repo, "commit-msg", force=args.force)
        return rc1 or rc2
    if args.commit_msg:
        return install_one_hook(repo, "commit-msg", force=args.force)
    return install_one_hook(repo, "pre-commit", force=args.force)


if __name__ == "__main__":
    sys.exit(main())
