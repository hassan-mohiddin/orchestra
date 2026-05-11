"""LLD-010 r4 T-INT-010 — end-to-end LLD-008 + 009 + 010 integration test.

Exercises L2-detect via lint_staged + L2-finalize via lint_commit_msg_finalize in
a tmpdir git repo with the canon-frozen fixture. Does NOT require the pre-commit
framework binary — invokes orchestra entrypoints directly to validate the same
contract that framework hooks would invoke.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from cli.lint import lint_commit_msg_finalize, lint_staged

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "test-canon-frozen.md"


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True)


def _commit(repo: Path, msg: str = "x") -> None:
    subprocess.run(["git", "-c", "user.email=t@e", "-c", "user.name=T",
                    "commit", "-m", msg, "--allow-empty"],
                   cwd=repo, check=True, capture_output=True)


def test_t_int_010_canon_inplace_via_framework_hook_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    """T-INT-010: canon-frozen body edit + no Addresses: → L2-finalize rejects."""
    # Seed canon-frozen fixture doc
    doc_path = tmp_repo / "docs/features/test-canon-frozen.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE, doc_path)
    subprocess.run(["git", "add", "docs/features/test-canon-frozen.md"],
                   cwd=tmp_repo, check=True)
    _commit(tmp_repo, "seed canon-frozen fixture")

    # Construct canon-inplace violation: modify body (Acceptance section)
    text = doc_path.read_text()
    modified = text.replace(
        "## Scope\n\nIn scope: fixture role only.\n",
        "## Scope\n\nIn scope: fixture role only. INPLACE EDIT VIOLATION.\n",
    )
    assert modified != text
    doc_path.write_text(modified)
    subprocess.run(["git", "add", "docs/features/test-canon-frozen.md"],
                   cwd=tmp_repo, check=True)

    # L2-detect runs through lint_staged (no findings; annotates pending)
    findings = lint_staged(tmp_repo)
    # No blocking findings from L2-detect
    blocking = [f for f in findings if f.severity == "error"]
    assert not blocking, f"L2-detect should not block: {blocking}"

    # commit-msg: no Addresses: line → L2-finalize rejects
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text("docs: tweak test-canon-frozen\n")
    rc = lint_commit_msg_finalize(str(msg_file), tmp_repo)
    assert rc == 1
