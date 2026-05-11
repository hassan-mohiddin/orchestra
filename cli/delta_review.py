"""Delta-review module (LLD-011 Phase 2 slices 2.17-2.27).

At iter-2 (and later iterations within the post-commit cap), spec-review runs
in delta mode: instead of re-reviewing the whole doc from scratch, sub-judges
receive a unified diff against iter-(N-1) plus the iter-(N-1) findings as
context. This addresses the "loop pathology" gap — sub-judges focus on what
changed rather than re-discovering already-known issues.

Provenance contract (LLD-011 §Design Provenance):
  - iter-(N-1) attestation must exist at docs/reviews/<doc-id>-r<N-1>.review.yaml
  - iter-(N-1) attestation must carry doc_subject.iter_blob_sha
  - retrieving that blob via `git cat-file -p` must succeed AND the retrieved
    bytes must re-hash to the stored SHA (tamper guard)

Any contract break → SpecReviewError → fail-closed write of a failure attestation.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


class SpecReviewError(Exception):
    """Fail-closed error in delta-review provenance / integrity / diff path.

    The message is a stable error code (e.g. `iter1_attestation_missing`) so
    callers can match it for failure-attestation reasons. Human detail is
    appended after the code, separated by `: `.
    """


def compute_prior_attestation_path(doc_path: Path, current_iteration: int) -> Path:
    """Return repo-relative path to the iter-(current-1) attestation.

    Mirrors `cli.spec_review.compute_attestation_path` but always selects
    `current_iteration - 1`. Strips any `-rN` revision suffix on the doc
    filename (supersession variants share an attestation namespace).

    Raises ValueError if current_iteration < 2 (no prior to load).
    """
    if current_iteration < 2:
        raise ValueError(
            f"compute_prior_attestation_path: current_iteration must be >= 2 "
            f"(got {current_iteration})"
        )
    stem = doc_path.stem
    base = re.sub(r"-r\d+$", "", stem)
    return Path("docs/reviews") / f"{base}-r{current_iteration - 1}.review.yaml"


def load_prior_attestation(
    doc_path: Path,
    current_iteration: int,
    repo_root: Path,
) -> dict:
    """Load + validate the iter-(current-1) attestation.

    Fail-closed contract:
      - File missing → SpecReviewError("iter1_attestation_missing: <path>")
      - YAML malformed → SpecReviewError("iter1_attestation_unparseable: ...")
      - doc_subject.iter_blob_sha missing → SpecReviewError("iter1_provenance_missing: ...")

    Returns the parsed attestation dict on success.
    """
    rel = compute_prior_attestation_path(doc_path, current_iteration)
    path = repo_root / rel

    if not path.exists():
        raise SpecReviewError(f"iter1_attestation_missing: {rel}")

    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise SpecReviewError(
            f"iter1_attestation_unparseable: {rel}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SpecReviewError(
            f"iter1_attestation_unparseable: {rel}: not a YAML mapping"
        )

    doc_subject = data.get("doc_subject") or {}
    if not doc_subject.get("iter_blob_sha"):
        raise SpecReviewError(
            f"iter1_provenance_missing: {rel} has no doc_subject.iter_blob_sha"
        )

    return data
