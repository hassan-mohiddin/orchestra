"""Tests for cli.vocabulary — canon parser (BUG-016 slice 1.1-1.6).

Tests assert that public symbols match the canon at
`docs/design/controlled-vocabulary.md § 4.X` byte-for-byte.

Test enums live inline (not re-imported from cli.vocabulary) so the test acts
as an INDEPENDENT verifier of the parser — drift between parser code and
canon must surface.
"""

from __future__ import annotations

import re

import pytest


# ---------------------------------------------------------------------------
# §4.1 status_enum_per_doc_type
# ---------------------------------------------------------------------------


def test_status_enums_match_canon():
    from cli import vocabulary

    expected = {
        "feature": frozenset({
            "Draft", "Proposed", "Approved", "In Progress",
            "Implemented", "Verified", "Rejected", "Superseded",
        }),
        "bug": frozenset({
            "Investigating", "Root Cause Found", "In Progress",
            "Fix Applied", "Verified", "Rejected", "Superseded",
        }),
        "adr": frozenset({
            "Draft", "Proposed", "Approved", "Implemented",
            "Superseded", "Rejected",
        }),
        "postmortem": frozenset({
            "Draft", "Reviewed", "Action Items Tracked", "Closed",
            "Rejected", "Superseded",
        }),
        "runbook": frozenset({
            "Current", "Outdated", "Deprecated", "Rejected", "Superseded",
        }),
        "design": frozenset({
            "Current", "Outdated", "Deprecated", "Rejected", "Superseded",
        }),
    }
    assert vocabulary.STATUS_ENUMS == expected


# ---------------------------------------------------------------------------
# §4.2 canon_frozen_statuses
# ---------------------------------------------------------------------------


def test_canon_frozen_statuses_match_canon():
    from cli import vocabulary

    expected = frozenset({"Approved", "Implemented", "Verified", "Fix Applied", "Current"})
    assert vocabulary.CANON_FROZEN_STATUSES == expected


# ---------------------------------------------------------------------------
# §4.3 severity_enums
# ---------------------------------------------------------------------------


def test_severity_enums_match_canon():
    from cli import vocabulary

    expected = {
        "bug_severity": ("Critical", "High", "Medium", "Low"),
        "finding_gravity": ("Critical", "Important", "Minor"),
        "incident_severity": ("SEV1", "SEV2", "SEV3", "SEV4"),
        "page_priority": ("P1", "P2", "P3"),
    }
    assert vocabulary.SEVERITY_ENUMS == expected


# ---------------------------------------------------------------------------
# §4.4 verdict_enum
# ---------------------------------------------------------------------------


def test_verdict_enum_match_canon():
    from cli import vocabulary

    assert vocabulary.VERDICT_ENUM == frozenset({"pass", "conditional_pass", "fail"})


# ---------------------------------------------------------------------------
# §4.5 doc_type_enum
# ---------------------------------------------------------------------------


def test_doc_type_enum_match_canon():
    from cli import vocabulary

    expected = frozenset({
        "feature", "bug", "adr", "postmortem", "runbook",
        "design", "plan", "research", "investigation", "policy",
    })
    assert vocabulary.DOC_TYPE_ENUM == expected


# ---------------------------------------------------------------------------
# §4.6 refs_eligible_prefixes
# ---------------------------------------------------------------------------


def test_refs_eligible_prefixes_match_canon():
    from cli import vocabulary

    expected = (
        "docs/features/", "docs/bugs/", "docs/adr/",
        "docs/design/", "docs/postmortems/", "docs/runbooks/",
    )
    assert vocabulary.REFS_ELIGIBLE_PREFIXES == expected


# ---------------------------------------------------------------------------
# §4.7 allowed_attestation_path_prefixes
# ---------------------------------------------------------------------------


def test_allowed_attestation_path_prefixes_match_canon():
    from cli import vocabulary

    expected = (
        "docs/features/", "docs/bugs/", "docs/adr/",
        "docs/design/", "docs/postmortems/", "docs/runbooks/",
        "docs/plans/",
        "docs/archive/features/", "docs/archive/bugs/", "docs/archive/adr/",
        "docs/archive/design/", "docs/archive/postmortems/",
        "docs/archive/runbooks/", "docs/archive/plans/",
    )
    assert vocabulary.ALLOWED_ATTESTATION_PATH_PREFIXES == expected


# ---------------------------------------------------------------------------
# §4.8 required_sections_per_doc_type
# ---------------------------------------------------------------------------


def test_required_sections_keys_cover_all_doc_types():
    from cli import vocabulary

    # canon §4.8 covers all 10 doc types
    assert set(vocabulary.REQUIRED_SECTIONS.keys()) == {
        "feature", "bug", "adr", "postmortem", "runbook",
        "design", "plan", "research", "investigation", "policy",
    }


def test_required_sections_feature_has_changelog():
    from cli import vocabulary

    feature = vocabulary.REQUIRED_SECTIONS["feature"]
    assert "Changelog" in feature
    assert "Problem Statement" in feature
    assert "Success Criteria" in feature


