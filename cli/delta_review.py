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

import difflib
import hashlib
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


def verify_integrity(attestation: dict) -> None:
    """Re-compute the attestation_integrity_hash and compare with stored value.

    Raises SpecReviewError("integrity_hash_mismatch: ...") on mismatch. Pass-
    through return on match. Wrapper around `cli.spec_review._verify_attestation_integrity_hash`
    to keep delta-review failure modes centralized.
    """
    # Local import avoids circular at module load (spec_review imports pdsa
    # which has no delta_review dep, but delta_review depends on spec_review's
    # provenance helpers — defer to call time).
    from cli import spec_review

    if not spec_review._verify_attestation_integrity_hash(attestation):
        raise SpecReviewError(
            "integrity_hash_mismatch: stored attestation_integrity_hash does not "
            "match recomputed hash. Iter-1 attestation has been tampered with or "
            "corrupted; aborting delta-review."
        )


def retrieve_iter1_bytes(blob_sha: str, repo_root: Path) -> bytes:
    """Retrieve iter-1 doc bytes via `git cat-file -p <blob_sha>` and cross-check.

    Per LLD-011 slices 2.22-2.24:
      - subprocess error (blob unknown / pruned) → SpecReviewError(iter1_blob_pruned)
      - retrieved bytes re-hashed via git hash-object → must equal stored SHA;
        mismatch → SpecReviewError(blob_sha_mismatch)
    """
    from cli import spec_review

    try:
        bytes_ = spec_review._retrieve_doc_bytes_by_blob_sha(blob_sha, repo_root)
    except subprocess.CalledProcessError as exc:
        raise SpecReviewError(
            f"iter1_blob_pruned: git cat-file failed for {blob_sha}: {exc}"
        ) from exc

    # Cross-check: SHA-1 of git-blob = "blob <len>\0<bytes>"
    header = f"blob {len(bytes_)}\0".encode()
    recomputed = hashlib.sha1(header + bytes_).hexdigest()
    if recomputed != blob_sha:
        raise SpecReviewError(
            f"blob_sha_mismatch: retrieved bytes hash to {recomputed!r} but "
            f"attestation stored {blob_sha!r}. Object DB integrity violation."
        )
    return bytes_


def compute_unified_diff(iter1_text: str, iter2_text: str) -> str:
    """Unified-diff between two doc revisions. Empty string when texts are identical."""
    if iter1_text == iter2_text:
        return ""
    return "".join(
        difflib.unified_diff(
            iter1_text.splitlines(keepends=True),
            iter2_text.splitlines(keepends=True),
            fromfile="iter-1",
            tofile="iter-2",
        )
    )


def is_noop_iteration(diff_text: str) -> bool:
    """True when the unified diff is empty (no changes between iter-1 and iter-2).

    Empty-diff iterations are NOT a free advance. Per iter-2 adversarial review
    finding (E10 documented bypass): an author bumping `Iteration:` without
    editing the doc would otherwise re-use iter-1 findings as iter-2's
    attestation and Status-flip on the same content. Callers MUST refuse to
    write an iter-2 attestation when this returns True — the doc has to be
    edited (or the author retracts the iteration bump) before iter-2 makes
    sense.

    Returns True iff `diff_text` is the empty string. The caller decides
    whether to fail-closed (recommended for post-commit iterations) or to
    write a no-op marker attestation (only acceptable for pre-commit Draft
    cycles, which are not subject to the 2-iter cap anyway).
    """
    return diff_text == ""


def assert_diff_non_empty(diff_text: str) -> None:
    """Fail-closed when iter-2 delta-review has nothing to review.

    Raises SpecReviewError("noop_iteration_refused: ...") when `diff_text` is
    empty. Closes the E10 bypass: author bumping `Iteration:` to advance the
    post-commit cap without editing the doc must instead edit the doc or
    retract the bump.
    """
    if is_noop_iteration(diff_text):
        raise SpecReviewError(
            "noop_iteration_refused: iter-N+1 dispatch refused because the "
            "doc bytes have not changed since iter-N. Bumping `Iteration:` "
            "without editing the doc would silently re-use iter-N findings "
            "as iter-N+1's attestation — that bypasses the spec-review "
            "discipline the iteration counter is supposed to enforce. "
            "Recovery: edit the doc OR retract the `Iteration:` bump."
        )


def build_delta_prompt(
    *,
    judge_id: str,
    diff_text: str,
    prior_findings: list[dict],
    prior_iteration: int,
) -> str:
    """Build a delta-mode prompt for sub-judge `judge_id`.

    Per LLD-011 §Design Delta-review: sub-judges receive
      1. the unified diff iter-(N-1) → iter-N
      2. iter-(N-1) findings as context (so duplicate findings can be dropped)
    Returns the prompt as a single string ready to dispatch.
    """
    if prior_findings:
        findings_block = "\n".join(
            f"- [{f.get('severity', '?')}] {f.get('location', '?')}: {f.get('problem', '?')}"
            f" (scope: {f.get('scope', '?')})"
            for f in prior_findings
        )
    else:
        findings_block = "(no prior findings)"

    return (
        f"# Delta Review — sub-judge `{judge_id}`\n\n"
        f"You are reviewing iter-{prior_iteration + 1} of a doc that was previously\n"
        f"reviewed at iter-{prior_iteration}. Focus your review on the DELTA, not on\n"
        f"re-discovering already-known issues.\n\n"
        f"## Unified diff (iter-{prior_iteration} → iter-{prior_iteration + 1})\n\n"
        f"```diff\n{diff_text}```\n\n"
        f"## Prior-iteration findings (iter-{prior_iteration})\n\n"
        f"{findings_block}\n\n"
        f"## Instructions\n"
        f"- Identify NEW findings introduced by the diff.\n"
        f"- Identify prior findings that are NOT addressed by the diff (carry-forward).\n"
        f"- Do NOT re-raise prior findings that the diff clearly resolves.\n"
        f"- Use your rubric (rubric-v1) to assess severity.\n"
    )
