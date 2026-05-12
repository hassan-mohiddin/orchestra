"""Canon parser for orchestra controlled vocabulary.

Sole reader of `docs/design/controlled-vocabulary.md`. Eager-loads 13 public
symbols at module import time. Parse failure aborts the importing process —
no silent fallback (would re-create the drift problem this canon solves).

See `docs/design/controlled-vocabulary.md § Domain/Module/Endpoint Details`
(LLD iter-7).
"""

from __future__ import annotations

import re
from pathlib import Path

from cli._shared import _repo_root

# ---------------------------------------------------------------------------
# Canon file load
# ---------------------------------------------------------------------------

CANON_PATH: Path = _repo_root() / "docs" / "design" / "controlled-vocabulary.md"

if not CANON_PATH.is_file():
    raise RuntimeError(f"vocabulary canon not found at {CANON_PATH}")

_CANON: str = CANON_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Low-level extractors
# ---------------------------------------------------------------------------


_HEADER_RE = re.compile(r"^### (\d+\.\d+)\s+`[^`]+`.*$", re.MULTILINE)


def _section_body(num: str) -> str:
    """Return text between `### <num> `…`` and the next `### N.N` / `## ` header."""
    header_pat = re.compile(rf"^### {re.escape(num)}\s+`[^`]+`.*$", re.MULTILINE)
    m = header_pat.search(_CANON)
    if not m:
        raise RuntimeError(f"vocabulary canon missing required subsection §{num}")
    start = m.end()
    rest = _CANON[start:]
    next_match = re.search(r"^(### \d+\.\d+|## )", rest, re.MULTILINE)
    end = start + (next_match.start() if next_match else len(rest))
    return _CANON[start:end]


def _table_rows(body: str, num: str) -> list[list[str]]:
    """Parse first markdown table in body; return data rows (skip header+sep)."""
    lines = [ln for ln in body.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 3:
        raise RuntimeError(f"vocabulary canon §{num} table malformed: too few rows")
    header = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    expected_cols = len(header)
    rows: list[list[str]] = []
    for idx, ln in enumerate(lines[2:], start=2):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) != expected_cols:
            raise RuntimeError(
                f"vocabulary canon §{num} table malformed at row {idx}: "
                f"expected {expected_cols} columns, got {len(cells)}"
            )
        rows.append(cells)
    return rows


def _fence_body(body: str, num: str) -> str:
    """Return contents of the first fenced code block in body."""
    m = re.search(r"```[^\n]*\n(.*?)\n```", body, re.DOTALL)
    if not m:
        raise RuntimeError(f"vocabulary canon §{num} fenced code block missing")
    return m.group(1).strip()


def _strip_backticks(s: str) -> str:
    s = s.strip()
    if s.startswith("`") and s.endswith("`"):
        return s[1:-1]
    return s


def _csv_values(text: str, num: str) -> tuple[str, ...]:
    parts: list[str] = []
    for raw in text.split(","):
        v = raw.strip()
        if "|" in v or "\t" in v:
            raise RuntimeError(
                f"vocabulary canon §{num} value {v!r} contains illegal character"
            )
        parts.append(v)
    return tuple(parts)


def _backtick_csv_values(text: str, num: str) -> tuple[str, ...]:
    """Extract every `…` group in text; check each for illegal chars."""
    out: list[str] = []
    for m in re.finditer(r"`([^`]+)`", text):
        v = m.group(1)
        if "|" in v or "\t" in v:
            raise RuntimeError(
                f"vocabulary canon §{num} value {v!r} contains illegal character"
            )
        out.append(v)
    if not out:
        raise RuntimeError(f"vocabulary canon §{num} table malformed: no backtick values")
    return tuple(out)


# ---------------------------------------------------------------------------
# §4.1 status_enum_per_doc_type
# ---------------------------------------------------------------------------


def _parse_status_enums() -> dict[str, frozenset[str]]:
    body = _section_body("4.1")
    out: dict[str, frozenset[str]] = {}
    for cells in _table_rows(body, "4.1"):
        doc_type = _strip_backticks(cells[0])
        values = _backtick_csv_values(cells[1], "4.1")
        out[doc_type] = frozenset(values)
    return out


STATUS_ENUMS: dict[str, frozenset[str]] = _parse_status_enums()


# ---------------------------------------------------------------------------
# §4.2 canon_frozen_statuses
# ---------------------------------------------------------------------------


def _parse_canon_frozen_statuses() -> frozenset[str]:
    body = _section_body("4.2")
    fence = _fence_body(body, "4.2")
    return frozenset(_csv_values(fence, "4.2"))


CANON_FROZEN_STATUSES: frozenset[str] = _parse_canon_frozen_statuses()


# ---------------------------------------------------------------------------
# §4.3 severity_enums (four named axes)
# ---------------------------------------------------------------------------


