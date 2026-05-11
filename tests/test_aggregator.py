"""Mechanical aggregator tests for spec-review v2 (LLD-011 Phase 1 slices 1.11-1.18).

Aggregator merges findings across sub-judges, dedups by (location, problem_hash),
unions raised_by, takes max severity. Pure Python, no LLM call, deterministic.
"""

from cli.aggregator import aggregate_findings, fuzzy_hash, normalize_location, sanitize_location


def test_sanitize_location_passes_legit():
    """Fix #4 — well-formed `Body § Intro` and `line 42` pass through unchanged."""
    assert sanitize_location("Body § Intro") == "Body § Intro"
    assert sanitize_location("line 42") == "line 42"


def test_sanitize_location_rejects_etc_passwd():
    """Fix #4 — `/etc/...` absolute system path triggers REJECTED-LOCATION."""
    assert sanitize_location("Body § /etc/passwd:1") == "[REJECTED-LOCATION]"


def test_sanitize_location_rejects_parent_escape():
    """Fix #4 — `..`-traversal in location is rejected."""
    assert sanitize_location("Body § ../../foo") == "[REJECTED-LOCATION]"


def test_sanitize_location_rejects_html():
    """Fix #4 — HTML/XML tags in location are rejected (chat-report injection guard)."""
    assert sanitize_location("Body § <script>x</script>") == "[REJECTED-LOCATION]"


def test_sanitize_location_rejects_javascript_url():
    """Fix #4 — javascript: URL scheme in location is rejected."""
    assert sanitize_location("Body § javascript:alert(1)") == "[REJECTED-LOCATION]"


def test_sanitize_location_rejects_control_char():
    """Fix #4 — control characters in location are rejected."""
    assert sanitize_location("Body § foo\x01bar") == "[REJECTED-LOCATION]"


def _sj(id_: str, findings: list[dict] | None = None, status: str = "completed") -> dict:
    """Build a minimal sub_judge dict for aggregator tests."""
    return {
        "id": id_,
        "status": status,
        "findings": findings or [],
    }


def _f(
    severity: str, location: str, problem: str, scope: str | None = None
) -> dict:
    f: dict = {
        "severity": severity,
        "location": location,
        "problem": problem,
        "raised_by": [],
    }
    if scope:
        f["scope"] = scope
    return f


def test_empty_input():
    """Slice 1.11 — aggregator returns empty list when given no sub-judges."""
    assert aggregate_findings([]) == []


def test_empty_findings_per_judge():
    """Slice 1.11 — aggregator returns empty list when all sub-judges have no findings."""
    sj_list = [_sj("structure"), _sj("semantic")]
    assert aggregate_findings(sj_list) == []


def test_single_subjudge_passthrough():
    """Slice 1.12 — single sub-judge with one finding produces one aggregated finding."""
    sj_list = [_sj("structure", [_f("Important", "Body § Intro", "missing section")])]
    out = aggregate_findings(sj_list)
    assert len(out) == 1
    assert out[0]["severity"] == "Important"
    assert out[0]["location"] == "Body § Intro"
    assert out[0]["raised_by"] == ["structure"]


def test_dedup_same_location_and_text():
    """Slice 1.13 — two sub-judges raise the same finding → one aggregated entry."""
    f1 = _f("Important", "Body § Intro", "missing section header")
    f2 = _f("Important", "Body § Intro", "missing section header")
    sj_list = [_sj("structure", [f1]), _sj("semantic", [f2])]
    out = aggregate_findings(sj_list)
    assert len(out) == 1
    assert sorted(out[0]["raised_by"]) == ["semantic", "structure"]


def test_severity_union_max():
    """Slice 1.14 — when two sub-judges raise same finding with different severities, max wins."""
    f1 = _f("Important", "Body § Intro", "missing section header")
    f2 = _f("Critical", "Body § Intro", "missing section header")
    sj_list = [_sj("structure", [f1]), _sj("semantic", [f2])]
    out = aggregate_findings(sj_list)
    assert len(out) == 1
    assert out[0]["severity"] == "Critical"


def test_raised_by_union_sorted_unique():
    """Slice 1.15 — raised_by is a sorted unique list (set semantics)."""
    f1 = _f("Important", "Body § Intro", "missing section header")
    f2 = _f("Important", "Body § Intro", "missing section header")
    f3 = _f("Important", "Body § Intro", "missing section header")
    sj_list = [
        _sj("semantic", [f1]),
        _sj("adversarial", [f2]),
        _sj("structure", [f3]),
    ]
    out = aggregate_findings(sj_list)
    assert out[0]["raised_by"] == ["adversarial", "semantic", "structure"]


def test_output_ordered_by_location():
    """Slice 1.16 — aggregated findings emit in location order."""
    sj_list = [
        _sj(
            "structure",
            [
                _f("Important", "Z § last", "z section issue"),
                _f("Important", "A § first", "a section issue"),
                _f("Important", "M § middle", "m section issue"),
            ],
        )
    ]
    out = aggregate_findings(sj_list)
    locs = [f["location"] for f in out]
    assert locs == ["A § first", "M § middle", "Z § last"]


def test_normalize_location_whitespace():
    """Slice 1.17 — normalize_location handles inconsistent whitespace and case."""
    assert normalize_location("Body § Intro") == normalize_location("  body § intro  ")
    assert normalize_location("Body §  Intro") == normalize_location("Body § Intro")
    assert normalize_location("Body§Intro") == normalize_location("Body § Intro")


def test_normalize_location_line_form():
    """Slice 1.17 — line N form normalized to lowercase."""
    assert normalize_location("Line 142") == normalize_location("line 142")


def test_fuzzy_hash_stable_on_case_and_word_order():
    """Slice 1.18 — fuzzy_hash gives the same hash for semantically same problem text."""
    # Case-insensitive
    assert fuzzy_hash("Missing section header") == fuzzy_hash("missing section header")
    # Word-order-insensitive (stopword strip + sort)
    assert fuzzy_hash("The section header is missing") == fuzzy_hash(
        "Section header missing"
    )


def test_fuzzy_hash_differs_on_different_content():
    """Slice 1.18 — fuzzy_hash differs when significant tokens differ."""
    assert fuzzy_hash("Missing section header") != fuzzy_hash("Wrong section header")


def test_skips_failed_subjudge():
    """Slice 1.11 boundary — failed sub-judge's findings excluded from aggregation."""
    sj_list = [
        _sj("structure", [_f("Important", "A § x", "from completed")]),
        _sj(
            "semantic",
            [_f("Critical", "B § y", "from failed should be skipped")],
            status="error",
        ),
    ]
    out = aggregate_findings(sj_list)
    assert len(out) == 1
    assert out[0]["location"] == "A § x"


def test_scope_preserved_through_merge():
    """Slice 1.13 boundary — scope tag survives merge; first sub-judge (by sorted id) wins."""
    f1 = _f("Important", "Body § Intro", "missing X", scope="class")
    f2 = _f("Important", "Body § Intro", "missing X", scope="instance")
    sj_list = [_sj("structure", [f1]), _sj("semantic", [f2])]
    out = aggregate_findings(sj_list)
    # semantic < structure when sorted alphabetically → semantic's f2 (instance) wins
    # Actually: 'semantic' < 'structure' alphabetically. semantic carries scope=instance.
    assert out[0]["scope"] == "instance"
