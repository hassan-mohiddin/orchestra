# Orchestra v1.0.0 — Announcement Drafts

Pre-written copy for each channel. Edit voice/tone to taste before posting.

---

## 1. Hacker News (Show HN)

**Title** (≤80 chars):
```
Show HN: Orchestra – Disciplined doc-driven plugin for Claude Code
```

**URL field:** `https://github.com/hassan-mohiddin/orchestra`

**Text body:** *(leave URL field above, paste below as text — but HN convention is body OR URL, not both. Pick one. If body, include URL inline.)*

```
Hi HN. I built Orchestra, a Claude Code plugin that turns "I should write a design doc first" from a habit into an enforced workflow.

It ships as a multi-skill umbrella. v1.0 has one skill — `orchestra:design-docs` — that produces typed docs (Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc) with industry-aligned templates and a 4-gate spec review. Future skills cover workflow, registry, tasks, and gates under the same brand.

What's actually in v1.0:

- 7 typed doc templates with required sections traced to industry sources (Nygard's ADR pattern, Google SRE postmortem with "Where We Got Lucky", agents.md cross-tool spec, llmstxt.org)
- A 4-gate spec review (Completeness / Evidence / Clarity / Consistency) — failures get named, not "doc needs work"
- Mandatory mermaid diagrams (sequence/activity/architecture/deployment) with a 28-error troubleshooting reference
- A bug iteration loop: one BUG-NNN doc spans every fix attempt, no orphan `fix:` commits, the doc doesn't get split across attempts
- 5 named doc gates (Discovery / Design / Spec Review / Commit / Implementation Sync) that block code from drifting from docs
- A Python lint CLI that validates the `Refs:` line on `fix:`/`feat:` commits, doc metadata, and status enums — pre-commit + GitHub Action ready
- An auto `DECISIONS.md` ADR index with bidirectional supersession consistency checking

Install: `/plugin marketplace add hassan-mohiddin/orchestra` then `/plugin install orchestra@orchestra`

The motivation is fairly direct: agents are great at writing code but terrible at preserving the load-bearing constraints in their head. Doc-driven development pushes the constraints into a written artifact the agent has to read before it codes. The gates make the agent re-read after every change. The naming taxonomy (ADR is RECORDED, not deliberated; LLD ≠ Plan; Bug doc spans attempts) prevents the most common doc-rot patterns I kept hitting.

Surveyed 16 competing plugins before shipping. None combined typed doc taxonomy + commit-line gate + bug iteration + mandatory mermaid. Closest competitor (SpillwaveSolutions/design-doc-mermaid) is abandoned and narrower; most popular (Pimzino/claude-code-spec-workflow) is gate-light.

License is MIT. Repo: https://github.com/hassan-mohiddin/orchestra

Happy to answer questions about the schema, the eval framework I used, or the skill iteration loop. Built it because my own (solo) workflow on a finance startup kept producing orphan fix commits and stale design docs — this is the discipline I needed to avoid that.
```

**Posting checklist:**
- HN convention: leave URL field empty, put body + link in body — OR put URL in URL field + body separate. Either works; body+URL hybrid is most engaging for Show HN.
- Best post times: Tue/Wed/Thu, 8–11am EST. Don't post Friday afternoon or weekends.
- Engage with every comment in first 90 minutes — front-page algorithm rewards engagement.

---

## 2. Reddit r/ClaudeAI

**Title:**
```
[Plugin] Orchestra v1.0 — Doc-driven discipline for Claude Code (typed templates, 4-gate review, commit gates)
```

