"""Provenance helpers for spec-review v2 (LLD-011 Phase 1 slices 1.19-1.22).

`iter_commit_sha` + `iter_blob_sha` are recorded in v2.0 attestations and used
by iter-2 delta-review to retrieve iter-1 doc bytes deterministically without
git-log hash walking. Helpers wrap git subprocess calls.
"""

import re
import subprocess
from pathlib import Path

import pytest


def _git_init(repo: Path) -> None:
    """Init a tmp git repo + minimal config (deterministic)."""
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "test"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
    )


def _git_commit_empty(repo: Path) -> str:
    """Create an empty commit, return its SHA."""
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=repo,
        check=True,
    )
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo)
        .decode()
        .strip()
    )


def test_iter_commit_sha_returns_hex(tmp_path: Path) -> None:
    """Slice 1.19 — _get_iter_commit_sha returns 40-hex SHA when HEAD exists."""
    from cli import spec_review

    _git_init(tmp_path)
    expected = _git_commit_empty(tmp_path)
    sha = spec_review._get_iter_commit_sha(tmp_path)
    assert sha == expected
    assert re.match(r"^[0-9a-f]{40}$", sha)


def test_iter_commit_sha_uncommitted(tmp_path: Path) -> None:
    """Slice 1.19 — returns '<uncommitted>' when no HEAD exists in repo."""
    from cli import spec_review

    _git_init(tmp_path)  # init but no commit
    sha = spec_review._get_iter_commit_sha(tmp_path)
    assert sha == "<uncommitted>"


def test_persist_doc_blob_returns_hex(tmp_path: Path) -> None:
    """Slice 1.20 — _persist_doc_blob returns 40-hex SHA via git hash-object -w."""
    from cli import spec_review

    _git_init(tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text("# hello\n\nworld\n")
    blob_sha = spec_review._persist_doc_blob(doc, tmp_path)
    assert re.match(r"^[0-9a-f]{40}$", blob_sha)


def test_persist_doc_blob_writes_to_object_db(tmp_path: Path) -> None:
    """Slice 1.20+1.21 — persisted blob is retrievable via `git cat-file -p`."""
    from cli import spec_review

    _git_init(tmp_path)
    doc = tmp_path / "doc.md"
    content = b"# hello\n\nworld\n"
    doc.write_bytes(content)
    blob_sha = spec_review._persist_doc_blob(doc, tmp_path)

    retrieved = spec_review._retrieve_doc_bytes_by_blob_sha(blob_sha, tmp_path)
    assert retrieved == content


def test_persist_works_for_uncommitted_doc(tmp_path: Path) -> None:
    """Slice 1.22 — provenance works even if doc was never committed."""
    from cli import spec_review

    _git_init(tmp_path)
    doc = tmp_path / "uncommitted.md"
    content = b"# never committed\n"
    doc.write_bytes(content)
    # No `git add` / `git commit` — doc is purely in working tree
    blob_sha = spec_review._persist_doc_blob(doc, tmp_path)
    retrieved = spec_review._retrieve_doc_bytes_by_blob_sha(blob_sha, tmp_path)
    assert retrieved == content


def test_retrieve_missing_blob_raises(tmp_path: Path) -> None:
    """Slice 1.21 — retrieval of a non-existent blob raises CalledProcessError (caller maps to SpecReviewError)."""
    from cli import spec_review

    _git_init(tmp_path)
    fake_sha = "0" * 40
    with pytest.raises(subprocess.CalledProcessError):
        spec_review._retrieve_doc_bytes_by_blob_sha(fake_sha, tmp_path)