def test_required_sections_bug_has_iteration_log():
    from cli import vocabulary

    bug = vocabulary.REQUIRED_SECTIONS["bug"]
    assert "Iteration Log" in bug
    assert "Regression Prevention" in bug


def test_required_sections_design_has_key_decisions():
    from cli import vocabulary

    design = vocabulary.REQUIRED_SECTIONS["design"]
    assert "Key Decisions" in design
    assert "Overview" in design


def test_required_sections_investigation_empty():
    from cli import vocabulary

    assert vocabulary.REQUIRED_SECTIONS["investigation"] == ()


# ---------------------------------------------------------------------------
# §4.9 review_gate_names
# ---------------------------------------------------------------------------


def test_review_gate_names_match_canon():
    from cli import vocabulary

    assert vocabulary.REVIEW_GATE_NAMES == ("completeness", "evidence", "clarity", "consistency")


# ---------------------------------------------------------------------------
# §4.10 filename_grammar_per_doc_type
# ---------------------------------------------------------------------------


def test_filename_grammar_feature():
    # Note: first-iter and supersession regexes share an ambiguity (`name` may
    # contain `-r\d+`); consumers (cli.lint § lint_doc_id_burn) disambiguate
    # by checking supersession first. Slice 1 just exposes the regex pair.
    from cli import vocabulary

    grammar = vocabulary.FILENAME_GRAMMAR["feature"]
    first = re.compile(grammar["first_iter"])
    sup = re.compile(grammar["supersession"])
    assert first.match("008-commit-skill.md")
    assert sup.match("008-commit-skill-r8.md")
    assert not first.match("BUG-014-foo.md")  # bug prefix should not match feature pattern


def test_filename_grammar_bug():
    from cli import vocabulary

    grammar = vocabulary.FILENAME_GRAMMAR["bug"]
    first = re.compile(grammar["first_iter"])
    sup = re.compile(grammar["supersession"])
    assert first.match("BUG-014-l4-bare-name.md")
    assert sup.match("BUG-014-l4-bare-name-r2.md")


def test_filename_grammar_design_bare_name():
    from cli import vocabulary

    grammar = vocabulary.FILENAME_GRAMMAR["design"]
    first = re.compile(grammar["first_iter"])
    sup = re.compile(grammar["supersession"])
    assert first.match("controlled-vocabulary.md")
    assert sup.match("orchestra-philosophy-r2.md")
    assert not first.match("BUG-014-foo.md")  # uppercase rejected


def test_filename_grammar_postmortem():
    from cli import vocabulary

    grammar = vocabulary.FILENAME_GRAMMAR["postmortem"]
    first = re.compile(grammar["first_iter"])
    sup = re.compile(grammar["supersession"])
    assert first.match("POSTMORTEM-2026-05-06-auth-leak.md")
    assert sup.match("POSTMORTEM-2026-05-06-auth-leak-r2.md")
    assert not first.match("001-postmortem.md")  # canon §4.10 single-pattern rule


def test_filename_grammar_runbook():
    from cli import vocabulary

    grammar = vocabulary.FILENAME_GRAMMAR["runbook"]
    first = re.compile(grammar["first_iter"])
    sup = re.compile(grammar["supersession"])
    assert first.match("RUNBOOK-celery-queue.md")
    assert sup.match("RUNBOOK-celery-queue-r2.md")


# ---------------------------------------------------------------------------
# §4.11 review_doc_filename_regex
# ---------------------------------------------------------------------------


def test_review_doc_filename_regex_matches_orchestra_yaml():
    from cli import vocabulary

    p = vocabulary.REVIEW_DOC_FILENAME_REGEX
    assert p.match("BUG-016-scattered-vocabulary-no-canon-r1.orchestra.review.yaml")
    assert p.match("011-spec-review-v2-r3.completeness.review.yaml")
    assert p.match("BUG-016-scattered-vocabulary-no-canon-r1.codex.review.md")
    assert not p.match("BUG-016-scattered-vocabulary-no-canon-r1.review.yaml")  # old form


# ---------------------------------------------------------------------------
# §4.12 terminal_state_suffix_conventions
# ---------------------------------------------------------------------------


def test_terminal_state_suffix_keys():
    from cli import vocabulary

    assert set(vocabulary.TERMINAL_STATE_SUFFIX.keys()) == {"Superseded", "Rejected", "Archived"}
    for entry in vocabulary.TERMINAL_STATE_SUFFIX.values():
        assert "metadata" in entry
        assert "filesystem_action" in entry


# ---------------------------------------------------------------------------
# §4.13 narrow_change_frontmatter_whitelist
# ---------------------------------------------------------------------------


def test_whitelist_frontmatter_fields_match_canon():
    from cli import vocabulary

    assert vocabulary.WHITELIST_FRONTMATTER_FIELDS == frozenset({
        "Status", "Iteration", "Superseded by",
    })


# ---------------------------------------------------------------------------
# Eager-load + module-level invariants
# ---------------------------------------------------------------------------


