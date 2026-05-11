"""--aggregate-and-write mode tests (LLD-011 self-application).

This mode is the v2 entrypoint used after the SKILL.md fans 6 parallel
Task-tool sub-judges out and collects their YAML outputs. Skill pipes those
YAMLs as a single mapping `{sub_judges: [...]}` to `cli.spec_review
--aggregate-and-write <doc>`. CLI then:

1. Re-runs PDSA + iter-cap gates (defensive — skill should have already
   passed these, but the CLI is the canon enforcement point).
2. Aggregates findings via cli.aggregator.
3. Computes overall_verdict_v2 (tiered mandatory + worst-of-completed).
4. Builds the v2.0 attestation: provenance (iter_blob_sha + iter_commit_sha),
   content_hash, attestation_integrity_hash.
5. Validates against attestation-schema-v2.0.json.
6. Atomic write to docs/reviews/<doc-id>-rN.review.yaml.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
from pathlib import Path

import jsonschema
import yaml


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "--quiet", "--initial-branch=main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)


def _fresh_v2_doc(tmp_path: Path, iteration: int = 1) -> Path:
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True, exist_ok=True)
    doc = docs / "008-foo.md"
    doc.write_text(
        f"# 008 Foo\n\n"
        f"> **Doc ID:** 008-foo\n"
        f"> **Date:** 2026-05-11\n"
        f"> **Status:** Draft\n"
        f"> **Iteration:** {iteration}\n\nbody.\n"
    )
    return doc


def _two_passing_subjudges() -> list[dict]:
    """Minimal pass-fixture: semantic + adversarial both complete with empty findings."""
    return [
        {
            "id": "semantic",
            "model": "claude-opus-4-7",
            "mandatory": True,
            "rubric_version": "semantic-v1",
            "status": "completed",
            "verdict": "pass",
            "findings": [],
            "justification": "no findings raised",
        },
        {
            "id": "adversarial",
            "model": "claude-opus-4-7",
            "mandatory": True,
            "rubric_version": "adversarial-v1",
            "status": "completed",
            "verdict": "pass",
            "findings": [],
            "justification": "no findings raised",
        },
    ]


def test_aggregate_and_write_pass(tmp_path, monkeypatch):
    """Self-application — happy path: pass attestation written to docs/reviews/<doc-id>-r1.review.yaml."""
    from cli import pdsa, spec_review

    _init_repo(tmp_path)
    doc = _fresh_v2_doc(tmp_path, iteration=1)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    def fake_pdsa(p):
        rep = pdsa.PdsaReport(doc_path=p)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_pdsa)

    stdin_payload = yaml.safe_dump({"sub_judges": _two_passing_subjudges()})
    monkeypatch.setattr(spec_review.sys, "stdin", io.StringIO(stdin_payload))

    rc = spec_review.main(["--aggregate-and-write", "docs/features/008-foo.md"])
    assert rc == 0, "expected pass attestation write to exit 0"

    out_path = tmp_path / "docs" / "reviews" / "008-foo-r1.review.yaml"
    assert out_path.exists(), "attestation file must be created"

    written = yaml.safe_load(out_path.read_text())
    assert written["schema_version"] == "2.0"
    assert written["overall_verdict"] == "pass"
    assert len(written["sub_judges"]) == 2
    assert written["findings_aggregated"] == []
    assert written["doc_subject"]["iter_blob_sha"]
    assert "attestation_integrity_hash" in written


def test_aggregate_and_write_validates_against_v2_schema(tmp_path, monkeypatch):
    """Self-application — written attestation conforms to attestation-schema-v2.0.json."""
    from cli import pdsa, spec_review

    _init_repo(tmp_path)
    _fresh_v2_doc(tmp_path, iteration=1)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    def fake_pdsa(p):
        rep = pdsa.PdsaReport(doc_path=p)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_pdsa)

    stdin_payload = yaml.safe_dump({"sub_judges": _two_passing_subjudges()})
    monkeypatch.setattr(spec_review.sys, "stdin", io.StringIO(stdin_payload))

    spec_review.main(["--aggregate-and-write", "docs/features/008-foo.md"])

    written = yaml.safe_load(
        (tmp_path / "docs" / "reviews" / "008-foo-r1.review.yaml").read_text()
    )
    schema = json.loads(spec_review.SCHEMA_V2_PATH.read_text())
    jsonschema.validate(written, schema)


def test_aggregate_and_write_aggregates_findings(tmp_path, monkeypatch):
    """Self-application — sub-judge findings flow through aggregator into findings_aggregated."""
    from cli import pdsa, spec_review

    _init_repo(tmp_path)
    _fresh_v2_doc(tmp_path, iteration=1)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    def fake_pdsa(p):
        rep = pdsa.PdsaReport(doc_path=p)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_pdsa)

    sjs = _two_passing_subjudges()
    sjs[0]["findings"] = [
        {
            "severity": "Important",
            "location": "Body § A",
            "problem": "missing edge case",
            "scope": "instance",
        }
    ]
    sjs[0]["verdict"] = "conditional_pass"
    del sjs[0]["justification"]  # findings present → justification not required

    stdin_payload = yaml.safe_dump({"sub_judges": sjs})
    monkeypatch.setattr(spec_review.sys, "stdin", io.StringIO(stdin_payload))

    spec_review.main(["--aggregate-and-write", "docs/features/008-foo.md"])
    written = yaml.safe_load(
        (tmp_path / "docs" / "reviews" / "008-foo-r1.review.yaml").read_text()
    )
    assert len(written["findings_aggregated"]) == 1
    assert written["findings_aggregated"][0]["severity"] == "Important"
    assert written["overall_verdict"] == "conditional_pass"


def test_aggregate_and_write_mandatory_failure(tmp_path, monkeypatch):
    """Self-application — mandatory sub-judge failure → overall=fail with reason=mandatory_subjudge_failed."""
    from cli import pdsa, spec_review

    _init_repo(tmp_path)
    _fresh_v2_doc(tmp_path, iteration=1)
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)

    def fake_pdsa(p):
        rep = pdsa.PdsaReport(doc_path=p)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_pdsa)

    sjs = _two_passing_subjudges()
    sjs[0]["status"] = "error"
    sjs[0]["verdict"] = "fail"
    del sjs[0]["justification"]
    sjs[0]["findings"] = []

    stdin_payload = yaml.safe_dump({"sub_judges": sjs})
    monkeypatch.setattr(spec_review.sys, "stdin", io.StringIO(stdin_payload))

    rc = spec_review.main(["--aggregate-and-write", "docs/features/008-foo.md"])
    assert rc == 1, "mandatory failure must exit 1"

    written = yaml.safe_load(
        (tmp_path / "docs" / "reviews" / "008-foo-r1.review.yaml").read_text()
    )
    assert written["overall_verdict"] == "fail"
    assert written["overall_verdict_basis"]["reason"] == "mandatory_subjudge_failed"
    assert "semantic" in written["overall_verdict_basis"]["mandatory_failures"]
