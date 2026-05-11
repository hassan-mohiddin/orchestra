"""Failure-attestation primitives (LLD-011 Phase 3 slices 3.15-3.22).

Failure-attestation invariant (LLD-011 §Aggregator): every dispatch attempt
produces an attestation file, even when no findings_aggregated entry exists
or sub-judges never returned. This module builds those attestations and the
output-quarantine helpers that flag tool_scope_violation.

Failure reasons (LLD-011 §Edge cases):
  - E11 prompt_missing          — sub-judge prompt.md absent at dispatch time
  - E17 model_unavailable       — optional sub-judge upstream provider error (soft-fail)
  - E17b model_unavailable_mandatory — mandatory sub-judge provider error (hard-fail)
  - E18 doc_disappeared         — doc removed between dispatch and write
  - E20 attestation_tampered    — iter-2 load detected integrity hash mismatch
  - E21 tool_scope_violation    — sub-judge output cited path outside its tool scope
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from cli.spec_review import MANDATORY_SUBJUDGES


def build_failure_attestation(
    *,
    schema_version: str = "2.0",
    doc_path: str,
    iteration: int,
    reason: str,
    failed_sub_judges: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict:
    """Construct a minimal-but-schema-conforming v2 attestation reflecting a hard failure.

    Used when:
      - The whole dispatch attempt failed before any sub-judge could complete.
      - A mandatory sub-judge failed (overall_verdict forced to fail).
      - An iter-2 integrity-verify failed (cannot proceed).

    Per LLD-011 §Failure-attestation invariant the attestation is still written
    (not skipped) so audit trail is preserved.
    """
    failed = failed_sub_judges or []
    mandatory_failures = sorted(set(failed) & MANDATORY_SUBJUDGES)
    return {
        "schema_version": schema_version,
        "doc_subject": {
            "path": doc_path,
            "iteration": iteration,
        },
        "sub_judges": [],
        "findings_aggregated": [],
        "overall_verdict": "fail",
        "overall_verdict_basis": {
            "worst_sub_judge_verdict": "fail",
            "excluded_sub_judges": [],
            "mandatory_failures": mandatory_failures,
            "reason": reason,
        },
        "notes": list(notes) if notes else [],
    }


# ---------------------------------------------------------------------------
# Output-quarantine for E21 tool_scope_violation (slices 3.20-3.22)
# ---------------------------------------------------------------------------


# Heuristic regex set. Conservative — false-positive bias is preferred over
# false-negative for security findings. References LLD-011 §Security S6.
# Expanded post-iter-1 adversarial review (fix #3) to cover Stripe, GitHub,
# GitLab, JWT, OAuth refresh tokens, DB connection URIs, generic high-entropy.
_SUSPICIOUS_PATH_PATTERNS: list[re.Pattern[str]] = [
    # Filesystem secret paths
    re.compile(r"\.env(?:\.[a-z]+)?\b", re.IGNORECASE),
    re.compile(r"\bsecrets?/", re.IGNORECASE),
    re.compile(r"id_(?:rsa|ed25519|ecdsa|dsa)\b", re.IGNORECASE),
    re.compile(r"\.aws/credentials\b", re.IGNORECASE),
    re.compile(r"\.ssh/", re.IGNORECASE),
    re.compile(r"\.netrc\b", re.IGNORECASE),
    re.compile(r"\.pgpass\b", re.IGNORECASE),

    # Cloud provider keys
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),  # AWS temp session key id
    re.compile(r"\b[A-Za-z0-9/+]{40}\b(?=.*aws)", re.IGNORECASE),  # AWS secret near 'aws'

    # GitHub
    re.compile(r"\bgh[ps]_[A-Za-z0-9]{36,}\b"),  # personal/access tokens
    re.compile(r"\bgho_[A-Za-z0-9]{36,}\b"),  # OAuth
    re.compile(r"\bghu_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bghr_[A-Za-z0-9]{36,}\b"),

    # GitLab
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bglft-[A-Za-z0-9_-]{20,}\b"),

    # Stripe
    re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{24,}\b"),
    re.compile(r"\bpk_(?:live|test)_[A-Za-z0-9]{24,}\b"),
    re.compile(r"\brk_(?:live|test)_[A-Za-z0-9]{24,}\b"),

    # Slack
    re.compile(r"\bxox[abprso]-[A-Za-z0-9-]{10,}\b"),

    # Generic OpenAI / Anthropic style
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),

    # JWT
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),

    # OAuth-style Bearer + generic refresh tokens
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b"),
    re.compile(r"\brefresh_token['\":=]\s*['\"]?[A-Za-z0-9._-]{20,}", re.IGNORECASE),

    # DB connection URIs with embedded credentials
    re.compile(r"\b(?:postgres|postgresql|mysql|mongodb|redis)://[^\s:@/]+:[^\s@]+@"),

    # PEM private key markers
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
]


@dataclass
class QuarantineResult:
    """Output-quarantine outcome.

    redacted_output: input text with violations replaced by `[REDACTED:<pattern>]`.
    violations: list of patterns matched. Empty list = clean output.
    """

    redacted_output: str
    violations: list[str]

    @property
    def clean(self) -> bool:
        return not self.violations


def quarantine_output(output_text: str) -> QuarantineResult:
    """Scan sub-judge output for credential / out-of-scope path leakage (E21).

    Per LLD-011 slice 3.20: regex-scan output. Each hit → replace with redacted
    marker AND record in violations. Caller maps violations to soft-fail or
    hard-fail based on whether the sub-judge is mandatory.
    """
    redacted = output_text
    violations: list[str] = []
    for pat in _SUSPICIOUS_PATH_PATTERNS:
        if pat.search(redacted):
            violations.append(pat.pattern)
            # Escape the pattern when used as a replacement string — backslashes
            # in the regex source (\b, \s, \d) would otherwise be interpreted as
            # backrefs by re.sub and raise re.error("bad escape").
            replacement = "[REDACTED:" + re.escape(pat.pattern) + "]"
            redacted = pat.sub(replacement, redacted)
    return QuarantineResult(redacted_output=redacted, violations=violations)


def quarantine_severity_for(judge_id: str) -> str:
    """Slice 3.21-3.22 — map quarantine event severity to soft / hard fail.

    Mandatory sub-judges (semantic, adversarial) → hard-fail status="error".
    Optional sub-judges → soft-fail status="error"; excluded from aggregation
    but does not block overall_verdict.
    """
    if judge_id in MANDATORY_SUBJUDGES:
        return "hard_fail"
    return "soft_fail"
