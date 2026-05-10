# Feature: orchestra v1.5 — Archive + Supersession File Conventions (LLD-006)

> **Doc ID:** 006-archive-and-supersession-conventions
> **Date:** 2026-05-07
> **DRI:** Hassan Mohiddin
> **Type:** Feature LLD
> **Status:** Rejected
> **Iteration:** 1
> **Reason:** Promotion rule branch 2: r4 reached canon-frozen (conditional_pass) on 2026-05-08; r1 was never canon-frozen → Rejected per Glossary promotion rule. r1 review (`docs/reviews/006-r1.review.yaml`) returned 12 findings.

## Glossary

- **canon doc** — reviewed, currently-active doc whose Status ∈ {Draft, Proposed, Approved, In Progress, Implemented, Verified, Investigating, Fix Applied, Current}. Lives at top-level type directory: `docs/features/`, `docs/bugs/`, `docs/adr/`, `docs/design/`, `docs/postmortems/`, `docs/runbooks/`, `docs/plans/`.
- **archived doc** — doc whose Status is {Rejected, Superseded}. Lives at `docs/archive/<type>/`. NOT eligible as `Refs:` target.
- **supersession** — process by which a new doc revision replaces a prior canon doc. New file created (never in-place edit); prior file moved to archive with `Status: Superseded` + `Superseded by: <new path>` frontmatter field.
- **doc-id burn** — policy that doc-ids are NEVER reused. Once doc-id N is assigned (even to a Rejected doc), N is permanently retired. New LLDs/BUGs/ADRs use the next available number.
- **rejection** — process by which a draft doc is abandoned without producing a successor of the same scope. The doc moves to archive with `Status: Rejected` + reason. Doc-id is burned.

## Problem Statement

orchestra v1.0–1.4 has no convention for handling docs whose lifecycle ends in revision or abandonment. Three concrete defects observed:

1. **Filesystem clutter when revisions accumulate.** LLD-005 attempt 2026-05-07 produced `005-v1.5-enforcement-core.md` (r1) + `005-v1.5-enforcement-core-r2.md` (r2). Both Rejected after bootstrap subagent reviews failed. Both currently sit in `docs/features/` alongside canonical docs (001, 002, 003), creating confusion: a fresh reader cannot tell which 005 is current canon vs which is archived attempt.
2. **No supersession-vs-override decision encoded.** Override (in-place edit of canon doc) loses audit trail, breaks fresh-reviewer ability to diff, and conflicts with the roll-forward principle (Redgate, Atlas, Temporal saga, ADR pattern). Supersession (new file with `Supersedes:` link) preserves audit but produces N files for N revisions — needs a home.
3. **Doc-id reuse is undefined.** When LLD-005 was abandoned, "doc-id 005" sat in ambiguity: reuse for the new smaller-scope LLD or burn? Reuse erases the historical fact that 005 was attempted and rejected. Burn preserves history at the cost of one integer per failed attempt.

These defects are organizational, not architectural — but they block ANY further LLD work because every subsequent rejection/supersession would compound the clutter.

## Success Criteria

### Acceptance items (testable)

- [ ] `docs/archive/<type>/` directory convention documented in STANDARDS.md
- [ ] Supersession-via-new-file pattern documented in STANDARDS.md (NEVER in-place edit reviewed canon)
- [ ] Doc-id-burn policy documented in STANDARDS.md
- [ ] `cli/lint.py` rejects any `Refs:` line pointing into `docs/archive/` (lint exit 1)
- [ ] `cli/lint.py` rejects in-place edit of canon docs whose Status was previously {Implemented, Verified, Approved, Current} via git diff inspection at commit-msg hook time
- [ ] `skills/design-docs/SKILL.md` updated to describe supersession + archive workflow
- [ ] `skills/design-docs/init/prompts.md` updated (no behavioral change, just terminology refresh)
- [ ] `cli/templates/standards-default-7.md` updated (template for new orchestra adopters ships these conventions)
- [ ] Existing rejected files moved: `docs/features/005-v1.5-enforcement-core.md` + `docs/features/005-v1.5-enforcement-core-r2.md` → `docs/archive/features/` (preserve filenames)
- [ ] Reviews stay in `docs/reviews/` (not moved); review files reference new archive paths in their `doc_subject.path` field via post-move update
- [ ] All v1.4 tests pass (85 baseline confirmed via `python -m pytest tests/` 2026-05-07; baseline output shown in §Testing)
- [ ] 2 new tests for archive lint behavior (positive + negative)
- [ ] 1 new eval scenario (`archive-refs-blocked`)
- [ ] Plugin version bumped 1.4.0 → 1.5.0 (1.4 was rolled back)