def _parse_severity_enums() -> dict[str, tuple[str, ...]]:
    body = _section_body("4.3")
    out: dict[str, tuple[str, ...]] = {}
    for cells in _table_rows(body, "4.3"):
        axis = _strip_backticks(cells[0])
        # Skip non-data rows (table header explanations have been filtered already)
        if not axis or axis.lower().startswith("axis name"):
            continue
        values = _backtick_csv_values(cells[1], "4.3")
        out[axis] = values
    return out


SEVERITY_ENUMS: dict[str, tuple[str, ...]] = _parse_severity_enums()


# ---------------------------------------------------------------------------
# §4.4 verdict_enum
# ---------------------------------------------------------------------------


def _parse_verdict_enum() -> frozenset[str]:
    body = _section_body("4.4")
    return frozenset(_csv_values(_fence_body(body, "4.4"), "4.4"))


VERDICT_ENUM: frozenset[str] = _parse_verdict_enum()


# ---------------------------------------------------------------------------
# §4.5 doc_type_enum
# ---------------------------------------------------------------------------


def _parse_doc_type_enum() -> frozenset[str]:
    body = _section_body("4.5")
    return frozenset(_csv_values(_fence_body(body, "4.5"), "4.5"))


DOC_TYPE_ENUM: frozenset[str] = _parse_doc_type_enum()


# ---------------------------------------------------------------------------
# §4.6 refs_eligible_prefixes
# ---------------------------------------------------------------------------


def _parse_path_list(num: str) -> tuple[str, ...]:
    body = _section_body(num)
    fence = _fence_body(body, num)
    out: list[str] = []
    for raw in fence.splitlines():
        v = raw.strip()
        if not v:
            continue
        if "|" in v or "\t" in v:
            raise RuntimeError(
                f"vocabulary canon §{num} value {v!r} contains illegal character"
            )
        out.append(v)
    return tuple(out)


REFS_ELIGIBLE_PREFIXES: tuple[str, ...] = _parse_path_list("4.6")


# ---------------------------------------------------------------------------
# §4.7 allowed_attestation_path_prefixes
# ---------------------------------------------------------------------------


ALLOWED_ATTESTATION_PATH_PREFIXES: tuple[str, ...] = _parse_path_list("4.7")


# ---------------------------------------------------------------------------
# §4.8 required_sections_per_doc_type
# ---------------------------------------------------------------------------


_INVESTIGATION_NULL_MARKER = "(none"


def _split_top_level_commas(raw: str) -> tuple[str, ...]:
    """Split on commas that are NOT inside parens.

    Canon §4.8 plan row contains `Header (goal, architecture, tech stack, LLD
    reference)` — the inner commas must not split the section name.
    """
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in raw:
        if ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth = max(depth - 1, 0)
            cur.append(ch)
        elif ch == "," and depth == 0:
            piece = "".join(cur).strip()
            if piece:
                parts.append(piece)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        parts.append(tail)
    return tuple(parts)


def _parse_required_sections() -> dict[str, tuple[str, ...]]:
    body = _section_body("4.8")
    out: dict[str, tuple[str, ...]] = {}
    for cells in _table_rows(body, "4.8"):
        doc_type = _strip_backticks(cells[0])
        raw = cells[1]
        if raw.lstrip().startswith(_INVESTIGATION_NULL_MARKER):
            out[doc_type] = ()
            continue
        sections = _split_top_level_commas(raw)
        for sec in sections:
            if "|" in sec or "\t" in sec:
                raise RuntimeError(
                    f"vocabulary canon §4.8 value {sec!r} contains illegal character"
                )
        out[doc_type] = sections
    return out


REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = _parse_required_sections()


# ---------------------------------------------------------------------------
# §4.9 review_gate_names
# ---------------------------------------------------------------------------


def _parse_review_gate_names() -> tuple[str, ...]:
    body = _section_body("4.9")
    return _csv_values(_fence_body(body, "4.9"), "4.9")


REVIEW_GATE_NAMES: tuple[str, ...] = _parse_review_gate_names()


# BUG-018 — v2.0+ attestation (LLD-011 spec-review v2) uses sub-judge ids as
# the `gate` keyword on `Addresses:` lines. Hardcoded here as a constant
# while the canon §4.9 v2 sub-section is added in the same BUG-018 ship
# (canon-frozen edit lands via --no-verify in the canon edit commit). Drift
# from canon §4.9 v2 sub-section will be caught by the dedicated drift gate
# once the canon edit lands.
REVIEW_SUB_JUDGE_IDS: tuple[str, ...] = (
    "structure",
    "semantic",
    "gate-compliance",
    "adversarial",
    "repo-context",
    "architectural-fit",
)


# ---------------------------------------------------------------------------
# §4.10 filename_grammar_per_doc_type
# ---------------------------------------------------------------------------


_FILENAME_PLACEHOLDERS: tuple[tuple[str, str], ...] = (
    # Order matters: longer tokens first so `NNN` doesn't pre-match `N` inside.
    ("YYYY-MM-DD", r"\d{4}-\d{2}-\d{2}"),
    ("NNN", r"\d{3}"),
    ("-rN", r"-r\d+"),
    ("name", r"[a-z][a-z0-9-]*"),
)


