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
