"""Iteration-cap and iteration-missing fail-closed tests (LLD-011 Phase 2 slices 2.28-2.29).

E13 from LLD-011 §Edge cases: a doc missing the `> **Iteration:** N` field is
silently defaulted to 1. That defaults the post-commit iter-cap counter to 1
even when prior attestations exist for the doc-id, allowing infinite-loop
bypass. Fix: when prior attestations exist AND iteration field is missing,
fail-closed with explicit error.

Phase 3 slices (3.7-3.14) will introduce the 2-iter hard cap and
`--override-cap` flag; Phase 2 only addresses the iteration-missing bypass.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Slice 2.29 — iteration field missing AND no prior attestations → default to 1
# ---------------------------------------------------------------------------


def test_iteration_missing_no_prior_defaults_to_1(tmp_path, monkeypatch):
    """Slice 2.29 — no iter field + no priors → main() treats as iter-1, proceeds."""
    from cli import pdsa, spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text("# foo\n\nbody.\n")  # no Iteration: field

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    # No prior attestations

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)

    def fake_run_pdsa(doc_path):
        rep = pdsa.PdsaReport(doc_path=doc_path)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_run_pdsa)

    dispatched: list[str] = []
    monkeypatch.setattr(
        spec_review,
        "dispatch_subagent",
        lambda p: dispatched.append(p) or "not yaml",
    )

    spec_review.main(["docs/features/008-foo.md"])
    # Dispatch attempted (iter-1 default applied)
    assert len(dispatched) == 1


# ---------------------------------------------------------------------------
# Slice 2.28 — iteration field missing AND prior attestation exists → fail-closed
# ---------------------------------------------------------------------------


@pytest.mark.real_pdsa
def test_iteration_missing_with_prior_fails_closed(tmp_path, monkeypatch, capsys):
    """Slice 2.28 — missing Iteration: + iter-1 attestation present → exit 1 + E13."""
    from cli import pdsa, spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    # No Iteration: field — would silently default to 1
    (docs / "008-foo.md").write_text("# foo\n\nbody.\n")

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    # Prior iter-1 attestation exists
    (reviews / "008-foo-r1.review.yaml").write_text(
        'schema_version: "2.0"\noverall_verdict: pass\n'
    )

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)

    def fake_run_pdsa(doc_path):
        rep = pdsa.PdsaReport(doc_path=doc_path)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_run_pdsa)

    dispatched: list[str] = []
    monkeypatch.setattr(
        spec_review,
        "dispatch_subagent",
        lambda p: dispatched.append(p) or "",
    )

    rc = spec_review.main(["docs/features/008-foo.md"])
    err = capsys.readouterr().err
    assert rc == 1
    assert dispatched == [], "dispatch must NOT run when E13 fires"
    assert "iteration_missing_with_prior" in err or "E13" in err


# ---------------------------------------------------------------------------
# Slice 2.28 — explicit iteration field still allowed even when priors exist
# ---------------------------------------------------------------------------


def _fresh_doc(tmp_path, iteration: int) -> None:
    """Helper: write a feature doc with explicit Iteration: N + full Doc ID block."""
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "008-foo.md").write_text(
        f"# 008 Foo\n\n"
        f"> **Doc ID:** 008-foo\n"
        f"> **Date:** 2026-05-11\n"
        f"> **Status:** Draft\n"
        f"> **Iteration:** {iteration}\n\nbody.\n"
    )


def _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa):
    """Helper: stub PDSA pass + capture dispatch calls. Returns the `dispatched` list."""
    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)

    def fake_run_pdsa(doc_path):
        rep = pdsa.PdsaReport(doc_path=doc_path)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_run_pdsa)

    dispatched: list[str] = []
    monkeypatch.setattr(
        spec_review, "dispatch_subagent", lambda p: dispatched.append(p) or ""
    )
    return dispatched


# ---------------------------------------------------------------------------
# Slice 3.7 — iter-1 dispatches normally
# ---------------------------------------------------------------------------


def test_iter1_dispatches(tmp_path, monkeypatch):
    """Slice 3.7 — iter-1 doc with no prior attestation → dispatch proceeds."""
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 1)
    dispatched = _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa)

    spec_review.main(["docs/features/008-foo.md"])
    assert len(dispatched) == 1


# ---------------------------------------------------------------------------
# Slice 3.8 — iter-2 dispatches (delta-review entry point exists)
# ---------------------------------------------------------------------------


def test_iter2_dispatches(tmp_path, monkeypatch):
    """Slice 3.8 — iter-2 doc + iter-1 prior attestation → dispatch proceeds (delta path)."""
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 2)
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text(
        'schema_version: "2.0"\noverall_verdict: pass\n'
    )
    dispatched = _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa)

    spec_review.main(["docs/features/008-foo.md"])
    assert len(dispatched) == 1


# ---------------------------------------------------------------------------
# Slice 3.9 — iter-3+ refused without override
# ---------------------------------------------------------------------------


def test_iter3_blocked_without_override(tmp_path, monkeypatch, capsys):
    """Slice 3.9 — iter-3 (post-commit) refused without --override-cap."""
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 3)
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text('schema_version: "2.0"\n')
    (reviews / "008-foo-r2.review.yaml").write_text('schema_version: "2.0"\n')

    dispatched = _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa)

    rc = spec_review.main(["docs/features/008-foo.md"])
    assert rc == 1
    assert dispatched == []
    err = capsys.readouterr().err
    assert "iter_cap" in err or "iteration cap" in err.lower()


# ---------------------------------------------------------------------------
# Slice 3.10 / 3.12 — --override-cap parsed and allows iter-3
# ---------------------------------------------------------------------------


def test_override_cap_allows_iter3(tmp_path, monkeypatch):
    """Slices 3.10+3.12 — --override-cap parsed; iter-3 proceeds with flag."""
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 3)
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text('schema_version: "2.0"\n')
    (reviews / "008-foo-r2.review.yaml").write_text('schema_version: "2.0"\n')

    dispatched = _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa)

    spec_review.main(["docs/features/008-foo.md", "--override-cap"])
    assert len(dispatched) == 1


# ---------------------------------------------------------------------------
# Slice 3.14 — --override-cap is a no-op on iter < 3
# ---------------------------------------------------------------------------


def test_override_cap_logged_in_notes(tmp_path, monkeypatch):
    """Slice 3.13 — successful iter-3 override writes degraded-mode notes into attestation."""
    import yaml as yaml_mod
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 3)
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text('schema_version: "2.0"\n')
    (reviews / "008-foo-r2.review.yaml").write_text('schema_version: "2.0"\n')

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)

    def fake_run_pdsa(doc_path):
        rep = pdsa.PdsaReport(doc_path=doc_path)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_run_pdsa)

    # Return a minimal v1.0-shape attestation (current main() write path uses v1 schema)
    import hashlib
    doc_path = tmp_path / "docs" / "features" / "008-foo.md"
    doc_hash = hashlib.sha256(doc_path.read_bytes()).hexdigest()

    def fake_dispatch(prompt):
        return (
            'schema_version: "1.0"\n'
            "doc_subject:\n"
            "  path: docs/features/008-foo.md\n"
            f"  content_hash: sha256:{doc_hash}\n"
            "  iteration: 3\n"
            "reviewer:\n"
            '  identifier: "subagent:general-purpose+spec-review-v1"\n'
            '  invoked_at: "2026-05-11T00:00:00Z"\n'
            "  context_isolation: fresh_subagent\n"
            "gates:\n"
            "  completeness: {verdict: pass, findings: [], justification: 'all sections present'}\n"
            "  evidence: {verdict: pass, findings: [], justification: 'all claims cited'}\n"
            "  clarity: {verdict: pass, findings: [], justification: 'fresh reader can act'}\n"
            "  consistency: {verdict: pass, findings: [], justification: 'no contradictions'}\n"
            "overall_verdict: pass\n"
        )
    monkeypatch.setattr(spec_review, "dispatch_subagent", fake_dispatch)

    rc = spec_review.main(["docs/features/008-foo.md", "--override-cap"])
    assert rc == 0, "iter-3 with override should write attestation"

    out_path = reviews / "008-foo-r3.review.yaml"
    assert out_path.exists()
    written = yaml_mod.safe_load(out_path.read_text())
    notes = written.get("notes", [])
    if isinstance(notes, str):
        notes = [notes]
    assert any("degraded mode" in n for n in notes), f"notes missing degraded-mode entry: {notes}"
    assert any("--override-cap" in n for n in notes)


def test_override_cap_noop_on_iter1(tmp_path, monkeypatch):
    """Slice 3.14 — passing --override-cap on iter-1 is a no-op (allowed, ignored)."""
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 1)
    dispatched = _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa)

    spec_review.main(["docs/features/008-foo.md", "--override-cap"])
    assert len(dispatched) == 1


# ---------------------------------------------------------------------------
# Slice 3.11 — interview-gate signal (CLI surfaces "override requires confirmation" message)
# ---------------------------------------------------------------------------


def test_iter3_no_override_emits_actionable_error(tmp_path, monkeypatch, capsys):
    """Slice 3.11 — iter-3 without override surfaces guidance to retry with --override-cap.

    Interview-gate live-confirmation happens at skill-invocation time
    (AskUserQuestion). CLI-level signal: the error message names the flag
    so the skill/operator can re-dispatch with explicit consent.
    """
    from cli import pdsa, spec_review

    _fresh_doc(tmp_path, 4)
    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    for r in (1, 2, 3):
        (reviews / f"008-foo-r{r}.review.yaml").write_text('schema_version: "2.0"\n')

    _wire_stubs(monkeypatch, tmp_path, spec_review, pdsa)

    spec_review.main(["docs/features/008-foo.md"])
    err = capsys.readouterr().err
    assert "--override-cap" in err


def test_explicit_iteration_with_prior_proceeds(tmp_path, monkeypatch):
    """Slice 2.28 — explicit `Iteration: 2` + iter-1 prior → main() proceeds (no E13)."""
    from cli import pdsa, spec_review

    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "008-foo.md").write_text("# foo\n\n> **Iteration:** 2\n\nbody.\n")

    reviews = tmp_path / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "008-foo-r1.review.yaml").write_text(
        'schema_version: "2.0"\noverall_verdict: pass\n'
    )

    monkeypatch.setattr(spec_review, "_resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(pdsa, "_invoke_lint", lambda argv: 0)

    def fake_run_pdsa(doc_path):
        rep = pdsa.PdsaReport(doc_path=doc_path)
        rep.checks["lint"] = pdsa.CheckResult(passed=True, detail="ok")
        return rep
    monkeypatch.setattr(spec_review, "run_pdsa", fake_run_pdsa)

    dispatched: list[str] = []
    monkeypatch.setattr(
        spec_review,
        "dispatch_subagent",
        lambda p: dispatched.append(p) or "",
    )

    spec_review.main(["docs/features/008-foo.md"])
    # Dispatch attempted because Iteration: was present
    assert len(dispatched) == 1
