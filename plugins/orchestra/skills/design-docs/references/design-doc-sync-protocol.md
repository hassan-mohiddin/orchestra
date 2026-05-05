# Design Doc Sync Protocol

## When to Update a Design Doc

After writing or updating ANY Feature LLD, Bug Report, or ADR, check whether a living
Design Doc (`docs/design/<component>.md`) needs updating.

### Sync Decision Tree

```
Did the LLD / Bug / ADR change...
  → Database schema?              → Update docs/design/database-design.md
  → API endpoints?                → Update docs/design/api-design.md
  → System components / topology? → Update docs/design/system-architecture.md
  → Infrastructure or deployment? → Update docs/design/devops.md
  → Security model?               → Update docs/design/security.md
  → None of the above?            → No Design Doc update needed
```

Multiple Design Docs may need updating from a single LLD or ADR.

## How to Update a Design Doc

### 1. Locate the Affected Section

Read the Design Doc. Find the section that relates to the LLD / ADR change.

### 2. Update Content

- Modify the section to reflect the **current** state (NOT "we added X" — just show what exists now)
- Update any affected Mermaid diagrams
- Keep the Design Doc as a snapshot of the current system, not a history log

### 3. Update Diagrams

If the change affects system topology, data flow, or deployment:

- Update the relevant Mermaid diagram in the Design Doc
- Ensure it matches the diagrams in the LLD
- Diagrams in the Design Doc show the big picture; LLD diagrams show detail

### 4. Add Changelog Entry

At the bottom of the Design Doc, add:

```markdown
## Changelog

| Date       | Feature          | Change                            |
| ---------- | ---------------- | --------------------------------- |
| YYYY-MM-DD | NNN-feature-name | Brief description of what changed |
```

## Living Design Doc files

| File                                 | Covers                                                   |
| ------------------------------------ | -------------------------------------------------------- |
| `docs/design/system-architecture.md` | Overall system components, service boundaries, data flow |
| `docs/design/database-design.md`     | Schema, tables, relationships, migrations                |
| `docs/design/api-design.md`          | Endpoints, contracts, auth, versioning                   |
| `docs/design/devops.md`              | CI/CD, deployment, infrastructure, monitoring            |
| `docs/design/security.md`            | Auth flow, data protection, threat model                 |

## Important Rules

1. **Design Doc = current state.** Never use past tense. If something was removed, remove it from the Design Doc.
2. **LLD = evolving record.** LLDs capture the original design AND track deviations — use the changelog to record when reality diverged from the original plan (bug discoveries, scope changes, implementation pivots).
3. **Diagrams must match.** If an LLD shows a sequence diagram involving Service A → Service B, and a Design Doc shows the architecture, both must agree on the service names and relationships.
4. **Don't bloat Design Docs.** The Design Doc is an overview. Detailed implementation goes in the LLD. The Design Doc links to relevant LLDs.

## Changelog on All Doc Types

All docs (Feature LLDs, Bug Reports, ADRs, Policies, Design Docs) require a Changelog section.

**Why:** Feature LLDs without a changelog become stale silently. When the implementation
deviates from the design — a storage path changes, a table is added, a decision is reversed —
there is no record of why. BUG-002 (linear adapter broken pipeline) was a direct consequence
of code that diverged from its intended design with no doc update and no changelog.

**Format for non-Design-Doc docs** (simpler, no Feature column needed):

```markdown
## Changelog

| Date | Change |
|---|---|
| YYYY-MM-DD | Initial draft |
| YYYY-MM-DD | Updated — [reason reality changed from original design] |
```

**When to add an entry:**
- Doc is first written (always)
- Status changes (Draft → Implemented → Verified)
- Implementation deviates from the documented design
- New information discovered during implementation changes scope or approach