**Body:**
```
Just shipped Orchestra v1.0.0 — a Claude Code plugin focused on enforcing doc-driven development. Sharing here because I've seen a lot of "Claude wrote great code but I have no idea what assumptions it baked in" posts.

**The problem it solves**

Agents are great at writing code, terrible at preserving design constraints. Without a written artifact to anchor on, every session re-derives context from scratch. This produces:
- Orphan `fix:` commits (one bug, three attempts, three half-baked commits, no record of what was actually broken)
- Design Docs that diverge silently from the code they describe
- ADRs that drift into RFC-style multi-option deliberation when a decision was already made
- Postmortems that miss the highest-signal section (near-misses)

**What Orchestra does**

It's a Claude Code plugin (`orchestra:design-docs` is the first skill) that produces typed docs and enforces gates around them.

🎼 **7 doc templates** with industry-traceable required sections:
- Feature LLD — design before code
- Bug Report — with mandatory Iteration Log section
- ADR — Nygard format (Context / Decision / Consequences), no RFC drift
- Postmortem — Google SRE shape with "Where We Got Lucky" section
- Runbook — 3am-friendly on-call format
- Design Doc — living component-level architecture
- ADR-short — for routine decisions

🚦 **4-gate spec review** (Completeness / Evidence / Clarity / Consistency). Failures get named, not vague.

🔗 **5 doc gates** (Discovery / Design / Spec Review / Commit / Sync). Block code from drifting from docs.

🐛 **Bug iteration loop**: one BUG-NNN doc spans every fix attempt. `fix:` commit only after user confirms. No more orphan fix commits.

📊 **Mandatory mermaid diagrams** for LLDs / Bugs / Postmortems. Plus an octal-safe auto-numbering script and 28-error troubleshooting reference.

🛠 **Python lint CLI** validates Refs:-line on `fix:`/`feat:` commits, doc metadata, and status enums. Pre-commit + GitHub Action templates ship in the repo.

📑 **Auto DECISIONS.md index** with bidirectional ADR supersession consistency checking.

🌉 **Cross-tool standards**: emits AGENTS.md (Linux Foundation Agentic AI Foundation, 60k+ projects) and llms.txt (Jeremy Howard / Answer.AI).

**Install**

```
/plugin marketplace add hassan-mohiddin/orchestra
/plugin install orchestra@orchestra
```

**Repo**: https://github.com/hassan-mohiddin/orchestra (MIT)

**Future**: v1.1 ships `orchestra:workflow` + `orchestra:skills-registry`. v1.2 adds `orchestra:tasks` + `orchestra:gates`. v1.3 adds `orchestra:plans` (TDD vertical slicing).

Happy to answer questions about the schema, the eval framework, or how this composes with obra/superpowers and mattpocock-skills.
```

**Posting checklist:**
- Cross-post to r/ChatGPTCoding and r/ArtificialIntelligence after Reddit dust settles
- Avoid r/programming (anti-AI sentiment)
- Engage with first 5–10 comments within an hour

---

## 3. Twitter / X thread

**Tweet 1 (hook):**
```
Just shipped Orchestra v1.0 for @AnthropicAI's Claude Code 🎼

A plugin that turns "I should write a design doc first" from a habit into an enforced workflow.

7 doc templates. 4-gate spec review. 5 doc gates. Bug iteration loop. Mandatory mermaid.

Thread 🧵
```

**Tweet 2:**
```
The problem: agents are great at writing code, terrible at preserving design constraints in their head.

Without a written artifact to anchor on, every session re-derives context. You end up with orphan fix-commits, stale Design Docs, RFC-shaped ADRs, postmortems that miss near-misses.
```

**Tweet 3:**
```
Orchestra ships a typed doc taxonomy with industry-traceable shapes:

→ Feature LLD (design before code)
→ Bug Report (mandatory Iteration Log)
→ ADR (Nygard: Context / Decision / Consequences)
→ Postmortem (Google SRE + "Where We Got Lucky")
→ Runbook (3am-friendly)
→ Design Doc (living)
```

**Tweet 4:**
```
The gates are what make it stick.

5 named doc gates: Discovery → Design → Spec Review → Commit → Implementation Sync.

Each blocks the next step. A `fix:`/`feat:` commit without a `Refs:` line pointing at a real doc fails the lint check. Pre-commit + GitHub Action templates ship.
```

**Tweet 5:**
```
The bug iteration loop is my favorite part.

Old way: BUG-001-attempt-1, BUG-001-attempt-2, three half-baked `fix:` commits, no record of what actually broke.

New way: one BUG-NNN doc spans every attempt. Iteration Log section. `fix:` commit only after user-confirms.
```

**Tweet 6:**
```
Patterns adopted from public sources:

ADR — Michael Nygard 2011
Postmortem — Google SRE Book
AGENTS.md — Linux Foundation Agentic AI Foundation (60k+ projects)
llms.txt — Jeremy Howard / Answer.AI
4-gate review — rvdbreemen/adr-kit

Defensible, not opinionated.
```

**Tweet 7:**
```
Install:

/plugin marketplace add hassan-mohiddin/orchestra
/plugin install orchestra@orchestra

Repo: https://github.com/hassan-mohiddin/orchestra
License: MIT.

v1.1 adds workflow + skills-registry skills. v1.2 adds tasks + gates.

Built it for my own startup. Sharing because the discipline is the point.
```

