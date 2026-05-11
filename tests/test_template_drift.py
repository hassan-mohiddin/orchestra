"""Slice 8 — CI drift gate for cli/templates/vocabulary-default-1.md.

Asserts that running `python -m scripts.generate_vocab_template` produces
byte-identical output to the committed `cli/templates/vocabulary-default-1.md`.
If the canon `docs/design/controlled-vocabulary.md` is edited without
regenerating the template, this test fails — surface the drift early.
"""

from __future__ import annotations

from cli._shared import _repo_root
from scripts.generate_vocab_template import CANON_PATH, generate


def test_vocabulary_template_matches_committed():
    canon_text = CANON_PATH.read_text(encoding="utf-8")
    expected = generate(canon_text)

    committed = (
        _repo_root() / "cli" / "templates" / "vocabulary-default-1.md"
    ).read_text(encoding="utf-8")

    assert committed == expected, (
        "vocabulary template drifted from canon. Regenerate via: "
        "`python -m scripts.generate_vocab_template`"
    )
