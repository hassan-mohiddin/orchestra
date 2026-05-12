"""Install / verify / uninstall orchestra's Claude Code hooks (LLD-012 SC-2).

Writes `.claude/settings.json` with three hook entries (SessionStart with
matcher `startup|resume|clear|compact`, PreCompact, UserPromptSubmit) per
LLD-012 §Hook architecture. Resolves the Python interpreter via
`sys.executable` at install time (codex finding #3 fix — do NOT hardcode
`.venv/bin/python`).

CLI surface:
    python -m cli.install_claude_hooks            # install
    python -m cli.install_claude_hooks --uninstall  # Phase 4.2
    python -m cli.install_claude_hooks --verify     # Phase 4.3 (CI gate)
    python -m cli.install_claude_hooks --force      # Phase 4.5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path(".claude/settings.json")
SESSION_START_MATCHER = "startup|resume|clear|compact"
ORCHESTRA_HOOK_MODULES = (
    "cli.hooks.session_start_inject",
    "cli.hooks.pre_compact_instruct",
    "cli.hooks.user_prompt_reinject",
)


class InstallError(Exception):
    """Raised when install/verify cannot proceed safely."""


def _resolve_interpreter() -> str:
    path = sys.executable
    if not path:
        raise InstallError("sys.executable is empty — cannot resolve hook interpreter")
    if not Path(path).exists():
        raise InstallError(f"resolved interpreter not found on disk: {path}")
    if not os.access(path, os.X_OK):
        raise InstallError(f"resolved interpreter not executable: {path}")
    return path


def build_orchestra_hooks(interpreter: str) -> dict[str, list[dict[str, Any]]]:
    """Return the three orchestra hook entries keyed by event name."""
    return {
        "SessionStart": [
            {
                "matcher": SESSION_START_MATCHER,
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{interpreter} -m cli.hooks.session_start_inject",
                    }
                ],
            }
        ],
        "PreCompact": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{interpreter} -m cli.hooks.pre_compact_instruct",
                    }
                ]
            }
        ],
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{interpreter} -m cli.hooks.user_prompt_reinject",
                    }
                ]
            }
        ],
    }


def _atomic_write_json(target: Path, data: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".settings-", suffix=".json.tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, sort_keys=False)
            fp.write("\n")
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def install(root: Path) -> Path:
    """Install orchestra hooks into `<root>/.claude/settings.json`. Returns path."""
    interpreter = _resolve_interpreter()
    settings_path = root / SETTINGS_PATH
    existing: dict[str, Any] = {}
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except json.JSONDecodeError:
            existing = {}
    hooks = existing.get("hooks") if isinstance(existing.get("hooks"), dict) else {}
    if not isinstance(hooks, dict):
        hooks = {}
    orchestra = build_orchestra_hooks(interpreter)
    hooks.update(orchestra)
    existing["hooks"] = hooks
    _atomic_write_json(settings_path, existing)
    return settings_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cli.install_claude_hooks")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.uninstall:
            raise InstallError("--uninstall not yet implemented (Phase 4.2)")
        if args.verify:
            raise InstallError("--verify not yet implemented (Phase 4.3)")
        install(Path.cwd())
        return 0
    except InstallError as exc:
        sys.stderr.write(f"FAIL: cli.install_claude_hooks: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
