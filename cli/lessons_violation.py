"""CLI wrapper for /orchestra:violation slash command (LLD-012 SC-6, SC-11).

Captures a structured violation lesson. Validates --rule against an
allowlist sourced from `.claude/rules/*.md` basenames (regular files
only — symlinks rejected per LLD-012 Out-of-Scope adversarial Crit #5
mitigation) plus `CLAUDE` and `workflow`. Path-traversal in --rule is
blocked at argument parse time.

Lesson is written as kind=violation, source=user, inject=true.
lessons_store.append_entry HTML-encodes + 200-char-caps observed/expected.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cli.lessons_store import LessonsStoreError, append_entry

ALWAYS_ALLOWED_RULE_IDS = ("CLAUDE", "workflow")
RULES_DIR = Path(".claude/rules")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _allowed_rule_ids(root: Path) -> set[str]:
    """Allowlist = basenames of .claude/rules/*.md (regular files only) + CLAUDE + workflow.

    Symlinks are skipped per Out-of-Scope adversarial Crit #5 mitigation:
    a PR cannot smuggle a symlinked file to widen the allowlist.
    """
    allowed: set[str] = set(ALWAYS_ALLOWED_RULE_IDS)
    rules_dir = root / RULES_DIR
    if rules_dir.is_dir():
        for path in sorted(rules_dir.glob("*.md")):
            if path.is_symlink() or not path.is_file():
                continue
            allowed.add(path.stem)
    return allowed


def _is_path_traversal(rule: str) -> bool:
    return "/" in rule or "\\" in rule or ".." in rule or rule.startswith(".")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli.lessons_violation",
        description="Capture a structured violation lesson (LLD-012 SC-6/SC-11).",
    )
    parser.add_argument("--rule", required=True, help="rule id (basename without .md)")
    parser.add_argument("--observed", required=True, help="what the agent did")
    parser.add_argument("--expected", required=True, help="what the agent should do")
    args = parser.parse_args(argv)

    if _is_path_traversal(args.rule):
        sys.stderr.write(
            f"FAIL: rule id contains path components or starts with dot: {args.rule!r}\n"
        )
        return 2

    root = Path.cwd()
    allowed = _allowed_rule_ids(root)
    if args.rule not in allowed:
        sys.stderr.write(
            f"FAIL: unknown rule: {args.rule!r}. Known: {sorted(allowed)}\n"
        )
        return 2

    entry = {
        "id": str(uuid.uuid4()),
        "ts": _now_iso(),
        "kind": "violation",
        "rule_violated": args.rule,
        "observed": args.observed,
        "expected": args.expected,
        "source": "user",
        "inject": True,
    }
    try:
        path = append_entry(entry)
    except LessonsStoreError as exc:
        sys.stderr.write(f"FAIL: cli.lessons_violation: {exc}\n")
        return 2
    print(f"violation lesson appended: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
