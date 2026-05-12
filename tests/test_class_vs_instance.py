"""Class-vs-instance scope tests (LLD-011 Phase 2 slices 2.14-2.16).

Per LLD-011 §Design class-vs-instance:
- instance findings = fix in the current iteration (scope=instance)
- class findings = systemic concern; iter-2 doc must include audit_attestation
  recording how authors swept the class issue across the doc (scope=class)

Aggregator preservation rule (slice 2.14): when two sub-judges raise the same
finding (same location + fuzzy_hash) but differ on scope, the canonical winner
(alphabetically-first sub-judge id) keeps its scope and the raised_by set
unions normally.
"""

from __future__ import annotations

from cli import aggregator


def _f(loc: str, problem: str, scope: str = "instance", severity: str = "Important") -> dict:
    return {
        "severity": severity,
        "location": loc,
        "problem": problem,
        "scope": scope,
    }


def _sj(id_: str, findings: list[dict]) -> dict:
    return {"id": id_, "status": "completed", "findings": findings}


def test_scope_preserved_single_finding():
    """Slice 2.14 — single finding with scope=class flows through unchanged."""
    out = aggregator.aggregate_findings(
        [_sj("semantic", [_f("Body § X", "p", scope="class")])]
    )
    assert len(out) == 1
    assert out[0]["scope"] == "class"


def test_scope_canonical_first_wins_on_merge():
    """Slice 2.14 — same (location, problem) merged across two sub-judges.

    Canonical = alphabetically-first sub-judge id wins for scope. raised_by unions.
    'adversarial' < 'semantic' so adversarial's scope wins.
    """
    out = aggregator.aggregate_findings([
        _sj("semantic", [_f("Body § X", "same problem here", scope="class")]),
        _sj("adversarial", [_f("Body § X", "same problem here", scope="instance")]),
    ])
    assert len(out) == 1
    assert out[0]["scope"] == "instance"
    assert sorted(out[0]["raised_by"]) == ["adversarial", "semantic"]


def test_scope_instance_default_preserved():
    """Slice 2.14 — instance scope flows through aggregator unchanged."""
    out = aggregator.aggregate_findings(
        [_sj("semantic", [_f("Body § Y", "q", scope="instance")])]
    )
    assert out[0]["scope"] == "instance"


def test_class_audit_required_when_iter1_has_class_findings(tmp_path, monkeypatch):
    """Slice 2.15 — iter-2 doc with class-scoped iter-1 findings must include audit_attestation.

    PDSA check `class_audit_attestation` reads the iter-1 attestation; if any
    iter-1 finding has scope=class, the iter-2 doc must contain an
    `## Audit Attestation` section recording the sweep.
    """
    import yaml as yaml_mod
    from cli import pdsa

    iter1_attestation = {
        "schema_version": "2.0",
        "findings_aggregated": [
            {
                "severity": "Important",
                "location": "Body § X",
                "problem": "shared problem",
                "scope": "class",
                "raised_by": ["semantic"],
            }
        ],
    }

    docs_features = tmp_path / "docs" / "features"
    docs_features.mkdir(parents=True)
    doc = docs_features / "999-foo.md"
    doc.write_text(
        "# 999 Foo\n\n> **Iteration:** 2\n\n"
        "## Problem Statement\nx\n## Success Criteria\nx\n## Scope\nx\n"
        "## Design\nx\n## API Changes\nx\n## Database Changes\nx\n"
        "## Edge Cases\nx\n## Security Considerations\nx\n## Testing Strategy\nx\n"
        "## Related Documents\nx\n## Changelog\nx\n"
    )

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "999-foo-r1.review.yaml").write_text(yaml_mod.safe_dump(iter1_attestation))

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)

    report = pdsa.run_pdsa(doc)

    assert "class_audit_attestation" in report.checks
    assert report.checks["class_audit_attestation"].passed is False


def test_class_audit_satisfied_when_doc_has_audit_section(tmp_path, monkeypatch):
    """Slice 2.15 — audit_attestation section in doc body satisfies the check."""
    import yaml as yaml_mod
    from cli import pdsa

    iter1_attestation = {
        "schema_version": "2.0",
        "findings_aggregated": [
            {
                "severity": "Important",
                "location": "Body § X",
                "problem": "shared problem",
                "scope": "class",
                "raised_by": ["semantic"],
            }
        ],
    }

    docs_features = tmp_path / "docs" / "features"
    docs_features.mkdir(parents=True)
    doc = docs_features / "999-foo.md"
    doc.write_text(
        "# 999 Foo\n\n> **Iteration:** 2\n\n"
        "## Problem Statement\nx\n## Success Criteria\nx\n## Scope\nx\n"
        "## Design\nx\n## API Changes\nx\n## Database Changes\nx\n"
        "## Edge Cases\nx\n## Security Considerations\nx\n## Testing Strategy\nx\n"
        "## Related Documents\nx\n## Changelog\nx\n"
        "## Audit Attestation\n\nSwept class finding `shared problem` across body. All cases resolved.\n"
    )

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "999-foo-r1.review.yaml").write_text(yaml_mod.safe_dump(iter1_attestation))

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)

    report = pdsa.run_pdsa(doc)

    assert report.checks["class_audit_attestation"].passed is True


def test_instance_no_audit_required(tmp_path, monkeypatch):
    """Slice 2.16 — iter-1 with only instance findings → audit check passes (nothing to sweep)."""
    import yaml as yaml_mod
    from cli import pdsa

    iter1_attestation = {
        "schema_version": "2.0",
        "findings_aggregated": [
            {
                "severity": "Minor",
                "location": "Body § X",
                "problem": "small issue",
                "scope": "instance",
                "raised_by": ["semantic"],
            }
        ],
    }

    docs_features = tmp_path / "docs" / "features"
    docs_features.mkdir(parents=True)
    doc = docs_features / "999-foo.md"
    doc.write_text("# 999 Foo\n\n> **Iteration:** 2\n\nbody.\n")

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "999-foo-r1.review.yaml").write_text(yaml_mod.safe_dump(iter1_attestation))

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    pdsa._discover_repo_root.cache_clear()
    monkeypatch.setattr(pdsa, "_discover_repo_root", lambda anchor: tmp_path)
    monkeypatch.chdir(tmp_path)

    report = pdsa.run_pdsa(doc)

    assert report.checks["class_audit_attestation"].passed is True


def test_class_audit_iter1_no_attestation(tmp_path, monkeypatch):
    """Slice 2.15 — no iter-1 attestation present → audit check passes (iter-1 doc)."""
    from cli import pdsa

    docs_features = tmp_path / "docs" / "features"
    docs_features.mkdir(parents=True)
    doc = docs_features / "999-foo.md"
    doc.write_text("# 999 Foo\n\n> **Iteration:** 1\n\nbody.\n")

    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)
    monkeypatch.chdir(tmp_path)

    report = pdsa.run_pdsa(doc)

    assert report.checks["class_audit_attestation"].passed is True


def test_aggregator_emits_scope_for_every_finding():
    """Slice 2.14 — every aggregated finding has a scope field (schema v2.13 requirement)."""
    out = aggregator.aggregate_findings([
        _sj("semantic", [_f("A § a", "p1", scope="instance"), _f("B § b", "p2", scope="class")]),
        _sj("adversarial", [_f("C § c", "p3", scope="class")]),
    ])
    assert len(out) == 3
    for f in out:
        assert "scope" in f
        assert f["scope"] in ("instance", "class")
