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
