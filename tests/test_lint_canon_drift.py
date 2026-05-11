"""Drift gate — cli.lint constants must match cli.vocabulary canon (slice 2).

Slice 2 of the vocab-canon migration imports 6 constants from `cli.vocabulary`
(canon §4.1, §4.2, §4.6, §4.7, §4.9, §4.13) so the two modules can never
diverge silently. REQUIRED_SECTIONS (canon §4.8) is deferred to slice 3
because the canon-strict form requires conditional-section handling in L2.
"""

from __future__ import annotations


def test_status_enums_canon_match():
    from cli import lint, vocabulary

    assert lint.STATUS_ENUMS == vocabulary.STATUS_ENUMS


def test_canon_frozen_statuses_canon_match():
    from cli import lint, vocabulary

    assert lint.CANON_FROZEN_STATUSES == vocabulary.CANON_FROZEN_STATUSES


def test_refs_eligible_prefixes_canon_match():
    from cli import lint, vocabulary

    assert lint.REFS_ELIGIBLE_PREFIXES == vocabulary.REFS_ELIGIBLE_PREFIXES


def test_whitelist_frontmatter_fields_canon_match():
    from cli import lint, vocabulary

    assert lint.WHITELIST_FRONTMATTER_FIELDS == vocabulary.WHITELIST_FRONTMATTER_FIELDS


def test_allowed_attestation_path_prefixes_canon_match():
    from cli import lint, vocabulary

    assert lint.ALLOWED_ATTESTATION_PATH_PREFIXES == vocabulary.ALLOWED_ATTESTATION_PATH_PREFIXES


def test_allowed_gates_canon_match():
    from cli import lint, vocabulary

    # ALLOWED_GATES is the historical lint name for canon §4.9 REVIEW_GATE_NAMES.
    assert lint.ALLOWED_GATES == vocabulary.REVIEW_GATE_NAMES