### Deliverables (recorded for sign-off, not lint-checkable)

- [ ] `docs/design/orchestra-philosophy.md` Changelog appended with v1.5 entry summarizing this LLD + LLD-007 (when shipped)
- [ ] README.md updated to reference STANDARDS.md archive section
- [ ] `docs/features/005-*.md` files retain Status: Rejected header (already set 2026-05-07; verify post-move)

## Scope

### In Scope

1. **Archive directory convention**: `docs/archive/<type>/` for all rejected + superseded docs. Type subdir mirrors top-level (`docs/archive/features/`, `docs/archive/bugs/`, etc.).
2. **Supersession workflow** (file-level; backward-flow process workflow deferred to later LLD):
   - Never in-place edit reviewed canon doc
   - New revision = new file with frontmatter `Supersedes: <prior path>`
   - Prior doc's frontmatter updated: `Status: Superseded`, `Superseded by: <new path>`
   - Prior doc moved from `docs/<type>/` to `docs/archive/<type>/`
3. **Rejection workflow**:
   - Draft doc abandoned without successor → move to archive with `Status: Rejected` + reason
   - Doc-id burned (never reused for new doc)
4. **Doc-id-burn policy**: enforced by linter — new doc-id must be > max(all doc-ids in `docs/<type>/` ∪ `docs/archive/<type>/`).
5. **Lint blocks Refs into archive**: `Refs: docs/archive/...` triggers commit-msg hook failure.
6. **Lint blocks in-place edit of canon-with-prior-Status**: any commit modifying a doc whose previously-committed Status was Implemented/Verified/Approved/Current fails unless the diff includes the supersession move.
7. **Skill + STANDARDS update** to document all of the above.
8. **Migration of existing rejected docs** (005 r1 + r2) as the dogfood test case.

### Out of Scope

- Spec-review subagent + attestation (LLD-007 — separate ship)
- Memory architecture / 4-placement (later LLD)
- Lesson capture (later LLD)
- Backward-flow process workflow (Pillar 5 of rejected LLD-005-r2 — split into "file convention" here + "process flow" in a later LLD; this LLD covers ONLY the file-level mechanic)
- Skills registry (LLD-008+ TBD)
- AST-level drift detection
- Modifying existing canon docs (001-003 LLDs, ADR-001, philosophy, BUG-001..008) to use new conventions retroactively — they remain as-is unless they're revised, in which case the new convention applies

## Design

### Archive directory convention

```
docs/
├── archive/
│   ├── features/
│   │   ├── 005-v1.5-enforcement-core.md         # rejected (was at docs/features/005-...)
│   │   └── 005-v1.5-enforcement-core-r2.md      # rejected (was at docs/features/005-...-r2)
│   ├── bugs/                                     # populated when first BUG is rejected/superseded
│   ├── adr/
│   ├── design/
│   ├── postmortems/
│   ├── runbooks/
│   └── plans/
├── features/                                     # canon LLDs (001, 002, 003, 006...)
├── bugs/                                         # canon BUGs
├── adr/
├── design/
├── postmortems/
├── runbooks/
├── plans/
├── reviews/                                      # NEVER moved to archive; permanent attestation record
└── investigations/                               # scratch (gitignored or as configured); NEVER archived (it's already non-canon)
```

`docs/reviews/` is NOT mirrored under archive. Reviews are append-only attestations bound to immutable content_hash; they remain valid evidence regardless of subject doc's lifecycle.

### Supersession workflow (file-level mechanic)