def test_module_exposes_13_public_symbols():
    from cli import vocabulary

    expected = {
        "STATUS_ENUMS", "CANON_FROZEN_STATUSES", "SEVERITY_ENUMS",
        "VERDICT_ENUM", "DOC_TYPE_ENUM", "REFS_ELIGIBLE_PREFIXES",
        "ALLOWED_ATTESTATION_PATH_PREFIXES", "REQUIRED_SECTIONS",
        "REVIEW_GATE_NAMES", "FILENAME_GRAMMAR", "REVIEW_DOC_FILENAME_REGEX",
        "TERMINAL_STATE_SUFFIX", "WHITELIST_FRONTMATTER_FIELDS",
    }
    public = {name for name in dir(vocabulary) if not name.startswith("_")
              and name.isupper() or (name[0].isupper() and "_" in name)}
    for sym in expected:
        assert hasattr(vocabulary, sym), f"missing public symbol: {sym}"


# ---------------------------------------------------------------------------
# §Failure modes (slice 1.5)
# ---------------------------------------------------------------------------


def _load_canon_with_replace(tmp_path, old: str, new: str):
    """Helper: copy canon into tmp_path, mutate, re-parse via fresh import."""
    import importlib
    import sys
    from cli import _shared

    src = _shared._repo_root() / "docs" / "design" / "controlled-vocabulary.md"
    body = src.read_text()
    if old:
        assert old in body, f"setup error: anchor {old!r} not found in canon"
        body = body.replace(old, new, 1)

    fake_root = tmp_path / "fake"
    (fake_root / ".claude-plugin").mkdir(parents=True)
    (fake_root / ".claude-plugin" / "plugin.json").write_text("{}")
    (fake_root / "docs" / "design").mkdir(parents=True)
    (fake_root / "docs" / "design" / "controlled-vocabulary.md").write_text(body)

    # Force vocabulary to read from fake_root by monkeypatching _repo_root
    sys.modules.pop("cli.vocabulary", None)
    from cli import vocabulary as _vmod  # noqa: F401  pre-import marker

    sys.modules.pop("cli.vocabulary", None)

    # Monkeypatch _shared._repo_root just for the next import
    real_repo_root = _shared._repo_root
    _shared._repo_root = lambda start=None: fake_root  # type: ignore[assignment]
    try:
        return importlib.import_module("cli.vocabulary")
    finally:
        _shared._repo_root = real_repo_root  # type: ignore[assignment]
        sys.modules.pop("cli.vocabulary", None)


def test_failure_subsection_missing(tmp_path):
    # Remove §4.1 header to simulate a missing subsection
    with pytest.raises(RuntimeError, match=r"vocabulary canon missing required subsection §4\.1"):
        _load_canon_with_replace(
            tmp_path,
            "### 4.1 `status_enum_per_doc_type`",
            "### 4.99 `removed`",
        )


def test_failure_canon_file_missing(tmp_path):
    import importlib
    import sys
    from cli import _shared

    fake_root = tmp_path / "noroot"
    (fake_root / ".claude-plugin").mkdir(parents=True)
    (fake_root / ".claude-plugin" / "plugin.json").write_text("{}")
    # NO docs/design/controlled-vocabulary.md

    sys.modules.pop("cli.vocabulary", None)
    real = _shared._repo_root
    _shared._repo_root = lambda start=None: fake_root  # type: ignore[assignment]
    try:
        with pytest.raises(RuntimeError, match=r"vocabulary canon not found"):
            importlib.import_module("cli.vocabulary")
    finally:
        _shared._repo_root = real  # type: ignore[assignment]
        sys.modules.pop("cli.vocabulary", None)


def test_failure_table_malformed(tmp_path):
    # Break §4.1 table: replace the header separator with a one-column row
    # Find one of the table rows and chop a column from it.
    old_row = "| `feature` | `Draft`, `Proposed`, `Approved`, `In Progress`, `Implemented`, `Verified`, `Rejected`, `Superseded` |"
    new_row = "| `feature` |"  # 2 cells instead of 3 (header has 2 cols actually — make it 1)
    # canon §4.1 table has 2 columns (`doc_type | values`); break to 1
    new_row = "| `feature` "
    with pytest.raises(RuntimeError, match=r"vocabulary canon §4\.1 table malformed"):
        _load_canon_with_replace(tmp_path, old_row, new_row)


def test_failure_illegal_character_in_value(tmp_path):
    # canon §4.2 is a fenced code block; insert an illegal char to one value
    old = "Approved, Implemented, Verified, Fix Applied, Current"
    new = "Approv|ed, Implemented, Verified, Fix Applied, Current"
    with pytest.raises(RuntimeError, match=r"vocabulary canon §4\.2 value .* contains illegal character"):
        _load_canon_with_replace(tmp_path, old, new)


def test_failure_header_renumbered_does_not_auto_discover(tmp_path):
    # Rename §4.1 to §4.99 — parser must NOT auto-discover; must raise on missing §4.1
    with pytest.raises(RuntimeError, match=r"vocabulary canon missing required subsection §4\.1"):
        _load_canon_with_replace(
            tmp_path,
            "### 4.1 `status_enum_per_doc_type`",
            "### 4.99 `status_enum_per_doc_type`",
        )
