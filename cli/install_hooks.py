"""Install orchestra git hooks into .git/hooks/.

Idempotent. Detects existing hook → diff + prompt (default skip).
With --force: replace unconditionally. With --on-conflict=<skip|replace|append>:
non-interactive (honored verbatim; --force precedence).

Usage:
    python -m cli.install_hooks                       # pre-commit only
    python -m cli.install_hooks --commit-msg          # commit-msg only
    python -m cli.install_hooks --all                 # both
    python -m cli.install_hooks --force               # replace existing
    python -m cli.install_hooks --on-conflict=skip    # non-interactive skip
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

SKILL_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "skills" / "commit" / "templates"

HOOK_TEMPLATES = {
    "pre-commit": SKILL_TEMPLATES_DIR / "pre-commit.sh",
    "commit-msg": SKILL_TEMPLATES_DIR / "commit-msg.sh",
}


class SecurityError(Exception):
    """Raised when hook destination fails symlink/containment safety check."""


def _verify_hook_destination_safe(hook_path: Path, repo_root: Path) -> None:
    """Reject symlinked destinations + parent dirs outside repo boundary.

    Per LLD-008 r7 Security § + codex r4 high #2: `.git/hooks/<hook>` could
    itself be a symlink pointing outside the repo. Fail-closed before any write.
    """
    if hook_path.is_symlink():
        raise SecurityError(
            f"refusing to write to symlinked hook destination: "
            f"{hook_path} -> {hook_path.readlink()}. Remove the symlink and retry."
        )
    resolved_parent = hook_path.parent.resolve()
    resolved_repo = repo_root.resolve()
    if not str(resolved_parent).startswith(str(resolved_repo)):
        raise SecurityError(
            f"hook destination outside repo boundary: {resolved_parent}"
        )


def install_one_hook(
    repo_root: Path,
    hook_name: str,
    force: bool = False,
    on_conflict: str | None = None,
    input_fn=input,
) -> int:
    """Install a single git hook. Returns 0 on success, non-zero on error.

    `on_conflict`: None (argparse sentinel — TTY fallback to prompt, non-TTY to
    skip), or one of {skip, replace, append} (honored verbatim, non-interactive).
    `force` takes precedence: when True, replaces unconditionally regardless of
    on_conflict.
    """
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

    _verify_hook_destination_safe(hook_path, repo_root)

    expected_content = template_path.read_text()

    if hook_path.exists() and not force:
        existing = hook_path.read_text()
        if existing == expected_content:
            print(f"orchestra {hook_name} hook already installed at {hook_path}")
            return 0

        # Resolve on_conflict sentinel: None → TTY fallback
        resolved = on_conflict
        if resolved is None:
            if sys.stdin.isatty():
                print(
                    f"existing {hook_name} hook at {hook_path} differs from "
                    f"orchestra hook.",
                    file=sys.stderr,
                )
                print(
                    "Choose: [a]ppend orchestra hook, [r]eplace, [s]kip (default skip):",
                    file=sys.stderr,
                )
                choice = input_fn("> ").strip().lower()
                resolved = {"a": "append", "r": "replace", "s": "skip"}.get(
                    choice, "skip"
                )
            else:
                resolved = "skip"

        if resolved == "skip":
            print(f"skipped {hook_path}", file=sys.stderr)
            return 0
        if resolved == "replace":
            shutil.copy(template_path, hook_path)
            os.chmod(hook_path, 0o755)
            print(f"replaced {hook_path}")
            return 0
        if resolved == "append":
            existing_no_shebang = existing
            if existing.startswith("#!"):
                existing_no_shebang = "\n".join(existing.split("\n")[1:])
            new_content = (
                expected_content.rstrip()
                + "\n\n# Original hook content (preserved):\n"
                + existing_no_shebang
            )
            hook_path.write_text(new_content)
            os.chmod(hook_path, 0o755)
            print(f"appended to {hook_path}")
            return 0
        # Should be unreachable (argparse choices restrict)
        print(f"error: unknown on_conflict value: {resolved!r}", file=sys.stderr)
        return 1

    # New install OR force=True path
    shutil.copy(template_path, hook_path)
    os.chmod(hook_path, 0o755)
    if force and hook_path.exists():
        print(f"installed orchestra {hook_name} hook at {hook_path}")
    else:
        print(f"installed orchestra {hook_name} hook at {hook_path}")
    return 0


# Backward-compat alias for v1.1 callers + tests
def install_hook(repo_root: Path, force: bool = False, input_fn=input) -> int:
    """v1.1 entry point — installs pre-commit only. Preserved for compatibility."""
    return install_one_hook(repo_root, "pre-commit", force=force, input_fn=input_fn)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra install-hooks")
    parser.add_argument(
        "--commit-msg",
        action="store_true",
        help="Install commit-msg hook (Refs: line check at message author time)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Install both pre-commit and commit-msg hooks",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing hook unconditionally (precedence over --on-conflict)",
    )
    parser.add_argument(
        "--on-conflict",
        choices=["skip", "replace", "append"],
        default=None,
        help="Conflict resolution when existing hook differs; default: interactive if TTY else skip",
    )
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()

    kwargs = {"force": args.force, "on_conflict": args.on_conflict}

    if args.all:
        rc1 = install_one_hook(repo, "pre-commit", **kwargs)
        rc2 = install_one_hook(repo, "commit-msg", **kwargs)
        return rc1 or rc2
    if args.commit_msg:
        return install_one_hook(repo, "commit-msg", **kwargs)
    return install_one_hook(repo, "pre-commit", **kwargs)


if __name__ == "__main__":
    sys.exit(main())
