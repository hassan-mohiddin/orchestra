"""Slice 6 — every docs/reviews/* filename matches canon §4.11 regex.

After slice 6 renames every attestation from `<stem>.review.yaml` to
`<stem>.orchestra.review.yaml`, this test gates against future drift.
Canon source: docs/design/controlled-vocabulary.md § 4.11.

Codex prose reviews (`*.codex.review.md`) and orchestra attestations
(`*.orchestra.review.yaml`) both match the canon regex via the `<judge>`
slot.
"""

from __future__ import annotations

from pathlib import Path

from cli import _shared, vocabulary


def test_all_review_filenames_match_canon():
    reviews_dir = _shared._repo_root() / "docs" / "reviews"
    if not reviews_dir.is_dir():
        return  # no reviews dir; nothing to enforce
    bad: list[str] = []
    for f in reviews_dir.iterdir():
        if not f.is_file():
            continue
        if not (f.name.endswith(".yaml") or f.name.endswith(".md")):
            continue
        # exclude editor temp files / pending-l2 sidecars
        if f.name.startswith(".") or "pending" in f.name:
            continue
        if not vocabulary.REVIEW_DOC_FILENAME_REGEX.match(f.name):
            bad.append(f.name)
    assert not bad, f"filenames violate canon §4.11 regex: {sorted(bad)}"
