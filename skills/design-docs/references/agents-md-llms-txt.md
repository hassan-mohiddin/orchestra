# AGENTS.md + llms.txt — Cross-Tool AI Context Files

Two emerging open standards for AI-agent context. The skill recommends maintaining both at the repo root for any project that wants broad AI-tool compatibility.

## What each file is for

| File | Audience | Location | Format |
|------|----------|----------|--------|
| `AGENTS.md` | Coding agents reading the repo (Cursor, Codex, Claude Code, Copilot, etc.) | Repo root | Plain markdown, no schema |
| `llms.txt` | External LLMs reading your published documentation site | Site root (alongside `robots.txt`) | Markdown with H1 / blockquote / H2 sections per spec |

These are NOT redundant — one is for *agents working inside the repo*, the other is for *LLMs consuming your published docs at inference time*.

## AGENTS.md

**Origin:** Sourcegraph + OpenAI + Google + Cursor consortium (mid-2025). Placed under Linux Foundation Agentic AI Foundation Dec 2025. 60,000+ open-source projects use it.

**Why it matters:** Cross-tool. A single file works across Cursor, Codex, Claude Code (via symlink), Copilot, Continue. Replaces tool-specific files (`CLAUDE.md`, `.cursorrules`, etc.) for the universal subset.

**Claude Code compatibility:** As of April 2026, Claude Code does NOT natively read AGENTS.md. Standard workaround:

```bash
ln -s AGENTS.md CLAUDE.md
```

Now both Claude Code (via CLAUDE.md) and other agents (via AGENTS.md) read the same source of truth.

### Common sections

```markdown
# AGENTS.md

## Project Overview
[1-2 paragraphs — what the project is, key architecture]

## Build / Test Commands
[Exact commands the agent should run — make targets, npm scripts]

## Code Style
[Lint config location, key conventions agents should follow]

## Testing
[How to run tests, where they live, TDD expectations]

## Security
[What the agent must not do — secrets, destructive ops, prod systems]

## Commit Guidelines
[Conventional commits? Refs: line required? Branch naming?]

## Repository Layout
[Top-level dirs + what lives where]
```

Keep under 200 lines. Agents will load this every session — pruning matters.

## llms.txt

**Origin:** Jeremy Howard / Answer.AI, September 2024 proposal. Adopted by Anthropic, Cloudflare, Vercel, Mintlify, Instructor, FastHTML.

**Why it matters:** When an external LLM is asked about your docs (via web search, RAG, or direct lookup), it can fetch a curated machine-friendly index instead of scraping HTML. Reduces hallucination, increases coverage.

### Format spec

```markdown
# Project Name

> One-sentence project description.

A few paragraphs of context. What the project does. Who it's for. Key concepts.

## Docs

- [Getting Started](https://example.com/getting-started.md): One-line summary
- [API Reference](https://example.com/api.md): One-line summary

## Optional

- [Changelog](https://example.com/changelog.md): One-line summary
- [Migration Guide](https://example.com/migration.md): One-line summary
```

Optional `llms-full.txt` variant: same structure but inlines full doc text rather than links. Used by sites that want LLMs to ingest the entire knowledge base in one fetch.

## When to maintain these

- **Public OSS project:** Both. Mandatory for ecosystem compatibility.
- **Private / internal repo with AI agent collaboration:** AGENTS.md only. llms.txt is for *published* docs.
- **Static landing page only, no public API:** Neither.

## Sync workflow

The `design-docs` skill should treat AGENTS.md and llms.txt as living docs:

1. **On first use** — emit a stub `AGENTS.md` from the project's existing context (CLAUDE.md, README, STANDARDS) and ask user to review
2. **On each major doc change** — if a new doc type, command, or convention is added, prompt to update AGENTS.md
3. **On Design Doc update** — if architecture changes materially, prompt to update llms.txt entries pointing to that Design Doc

This is analogous to the Design Doc Sync Protocol — AGENTS.md and llms.txt rot fast without explicit sync triggers.

## Templates

Stub templates ship at:
- `.claude/skills/design-docs/templates/agents-md.md`
- `.claude/skills/design-docs/templates/llms-txt.md`

Both are starting points, not prescriptive shapes. Adapt to project.

## References

- AGENTS.md spec + project list: <https://agents.md/>
- llms.txt spec: <https://llmstxt.org/>
- Jeremy Howard original post: <https://www.answer.ai/posts/2024-09-03-llmstxt.html>
- AGENTS.md vs CLAUDE.md comparison: <https://hivetrail.com/blog/agents-md-vs-claude-md-cross-tool-standard>
