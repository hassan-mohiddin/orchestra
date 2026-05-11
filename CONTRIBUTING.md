# Contributing to Orchestra

Contributions welcome. Read this first to keep PRs frictionless.

## Quick path

1. Open an issue describing the change before coding (especially for new templates / gates / skills)
2. Fork + branch off `main`
3. Install the pre-commit hook (one-time, after clone) — see § Pre-commit hook below
4. Run `python -m cli.lint --doc <changed-doc>` on any docs you touch
5. Submit PR referencing the issue

## Pre-commit hook (required for contributors)

orchestra dogfoods its own commit-discipline. After cloning, install the hooks:

### Raw path (no pre-commit framework installed)

```bash
python -m cli.install_hooks --all
```

Installs `.git/hooks/{pre-commit,commit-msg}`. Pre-commit runs `python -m cli.lint --pre-commit` (L1 Refs-eligibility + L2-detect canon-inplace annotation + L3 attestation-path + L4 doc-id-burn). commit-msg runs Refs:-line check + `python -m cli.lint --commit-msg-finalize` (v1.7+ L2-finalize tiered narrow-change per BUG-011).

### Framework path (pre-commit.com installed)

```bash
python -m cli.install_hooks --apply
```

Auto-merges orchestra entries into `.pre-commit-config.yaml` (creates one if absent), runs `pre-commit install --hook-type pre-commit --hook-type commit-msg`, and verifies. On failure: rolls back from `.pre-commit-config.yaml.orchestra-backup`.

Verify post-install:

```bash
python -m cli.install_hooks --verify
```

### Bypass / overrides

- `python -m cli.install_hooks --force-raw` — bypass framework detection; install raw hooks even if `.pre-commit-config.yaml` present.
- `ORCHESTRA_BYPASS=1 git commit -m "..." -m "Bypass: <reason>"` — emergency override; rejected in CI (multi-var detection: `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `BUILDKITE`, `CIRCLECI`, `TRAVIS`, `JENKINS_URL`); audit-logged to `.git/orchestra-bypass-audit.log`.
- `ORCHESTRA_STRICT=1` — opt-in fail-closed at commit-msg-time when pending file absent (closes `--no-verify` bypass surface).
- `ORCHESTRA_INIT_STRICT=1` — opt-in fail-closed for `cli.init` bootstrap when hook install fails.
- `git commit --no-verify` — sanctioned mechanical bypass (per LLD-008 Glossary `mechanical backstop`); pre-commit skipped → pending file never written → L2-finalize fail-opens. User accepts responsibility.

### Tiered narrow-change rule (v1.7+, BUG-011)

Canon-frozen docs (`Status` ∈ `{Approved, Implemented, Verified, Fix Applied, Current}`):

- **Critical** finding → supersession REQUIRED (no exception).
- **Important** ≤3 findings → narrow-change permitted with `Addresses:` lines + per-finding Changelog row.
- **Important** ≥4 findings → supersession REQUIRED.
- **Minor** any count → narrow-change permitted with `Addresses:` lines + per-finding Changelog row.

`Addresses:` line format:

```
Addresses: docs/reviews/<doc-id>-rN.review.yaml gate <completeness|evidence|clarity|consistency> finding <N> (Minor|Important|Critical)
```

See `skills/commit/references/supersession-decision.md` for the full decision tree.

### Manual uninstall

```bash
# Raw mode
rm .git/hooks/pre-commit .git/hooks/commit-msg

# Framework mode
pre-commit uninstall --hook-type pre-commit --hook-type commit-msg
# Then remove the `- repo: local` block with orchestra-lint + orchestra-commit-msg ids from .pre-commit-config.yaml
```

**Why it matters**: orchestra repo previously did not install its own hook (BUG-010). Two canon-inplace violations landed (`653db4e` + `bc359e7` 2026-05-10) before user observation caught them. Pre-commit hook is the first-line defense; `cli.lint --commit <SHA>` (BUG-009 retroactive L2) is the post-hoc backstop.

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
