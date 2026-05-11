"""Rubric-freeze helpers for spec-review v2 (LLD-011 Phase 3 slices 3.2-3.6).

Each sub-judge rubric is stored as `rubric-v<N>.md` under
`skills/spec-review/judges/<judge-id>/`. At iter-1 the dispatcher picks the
latest available version and records it in the attestation. At iter-2+ the
dispatcher MUST reuse the iter-1 frozen version — even if a newer rubric
exists on disk. Missing iter-1 version → fail-closed: verdicts could otherwise
silently diverge from iter-1 baseline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class RubricFreezeError(Exception):
    """Fail-closed error in the rubric-freeze pipeline.

    Error code is the first word of the message (e.g. `rubric_version_not_found`).
    """


@dataclass
class RubricInfo:
    """Resolved rubric for a single sub-judge at dispatch time."""

    version: int
    path: Path
    body: str


_RUBRIC_RE = re.compile(r"^rubric-v(\d+)\.md$")


def find_latest_rubric_version(judge_id: str, judges_root: Path) -> int:
    """Return the highest N for `<judges_root>/<judge_id>/rubric-v<N>.md`.

    Raises ValueError if no rubric files exist for the judge.
    """
    judge_dir = judges_root / judge_id
    if not judge_dir.exists():
        raise ValueError(f"no rubric directory for sub-judge {judge_id} under {judges_root}")

    versions: list[int] = []
    for child in judge_dir.iterdir():
        m = _RUBRIC_RE.match(child.name)
        if m:
            versions.append(int(m.group(1)))
    if not versions:
        raise ValueError(f"no rubric files for sub-judge {judge_id} in {judge_dir}")
    return max(versions)


def resolve_rubric_for_dispatch(
    judge_id: str,
    iteration: int,
    judges_root: Path,
    prior_rubric_version: int | None,
) -> RubricInfo:
    """Pick the rubric version to dispatch with.

    Iter-1 (`prior_rubric_version is None`): use the latest available version.
    Iter-2+ (`prior_rubric_version is not None`): reuse that exact version.
    Missing target version → RubricFreezeError("rubric_version_not_found: ...").
    """
    if iteration == 1 or prior_rubric_version is None:
        version = find_latest_rubric_version(judge_id, judges_root)
    else:
        version = prior_rubric_version

    path = judges_root / judge_id / f"rubric-v{version}.md"
    if not path.exists():
        raise RubricFreezeError(
            f"rubric_version_not_found: iter-{iteration} sub-judge {judge_id!r} "
            f"requires rubric-v{version}.md but {path} does not exist. "
            f"Iter-1 attested rubric_version cannot be reproduced; aborting to "
            f"keep verdicts comparable across iterations."
        )

    return RubricInfo(version=version, path=path, body=path.read_text())