```
INITIAL STATE:
  docs/features/NNN-foo.md   (Status: Implemented)

WHEN GAP DISCOVERED:
  1. Create docs/features/NNN-foo-r2.md with frontmatter:
       > Doc ID: NNN-foo-r2
       > Iteration: 2
       > Supersedes: docs/features/NNN-foo.md
       > Status: Draft
  2. Author + reviewer iterate on r2 (review process out of scope for THIS LLD; defined in LLD-007)
  3. When r2 is reviewed-and-accepted (Status flips to Approved or higher):
     a. Update r1's frontmatter:
          > Status: Superseded
          > Superseded by: docs/archive/features/NNN-foo-r2.md  ← path AFTER move
       (initial commit can use docs/features/NNN-foo.md path, then update during the move; OR use repo-relative resolution at lint time)
     b. Move r1 from docs/features/ to docs/archive/features/
     c. The NEW canon (r2) stays at docs/features/NNN-foo-r2.md until its own supersession event

ON FURTHER REVISION (r3):
  Same pattern. r3 supersedes r2. r2 moves to docs/archive/features/ alongside r1.
  At any time, exactly one revision lives at docs/features/ — the latest canon.
```

Critical rule: **NEVER in-place edit reviewed canon.** A doc whose Status was previously Implemented/Verified/Approved/Current cannot be modified except to:
- Append a Changelog entry (allowed, narrow exception — no body changes)
- Update Status field (e.g. Implemented → Verified)
- Update Superseded by + Status during supersession move

Any other change requires supersession.

### Rejection workflow

```
INITIAL STATE:
  docs/features/NNN-foo.md   (Status: Draft, never reached Approved)

WHEN ABANDONED:
  1. Update frontmatter:
       > Status: Rejected
       > Reason: <one-line summary>
  2. Move to docs/archive/features/
  3. Doc-id NNN is BURNED. Next LLD uses NNN+1.

NO successor doc is implied. (Distinction from supersession.)
```

### Doc-id-burn policy

For each type directory, lint computes:
```
max_id = max(parse_id(p) for p in docs/<type>/*.md ∪ docs/archive/<type>/*.md)
next_id = max_id + 1
```

When a new doc is added, lint checks: `parse_id(new_doc) > max_id` (strictly greater). Reuse rejected.

This burns ~1 integer per rejected doc-id, accepted cost for preserved history.

### Lint changes

Two new checks added to `cli/lint.py`:

**Check L1 (commit-msg hook):** No `Refs:` line points into `docs/archive/`.

```python
ARCHIVE_REFS_RE = re.compile(r"^Refs:\s+docs/archive/", re.MULTILINE)

def lint_commit_no_archive_refs(commit_body: str) -> list[Finding]:
    if ARCHIVE_REFS_RE.search(commit_body):
        return [Finding("error", "commit-msg",
            "Refs: line points into docs/archive/. Archived docs are not valid references; "
            "Refs must point to canon docs in docs/<type>/ only.")]
    return []
```

**Check L2 (commit-msg hook):** Canon-doc in-place-edit is rejected when Status is past-Draft.

```python
def lint_commit_no_canon_inplace_edit(repo_root: Path, staged_files: list[str]) -> list[Finding]:
    findings = []
    for path in staged_files:
        if not path.startswith(("docs/features/", "docs/bugs/", "docs/adr/",
                                "docs/design/", "docs/postmortems/", "docs/runbooks/")):
            continue
        # Read prior committed version of the file (HEAD~1)
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"HEAD:{path}"], cwd=repo_root, text=True)
        except subprocess.CalledProcessError:
            continue  # New file, no prior version
        prior_status = parse_status(prior_text)
        if prior_status in {"Implemented", "Verified", "Approved", "Current",
                            "Fix Applied"}:
            # Check current diff is allowed-narrow (Changelog append + Status field only)
            new_text = (repo_root / path).read_text()
            if not is_narrow_change(prior_text, new_text):
                findings.append(Finding("error", path,
                    f"Doc Status was {prior_status} (canon-frozen). "
                    f"Use supersession (new file with Supersedes:) instead of in-place edit. "
                    f"See STANDARDS.md § Supersession Workflow."))
    return findings
```

`is_narrow_change()` allows Changelog row appends, Status field updates, and Superseded by/Supersedes field updates ONLY. Implementation: parse both texts, diff section-by-section, fail if any section other than Changelog/frontmatter changed.

### STANDARDS.md update

