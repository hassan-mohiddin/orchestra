"""Bias mitigation tests (v1 S28-S30 slices).

v2 (LLD-011) drops the `max_tokens: 4000` cap entirely — length-bias mitigation
moved from output cap to prompt-level terseness instruction per LLD-011 design
decision. The S30 `test_skill_md_specifies_max_tokens_4000` test was removed
when SKILL.md was rewritten for v2 dispatch (slice 1.26). The remaining tests
(position-bias prompt instruction + same-iteration overwrite refusal) are
preserved as regression locks because both behaviors carry over to v2.
"""

from pathlib import Path


def test_finding_order_random_seed_in_prompt():
    """T13a / S28 — A8: prompt instructs ordering by location (position-bias mitigation)."""
    template = (
        Path(__file__).parent.parent
        / "skills"
        / "spec-review"
        / "prompt-template.md"
    ).read_text()
    # Position-bias instruction: order by location, not severity
    assert "by location" in template
    assert "BIAS MITIGATIONS" in template


def test_force_required_for_same_iteration_overwrite(tmp_path, capsys, monkeypatch):
    """T13b / S29 — A8: pre-existing attestation + no --force → exit 1."""
    from cli import spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text("# foo\n\n> **Iteration:** 1\n\n## Body\n")

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    out = reviews / "008-foo-r1.review.yaml"
    out.write_text("existing\n")

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    assert "already exists" in capsys.readouterr().err


# test_skill_md_specifies_max_tokens_4000 removed — v2 (LLD-011) drops the
# output-token cap in favor of prompt-level terseness instruction. Codex
# adversarial review on LLD-011 noted that v1's 4000-token cap caused mid-
# finding truncation; v2 keeps length-bias mitigation at the prompt level only.
