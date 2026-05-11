"""orchestra spec-review skill sidecar — schema validation + attestation write.

Reads YAML attestation from stdin (subagent output piped in by the skill body).
Validates against `skills/spec-review/attestation-schema-v1.0.json`.
Performs path canonicalization, hash binding, verdict authoritative-compute,
stale-state check, and atomic-write to `docs/reviews/<doc-id>-rN.review.yaml`.

Exit codes:
  0 — pass / conditional_pass attestation written
  1 — fail attestation written OR validation/identity/verdict mismatch
  2 — path traversal blocked

LLD reference: docs/features/007-spec-review-architecture.md
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

SCHEMA_PATH = (
    Path(__file__).parent.parent
    / "skills"
    / "spec-review"
    / "attestation-schema-v1.0.json"
)
PROMPT_TEMPLATE_PATH = (
    Path(__file__).parent.parent / "skills" / "spec-review" / "prompt-template.md"
)
MAX_RETRIES = 0  # v1.6.1: stdin-bound dispatch has no useful retry — second
                 # sys.stdin.read() returns empty. User re-invokes the slash
                 # command for fresh subagent dispatch.
SUBAGENT_OUTPUT_TOKEN_CAP = 4000

VERDICT_RANK = {"pass": 0, "conditional_pass": 1, "fail": 2}

# LLD-011 §Schema v2.0 Mandatory map: sub-judges whose failure forces
# overall_verdict=fail with reason=mandatory_subjudge_failed. Both run on Opus
# because they cover (a) the v1 4-gate baseline (semantic) and (b) the v2 depth
# axis (adversarial red-team). Losing either degrades the verdict beyond
# "we can assert pass." Not subagent-controlled — recorded authoritatively.
MANDATORY_SUBJUDGES: frozenset[str] = frozenset({"semantic", "adversarial"})


class _NoTimestampLoader(yaml.SafeLoader):
    """SafeLoader without implicit timestamp resolution.

    Keeps `invoked_at: 2026-05-10T00:00:00Z` as string for schema validation
    (json-schema `format: date-time` checks string format, not datetime objects).
    """


_NoTimestampLoader.yaml_implicit_resolvers = {
    k: [(tag, regexp) for tag, regexp in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _resolve_repo_root() -> Path:
    """Seam — overridable in tests. Returns the git repo root for cwd."""
    out = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
    return Path(out)


def parse_iteration_from_text(text: str) -> int:
    """Read `> **Iteration:** N` from doc metadata block. Default: 1."""
    m = re.search(r"^>\s+\*\*Iteration:\*\*\s+(\d+)\s*$", text, re.MULTILINE)
    if not m:
        return 1
    return int(m.group(1))


def compute_overall_verdict_v2(sub_judges: list[dict]) -> dict:
    """Compute overall_verdict + basis per LLD-011 tiered policy (slices 1.27-1.29).

    Algorithm:
        1. Bucket sub-judges by status. Failed sub-judges in MANDATORY_SUBJUDGES
           go to `mandatory_failures`; failed optional sub-judges go to
           `excluded_sub_judges`. Completed sub-judges go to a `completed` list.
        2. If `mandatory_failures` non-empty: overall_verdict=fail with reason=
           mandatory_subjudge_failed. Excluded list preserved for audit.
        3. Else if no sub-judges completed: overall_verdict=fail with reason=
           all_subjudges_failed. (Failure-attestation invariant — even when
           the pipeline produces no aggregated findings, the verdict is still
           computed and the attestation still persisted.)
        4. Otherwise: overall_verdict = worst verdict across completed
           sub-judges (max via VERDICT_RANK). No reason.

    Returns:
        dict with keys `overall_verdict` and `overall_verdict_basis`.
    """
    mandatory_failures: list[str] = []
    excluded: list[str] = []
    completed: list[dict] = []

    for sj in sub_judges:
        sjid = sj["id"]
        status = sj.get("status", "completed")
        if status == "completed":
            completed.append(sj)
        elif sjid in MANDATORY_SUBJUDGES:
            mandatory_failures.append(sjid)
        else:
            excluded.append(sjid)

    if mandatory_failures:
        return {
            "overall_verdict": "fail",
            "overall_verdict_basis": {
                "worst_sub_judge_verdict": "fail",
                "excluded_sub_judges": sorted(excluded),
                "mandatory_failures": sorted(mandatory_failures),
                "reason": "mandatory_subjudge_failed",
            },
        }

    if not completed:
        return {
            "overall_verdict": "fail",
            "overall_verdict_basis": {
                "worst_sub_judge_verdict": "fail",
                "excluded_sub_judges": sorted(excluded),
                "mandatory_failures": [],
                "reason": "all_subjudges_failed",
            },
        }

    worst = max(
        (sj["verdict"] for sj in completed),
        key=lambda v: VERDICT_RANK.get(v, -1),
    )
    return {
        "overall_verdict": worst,
        "overall_verdict_basis": {
            "worst_sub_judge_verdict": worst,
            "excluded_sub_judges": sorted(excluded),
            "mandatory_failures": [],
            "reason": None,
        },
    }


def _compute_attestation_integrity_hash(payload: dict) -> str:
    """SHA-256 over canonical YAML payload with the hash field zeroed (LLD-011 slice 1.23).

    Algorithm:
        1. Deep-copy payload.
        2. Remove `attestation_integrity_hash` field (so its own value cannot
           affect the hash — this is the standard self-referential-hash pattern).
        3. Serialize to canonical YAML: sort_keys=True, no flow style.
        4. SHA-256 hex digest of UTF-8 bytes. Prefix with "sha256:".

    Detects post-write tampering with any field other than the hash itself.
    Does NOT prevent authenticated spoof (rewrite-everything including hash) —
    that's the documented limitation in LLD-011 §Security S8.
    """
    import copy

    canonical_payload = copy.deepcopy(payload)
    canonical_payload.pop("attestation_integrity_hash", None)
    canonical_yaml = yaml.safe_dump(
        canonical_payload, sort_keys=True, default_flow_style=False
    )
    digest = hashlib.sha256(canonical_yaml.encode("utf-8")).hexdigest()
    return "sha256:" + digest


def _verify_attestation_integrity_hash(payload: dict) -> bool:
    """Re-compute hash and compare to stored value (LLD-011 slices 1.24-1.25).

    Returns:
        True if the stored hash matches the recomputed canonical-payload hash.
        False if the field is missing, malformed, or tampered.
    """
    stored = payload.get("attestation_integrity_hash")
    if not isinstance(stored, str):
        return False
    computed = _compute_attestation_integrity_hash(payload)
    return computed == stored


def _get_iter_commit_sha(repo_root: Path) -> str:
    """Get current git HEAD SHA (LLD-011 slice 1.19).

    Recorded in v2.0 attestation `doc_subject.iter_commit_sha` for audit. Not
    used for byte retrieval (the blob SHA handles that). Returns the literal
    string '<uncommitted>' if the repo has no HEAD yet (fresh `git init`).
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return "<uncommitted>"


