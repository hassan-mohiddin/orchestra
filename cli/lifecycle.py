"""design-docs lifecycle — supersession + rejection helpers (LLD-006-r4 v1.5).

Subcommands:
    python -m cli.lifecycle reject --file <path> --reason <one-line>
    python -m cli.lifecycle update-attestation-paths --reviews <path> [--reviews ...]

Behavior:
    reject:
        Sets Status: Rejected + Reason: <one-line> in metadata block.
        Iteration field unchanged. Idempotent.

    update-attestation-paths:
        For each review.yaml: locate the actual subject doc via canon-or-archive
        resolution and rewrite doc_subject.path to current location. Idempotent.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

from cli.lint import resolve_supersession_link

STATUS_LINE_RE = re.compile(r"^(>\s+\*\*Status:\*\*\s+).+$", re.MULTILINE)
REASON_LINE_RE = re.compile(r"^>\s+\*\*Reason:\*\*\s+.+$", re.MULTILINE)
METADATA_BLOCK_END_RE = re.compile(r"^>\s+\*\*[^:*]+:\*\*\s+.+$", re.MULTILINE)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def reject_doc(file_path: Path, reason: str) -> None:
    """Set Status: Rejected + Reason: <one-line>. Idempotent.

    Operates on the metadata-block format used by orchestra docs:
        > **Status:** <value>
        > **Reason:** <value>   ← inserted on rejection if not present
    """
    text = _read_text(file_path)

    new_text, n = STATUS_LINE_RE.subn(r"\1Rejected", text, count=1)
    if n == 0:
        raise ValueError(f"{file_path}: no `> **Status:** ...` line found in metadata block")

    if REASON_LINE_RE.search(new_text):
        new_text = REASON_LINE_RE.sub(f"> **Reason:** {reason}", new_text, count=1)
    else:
        # Insert Reason: line directly after the Status: line
        new_text = re.sub(
            r"^(>\s+\*\*Status:\*\*\s+Rejected)$",
            rf"\1\n> **Reason:** {reason}",
            new_text,
            count=1,
            flags=re.MULTILINE,
        )

    if new_text != text:
        _write_text(file_path, new_text)


def update_attestation_paths(repo_root: Path, review_paths: list[Path]) -> list[str]:
    """For each review.yaml: read doc_subject.path, resolve via canon-or-archive,
    rewrite path to current location. Returns list of human-readable change descriptions.
    """
    changes: list[str] = []
    for rp in review_paths:
        if not rp.exists():
            changes.append(f"{rp}: SKIP (file not found)")
            continue
        raw = rp.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            changes.append(f"{rp}: SKIP (not a YAML mapping)")
            continue
        doc_subject = data.get("doc_subject") or {}
        old_path = doc_subject.get("path", "")
        if not old_path:
            changes.append(f"{rp}: SKIP (no doc_subject.path)")
            continue
        # Resolve current location (canon first, then archive)
        resolved = resolve_supersession_link(repo_root, old_path)
        if resolved is None:
            # Try the inverse: if old path was under archive, check canon
            parts = Path(old_path).parts
            if (parts and parts[0] == "docs" and len(parts) >= 3 and parts[1] == "archive"):
                canon_candidate = repo_root / "docs" / "/".join(parts[2:])
                if canon_candidate.exists():
                    resolved = canon_candidate
        if resolved is None:
            changes.append(f"{rp}: ERROR (cannot resolve {old_path!r})")
            continue
        new_path = str(resolved.relative_to(repo_root))
        if new_path == old_path:
            changes.append(f"{rp}: unchanged ({old_path})")
            continue
        # Rewrite the path field in-place via simple regex on raw text — preserves
        # YAML formatting + comments better than dump-after-load.
        pattern = re.compile(
            rf"(^\s*path:\s*)(['\"]?){re.escape(old_path)}(['\"]?)\s*$",
            re.MULTILINE,
        )
        new_raw, n = pattern.subn(rf"\g<1>\g<2>{new_path}\g<3>", raw, count=1)
        if n == 0:
            # Fallback: dump full YAML
            data["doc_subject"]["path"] = new_path
            new_raw = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
        rp.write_text(new_raw, encoding="utf-8")
        changes.append(f"{rp}: {old_path} → {new_path}")
    return changes


def repo_root_from_cwd() -> Path:
    return Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True,
    ).strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="design-docs lifecycle")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_reject = sub.add_parser("reject", help="Mark a Draft/Proposed doc as Rejected")
    p_reject.add_argument("--file", required=True, help="Doc file path")
    p_reject.add_argument("--reason", required=True, help="One-line rejection reason")

    p_update = sub.add_parser("update-attestation-paths",
                              help="Rewrite doc_subject.path in review YAMLs to current location")
    p_update.add_argument("--reviews", action="append", required=True,
                          help="Review YAML path (repeat for multiple)")

    args = parser.parse_args(argv)

    try:
        root = repo_root_from_cwd()
    except subprocess.CalledProcessError:
        print("error: not inside a git repository", file=sys.stderr)
        return 2

    if args.cmd == "reject":
        try:
            reject_doc(Path(args.file), args.reason)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"OK: {args.file} → Status: Rejected + Reason: {args.reason!r}")
        return 0

    if args.cmd == "update-attestation-paths":
        review_paths = [Path(p) for p in args.reviews]
        changes = update_attestation_paths(root, review_paths)
        for line in changes:
            print(line)
        if any("ERROR" in c for c in changes):
            return 1
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
