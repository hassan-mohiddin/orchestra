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
GITIGNORE_SITE_ENTRY = "site/"

MKDOCS_INSTALL_FILES = [
    ("mkdocs.yml", "mkdocs.yml"),
    ("docs/index.md", "docs-index.md"),
    ("docs/tags.md", "tags.md"),
    ("requirements-docs.txt", "requirements-docs.txt"),
    ("mkdocs_hooks.py", "mkdocs_hooks.py"),
]


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


@dataclass
class InstallResult:
    files_written: list[Path] = field(default_factory=list)
    files_skipped: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# BUG-005: dirs that count as "default-7" content paths the template nav
# already covers, and orchestra-internal dirs that should never appear in
# the user-facing nav.
_DEFAULT_7_DIRS = frozenset({
    "features", "bugs", "adr", "design", "postmortems", "runbooks", "plans",
})
_INTERNAL_DIRS = frozenset({"archive", "investigations", "reviews"})


def _scan_extra_doc_dirs(docs_dir: Path) -> list[str]:
    """Return sorted list of non-default-7, non-internal subdirs under docs_dir.

    Hidden dirs and plain files are ignored. Returns [] when docs_dir
    doesn't exist (e.g., pre-init). Safe to call before scaffold_bucket_1.
    """
    if not docs_dir.is_dir():
        return []
    extras: list[str] = []
    for child in docs_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if name.startswith("."):
            continue
        if name in _DEFAULT_7_DIRS or name in _INTERNAL_DIRS:
            continue
        extras.append(name)
    return sorted(extras)


def _title_case_segment(name: str) -> str:
    """Hyphen-aware title-casing: 'my-policies' → 'My Policies'."""
    return " ".join(part.title() for part in name.split("-"))


def _generate_nav_entries(extras: list[str]) -> str:
    """Build YAML nav entry lines (2-space indent) for the given extra dir names."""
    return "".join(
        f"  - {_title_case_segment(name)}: {name}/\n"
        for name in extras
    )


def _inject_nav_entries(mkdocs_yml: str, extras: list[str]) -> str:
    """Insert auto-detected nav entries inside the existing `nav:` block.

    Finds the line `nav:` and appends the generated entries immediately
    after the last existing nav line (before the next blank line / top-level
    key). YAML safety: 2-space indent matches template convention.
    """
    if not extras:
        return mkdocs_yml
    addition = _generate_nav_entries(extras)
    lines = mkdocs_yml.splitlines(keepends=True)
    out: list[str] = []
    in_nav = False
    inserted = False
    for line in lines:
        if not in_nav:
            out.append(line)
            if line.rstrip() == "nav:":
                in_nav = True
            continue
        # In nav block — append our entries before the first non-nav line
        if inserted or line.startswith("  ") or line.strip() == "":
            if line.strip() == "" and not inserted:
                out.append(addition)
                inserted = True
            out.append(line)
        else:
            # Top-level key reached (e.g., `hooks:`) — inject before it
            if not inserted:
                out.append(addition)
                inserted = True
            out.append(line)
    if in_nav and not inserted:
        # nav: was last block in file — append at end
        out.append(addition)
    return "".join(out)


def _ensure_gitignore_entry(repo_root: Path, entry: str) -> bool:
    """Append a path entry to .gitignore if not present. Idempotent."""
    gitignore = repo_root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if entry in existing:
        return False
    sep = "\n" if existing and not existing.endswith("\n") else ""
    gitignore.write_text(existing + sep + entry + "\n")
    return True


def _ensure_gitignore_rendered(repo_root: Path) -> bool:
    """Append docs/.rendered/ to .gitignore if not present. Idempotent."""
    return _ensure_gitignore_entry(repo_root, GITIGNORE_RENDERED_ENTRY)


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


