"""Top-level dispatch + flow integration tests for spec-review v2 (LLD-011)."""

from pathlib import Path

from cli import spec_review


JUDGES_DIR = (
    Path(__file__).parent.parent / "skills" / "spec-review" / "judges"
)
SUB_JUDGE_IDS = [
    "structure",
    "semantic",
    "gate-compliance",
    "adversarial",
    "repo-context",
    "architectural-fit",
]


def test_mandatory_map():
    """Slice 1.8 — MANDATORY_SUBJUDGES is a frozenset of {semantic, adversarial}.

    Per LLD-011 §Schema v2.0 Mandatory map: semantic + adversarial are mandatory.
    Their failure forces overall_verdict=fail with reason=mandatory_subjudge_failed.
    """
    assert spec_review.MANDATORY_SUBJUDGES == frozenset({"semantic", "adversarial"})
    assert isinstance(spec_review.MANDATORY_SUBJUDGES, frozenset)


def test_judge_prompt_files_present():
    """Slice 1.9 — every sub-judge has a non-empty prompt.md at the expected path."""
    for jid in SUB_JUDGE_IDS:
        path = JUDGES_DIR / jid / "prompt.md"
        assert path.exists(), f"missing prompt.md for sub-judge {jid}: {path}"
        assert path.read_text().strip(), f"prompt.md is empty for sub-judge {jid}"


def test_judge_rubric_files_present():
    """Slice 1.10 — every sub-judge has a non-empty rubric-v1.md at the expected path."""
    for jid in SUB_JUDGE_IDS:
        path = JUDGES_DIR / jid / "rubric-v1.md"
        assert path.exists(), f"missing rubric-v1.md for sub-judge {jid}: {path}"
        assert path.read_text().strip(), f"rubric-v1.md is empty for sub-judge {jid}"


SKILL_MD = (
    Path(__file__).parent.parent / "skills" / "spec-review" / "SKILL.md"
)


def test_skill_md_describes_v2_dispatch():
    """Slice 1.26 — SKILL.md describes v2 parallel dispatch protocol.

    The skill body is consumed by Claude Code at invocation time. We test by
    content presence: it must mention all 6 sub-judge IDs and the parallel-
    dispatch instruction. The actual dispatch behavior is integration-tested
    at skill-invocation time (outside pytest).
    """
    body = SKILL_MD.read_text()
    # All 6 sub-judges named
    for jid in SUB_JUDGE_IDS:
        assert jid in body, f"SKILL.md missing reference to sub-judge {jid}"
    # Parallel-dispatch instruction
    assert "parallel" in body.lower()
    assert "single message" in body.lower() or "single-message" in body.lower()
    # Schema v2.0 reference
    assert "v2.0" in body
    # Provenance + integrity primitives mentioned
    assert "iter_blob_sha" in body or "git hash-object -w" in body
    assert "attestation_integrity_hash" in body or "integrity hash" in body.lower()
    # Failure-attestation invariant
    assert "failure" in body.lower()


def test_parse_codex_findings_severity_counts():
    """Slice 1.31 — codex .md parser extracts severity counts from typical codex output."""
    codex_md = """# Codex Adversarial Review

Target: working tree diff
Verdict: needs-attention

Findings:
- [critical] First critical issue (path:1)
  Description here.
- [high] Some high issue (path:5)
  Body.
- [high] Another high issue (path:10)
  Body.
- [medium] Medium issue (path:15)
  Body.

Next steps:
- ...
"""
    counts = spec_review.parse_codex_findings(codex_md)
    assert counts["Critical"] == 1
    assert counts["Important"] == 2  # codex `[high]` maps to Important
    assert counts["Minor"] == 1  # codex `[medium]` maps to Minor


def test_parse_codex_findings_no_findings():
    """Slice 1.31 — parser handles codex output with no findings (all zeros)."""
    codex_md = """# Codex Adversarial Review

Verdict: pass

Findings: none.

Next steps:
- ...
"""
    counts = spec_review.parse_codex_findings(codex_md)
    assert counts["Critical"] == 0
    assert counts["Important"] == 0
    assert counts["Minor"] == 0


def test_parse_codex_findings_unknown_format():
    """Slice 1.31 — parser tolerates unknown format and returns zero counts (no crash)."""
    counts = spec_review.parse_codex_findings("totally unrelated content")
    assert counts["Critical"] == 0
    assert counts["Important"] == 0
    assert counts["Minor"] == 0


def test_render_cross_judge_report_orchestra_only():
    """Slice 1.30 — report renders with orchestra alone (no codex)."""
    orchestra = {
        "doc_subject": {"path": "docs/features/example.md", "iteration": 1},
        "findings_aggregated": [
            {
                "severity": "Critical",
                "location": "Body § A",
                "problem": "p1",
                "raised_by": ["semantic"],
            },
            {
                "severity": "Important",
                "location": "Body § B",
                "problem": "p2",
                "raised_by": ["adversarial"],
            },
        ],
    }
    out = spec_review.render_cross_judge_report(orchestra, codex_md=None)
    assert "Spec-Review v2 Report" in out
    assert "orchestra" in out
    # Counts present
    assert "1" in out  # Critical count
    # No codex row
    assert "codex" not in out.lower() or "no codex" in out.lower()


