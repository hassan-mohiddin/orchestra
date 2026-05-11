"""Tests for FINDING_REF_RE + ALLOWED_GATES (LLD-009 r6 T6)."""

from __future__ import annotations

from cli.lint import ALLOWED_GATES, FINDING_REF_RE


def test_allowed_gates_matches_attestation_schema() -> None:
    assert ALLOWED_GATES == ("completeness", "evidence", "clarity", "consistency")


def test_valid_addresses_line_passes() -> None:
    msg = (
        "docs: fix minor finding\n\n"
        "Addresses: docs/reviews/008-commit-skill-r4.review.yaml gate completeness finding 3 (Minor)\n"
    )
    matches = FINDING_REF_RE.findall(msg)
    assert matches == [
        ("docs/reviews/008-commit-skill-r4.review.yaml", "completeness", "3", "Minor"),
    ]


def test_multiple_addresses_lines_match() -> None:
    msg = (
        "docs: address findings\n\n"
        "Addresses: docs/reviews/009-x-r1.review.yaml gate evidence finding 1 (Important)\n"
        "Addresses: docs/reviews/009-x-r1.review.yaml gate clarity finding 2 (Minor)\n"
    )
    matches = FINDING_REF_RE.findall(msg)
    assert len(matches) == 2
    assert matches[0][1] == "evidence"
    assert matches[1][1] == "clarity"


def test_mid_prose_addresses_does_not_match() -> None:
    """Embedded mid-prose `Addresses:` should NOT match — anchored line-start."""
    msg = "Body text mentions Addresses: docs/reviews/x.review.yaml gate completeness finding 1 (Minor) inline."
    assert FINDING_REF_RE.findall(msg) == []


def test_path_traversal_rejected_at_regex_layer() -> None:
    msg = (
        "Addresses: ../etc/passwd gate completeness finding 1 (Minor)\n"
    )
    assert FINDING_REF_RE.findall(msg) == []


def test_path_outside_docs_reviews_rejected() -> None:
    msg = (
        "Addresses: docs/plans/x.yaml gate completeness finding 1 (Minor)\n"
    )
    assert FINDING_REF_RE.findall(msg) == []


def test_unknown_gate_rejected() -> None:
    msg = (
        "Addresses: docs/reviews/x.review.yaml gate banana finding 1 (Minor)\n"
    )
    assert FINDING_REF_RE.findall(msg) == []


def test_bad_severity_rejected() -> None:
    msg = (
        "Addresses: docs/reviews/x.review.yaml gate completeness finding 1 (Trivial)\n"
    )
    assert FINDING_REF_RE.findall(msg) == []


def test_non_yaml_extension_rejected() -> None:
    msg = (
        "Addresses: docs/reviews/x.review.txt gate completeness finding 1 (Minor)\n"
    )
    assert FINDING_REF_RE.findall(msg) == []