def install_mkdocs(repo_root: Path, force: bool = False,
                   auto_nav: bool = False) -> InstallResult:
    """Write 5 files (mkdocs.yml, docs/index.md, docs/tags.md,
    requirements-docs.txt, mkdocs_hooks.py) and append site/ to .gitignore.

    Idempotent: skip-existing default. --force overwrites. When
    `auto_nav=True` and the repo has non-default-7 doc dirs (e.g.,
    `docs/policies/`, `docs/research/`), append matching nav entries
    to mkdocs.yml. Regardless of `auto_nav`, when extras are detected
    a warning is appended to `result.warnings` listing them.

    BUG-007 v1.6.2: emits a post-install warning when `.pre-commit-config.yaml`
    is present, since the shipped mkdocs.yml uses a YAML python-tag for the
    mkdocs-mermaid2-plugin fence wiring which strict `check-yaml` hooks reject
    without `--unsafe`.

    BUG-005 v2.0.1: scans docs/ for non-default-7 dirs after install;
    warns + optionally rewrites mkdocs.yml nav.
    """
    templates_dir = Path(__file__).parent / "templates"
    result = InstallResult()

    for target_rel, template_name in MKDOCS_INSTALL_FILES:
        target = repo_root / target_rel
        template = templates_dir / template_name
        if not template.exists():
            result.errors.append(f"template missing: {template}")
            continue
        if target.exists() and not force:
            result.files_skipped.append(target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(template.read_text())
        result.files_written.append(target)

    _ensure_gitignore_entry(repo_root, GITIGNORE_SITE_ENTRY)

    # BUG-005: detect non-default-7 doc dirs not in the nav template.
    extras = _scan_extra_doc_dirs(repo_root / "docs")
    if extras:
        if auto_nav:
            mkdocs_path = repo_root / "mkdocs.yml"
            if mkdocs_path.exists():
                content = mkdocs_path.read_text()
                mkdocs_path.write_text(_inject_nav_entries(content, extras))
        else:
            result.warnings.append(
                f"Detected {len(extras)} non-default doc dir(s) not in "
                f"mkdocs nav: {', '.join(extras)}. Add manually or rerun "
                f"with --auto-nav."
            )

    # BUG-007: warn when pre-commit framework is in use
    if (repo_root / ".pre-commit-config.yaml").exists():
        print(
            "NOTE: Your repo uses pre-commit. The shipped mkdocs.yml contains a\n"
            "  YAML python-tag (`!!python/name:mermaid2.fence_mermaid_custom`)\n"
            "  required by mkdocs-mermaid2-plugin. Strict `check-yaml` hooks reject\n"
            "  python-tags without --unsafe. Update your .pre-commit-config.yaml:\n"
            "    - id: check-yaml\n"
            "      args: [--unsafe]\n"
            "  Or commits touching mkdocs.yml will fail with a python-tag error.\n"
            "  See cli/templates/precommit-yaml-patch.txt for the exact snippet.",
        )

    return result


def _mkdocs_available() -> bool:
    return shutil.which("mkdocs") is not None


def build_site(repo_root: Path, output_dir: Path = Path("site")) -> int:
    """Wrap `mkdocs build`. Validates mkdocs installed; instructs if not."""
    if not _mkdocs_available():
        raise ViewerError(
            "mkdocs not installed. Run: pip install -r requirements-docs.txt"
        )
    return subprocess.call(
        ["mkdocs", "build", "-d", str(output_dir)],
        cwd=str(repo_root),
    )


def publish_gh_pages(repo_root: Path) -> int:
    """Wrap `mkdocs gh-deploy`. Validates clean working tree first."""
    if not _mkdocs_available():
        raise ViewerError(
            "mkdocs not installed. Run: pip install -r requirements-docs.txt"
        )
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise ViewerError("git working tree is dirty. Commit or stash first.")
    return subprocess.call(
        ["mkdocs", "gh-deploy", "--force"],
        cwd=str(repo_root),
    )


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

    p_install = sub.add_parser("install-mkdocs", help="Install mkdocs config + templates")
    p_install.add_argument("--force", action="store_true",
                           help="Overwrite existing mkdocs.yml + index.md")
    p_install.add_argument("--auto-nav", action="store_true",
                           help="Append nav entries for non-default-7 doc dirs "
                                "(e.g., docs/policies/, docs/research/) detected at install time.")

    p_build = sub.add_parser("build", help="Build static doc site via mkdocs")
    p_build.add_argument("--output", default="site")

    p_publish = sub.add_parser("publish-gh-pages",
                               help="Publish doc site to gh-pages branch")

    args = parser.parse_args(argv)

    repo_root = Path.cwd()

    try:
        if args.cmd == "install-mkdocs":
            result = install_mkdocs(repo_root, force=args.force,
                                    auto_nav=args.auto_nav)
            for p in result.files_written:
                print(f"  + {p.relative_to(repo_root) if p.is_relative_to(repo_root) else p}")
            for p in result.files_skipped:
                rel = p.relative_to(repo_root) if p.is_relative_to(repo_root) else p
                print(f"  = {rel} (exists; use --force to overwrite)")
            for w in result.warnings:
                print(f"  ⚠ {w}", file=sys.stderr)
            for err in result.errors:
                print(f"  ! {err}", file=sys.stderr)
            return 0 if result.ok else 1
        if args.cmd == "build":
            return build_site(repo_root, output_dir=Path(args.output))
        if args.cmd == "publish-gh-pages":
            return publish_gh_pages(repo_root)
    except ViewerError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

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
    # argparse subparsers(required=True) guarantees one branch matches, but
    # mypy/pyrefly need explicit fallthrough.
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
