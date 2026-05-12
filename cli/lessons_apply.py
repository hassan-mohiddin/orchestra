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
from pathlib import Path

import yaml

ITERATION_RE = re.compile(r"^>\s*\*\*Iteration:\*\*\s*(\d+)", re.MULTILINE)
TARGET_RE = re.compile(r"^>\s*\*\*Target:\*\*\s*(\S+)", re.MULTILINE)
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
        attestation = assert_passed_attestation(args.proxy_path, root)
    except ApplyError as exc:
        sys.stderr.write(f"FAIL: cli.lessons_apply: {exc}\n")
        return 2
    print(f"attestation verified: {attestation}")
    print("mutation step lands in Slice 6.4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
