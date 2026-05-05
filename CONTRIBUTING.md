# Contributing to design-docs

Contributions welcome. Read this first to keep PRs frictionless.

## Quick path

1. Open an issue describing the change before coding (especially for new templates / gates)
2. Fork + branch off `main`
3. Run `python -m design_docs.lint --doc <changed-doc>` on any docs you touch
4. Submit PR referencing the issue

## What we want

- **New doc-type templates** with industry-source citations
- **Mermaid diagram-type guides** (we have 5; gaps welcome — sequence, activity, ER, gantt, etc.)
- **Lint CLI improvements** — false-positive fixes, new validation rules with config flags
- **Config conveniences** for non-canonical repo layouts
- **Examples** — filled-in samples that showcase a doc type. We accept domain-specific examples (ML, fintech, infra) as long as they don't leak any real secrets.

## What we don't want

- Templates without industry-source citations. The plugin's value is *defensible* doc shapes, not opinion.
- "Improvements" to required sections without a documented failure mode that motivates the change.
- Breaking config changes in patch / minor versions.
- Project-specific code / paths in templates. Use config keys.
- Vibes-based PR descriptions. Cite a competing skill, a published doc, or a concrete failure if proposing a change.

## Quality bar

Every PR must:

- Pass `python -m design_docs.lint --pre-commit`
- Update `CHANGELOG.md` with a one-liner under `## Unreleased`
- Bump version in `.claude-plugin/plugin.json` per semver if shipping a new feature or breaking change
- Reference the relevant doc / industry source in the PR body

## Skill iteration changes

Changes to `skills/design-docs/SKILL.md` description or decision tree must include eval results:

1. Save before/after via `cp -r skills/design-docs/ /tmp/skill-snapshot/`
2. Run skill-creator eval on 5+ scenarios (see `evals/` for the scenario set we ship)
3. Attach `benchmark.json` + `benchmark.md` to the PR
4. Both pass rate and trigger accuracy must hold or improve

We will not merge a SKILL.md change that drops baseline scores.

## Releases

- Version bumps go in `.claude-plugin/plugin.json` AND a git tag `v<semver>`
- Tagged releases auto-publish to the Claude Code marketplace via GitHub Action

## Code of conduct

Be helpful, blunt, and ship-oriented. No tone policing. Disagreement on technical merits is the point.

## License

By contributing, you agree your contributions are MIT-licensed under this project's `LICENSE`.
