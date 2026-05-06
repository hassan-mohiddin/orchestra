"""Orchestra Tier 2 mermaid export — render diagrams to PNG/SVG via mermaid-cli.

Usage:
    python -m cli.viewer render docs/features/001-feature.md
    python -m cli.viewer render-all
    python -m cli.viewer render docs/x.md --format png --output build/diagrams
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_OUTPUT_DIR = "docs/.rendered"
GITIGNORE_RENDERED_ENTRY = "docs/.rendered/"


class ViewerError(Exception):
    """Raised when render preconditions fail (e.g., npx absent)."""


_extract_mermaid_module = None


def _load_extract_mermaid():
    """Load skills/design-docs/scripts/extract_mermaid.py via importlib path-loading."""
    global _extract_mermaid_module
    if _extract_mermaid_module is not None:
        return _extract_mermaid_module
    repo_root = Path(__file__).parent.parent
    em_path = repo_root / "skills" / "design-docs" / "scripts" / "extract_mermaid.py"
    spec = importlib.util.spec_from_file_location("extract_mermaid", em_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {em_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _extract_mermaid_module = module
    return module


@dataclass
class RenderResult:
    rendered: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)
    skipped: str = ""

    @property
    def ok(self) -> bool:
        return not self.failed


def _ensure_gitignore_rendered(repo_root: Path) -> bool:
    """Append docs/.rendered/ to .gitignore if not present. Idempotent."""
    gitignore = repo_root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if GITIGNORE_RENDERED_ENTRY in existing:
        return False
    sep = "\n" if existing and not existing.endswith("\n") else ""
    gitignore.write_text(existing + sep + GITIGNORE_RENDERED_ENTRY + "\n")
    return True


def render_doc(doc: Path, output_dir: Path, format: str = "svg",
               check_npx: bool = True) -> RenderResult:
    """Extract mermaid blocks, export each to <output_dir>/<doc-stem>-<NN>.<format>."""
    if check_npx and not shutil.which("npx"):
        raise ViewerError(
            "npx not found — install Node.js to use mermaid render. "
            "No global install needed; npx fetches mermaid-cli per-invocation."
        )

    em = _load_extract_mermaid()
    diagrams = em.extract_diagrams_from_file(doc)
    if not diagrams:
        return RenderResult(skipped="no mermaid blocks")

    output_dir.mkdir(parents=True, exist_ok=True)
    result = RenderResult()

    for d in diagrams:
        out_file = output_dir / f"{doc.stem}-{d.index:02d}.{format}"
        try:
            proc = subprocess.run(
                ["npx", "-y", "@mermaid-js/mermaid-cli",
                 "-i", "/dev/stdin", "-o", str(out_file),
                 "-w", "1600", "-H", "1200"],
                input=d.content, capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0:
                result.rendered.append(out_file)
            else:
                msg = (proc.stderr or proc.stdout or "unknown").strip().splitlines()
                result.failed.append((doc, msg[-1] if msg else "no output"))
        except subprocess.TimeoutExpired:
            result.failed.append((doc, f"timeout (60s) on diagram {d.index}"))

    return result


def render_all(repo_root: Path, output_dir: Path, format: str = "svg",
               check_npx: bool = True) -> list[RenderResult]:
    """Walk docs/, render every mermaid block found."""
    docs_dir = repo_root / "docs"
    results: list[RenderResult] = []
    if not docs_dir.exists():
        return results
    for md in sorted(docs_dir.rglob("*.md")):
        results.append(render_doc(md, output_dir, format, check_npx=check_npx))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestra viewer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="Render mermaid blocks of one doc")
    p_render.add_argument("doc", help="Path to markdown file")
    p_render.add_argument("--format", choices=["png", "svg"], default="svg")
    p_render.add_argument("--output", default=DEFAULT_OUTPUT_DIR)

    p_all = sub.add_parser("render-all", help="Walk docs/, render all mermaid")
    p_all.add_argument("--format", choices=["png", "svg"], default="svg")
    p_all.add_argument("--output", default=DEFAULT_OUTPUT_DIR)

    args = parser.parse_args(argv)

    repo_root = Path.cwd()
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    appended = _ensure_gitignore_rendered(repo_root)
    if appended:
        print(f"appended {GITIGNORE_RENDERED_ENTRY} to .gitignore")

    try:
        if args.cmd == "render":
            result = render_doc(Path(args.doc), output_dir, format=args.format)
            for p in result.rendered:
                print(f"  ✓ {p}")
            if result.skipped:
                print(f"  → {result.skipped}")
            for doc, err in result.failed:
                print(f"  ✗ {doc}: {err}", file=sys.stderr)
            return 0 if result.ok else 1
        if args.cmd == "render-all":
            results = render_all(repo_root, output_dir, format=args.format)
            total_rendered = sum(len(r.rendered) for r in results)
            total_failed = sum(len(r.failed) for r in results)
            print(f"rendered: {total_rendered}, failed: {total_failed}")
            for r in results:
                for p in r.rendered:
                    print(f"  ✓ {p}")
                for doc, err in r.failed:
                    print(f"  ✗ {doc}: {err}", file=sys.stderr)
            return 0 if total_failed == 0 else 1
    except ViewerError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
