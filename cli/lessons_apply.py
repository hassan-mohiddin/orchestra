"""Apply a proxy mutation after spec-review attestation passes (LLD-012 SC-9).

Slice 6.3: iteration-aware attestation lookup + verdict guard.
Slice 6.4: mutate schema-layer target + append `source: auto-promote` marker
entry to current month's lessons file.

User-invoked CLI (NOT auto-triggered — Class-B reconciliation per SC-8):

    python -m cli.lessons_apply docs/proposed-rule-mutations/<rule>-<date>.md

Refuses to mutate unless a matching attestation exists at
`docs/reviews/<proxy-stem>-rN.orchestra.review.yaml` (or legacy
`.review.yaml`) with `overall_verdict ∈ {pass, conditional_pass}`.
N is read from the proxy doc's `> **Iteration:** N` line (default 1).
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from cli.lessons_store import append_entry
from cli.tldr_extractor import TLDR_CLOSE_MARKER, TLDR_HEADER_RE

ITERATION_RE = re.compile(r"^>\s*\*\*Iteration:\*\*\s*(\d+)", re.MULTILINE)
TARGET_RE = re.compile(r"^>\s*\*\*Target:\*\*\s*(\S+)", re.MULTILINE)
DOC_ID_RE = re.compile(r"^>\s*\*\*Doc ID:\*\*\s*(\S+)", re.MULTILINE)
PROPOSED_TLDR_RE = re.compile(
    r"## Proposed TLDR\s*\n\s*```diff\s*\n(.*?)\n```",
    re.DOTALL,
)
ADDED_BULLET_RE = re.compile(r"^\+- (.+?)\s*$", re.MULTILINE)
EVIDENCE_ID_RE = re.compile(r"^\|\s*([0-9a-f][0-9a-f-]*)\s*\|", re.MULTILINE)
ACCEPTED_VERDICTS = ("pass", "conditional_pass")
ATTESTATION_VARIANTS = (".orchestra.review.yaml", ".review.yaml")
REVIEWS_DIR = Path("docs/reviews")


class ApplyError(Exception):
    """Raised when a mutation cannot be applied (missing attestation, bad verdict, etc.)."""


def _read_proxy_iteration(text: str) -> int:
    match = ITERATION_RE.search(text)
    return int(match.group(1)) if match else 1


def _read_proxy_target(text: str) -> str | None:
    match = TARGET_RE.search(text)
    return match.group(1) if match else None


def _read_proposed_bullet(text: str) -> str | None:
    block = PROPOSED_TLDR_RE.search(text)
    if not block:
        return None
    matches = ADDED_BULLET_RE.findall(block.group(1))
    return matches[0] if matches else None


def _read_source_lesson_ids(text: str) -> list[str]:
    return [
        m
        for m in EVIDENCE_ID_RE.findall(text)
        if m != "id" and not m.startswith("-")
    ]


def _read_rule_id(text: str, fallback_stem: str) -> str:
    match = DOC_ID_RE.search(text)
    if match:
        raw = match.group(1)
        return re.sub(r"-\d{4}-\d{2}-\d{2}$", "", raw)
    return re.sub(r"-\d{4}-\d{2}-\d{2}$", "", fallback_stem)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mutate_target_tldr(target_path: Path, new_bullet: str) -> None:
    """Append `new_bullet` to the target file's TLDR section.

    Inserts before the close marker `<!-- Full rule body below this section -->`.
    Atomic write via write-to-temp + os.replace.
    """
    import os
    import tempfile

    text = target_path.read_text(encoding="utf-8")
    header_match = TLDR_HEADER_RE.search(text)
    if header_match is None:
        raise ApplyError(f"target has no `## TLDR — Nonnegotiables` section: {target_path}")
    close_idx = text.find(TLDR_CLOSE_MARKER, header_match.end())
    if close_idx == -1:
        raise ApplyError(
            f"target TLDR section has no close marker `{TLDR_CLOSE_MARKER}`: {target_path}"
        )
    insert_at = text.rfind("\n", 0, close_idx)
    if insert_at == -1:
        insert_at = close_idx
    while insert_at > 0 and text[insert_at - 1] == "\n":
        insert_at -= 1
    new_text = text[:insert_at] + f"\n- {new_bullet}" + text[insert_at:]
    fd, tmp = tempfile.mkstemp(
        prefix=".tldr-", suffix=".md.tmp", dir=str(target_path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(new_text)
        os.replace(tmp, target_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _append_promotion_marker(
    rule_id: str,
    proxy_path: Path,
    source_lesson_ids: list[str],
    root: Path,
) -> Path:
    entry = {
        "id": str(uuid.uuid4()),
        "ts": _now_iso(),
        "kind": "promotion-marker",
        "rule_violated": rule_id,
        "proxy_artifact": proxy_path.relative_to(root).as_posix(),
        "source_lesson_ids": source_lesson_ids,
        "source": "auto-promote",
        "inject": False,
    }
    return append_entry(entry)


def apply_proxy(proxy_path: Path, root: Path | None = None) -> dict[str, object]:
    """Verify attestation + mutate target + write auto-promote marker."""
    if root is None:
        root = Path.cwd()
    attestation = assert_passed_attestation(proxy_path, root)
    text = proxy_path.read_text(encoding="utf-8")
    target_rel = _read_proxy_target(text)
    if not target_rel:
        raise ApplyError(f"proxy has no `> **Target:**` line: {proxy_path}")
    target_path = root / target_rel
    if not target_path.exists():
        raise ApplyError(f"target file does not exist: {target_path}")
    new_bullet = _read_proposed_bullet(text)
    if not new_bullet:
        raise ApplyError(
            f"proxy `## Proposed TLDR` block has no `+- <bullet>` line: {proxy_path}"
        )
    rule_id = _read_rule_id(text, proxy_path.stem)
    source_ids = _read_source_lesson_ids(text)
    _mutate_target_tldr(target_path, new_bullet)
    marker_path = _append_promotion_marker(rule_id, proxy_path, source_ids, root)
    return {
        "attestation": attestation,
        "target": target_path,
        "added_bullet": new_bullet,
        "marker_lesson_file": marker_path,
        "source_lesson_ids": source_ids,
    }


def _find_attestation(proxy_path: Path, iteration: int, root: Path) -> Path | None:
    stem = proxy_path.stem
    reviews_dir = root / REVIEWS_DIR
    for variant in ATTESTATION_VARIANTS:
        candidate = reviews_dir / f"{stem}-r{iteration}{variant}"
        if candidate.exists():
            return candidate
    return None


def _load_verdict(path: Path) -> str | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data.get("overall_verdict") or data.get("verdict")


def assert_passed_attestation(proxy_path: Path, root: Path | None = None) -> Path:
    """Return the attestation path if verdict ∈ ACCEPTED_VERDICTS.

    Raises ApplyError on: missing proxy, missing attestation, malformed
    attestation YAML, or non-accepted verdict.
    """
    if root is None:
        root = Path.cwd()
    if not proxy_path.exists():
        raise ApplyError(f"proxy artifact not found: {proxy_path}")
    text = proxy_path.read_text(encoding="utf-8")
    iteration = _read_proxy_iteration(text)
    attestation = _find_attestation(proxy_path, iteration, root)
    if attestation is None:
        raise ApplyError(
            f"no attestation found for {proxy_path.name} iter-{iteration} "
            f"at {REVIEWS_DIR.as_posix()}/"
        )
    verdict = _load_verdict(attestation)
    if verdict not in ACCEPTED_VERDICTS:
        raise ApplyError(
            f"attestation verdict {verdict!r} not in {list(ACCEPTED_VERDICTS)}: {attestation}"
        )
    return attestation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli.lessons_apply",
        description="Apply a proxy mutation after spec-review attestation passes.",
    )
    parser.add_argument("proxy_path", type=Path, help="docs/proposed-rule-mutations/<rule>-<date>.md")
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        result = apply_proxy(args.proxy_path, root)
    except ApplyError as exc:
        sys.stderr.write(f"FAIL: cli.lessons_apply: {exc}\n")
        return 2
    print(f"attestation: {result['attestation']}")
    print(f"target mutated: {result['target']}")
    print(f"added bullet: {result['added_bullet']}")
    print(f"auto-promote marker appended to: {result['marker_lesson_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
