"""Slice 11 — CI drift gate for spec-review schema + prompt-template ↔ canon.

Asserts value-equality between:
- skills/spec-review/attestation-schema-v1.0.json: severity / verdict /
  gate-name enums  ↔  canon §4.3 finding_gravity / §4.4 / §4.9
- skills/spec-review/prompt-template.md: severity copy  ↔  canon §4.3

No value change is intended in slice 11 (canon mirrors current schema);
the test fires if anyone edits one and forgets the other.
"""

from __future__ import annotations

import json
import re

from cli import _shared, vocabulary

_REPO = _shared._repo_root()
_SCHEMA_PATH = _REPO / "skills" / "spec-review" / "attestation-schema-v1.0.json"
_PROMPT_PATH = _REPO / "skills" / "spec-review" / "prompt-template.md"


def _load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_severity_matches_canon():
    schema = _load_schema()
    finding_props = schema["definitions"]["gate"]["properties"]["findings"]["items"]["properties"]
    sev_enum = tuple(finding_props["severity"]["enum"])
    assert sev_enum == vocabulary.SEVERITY_ENUMS["finding_gravity"], (
        f"schema severity enum {sev_enum} != canon §4.3 finding_gravity "
        f"{vocabulary.SEVERITY_ENUMS['finding_gravity']}"
    )


def test_schema_overall_verdict_matches_canon():
    schema = _load_schema()
    verdict_enum = frozenset(schema["properties"]["overall_verdict"]["enum"])
    assert verdict_enum == vocabulary.VERDICT_ENUM, (
        f"schema overall_verdict enum != canon §4.4 ({vocabulary.VERDICT_ENUM})"
    )


def test_schema_per_gate_verdict_matches_canon():
    schema = _load_schema()
    verdict_enum = frozenset(
        schema["definitions"]["gate"]["properties"]["verdict"]["enum"]
    )
    assert verdict_enum == vocabulary.VERDICT_ENUM, (
        f"schema per-gate verdict enum != canon §4.4 ({vocabulary.VERDICT_ENUM})"
    )


def test_schema_gate_names_match_canon():
    schema = _load_schema()
    required_gates = tuple(schema["properties"]["gates"]["required"])
    gate_props = tuple(schema["properties"]["gates"]["properties"].keys())
    canon = vocabulary.REVIEW_GATE_NAMES
    assert required_gates == canon, (
        f"schema gates.required {required_gates} != canon §4.9 {canon}"
    )
    assert gate_props == canon, (
        f"schema gates.properties keys {gate_props} != canon §4.9 {canon}"
    )


def test_prompt_template_severity_matches_canon():
    text = _PROMPT_PATH.read_text(encoding="utf-8")
    # Detect the severity-listing line: "severity: Critical | Important | Minor"
    m = re.search(r"severity:\s+([A-Za-z|\s]+?)$", text, re.MULTILINE)
    assert m, "prompt-template missing severity: line"
    listed = tuple(v.strip() for v in m.group(1).split("|") if v.strip())
    canon = vocabulary.SEVERITY_ENUMS["finding_gravity"]
    assert listed == canon, (
        f"prompt-template severity list {listed} != canon §4.3 {canon}"
    )
