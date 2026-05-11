"""Generate `cli/templates/vocabulary-default-1.md` from canon.

Reads `docs/design/controlled-vocabulary.md` (orchestra's own dogfooded
canon), strips orchestra-repo-specific content (Changelog, Replaces:
paragraphs, file-count snapshots), and writes the consumer-installable
template at `cli/templates/vocabulary-default-1.md`.

Run via `python -m scripts.generate_vocab_template` (or directly). CI
gate at `tests/test_template_drift.py` asserts the committed artifact
matches a fresh regeneration; drift fails the test.

Slice 8 of `docs/plans/2026-05-11-vocab-canon-migration.md`.
"""

from __future__ import annotations

import re
from pathlib import Path

from cli._shared import _repo_root


CANON_PATH = _repo_root() / "docs" / "design" / "controlled-vocabulary.md"
TEMPLATE_PATH = _repo_root() / "cli" / "templates" / "vocabulary-default-1.md"

_TEMPLATE_BANNER = (
    "<!--\n"
    "  GENERATED FILE — do not edit by hand.\n"
    "  Regenerate via: python -m scripts.generate_vocab_template\n"
    "  Canon source: docs/design/controlled-vocabulary.md\n"
    "  Template version: 1.0\n"
    "-->\n\n"
)


def generate(canon_text: str) -> str:
    """Strip orchestra-specific content; return consumer-template body."""
    out: list[str] = [_TEMPLATE_BANNER]

    in_changelog = False
    in_replaces_block = False
    for line in canon_text.splitlines(keepends=True):
        stripped = line.strip()

        # Stop emitting at the Changelog section heading.
        if stripped.startswith("## Changelog"):
            in_changelog = True
        if in_changelog:
            continue

        # Drop "Replaces:" paragraph lines (cite to orchestra files).
        if stripped.startswith("**Replaces:**"):
            in_replaces_block = True
            continue
        if in_replaces_block:
            # Replaces blocks are one paragraph; blank line ends them.
            if not stripped:
                in_replaces_block = False
            continue

        # Drop "**Extends:**" lines (orchestra-specific migration task ref).
        if stripped.startswith("**Extends:**"):
            continue

        # Drop "Known gap" paragraphs in §4.10 (orchestra-specific BUG-014 cite).
        if stripped.startswith("**Known gap.**"):
            continue

        # Replace orchestra-specific file-count snapshots with generic phrasing.
        line = re.sub(
            r"`\d+ \*\.review\.yaml files at LLD iter-\d+ draft time`",
            "`<all *.review.yaml files in docs/reviews/>`",
            line,
        )

        out.append(line)

    body = "".join(out).rstrip() + "\n"
    return body


def main() -> int:
    canon_text = CANON_PATH.read_text(encoding="utf-8")
    template_text = generate(canon_text)
    TEMPLATE_PATH.write_text(template_text, encoding="utf-8")
    print(f"wrote {TEMPLATE_PATH.relative_to(_repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