**Posting checklist:**
- Post Tuesday or Wednesday morning, US Eastern time
- Reply to @claude_code, @AnthropicAI, @obra, @mattpocockuk if they engage
- Pin the thread to your profile for first week

---

## 4. Dev.to / Hashnode article

**Title:** `Orchestra — A Doc-Driven Plugin for Claude Code, And Why I Built It`

**Tags:** `claudecode`, `ai`, `documentation`, `tooling`, `opensource`

**Body:** *(longer-form. Structure below; flesh out to ~1500 words.)*

```markdown
# Orchestra — A Doc-Driven Plugin for Claude Code, And Why I Built It

> Just shipped [Orchestra v1.0](https://github.com/hassan-mohiddin/orchestra), a Claude Code plugin that enforces doc-driven development. This is the long-form story behind it.

## The problem

I run an AI personal-finance startup as a solo founder. Most of my engineering work is now agent-led — Claude Code does the writing, I do the steering. After about a year of this, I noticed three failure modes that kept eating my time:

1. **Orphan fix-commits.** Bug → attempt 1 → attempt 2 → attempt 3 → eventually it works. But the git history shows three `fix:` commits with overlapping intent and no record of what was actually broken.

2. **Design Doc rot.** I'd write an architecture doc once, ship the feature, and never sync the doc when the implementation drifted. Six months later, the doc was a lie.

3. **ADR-shaped RFCs.** I'd start writing an "architecture decision record" and end up with a multi-page deliberation between three options, no clear chosen direction. By Nygard's original definition, that's not an ADR — that's an RFC.

These failure modes share a root cause: **without a written artifact, the agent re-derives context from scratch every session, and the load-bearing constraints get lost.**

## The hypothesis

What if the doc was the source of truth, not the code?

- Every feature has a Feature LLD before any code is written
- Every bug has a Bug Report before any fix is attempted, and the same doc spans every iteration
- Every architectural decision is RECORDED in an ADR (not deliberated)
- Every incident produces a Postmortem with a "Where We Got Lucky" section (the highest-signal section, per Google SRE)
- Every doc passes a named 4-gate spec review before commit

The agent reads the doc, then writes code. The doc lints in CI. Commits without a `Refs:` line back to a real doc fail.

## What I shipped

Orchestra is a [Claude Code plugin](https://code.claude.com/docs/en/plugins) that ships this discipline as the `orchestra:design-docs` skill.

[... continue with: install, examples, skill internals, eval results, comparison to obra/superpowers and mattpocock-skills, future roadmap, lessons from the v2.1.129 schema validator debugging session ...]
```

---

## 5. LinkedIn

**Post:**
```
🎼 Shipped Orchestra v1.0 — a Claude Code plugin that enforces doc-driven AI engineering.

Built it because my own (solo founder) agent-led workflow kept producing orphan fix-commits, stale design docs, and ADRs that drifted into RFC-style deliberation.

What's in v1.0:

→ 7 typed doc templates with industry-traceable required sections
→ 4-gate spec review (Completeness / Evidence / Clarity / Consistency)
→ 5 doc gates (Discovery / Design / Spec Review / Commit / Implementation Sync)
→ Bug iteration loop — one doc spans every fix attempt
→ Mandatory mermaid diagrams + 28-error troubleshooting reference
→ Python lint CLI that validates Refs:-line on fix/feat commits
→ AGENTS.md / llms.txt cross-tool sync

Patterns from Michael Nygard (ADR), Google SRE (postmortems), Pragmatic Engineer (RFC vs ADR taxonomy), Linux Foundation Agentic AI Foundation (AGENTS.md), and Jeremy Howard / Answer.AI (llms.txt).

Install: `/plugin marketplace add hassan-mohiddin/orchestra`

Repo: https://github.com/hassan-mohiddin/orchestra

Future skills under the Orchestra umbrella: workflow, skills-registry, tasks, gates, plans.

#AIEngineering #ClaudeCode #SoftwareEngineering #DocumentationDriven
```

---

## 6. awesome-claude-code (Hesreallyhim) — wait until 2026-05-13

The repo's spam guard requires the resource repo to be **at least 7 days old**. Orchestra was created 2026-05-06. Earliest submission: **2026-05-13**.

Submission method: web form ONLY (no PR, no `gh` CLI).

URL: https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml

**Pre-filled fields to use on 2026-05-13:**

