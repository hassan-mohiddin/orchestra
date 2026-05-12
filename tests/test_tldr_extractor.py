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
