from cli.tldr_extractor import TldrSection, extract_tldr


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