New section after § Spec Review Rule:

```markdown
## Archive Convention

Rejected and superseded docs live in `docs/archive/<type>/`. Canon docs live at top-level type directories. Reviews (`docs/reviews/`) are append-only attestations and never move.

Lifecycle terminal states:
- **Rejected** — draft abandoned, no successor; doc-id burned.
- **Superseded** — replaced by a newer revision; new revision (`-r<N>` suffix) lives at canon path; old revision moves to archive with `Superseded by:` frontmatter link.

## Supersession Workflow

NEVER in-place edit reviewed canon docs. Reviewed canon = doc whose Status was Implemented, Verified, Approved, Current, or Fix Applied. Allowed in-place changes:
- Append Changelog row
- Update Status field (lifecycle progression)
- Update Superseded by / Supersedes link fields during supersession

Anything else requires supersession:
1. Create `<type>/NNN-name-r<N+1>.md` with `Supersedes: <prior path>` frontmatter
2. Iterate + review r<N+1> until Approved
3. Update prior file frontmatter: `Status: Superseded`, `Superseded by: <new path>`
4. Move prior file to `docs/archive/<type>/`

## Doc-ID Burn Policy

Doc-ids are never reused. New doc-id must be strictly greater than max(all doc-ids in canon + archive of that type). Lint enforces.

## Refs: Line Restriction

`Refs:` lines on `fix:` / `feat:` commits must point to canon docs only. Archive references are rejected.
```

### design-docs skill update

`skills/design-docs/SKILL.md` adds a new section after the existing workflow description:

```markdown
## Archive + Supersession (v1.5+)

When you need to revise a reviewed doc:
1. NEVER edit in place. Status: Implemented/Verified/Approved/Current is canon-frozen.
2. Create new revision file: `<type>/NNN-name-r<N+1>.md` with `Supersedes: <prior>` frontmatter.
3. Run review (Gate 3) on the new revision (see LLD-007 when shipped).
4. After acceptance, update prior file's frontmatter (`Status: Superseded`, `Superseded by:`) and move it to `docs/archive/<type>/`.

When abandoning a draft (no successor planned):
1. Update doc frontmatter: `Status: Rejected`, `Reason: <one-line>`.
2. Move to `docs/archive/<type>/`.
3. Doc-id is burned. New LLDs use the next-greater number.

`Refs:` lines must point to canon docs only. Lint blocks references to archived docs.
```

### Migration of existing rejected docs

Two `mv` operations + frontmatter touch-ups (Status fields already set 2026-05-07):

```bash
git mv docs/features/005-v1.5-enforcement-core.md docs/archive/features/005-v1.5-enforcement-core.md
git mv docs/features/005-v1.5-enforcement-core-r2.md docs/archive/features/005-v1.5-enforcement-core-r2.md
```

Update `docs/reviews/005-r1.review.yaml` and `docs/reviews/005-r2.review.yaml` to reference new paths in `doc_subject.path` field. (Manual edit; small mechanical change.)

After migration:
- Next LLD that addresses the v1.5 enforcement-core scope uses doc-id 007+ (005 + 006 are burned/used)
- `docs/features/` shows only canon: 001, 002, 003, 006 (this LLD)

## Edge Cases