def test_gate_fires_on_critical():
    """Slice 1.32 — should_fire_interview_gate returns True when aggregate has Critical."""
    findings = [
        {"severity": "Critical", "location": "A § x", "problem": "p", "raised_by": ["s"]},
    ]
    assert spec_review.should_fire_interview_gate(findings) is True


def test_gate_fires_on_important():
    """Slice 1.32 — should_fire_interview_gate returns True when aggregate has Important."""
    findings = [
        {"severity": "Important", "location": "A § x", "problem": "p", "raised_by": ["s"]},
    ]
    assert spec_review.should_fire_interview_gate(findings) is True


def test_gate_fires_with_mixed():
    """Slice 1.32 — gate fires when Critical AND Minor coexist."""
    findings = [
        {"severity": "Critical", "location": "A § x", "problem": "p1", "raised_by": ["s"]},
        {"severity": "Minor", "location": "B § y", "problem": "p2", "raised_by": ["s"]},
    ]
    assert spec_review.should_fire_interview_gate(findings) is True


def test_gate_skips_only_minor():
    """Slice 1.33 — should_fire_interview_gate returns False when only Minor findings."""
    findings = [
        {"severity": "Minor", "location": "A § x", "problem": "p1", "raised_by": ["s"]},
        {"severity": "Minor", "location": "B § y", "problem": "p2", "raised_by": ["s"]},
    ]
    assert spec_review.should_fire_interview_gate(findings) is False


def test_gate_skips_empty_findings():
    """Slice 1.33 — should_fire_interview_gate returns False when no findings (pass case)."""
    assert spec_review.should_fire_interview_gate([]) is False


import pytest


@pytest.mark.real_pdsa
def test_pdsa_blocks_dispatch(tmp_path, monkeypatch, capsys):
    """Slice 2.12 — PDSA failure halts main() before sub-judge dispatch.

    Contract: when PDSA reports `passed=False`, main() emits the YAML report
    to stderr, returns non-zero, and never invokes dispatch_subagent.
    """
    from cli import pdsa, spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text(
        "# foo\n\n> **Iteration:** 1\n\n## Body\n\nbody.\n"
    )

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    # PDSA lint fails → PDSA report.passed False
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 1)

    dispatched: list[str] = []
    def fake_dispatch(prompt: str) -> str:
        dispatched.append(prompt)
        return ""
    monkeypatch.setattr(spec_review, "dispatch_subagent", fake_dispatch)

    rc = spec_review.main(["docs/features/008-foo.md"])

    assert rc != 0
    assert dispatched == [], "dispatch_subagent must NOT run after PDSA fail"
    err = capsys.readouterr().err
    assert "pdsa" in err.lower()


def test_pdsa_passes_dispatch_proceeds(tmp_path, monkeypatch):
    """Slice 2.12 — PDSA passing allows main() to proceed to dispatch."""
    from cli import pdsa, spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text(
        "# foo\n\n> **Iteration:** 1\n\n## Body\n\nbody.\n"
    )

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    # PDSA lint passes
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    # Stub required_sections + filename_grammar etc. to all-pass for unknown doc layout
    # by monkeypatching run_pdsa to return clean report.
    def fake_run_pdsa(doc_path):
        report = pdsa.PdsaReport(doc_path=doc_path)
        report.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return report
    monkeypatch.setattr(spec_review, "run_pdsa", fake_run_pdsa)

    dispatched: list[str] = []
    def fake_dispatch(prompt: str) -> str:
        dispatched.append(prompt)
        # Short-circuit: return invalid YAML so we return early after dispatch
        return "not yaml at all"
    monkeypatch.setattr(spec_review, "dispatch_subagent", fake_dispatch)

    spec_review.main(["docs/features/008-foo.md"])

    # Key assertion: dispatch happened (PDSA didn't block)
    assert len(dispatched) == 1


def test_render_cross_judge_report_with_codex():
    """Slice 1.30 — report renders cross-judge counts when codex present."""
    orchestra = {
        "doc_subject": {"path": "docs/features/example.md", "iteration": 1},
        "findings_aggregated": [
            {
                "severity": "Critical",
                "location": "Body § A",
                "problem": "p1",
                "raised_by": ["semantic"],
            }
        ],
    }
    codex_md = "Findings:\n- [critical] X\n- [high] Y\n"
    out = spec_review.render_cross_judge_report(orchestra, codex_md=codex_md)
    assert "orchestra" in out
    assert "codex" in out
    # Both judges have counts in the table
    assert "| orchestra |" in out
    assert "| codex |" in out