def _persist_doc_blob(doc_path: Path, repo_root: Path) -> str:
    """Persist doc bytes as a git blob via `git hash-object -w` (LLD-011 slice 1.20).

    The `-w` flag writes the loose blob object to `.git/objects/` so it can be
    retrieved later via `git cat-file -p <sha>` even if the doc itself was never
    committed. This is the foundation of v2 delta-review provenance — iter-2 can
    deterministically reconstruct iter-1 bytes without git-log walking.

    Returns the 40-hex blob SHA.
    """
    out = subprocess.check_output(
        ["git", "hash-object", "-w", str(doc_path)],
        cwd=repo_root,
    )
    return out.decode("utf-8").strip()


def _retrieve_doc_bytes_by_blob_sha(blob_sha: str, repo_root: Path) -> bytes:
    """Retrieve doc bytes by stored blob SHA (LLD-011 slice 1.21).

    Used at iter-2 to reconstruct iter-1 doc bytes for delta-review diffing.
    Raises subprocess.CalledProcessError if the blob is unretrievable (pruned by
    git gc, or never written). Caller (delta_review module) maps that to a
    fail-closed SpecReviewError per LLD-011 §Edge case E5.
    """
    return subprocess.check_output(
        ["git", "cat-file", "-p", blob_sha],
        cwd=repo_root,
        stderr=subprocess.DEVNULL,
    )