- **Doc moved to archive but reviews/<doc-id>-rN.review.yaml still points at old path.** Mitigation: post-move update of `doc_subject.path` field. Reviews remain valid (content_hash unchanged); only path reference updates.
- **Two sibling supersession candidates** (`NNN-foo-r2.md` and `NNN-foo-r2-alt.md` both drafted). Lint detects via Supersedes link analysis: if two non-superseded candidates exist with same `Supersedes:` target, surfaces conflict + requires user to abandon one.
- **In-place edit of canon required for typo / link rot fix.** Allowed narrow exception: `is_narrow_change()` permits Changelog append + Status update + Superseded fields. Pure typo fix in body content is NOT permitted under v1.5 — must supersede. Friction is intentional (forces the question: is this a typo or a meaning change?). User can override via `--allow-canon-edit` flag with audit log to metrics.jsonl.
- **Archive folder grows large over years.** No enforced TTL; storage is cheap, history valuable. Tooling can add `cli.archive --summary` (deferred).
- **Doc never reached Approved (still Draft) and is being abandoned.** Rejection path: Status: Rejected + move to archive. Doc-id burned. No successor.
- **Lint runs on a freshly-cloned repo with no git history.** L2 in-place-edit check needs `git show HEAD~1:<path>` which may fail on first commit. Lint falls back to "skip canon-edit check on missing prior" — first commit can't violate the rule because there's no prior canon.
- **Migration from v1.4 (no archive convention) to v1.5.** Existing rejected/superseded docs (if any) stay in place until user runs `cli.upgrade --migrate-archives`. Opt-in. Doc-ids in legacy positions still trigger burn-policy lint (max-id includes both top-level and archive).
- **User force-deletes an archive file.** Lint cannot detect (file simply absent). Documented as a "don't do that" — git history retains.
- **Same content_hash across two doc files** (e.g. someone copies). content_hash bound to attestation, not to canon path; reviews would treat them as same subject. Operationally rare; documented edge.

## Security

- **Path traversal in `Refs:`.** `Refs:` line is regex-matched; the only paths accepted are repo-relative under `docs/`. Absolute paths or `..` rejected by existing lint.
- **In-place-edit override flag (`--allow-canon-edit`).** Logged to `metrics.jsonl` with diff hash; audit trail preserved. Future LLD may require explicit user-confirm.
- **`docs/archive/` content visibility.** Archive is in-repo, version-controlled. No new exposure surface. mkdocs site can hide archive nav with a one-line config (deferred to user choice).

## Testing

### Pytest baseline (verified)

```
$ python -m pytest tests/
============================== 85 passed in 6.60s ==============================
```

(2026-05-07 confirmed; output captured directly.)

### New unit tests (≥2)

| Test file | Coverage |
|---|---|
| `tests/test_lint_archive_refs.py` | Refs into `docs/archive/` rejected; Refs into `docs/<type>/` accepted (positive + negative + edge: trailing slash) — 3 tests |
| `tests/test_lint_canon_inplace_edit.py` | In-place body edit of Implemented doc rejected; Changelog append accepted; Status field update accepted; brand-new doc accepted — 4 tests |
| `tests/test_lint_doc_id_burn.py` | New doc with id ≤ max(canon ∪ archive) rejected; new doc with id = max+1 accepted — 2 tests |

Total new: 9 tests. Suite: 85 + 9 = 94.

### New eval scenario

| Scenario | What |
|---|---|
| `archive-refs-blocked` | Fixture repo with `docs/archive/features/005-old.md`. Stage commit with `Refs: docs/archive/features/005-old.md`. Verify lint exits 1 with archive-rejection message. |

### Manual verification

- After migration: `docs/features/` lists only 001, 002, 003, 006 (cosmetic check).
- `git log` on archived files preserves full history.
- `docs/reviews/005-r{1,2}.review.yaml` doc_subject.path field correctly points into archive.

## Related Documents

- `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` — Round 1-5 research informing v1.5 architecture
- `docs/archive/features/005-v1.5-enforcement-core.md` — rejected r1 (post-move); canonical example of dogfood
- `docs/archive/features/005-v1.5-enforcement-core-r2.md` — rejected r2 (post-move)
- `docs/reviews/005-r1.review.yaml` — r1 attestation (FAIL verdict)
- `docs/reviews/005-r2.review.yaml` — r2 attestation (FAIL verdict)
- `docs/features/001-design-docs-init.md` — original cli.lint design (still canon)
- `docs/design/orchestra-philosophy.md` — to be updated with v1.5 entry post-merge
- ADR pattern (joelparkerhenderson/architecture-decision-record GitHub) — supersession pattern source
- Roll-forward database migrations (Redgate, Atlas) — supersession-vs-override industry practice

## Changelog

| Date | Change |
|---|---|
| 2026-05-07 | Initial draft. Status: Draft. Scope: archive convention + supersession file mechanic + doc-id-burn + lint blocks + skill update + STANDARDS update. Migration of existing 005 r1+r2 included as dogfood. Spec review (LLD-007) and backward-flow process (later LLD) explicitly out of scope to keep this LLD reviewable in one pass. Bootstrap subagent review pending. |