- Display Name: `orchestra`
- Category: `Agent Skills`
- Sub-Category: `General` (no plugin-specific sub-cat available)
- Primary Link: `https://github.com/hassan-mohiddin/orchestra`
- Author Name: `Hassan Mohiddin`
- Author Link: `https://github.com/hassan-mohiddin`
- License: `MIT`
- Description: `Disciplined AI engineering toolkit for Claude Code. Ships typed design-doc templates (Feature LLD, Bug Report, ADR, Postmortem, Runbook, Design Doc) with a 4-gate spec review (Completeness / Evidence / Clarity / Consistency), mandatory mermaid diagrams, an octal-safe auto-numbering script, and a bug-iteration loop that prevents orphan fix-commits. Includes a Python lint CLI for Refs:-line + metadata + status validation, and an auto DECISIONS.md generator with bidirectional ADR supersession consistency checking. Patterns adopted from Michael Nygard (ADR), Google SRE (postmortems), Pragmatic Engineer (RFC vs ADR), agents.md, and llmstxt.org.`
- Validate Claims: `Install the plugin via /plugin marketplace add hassan-mohiddin/orchestra. Then say to Claude: "Found a bug — auth tokens are not refreshing on the worker path." The skill should produce a Bug Report at docs/bugs/BUG-NNN-name.md with all 10 required sections including the Iteration Log section, a sequence-diagram mermaid block, and a Changelog. Verify by running 'python -m cli.lint --doc docs/bugs/BUG-NNN-name.md' which should return 'PASS — all design-docs checks green'.`
- Specific Tasks: `Test 1: Ask Claude "I want to add user search to the app" — verify it produces a Feature LLD with measurable success-criteria checkboxes and a mermaid sequence diagram. Test 2: Ask Claude "Auth had a 23-min outage; write the postmortem" — verify the output includes the "Where We Got Lucky" section. Test 3: Run 'python -m cli.decisions_index --adr-dir examples/adr/' to see the auto DECISIONS.md generator with bidirectional supersession check.`
- Specific Prompts: `Prompt 1: "I want to add transaction search to the app." Prompt 2: "We've decided to migrate from Postgres to TimescaleDB — record this." Prompt 3: "Auth had a 23-minute outage this morning, write the postmortem."`
- Additional Comments: `Multi-skill umbrella (matches obra/superpowers shape). v1.0 ships orchestra:design-docs as the first skill. Future v1.1+ skills: workflow, skills-registry, tasks, gates, plans. Plugin is published to the official Anthropic marketplace (pending review at submission time).`
- Checklist: tick all 5 boxes (yes — unique, >7 days old, all links work, no other open issues, human submitter)

---

## 7. travisvn/awesome-claude-skills

PR opened by automation: https://github.com/travisvn/awesome-claude-skills/pull/691

No further action required from you. Engage if maintainer comments.

---

## 8. Other channels worth considering

- **Lobsters** (lobste.rs) — invite-only, but if you have an account, post under "ai" or "programming" tag with the GH repo URL
- **Anthropic Discord** — community shoutout if you're in
- **Product Hunt** — launch as "Orchestra: Claude Code plugin for doc-driven engineering". Schedule for a Tuesday/Thursday. Best for visibility outside the dev-tool bubble.
- **IndieHackers** — post in "Show IH" with the founder/solo angle ("I built this for my own AI-finance startup")
- **Skool / Discord communities for AI builders** — varies; pick 1–2 you're already active in
- **Personal blog** — if you have one, a longer-form writeup linking back to the repo is permanent SEO. Cross-post on Hashnode/Dev.to.

---

## Posting sequence (recommended)

| Day | Channel | Why |
|---|---|---|
| Day 0 (today) | LinkedIn + Twitter thread | Warm-up; tells your direct network |
| Day 1 | Reddit r/ClaudeAI | Early-week engagement window |
| Day 2 | HN Show HN | Tue/Wed/Thu morning |
| Day 3 | Dev.to / Hashnode article | After HN traffic peaks |
| Day 7+ | awesome-claude-code form | Wait for the 7-day spam-guard window |
| Anytime | Anthropic Discord, IndieHackers, Lobsters | Lower pressure, post when you have time |

---

## After approval

If awesome-claude-code accepts, add the badge to README.md:

```markdown
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code)
```

If marketplace listing approves (orchestra appears in `anthropics/claude-plugins-official`), update the README install section to:

```markdown
/plugin marketplace add anthropics/claude-plugins-official
/plugin install orchestra@claude-plugins-official
```

(Keep the direct-from-fork install path documented too — for users who don't want the official marketplace.)