def _detect_schema_version(path: Path) -> str | None:
    """Detect schema_version of an existing attestation YAML (LLD-011 slice 1.6).

    Returns:
        "1.0" or "2.0" if file exists and parses cleanly with a string schema_version
        None if file is missing, unreadable, malformed, or missing schema_version
    """
    if not path.exists():
        return None
    try:
        data = yaml.load(path.read_text(), Loader=_NoTimestampLoader)
    except (yaml.YAMLError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("schema_version")
    return version if isinstance(version, str) else None


def dispatch_subagent(prompt: str) -> str:
    """Read subagent YAML from stdin (production) or monkeypatched (tests).

    Skill body (SKILL.md) is responsible for the actual Task-tool dispatch
    at the agent layer; this Python module only validates + writes.
    """
    return sys.stdin.read()


def canonicalize_doc_path(input_path: str, repo_root: Path) -> Path:
    """Fail-closed canonicalization (F1+F5).

    Rejects absolute paths, `..` escapes, and symlinks resolving outside
    `<repo_root>/docs/`. Raises ValueError on logical reject; raises
    FileNotFoundError/OSError on resolve failure (caller maps both).
    """
    p = Path(input_path)
    if p.is_absolute():
        raise ValueError(f"absolute path not allowed: {input_path}")
    candidate = (repo_root / p).resolve(strict=True)
    docs_root = (repo_root / "docs").resolve(strict=True)
    try:
        candidate.relative_to(docs_root)
    except ValueError:
        raise ValueError(
            f"path resolves outside repo docs/ tree: {input_path} → {candidate}"
        )
    return candidate


def compute_attestation_path(doc_path: Path, iteration: int) -> Path:
    """Repo-relative attestation path for a doc + iteration."""
    name = doc_path.stem
    base = re.sub(r"-r\d+$", "", name)
    return Path("docs/reviews") / f"{base}-r{iteration}.review.yaml"


def render_prompt_from_text(doc_text: str, schema: dict) -> str:
    """Render prompt from snapshot text (no I/O on doc — F8 TOCTOU fix)."""
    template = PROMPT_TEMPLATE_PATH.read_text()
    return template.replace("<doc text inlined here at dispatch time>", doc_text)


def compute_overall_verdict(gates: dict) -> str:
    """Worst-case verdict across gates (F2)."""
    worst_rank = 0
    for gate in gates.values():
        rank = VERDICT_RANK.get(gate.get("verdict", ""), 0)
        if rank > worst_rank:
            worst_rank = rank
    return next(k for k, v in VERDICT_RANK.items() if v == worst_rank)


def _atomic_write(out_path: Path, content: str) -> None:
    """Atomic write via temp + fsync + os.replace (A24+PF10)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f".{out_path.name}.tmp.{os.getpid()}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, out_path)
    except Exception:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra:spec-review")
    parser.add_argument("doc_path", help="Repo-relative path to doc to review")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing attestation for same iteration",
    )
    args = parser.parse_args(argv)

    repo_root = _resolve_repo_root()

    try:
        canonical_path = canonicalize_doc_path(args.doc_path, repo_root)
    except (ValueError, FileNotFoundError, OSError) as e:
        print(f"error: path_traversal_blocked: {e}", file=sys.stderr)
        return 2

    # F6+F8: single immutable snapshot
    doc_bytes = canonical_path.read_bytes()
    doc_text = doc_bytes.decode("utf-8")
    pre_dispatch_hash = "sha256:" + hashlib.sha256(doc_bytes).hexdigest()
    iteration = parse_iteration_from_text(doc_text)

    # F9: anchor attestation path under repo_root
    out_path = repo_root / compute_attestation_path(canonical_path, iteration)

    # LLD-011 slice 1.7: refuse to overwrite v1.0 attestations (frozen-historical).
    # Even --force is rejected — v1.0 audit trail is preserved permanently.
    existing_version = _detect_schema_version(out_path)
    if existing_version == "1.0":
        print(
            f"error: v1.0_attestation_frozen: {out_path} is a v1.0 attestation "
            "and cannot be overwritten by v2.0 (--force does not apply). v1.0 "
            "attestations are frozen-historical per LLD-011. To run a v2.0 review, "
            "bump the doc's Iteration: field to start a fresh review cycle at iter N+1.",
            file=sys.stderr,
        )
        return 1

    if out_path.exists() and not args.force:
        print(
            f"error: {out_path} already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    schema = json.loads(SCHEMA_PATH.read_text())
    prompt = render_prompt_from_text(doc_text, schema)

    attestation = None
    yaml_text = dispatch_subagent(prompt)
    try:
        attestation = yaml.load(yaml_text, Loader=_NoTimestampLoader)
        jsonschema.validate(attestation, schema)
    except (yaml.YAMLError, jsonschema.ValidationError, TypeError) as e:
        print(
            f"error: schema_validation_failed: {e}. "
            f"Re-invoke /orchestra:spec-review for fresh dispatch.",
            file=sys.stderr,
        )
        return 1

    # Iteration check
    if attestation["doc_subject"]["iteration"] != iteration:
        print(
            f"error: iteration_mismatch: attestation iteration "
            f"{attestation['doc_subject']['iteration']} ≠ doc Iteration: {iteration}",
            file=sys.stderr,
        )
        return 1

    # F4: hard-fail on path mismatch
    canonical_relpath = str(canonical_path.relative_to(repo_root))
    if attestation["doc_subject"]["path"] != canonical_relpath:
        print(
            f"error: path_mismatch: attestation path "
            f"{attestation['doc_subject']['path']!r} ≠ canonical input "
            f"{canonical_relpath!r}",
            file=sys.stderr,
        )
        return 1

    # F6+F8: stale-state byte-compare. Wrap in try/except for doc_disappeared
    # case (v1.6.1 finding #9) — doc moved/deleted between dispatch and write.
    try:
        write_time_bytes = canonical_path.read_bytes()
    except (FileNotFoundError, OSError) as e:
        print(
            f"error: doc_disappeared: doc removed/inaccessible between dispatch "
            f"and write. {e}. Re-run spec-review.",
            file=sys.stderr,
        )
        return 1
    if write_time_bytes != doc_bytes:
        print(
            f"error: stale_state: doc bytes changed between dispatch and write. "
            f"Pre-dispatch hash {pre_dispatch_hash}. Re-run spec-review.",
            file=sys.stderr,
        )
        return 1

    # Bind authoritative hash (subagent value not trusted)
    attestation["doc_subject"]["content_hash"] = pre_dispatch_hash

    # F2: hard-fail on overall_verdict mismatch
    computed_overall = compute_overall_verdict(attestation["gates"])
    if attestation["overall_verdict"] != computed_overall:
        print(
            f"error: verdict_mismatch: claimed overall_verdict "
            f"{attestation['overall_verdict']!r} ≠ computed worst-case "
            f"{computed_overall!r} from gate verdicts",
            file=sys.stderr,
        )
        return 1

    # A24+PF10: atomic write
    yaml_content = yaml.safe_dump(
        attestation, sort_keys=False, default_flow_style=False
    )
    try:
        _atomic_write(out_path, yaml_content)
    except Exception as e:
        print(f"error: atomic_write_failed: {e}", file=sys.stderr)
        return 1

    print(f"OK: attestation written to {out_path}")
    print(f"verdict: {attestation['overall_verdict']}")

    return 0 if attestation["overall_verdict"] in ("pass", "conditional_pass") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
