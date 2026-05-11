"""Tests for _verify_changelog_row_per_finding (LLD-009 r6 T5a-c)."""

from __future__ import annotations

from cli.lint import _verify_changelog_row_per_finding


REF = ("docs/reviews/008-commit-skill-r4.review.yaml", "completeness", 3, "Minor")
PRIOR_BODY = """# Doc

Body.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Initial. |
"""

NEW_BODY_WITH_ROW = """# Doc

Body.

## Changelog

| Date | Change |
|---|---|
| 2026-05-10 | Initial. |
| 2026-05-11 | Addresses: docs/reviews/008-commit-skill-r4.review.yaml gate completeness finding 3 (Minor) — fixed wording per reviewer note |
"""

NEW_BODY_MISSING_ROW = PRIOR_BODY


def test_new_row_matches_exemplar() -> None:
    ok, why = _verify_changelog_row_per_finding(NEW_BODY_WITH_ROW, PRIOR_BODY, [REF])
    assert ok, f"unexpected fail: {why}"


def test_missing_new_row_rejects() -> None:
    ok, why = _verify_changelog_row_per_finding(NEW_BODY_MISSING_ROW, PRIOR_BODY, [REF])
    assert not ok
    assert "missing_changelog_row" in why


def test_prior_row_alone_blocks_false_accept() -> None:
    """Row inherited from prior Changelog CANNOT satisfy current finding cite (T5c)."""
    # Prior already has the addresses row; new_body equals prior — no new rows
    prior_with_row = NEW_BODY_WITH_ROW
    new_no_new_row = NEW_BODY_WITH_ROW  # identical → delta empty
    ok, why = _verify_changelog_row_per_finding(new_no_new_row, prior_with_row, [REF])
    assert not ok
    assert "missing_changelog_row" in why
