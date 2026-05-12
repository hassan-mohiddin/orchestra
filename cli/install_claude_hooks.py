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


def _is_orchestra_hook_entry(entry: dict[str, Any]) -> bool:
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        return False
    for hook in hooks:
        cmd = hook.get("command", "") if isinstance(hook, dict) else ""
        if any(module in cmd for module in ORCHESTRA_HOOK_MODULES):
            return True
    return False


def uninstall(root: Path) -> Path:
    """Remove orchestra-installed hook entries from settings.json.

    Preserves any non-orchestra hook entries authored by other plugins.
    No-op if settings.json is absent.
    """
    settings_path = root / SETTINGS_PATH
    if not settings_path.exists():
        return settings_path
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return settings_path
    if not isinstance(data, dict):
        return settings_path
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return settings_path
    for event in list(hooks.keys()):
        entries = hooks[event]
        if not isinstance(entries, list):
            continue
        kept = [e for e in entries if isinstance(e, dict) and not _is_orchestra_hook_entry(e)]
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if hooks:
        data["hooks"] = hooks
    else:
        data.pop("hooks", None)
    _atomic_write_json(settings_path, data)
    return settings_path


def verify(root: Path) -> list[str]:
    """Audit installed orchestra hooks. Returns list of error strings (empty = clean).

    Detects:
    - settings.json missing or malformed
    - resolved interpreter path stale (not on disk or not executable)
    - hook command tampered (form differs from `<exe> -m <module>` exactly)
    - orchestra hook modules missing from settings
    """
    errors: list[str] = []
    settings_path = root / SETTINGS_PATH
    if not settings_path.exists():
        errors.append(f"settings.json missing at {settings_path}")
        return errors
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"settings.json malformed JSON: {exc}")
        return errors
    if not isinstance(data, dict):
        errors.append("settings.json root is not an object")
        return errors
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        errors.append("settings.json has no `hooks` object")
        return errors

    found_modules: set[str] = set()
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            inner = entry.get("hooks")
            if not isinstance(inner, list):
                continue
            for hook in inner:
                if not isinstance(hook, dict):
                    continue
                cmd = hook.get("command", "")
                if not isinstance(cmd, str) or not cmd:
                    continue
                matched_module = next(
                    (m for m in ORCHESTRA_HOOK_MODULES if m in cmd), None
                )
                if matched_module is None:
                    continue
                found_modules.add(matched_module)
                parts = cmd.split()
                if (
                    len(parts) != 3
                    or parts[1] != "-m"
                    or parts[2] != matched_module
                ):
                    errors.append(
                        f"hook command for {matched_module} tampered "
                        f"(expected `<exe> -m {matched_module}` exactly): {cmd!r}"
                    )
                    continue
                interpreter = parts[0]
                if not Path(interpreter).exists():
                    errors.append(
                        f"stale interpreter for {matched_module}: {interpreter} not found"
                    )
                elif not os.access(interpreter, os.X_OK):
                    errors.append(
                        f"non-executable interpreter for {matched_module}: {interpreter}"
                    )

    missing = set(ORCHESTRA_HOOK_MODULES) - found_modules
    if missing:
        errors.append(
            f"orchestra hook modules missing from settings: {sorted(missing)}"
        )
    return errors


def install(root: Path, force: bool = False) -> Path:
    """Install orchestra hooks into `<root>/.claude/settings.json`. Returns path.

    Idempotent: if the resulting settings would be byte-identical to what's
    already on disk, the file is not rewritten (mtime preserved). Pass
    `force=True` to bypass the idempotency check and rewrite unconditionally
    (useful after venv rebuild — the new sys.executable path is the same
    string so idempotency would no-op even when the user expects a refresh).
    """
    interpreter = _resolve_interpreter()
    settings_path = root / SETTINGS_PATH
    existing: dict[str, Any] = {}
    on_disk_text: str | None = None
    if settings_path.exists():
        try:
            on_disk_text = settings_path.read_text(encoding="utf-8")
            existing = json.loads(on_disk_text)
            if not isinstance(existing, dict):
                existing = {}
        except json.JSONDecodeError:
            existing = {}
            on_disk_text = None
    hooks = existing.get("hooks") if isinstance(existing.get("hooks"), dict) else {}
    if not isinstance(hooks, dict):
        hooks = {}
    orchestra = build_orchestra_hooks(interpreter)
    for event, new_entries in orchestra.items():
        existing_entries = hooks.get(event, [])
        if not isinstance(existing_entries, list):
            existing_entries = []
        preserved = [
            e
            for e in existing_entries
            if isinstance(e, dict) and not _is_orchestra_hook_entry(e)
        ]
        hooks[event] = preserved + new_entries
    existing["hooks"] = hooks
    if not force and on_disk_text is not None:
        candidate = json.dumps(existing, indent=2, sort_keys=False) + "\n"
        if candidate == on_disk_text:
            return settings_path
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
            uninstall(Path.cwd())
            return 0
        if args.verify:
            errors = verify(Path.cwd())
            if errors:
                for e in errors:
                    sys.stderr.write(f"FAIL: {e}\n")
                return 1
            return 0
        install(Path.cwd(), force=args.force)
        return 0
    except InstallError as exc:
        sys.stderr.write(f"FAIL: cli.install_claude_hooks: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
