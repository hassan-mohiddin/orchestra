"""Orchestra mkdocs hook — synthesize Material theme tags from doc metadata blocks.

Extracts `Status:` field from orchestra metadata block (no front-matter retrofit
required) and prepends a YAML front-matter `tags:` array so the Material `tags`
plugin can render status-filtered views.

Registered in mkdocs.yml under `hooks:`.
"""

from __future__ import annotations

import re

METADATA_STATUS_RE = re.compile(
    r"^>\s+\*\*Status:\*\*\s+([^|\n]+)",
    re.MULTILINE,
)


def on_page_markdown(markdown: str, page, config, files) -> str:
    """mkdocs hook — fires before markdown → HTML rendering.

    Reads orchestra metadata block (`> **Status:** Verified`), extracts status,
    prepends a tags front-matter so Material renders status filtering.

    Idempotent — won't double-add tags if the page already has a `tags:` block.
    """
    head = "\n".join(markdown.splitlines()[:30])
    match = METADATA_STATUS_RE.search(head)
    if not match:
        return markdown

    status = match.group(1).strip()
    if not status or status == "Untagged":
        status = "Untagged"

    if markdown.startswith("---\n") and "tags:" in markdown.split("---", 2)[1]:
        return markdown

    if markdown.startswith("---\n"):
        front_matter, _, body = markdown.partition("---\n")[2].partition("\n---\n")
        new_front = f"---\n{front_matter}\ntags:\n  - {status}\n---\n"
        return new_front + body

    return f"---\ntags:\n  - {status}\n---\n\n" + markdown