def _template_to_regex(tpl: str) -> str:
    """Translate canon pattern template (e.g. `NNN-name.md`) to anchored regex."""
    sentinels: list[tuple[str, str]] = []
    s = tpl
    for i, (token, regex) in enumerate(_FILENAME_PLACEHOLDERS):
        sentinel = f"\x00{i}\x00"
        s = s.replace(token, sentinel)
        sentinels.append((sentinel, regex))
    s = re.escape(s)
    for sentinel, regex in sentinels:
        s = s.replace(re.escape(sentinel), regex)
    return f"^{s}$"


def _parse_filename_grammar() -> dict[str, dict[str, str]]:
    body = _section_body("4.10")
    out: dict[str, dict[str, str]] = {}
    for cells in _table_rows(body, "4.10"):
        doc_type = _strip_backticks(cells[0])
        first_raw = cells[1]
        sup_raw = cells[2]
        first_match = re.search(r"`([^`]+)`", first_raw)
        sup_match = re.search(r"`([^`]+)`", sup_raw)
        entry: dict[str, str] = {}
        if first_match:
            entry["first_iter"] = _template_to_regex(first_match.group(1))
        if sup_match:
            entry["supersession"] = _template_to_regex(sup_match.group(1))
        out[doc_type] = entry
    return out


FILENAME_GRAMMAR: dict[str, dict[str, str]] = _parse_filename_grammar()


# ---------------------------------------------------------------------------
# §4.11 review_doc_filename_regex
# ---------------------------------------------------------------------------


_REVIEW_PLACEHOLDERS: tuple[tuple[str, str], ...] = (
    # <doc-id> is the doc's filename stem (no `.md`) per canon §4.11 grammar
    # table — stems may include `.` (e.g. `v1.4` in legacy postmortem names).
    ("<doc-id>", r"[A-Za-z0-9][A-Za-z0-9.\-]*"),
    ("<N>", r"\d+"),
    ("<judge>", r"[a-z][a-z0-9-]*"),
    ("<ext>", r"(?:yaml|md)"),
)


def _parse_review_doc_filename_regex() -> re.Pattern[str]:
    body = _section_body("4.11")
    code = _fence_body(body, "4.11")
    if not code.startswith("docs/reviews/"):
        raise RuntimeError(
            f"vocabulary canon §4.11 unexpected pattern: {code!r}"
        )
    fname_tpl = code[len("docs/reviews/"):]
    s = fname_tpl
    sentinels: list[tuple[str, str]] = []
    for i, (token, regex) in enumerate(_REVIEW_PLACEHOLDERS):
        sentinel = f"\x00R{i}R\x00"
        s = s.replace(token, sentinel)
        sentinels.append((sentinel, regex))
    s = re.escape(s)
    for sentinel, regex in sentinels:
        s = s.replace(re.escape(sentinel), regex)
    return re.compile(f"^{s}$")


REVIEW_DOC_FILENAME_REGEX: re.Pattern[str] = _parse_review_doc_filename_regex()


# ---------------------------------------------------------------------------
# §4.12 terminal_state_suffix_conventions
# ---------------------------------------------------------------------------


def _parse_terminal_state_suffix() -> dict[str, dict[str, str]]:
    body = _section_body("4.12")
    out: dict[str, dict[str, str]] = {}
    for cells in _table_rows(body, "4.12"):
        state = _strip_backticks(cells[0])
        out[state] = {
            "metadata": cells[1],
            "filesystem_action": cells[2],
        }
    return out


TERMINAL_STATE_SUFFIX: dict[str, dict[str, str]] = _parse_terminal_state_suffix()


# ---------------------------------------------------------------------------
# §4.13 narrow_change_frontmatter_whitelist
# ---------------------------------------------------------------------------


def _parse_whitelist_frontmatter_fields() -> frozenset[str]:
    body = _section_body("4.13")
    return frozenset(_csv_values(_fence_body(body, "4.13"), "4.13"))


WHITELIST_FRONTMATTER_FIELDS: frozenset[str] = _parse_whitelist_frontmatter_fields()


__all__ = [
    "STATUS_ENUMS",
    "CANON_FROZEN_STATUSES",
    "SEVERITY_ENUMS",
    "VERDICT_ENUM",
    "DOC_TYPE_ENUM",
    "REFS_ELIGIBLE_PREFIXES",
    "ALLOWED_ATTESTATION_PATH_PREFIXES",
    "REQUIRED_SECTIONS",
    "REVIEW_GATE_NAMES",
    "REVIEW_SUB_JUDGE_IDS",
    "FILENAME_GRAMMAR",
    "REVIEW_DOC_FILENAME_REGEX",
    "TERMINAL_STATE_SUFFIX",
    "WHITELIST_FRONTMATTER_FIELDS",
    "CANON_PATH",
]
