import logging

import pytest

from cli.tldr_extractor import TldrError, TldrSection, extract_tldr


def test_extracts_valid_tldr_section() -> None:
    text = (
        "# Title\n"
        "\n"
        "intro paragraph\n"
        "\n"
        "## TLDR — Nonnegotiables\n"
        "\n"
        "- STOP on ambiguous scope.\n"
        "- No code without doc.\n"
        "\n"
        "<!-- Full rule body below this section -->\n"
        "\n"
        "Full body here.\n"
    )
    result = extract_tldr(text)
    assert isinstance(result, TldrSection)
    assert result.bullets == ["STOP on ambiguous scope.", "No code without doc."]


def test_missing_close_marker_warns_and_extracts_to_eof(
    caplog: pytest.LogCaptureFixture,
) -> None:
    text = (
        "## TLDR — Nonnegotiables\n"
        "\n"
        "- alpha.\n"
        "- beta.\n"
    )
    with caplog.at_level(logging.WARNING, logger="cli.tldr_extractor"):
        result = extract_tldr(text)
    assert isinstance(result, TldrSection)
    assert result.bullets == ["alpha.", "beta."]
    assert any(
        "close marker" in rec.message.lower() for rec in caplog.records
    ), f"expected WARN about missing close marker, got {caplog.records!r}"


def _wrap_tldr(bullet_lines: list[str]) -> str:
    body = "\n".join(bullet_lines)
    return (
        "## TLDR — Nonnegotiables\n"
        "\n"
        f"{body}\n"
        "\n"
        "<!-- Full rule body below this section -->\n"
    )


def test_overflow_rejects_with_diagnostic() -> None:
    too_many = _wrap_tldr([f"- bullet {i}." for i in range(8)])
    result = extract_tldr(too_many)
    assert isinstance(result, TldrError)
    assert result.reason == "overflow"
    assert "8" in result.detail or "count" in result.detail.lower()

    over_length = _wrap_tldr(["- " + "x" * 81])
    result2 = extract_tldr(over_length)
    assert isinstance(result2, TldrError)
    assert result2.reason == "overflow"
    assert "80" in result2.detail or "length" in result2.detail.lower()


def test_multiple_tldr_sections_rejects() -> None:
    text = (
        "## TLDR — Nonnegotiables\n"
        "\n"
        "- first.\n"
        "\n"
        "<!-- Full rule body below this section -->\n"
        "\n"
        "## TLDR — Nonnegotiables\n"
        "\n"
        "- second.\n"
        "\n"
        "<!-- Full rule body below this section -->\n"
    )
    result = extract_tldr(text)
    assert isinstance(result, TldrError)
    assert result.reason == "ambiguous_tldr"
