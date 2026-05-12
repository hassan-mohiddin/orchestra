"""CLI wrapper for /orchestra:teach slash command (LLD-012 SC-6).

Captures a free-text teach lesson. The shim at `commands/teach.md` invokes
this module via `python -m cli.lessons_teach -- "<free text>"`. The lesson
is written as kind=teach, source=user, inject=false — NEVER injected into
system-priority context (LLD-012 SC-11 allowlist).
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone

from cli.lessons_store import LessonsStoreError, append_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli.lessons_teach",
        description="Capture a free-text teach lesson (LLD-012 SC-6).",
    )
    parser.add_argument("text", nargs="+", help="free-text lesson body")
    args = parser.parse_args(argv)
    body = " ".join(args.text).strip()
    if not body:
        sys.stderr.write("FAIL: teach body is empty\n")
        return 2
    entry = {
        "id": str(uuid.uuid4()),
        "ts": _now_iso(),
        "kind": "teach",
        "rule_violated": None,
        "body": body,
        "source": "user",
        "inject": False,
    }
    try:
        path = append_entry(entry)
    except LessonsStoreError as exc:
        sys.stderr.write(f"FAIL: cli.lessons_teach: {exc}\n")
        return 2
    print(f"teach lesson appended: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
