"""Prompt template structural test (S27 slice)."""

from pathlib import Path


def test_prompt_template_has_7_elements():
    """T3 / S27 — A4: rendered prompt contains all 7 adversarial elements.

    Elements: role anchor, scope fence, 4-gate rubric, anti-sycophancy,
    anti-pedantry, forced YAML schema, minimum-issue framing.
    """
    template = (
        Path(__file__).parent.parent
        / "skills"
        / "spec-review"
        / "prompt-template.md"
    ).read_text()

    required_headings = [
        "ROLE ANCHOR",
        "SCOPE FENCE",
        "4-GATE RUBRIC",
        "ANTI-SYCOPHANCY",
        "ANTI-PEDANTRY",
        "OUTPUT FORMAT",
        "MINIMUM-ISSUE FRAMING",
    ]
    for heading in required_headings:
        assert heading in template, f"prompt-template.md missing: {heading}"
