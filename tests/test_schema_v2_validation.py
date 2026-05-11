"""Schema v2.0 attestation validation tests (LLD-011 Phase 1 slices 1.1-1.5).

Schema lives at skills/spec-review/attestation-schema-v2.0.json (JSON-Schema draft-07).
Validation is performed by jsonschema.validate() in cli.spec_review at write time and at
iter-2 load time. These tests exercise the schema in isolation.
"""

import json
from pathlib import Path

import jsonschema
import pytest


SCHEMA_V2_PATH = (
    Path(__file__).parent.parent
    / "skills"
    / "spec-review"
    / "attestation-schema-v2.0.json"
)


def _load_schema_v2() -> dict:
    """Read the v2.0 JSON Schema file from disk."""
    return json.loads(SCHEMA_V2_PATH.read_text())


def _minimal_conforming_attestation() -> dict:
    """Build a minimal v2.0 attestation that satisfies every required field.

    Uses 2 mandatory sub-judges (semantic + adversarial) with empty findings +
    required justification. All other top-level required fields populated.
    """
    return {
        "schema_version": "2.0",
        "doc_subject": {
            "path": "docs/features/example.md",
            "content_hash": "sha256:" + "a" * 64,
            "iter_commit_sha": "a" * 40,
            "iter_blob_sha": "b" * 40,
            "iteration": 1,
        },
        "peer_judge": {
            "id": "orchestra:spec-reviewer",
            "invoked_at": "2026-05-11T12:34:56Z",
            "context_isolation": "fresh_subagent_per_subjudge",
        },
        "sub_judges": [
            {
                "id": "semantic",
                "model": "claude-opus-4-7",
                "mandatory": True,
                "rubric_version": "semantic-v1",
                "status": "completed",
                "verdict": "pass",
                "findings": [],
                "justification": "minimal valid fixture — no findings raised",
            },
            {
                "id": "adversarial",
                "model": "claude-opus-4-7",
                "mandatory": True,
                "rubric_version": "adversarial-v1",
                "status": "completed",
                "verdict": "pass",
                "findings": [],
                "justification": "minimal valid fixture — no findings raised",
            },
        ],
        "findings_aggregated": [],
        "overall_verdict": "pass",
        "overall_verdict_basis": {
            "worst_sub_judge_verdict": "pass",
            "excluded_sub_judges": [],
            "mandatory_failures": [],
            "reason": None,
        },
        "attestation_integrity_hash": "sha256:" + "c" * 64,
    }


def test_minimal_conforming():
    """Schema v2.0 accepts a minimal valid attestation with all required fields populated.

    Slice 1.1 acceptance: the schema file exists at the expected path and validates a
    hand-constructed minimal payload without raising.
    """
    schema = _load_schema_v2()
    jsonschema.validate(_minimal_conforming_attestation(), schema)


def test_rejects_missing_sub_judges():
    """Slice 1.2 — schema rejects attestation missing the required `sub_judges` field."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    del payload["sub_judges"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_invalid_severity():
    """Slice 1.3 — schema rejects findings with severity outside the Critical|Important|Minor enum."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["findings_aggregated"] = [
        {
            "severity": "Catastrophic",
            "location": "Body § Intro",
            "problem": "fabricated severity",
            "raised_by": ["semantic"],
        }
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_invalid_verdict():
    """Slice 1.4 — schema rejects overall_verdict outside pass|conditional_pass|fail."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["overall_verdict"] = "maybe"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_version_pinning():
    """Slice 1.5 — schema rejects any schema_version other than '2.0'."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["schema_version"] = "1.0"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_scope_field_instance_valid():
    """Slice 2.13 — finding with scope=instance validates."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["findings_aggregated"] = [
        {
            "severity": "Important",
            "location": "Body § X",
            "problem": "p",
            "scope": "instance",
            "raised_by": ["semantic"],
        }
    ]
    jsonschema.validate(payload, schema)


def test_scope_field_class_valid():
    """Slice 2.13 — finding with scope=class validates."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["findings_aggregated"] = [
        {
            "severity": "Important",
            "location": "Body § Y",
            "problem": "p2",
            "scope": "class",
            "raised_by": ["adversarial"],
        }
    ]
    jsonschema.validate(payload, schema)


def test_scope_field_invalid_value_rejected():
    """Slice 2.13 — schema rejects scope outside instance|class enum."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["findings_aggregated"] = [
        {
            "severity": "Important",
            "location": "Body § Z",
            "problem": "p3",
            "scope": "global",
            "raised_by": ["semantic"],
        }
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_scope_field_required_on_findings():
    """Slice 2.13 — finding without scope field is rejected."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["findings_aggregated"] = [
        {
            "severity": "Important",
            "location": "Body § A",
            "problem": "no scope",
            "raised_by": ["semantic"],
        }
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_version_pinning_rejects_future():
    """Slice 1.5 — schema also rejects forward versions like '3.0' (const, not minimum)."""
    schema = _load_schema_v2()
    payload = _minimal_conforming_attestation()
    payload["schema_version"] = "3.0"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
