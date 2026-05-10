"""Bias mitigation tests (S28-S30 slices)."""

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


def test_skill_md_specifies_max_tokens_4000():
    """T13c / S30 — A8: SKILL.md prose contains `max_tokens: 4000` (length-bias mitigation)."""
    skill_md = (
        Path(__file__).parent.parent / "skills" / "spec-review" / "SKILL.md"
    ).read_text()
    assert "max_tokens: 4000" in skill_md
