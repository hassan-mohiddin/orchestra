# Contributing to Orchestra

Contributions welcome. Read this first to keep PRs frictionless.

## Quick path

1. Open an issue describing the change before coding (especially for new templates / gates / skills)
2. Fork + branch off `main`
3. Run `python -m cli.lint --doc <changed-doc>` on any docs you touch
4. Submit PR referencing the issue

## What we want

- **New doc-type templates** with industry-source citations
- **New Orchestra skills** — `workflow`, `skills-registry`, `tasks`, `gates`, etc. Each skill should be independently invokable but compose with `design-docs`.
- **Mermaid diagram-type guides** (we have 5; gaps welcome — sequence, activity, ER, gantt, etc.)
- **Lint CLI improvements** — false-positive fixes, new validation rules with config flags
- **Config conveniences** for non-canonical repo layouts
- **Examples** — filled-in samples that showcase a doc type. We accept domain-specific examples (ML, fintech, infra) as long as they don't leak any real secrets.

## What we don't want

- Templates without industry-source citations. Orchestra's value is *defensible* shapes, not opinion.
- "Improvements" to required sections without a documented failure mode that motivates the change.
- Breaking config changes in patch / minor versions.
- Project-specific code / paths in templates. Use config keys.
- Vibes-based PR descriptions. Cite a competing skill, a published doc, or a concrete failure if proposing a change.

## Quality bar

Every PR must:

- Pass `python -m cli.lint --pre-commit`
- Update `CHANGELOG.md` with a one-liner under `## Unreleased`
- Bump version in `.claude-plugin/plugin.json` per semver if shipping a new feature or breaking change
- Reference the relevant doc / industry source in the PR body

## Skill iteration changes

Changes to any `skills/<skill>/SKILL.md` description or decision tree must include eval results:

1. Save before/after via `cp -r skills/<skill>/ /tmp/skill-snapshot/`
2. Run skill-creator eval on 5+ scenarios (see `evals/` for the scenario set we ship)
3. Attach `benchmark.json` + `benchmark.md` to the PR
4. Both pass rate and trigger accuracy must hold or improve

We will not merge a SKILL.md change that drops baseline scores.

## Adding a new Orchestra skill

When adding a new skill to the umbrella (e.g. `orchestra:workflow`):

1. Create `skills/<name>/` with its own `SKILL.md`
2. Update `README.md` Roadmap table — flip the new skill's status
3. Update `CHANGELOG.md` under `## Unreleased` with the new skill description
4. Add filled-in examples under `examples/<skill-name>/`
5. Update `cli/lint.py` if the new skill produces docs that need validation

Each Orchestra skill should be independently invokable but composable with the others. They all play the same score (the doc-driven, gate-enforced philosophy) but their solos differ.

## Releases

- Version bumps go in `.claude-plugin/plugin.json` AND a git tag `v<semver>`
- Tagged releases auto-publish to the Claude Code marketplace via GitHub Action

## Code of conduct

Be helpful, blunt, and ship-oriented. No tone policing. Disagreement on technical merits is the point.

## License

By contributing, you agree your contributions are MIT-licensed under this project's `LICENSE`.
