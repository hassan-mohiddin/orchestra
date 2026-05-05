# AGENTS.md

Cross-tool AI agent context file. Read by Cursor, Codex, Claude Code (via `ln -s AGENTS.md CLAUDE.md`), Copilot, Continue, and others.

## Project Overview

[1-2 paragraphs — what the project is, the core problem it solves, the key components.]

## Tech Stack

- **Frontend:** [Framework + version]
- **Backend:** [Framework + version]
- **Database:** [System]
- **Infra:** [Deployment + CI]

## Build / Test Commands

```bash
# Most-used commands the agent should know
[command]   # What it does
[command]   # What it does
```

## Code Style

- Lint config: [path]
- Type checking: [command]
- Format on save: [yes/no, tool]
- Naming conventions: [if non-default]

## Testing

- Test framework: [name]
- Test location: [path pattern]
- Run all tests: `[command]`
- Run single test: `[command]`
- TDD expectation: [Yes — write failing test first / No — tests after implementation OK]

## Security

What the agent MUST NOT do without explicit user confirmation:

- Modify production systems
- Touch secrets, credentials, or `.env` files
- Run destructive git ops (force-push, reset --hard) on shared branches
- Delete database tables or records
- Send messages / emails / Slack on behalf of the user

## Commit Guidelines

- Format: [Conventional Commits / other]
- Required trailers: [e.g. `Refs: docs/...` for fix:/feat:]
- Branch naming: [pattern]
- Pre-commit hooks: [list]

## Repository Layout

```
project-root/
├── apps/        # [Description]
├── packages/    # [Description]
├── docs/        # [Description]
└── ...
```

## Doc Conventions

Where design docs live and how to find them:
- Feature designs: [path]
- Bug reports: [path]
- Decisions (ADRs): [path]
- Living architecture: [path]

## Common Gotchas

- [Project-specific quirk that's surprised contributors]
- [Non-obvious dependency or ordering constraint]

## Where to Ask Questions

- Internal docs: [path]
- External docs site: [URL]
- Team chat: [channel]
