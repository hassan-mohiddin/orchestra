# Feature: orchestra v1.5 — Archive + Supersession File Conventions (LLD-006-r2)

> **Doc ID:** 006-archive-and-supersession-conventions-r2
> **Date:** 2026-05-07
> **DRI:** Hassan Mohiddin
> **Type:** Feature LLD
> **Status:** Rejected
> **Iteration:** 2
> **Supersedes:** docs/features/006-archive-and-supersession-conventions.md
> **Reason:** Rejected on r2 review fail (`docs/reviews/006-r2.review.yaml` — 10 findings, 2 critical including doc-id-burn vs supersession self-defeating bug). Promotion rule applies on r4 canon-frozen pass (2026-05-08).

## Glossary

- **canon doc** — currently-active doc whose Status ∈ canon-statuses. Lives at top-level type directory.
- **archived doc** — doc whose Status ∈ {Rejected, Superseded}. Lives at `docs/archive/<type>/`. NOT eligible as `Refs:` target.
- **canon-statuses** (single source of truth) — the set: `{Draft, Proposed, Approved, In Progress, Implemented, Verified, Investigating, Fix Applied, Current}`.
- **canon-frozen statuses** (single source of truth) — the set: `{Approved, Implemented, Verified, Fix Applied, Current}`. These statuses are post-review; in-place edit forbidden except for narrow-changes.
- **narrow change** (single source of truth) — modification to a canon-frozen doc allowed without supersession. Exactly:
  - **Changelog table:** append-only (new row added at end). Row modification or removal forbidden.
  - **Frontmatter fields (whitelisted):** `Status`, `Iteration`, `Superseded by` only. All other frontmatter fields immutable post-review.
  - **No body changes** (any heading/paragraph/code-block change requires supersession).
- **supersession** — process by which a new doc revision replaces a prior canon doc. New file created (never in-place edit); prior file (if ever reached canon) moved to archive with `Status: Superseded` + `Superseded by:` frontmatter field.
- **doc-id burn** — policy that doc-ids are never reused. New doc-id strictly greater than max(canon ∪ archive).
- **rejection** — process by which a draft doc is abandoned without producing a successor of the same scope. Doc moves to archive with `Status: Rejected`.
- **rejected-supersession** (new in r2) — special case: a draft (`Supersedes: <prior>`) gets Rejected before reaching canon. Resolution rule below.
- **filename convention** — first iteration = `NNN-name.md` (no suffix). Each supersession adds suffix: `NNN-name-r2.md`, `NNN-name-r3.md`. Iteration 1 implicit; r2+ explicit.

## Problem Statement

orchestra v1.0–1.4 has no convention for handling docs whose lifecycle ends in revision or abandonment. Three concrete defects observed:

1. **Filesystem clutter when revisions accumulate.** LLD-005 attempt 2026-05-07 produced 005-r1 + 005-r2; both Rejected. Both currently sit in `docs/features/` alongside canonical docs (001, 002, 003), creating confusion: a fresh reader cannot tell which is current canon vs which is archived attempt.
2. **No supersession-vs-override decision encoded.** Override (in-place edit of canon doc) loses audit trail and breaks fresh-reviewer ability to diff. Supersession (new file with `Supersedes:` link) preserves audit but produces N files for N revisions — needs a home and a defined lifecycle.
3. **Doc-id reuse is undefined.** When LLD-005 was abandoned, "doc-id 005" sat in ambiguity: reuse for new LLD or burn? Reuse erases history; burn preserves it at cost of one integer per failed attempt.

These defects are organizational, not architectural. They block ANY further LLD work because every subsequent rejection/supersession would compound the clutter.

### Authority for the supersession-vs-override choice

Supersession (immutable + linked + visible history) over override (in-place edit) is established practice in three reference systems with verifiable sources:

- **ADR pattern.** Michael Nygard's original ADR proposal (2011, https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions ; widely-cited Joel Parker Henderson collection: https://github.com/joelparkerhenderson/architecture-decision-record) — accepted ADRs are immutable; revision = new ADR with `Supersedes:` link.
- **Database migration roll-forward.** Atlas docs on rollbacks: https://atlasgo.io/blog/2024/11/14/the-hard-truth-about-gitops-and-db-rollbacks — production preference is roll-forward (corrective new state) over rewind; preserves audit trail.
- **Temporal saga compensation.** https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas — even "rollback" is implemented as forward-running compensation steps that reference prior state.

Common thread: rewind loses data + audit; corrective forward step retains both.

## Success Criteria

### Acceptance items (testable)

- [ ] `docs/archive/<type>/` directory convention documented in `cli/templates/standards-default-7.md`
- [ ] Supersession-via-new-file pattern documented in STANDARDS template (NEVER in-place edit reviewed canon)
- [ ] Doc-id-burn policy documented in STANDARDS template
- [ ] **Rejected-supersession** rule documented (when a draft `Supersedes: <prior>` is itself Rejected before reaching canon)
- [ ] `cli/lint.py` rejects any `Refs:` line on **any commit type** pointing into `docs/archive/` (exit 1)
- [ ] `cli/lint.py` rejects in-place edit of canon-frozen docs (status ∈ canon-frozen-statuses) when diff is not a `narrow change` (per the Glossary definition); HEAD comparison via `git show HEAD:<path>`
- [ ] `cli/lint.py` rejects new doc-id ≤ max(canon ∪ archive) within type directory
- [ ] `cli/lint.py` enforces attestation `doc_subject.path` resolves to either current path of subject or to path under `docs/archive/` (path-mutation guard)
- [ ] `skills/design-docs/SKILL.md` updated with archive + supersession + rejected-supersession workflow
- [ ] `skills/design-docs/init/prompts.md` updated (terminology refresh; no behavioral change)
- [ ] `cli/templates/standards-default-7.md` updated with archive + supersession + doc-id-burn + Refs sections
- [ ] Existing rejected files moved: `docs/features/005-*.md` (both r1 + r2) → `docs/archive/features/` (preserve filenames). Update `docs/reviews/005-r{1,2}.review.yaml` `doc_subject.path` field after move.
- [ ] Existing **superseded** files (LLD-006-r1 itself, after LLD-006-r2 reaches canon) moved: `docs/features/006-archive-and-supersession-conventions.md` → `docs/archive/features/`. r1 frontmatter updated: `Status: Superseded`, `Superseded by: docs/features/006-archive-and-supersession-conventions-r2.md`.
- [ ] Reviews stay in `docs/reviews/` (not moved); review files reference new archive paths in `doc_subject.path` field via post-move update
- [ ] All v1.4 tests pass (verified baseline 85; see §Testing for command + output)
- [ ] **≥9 new tests** for archive lint behavior (binding floor; testing § enumerates 9 specific tests)
- [ ] 1 new eval scenario (`archive-refs-blocked`) at `eval/scenarios/archive-refs-blocked.json`
- [ ] Plugin version bumped 1.3.0 → 1.5.0 (1.4.0 was never released — work was rolled back via `git reset --hard f88abb7` 2026-05-07; 1.4 follows the same burn logic as burnt doc-ids — never reused)

### Deliverables (recorded for sign-off, not lint-checkable)

- [ ] `docs/design/orchestra-philosophy.md` Changelog appended with v1.5 entry summarizing this LLD + LLD-007 (when shipped). NOTE: Changelog append IS a `narrow change` per Glossary, so does NOT trigger supersession.
- [ ] README.md updated to reference STANDARDS archive section
- [ ] LLD-006-r1 frontmatter updated to `Status: Superseded` + `Superseded by:` field after r2 reaches canon (this is the dogfood demonstration of the supersession primitive on the LLD that defines it)

## Scope

### In Scope

1. **Archive directory convention**: `docs/archive/<type>/` for all rejected + superseded docs. Type subdir mirrors top-level.
2. **Supersession workflow** (file-level mechanic; backward-flow process workflow deferred):
   - Never in-place edit canon-frozen doc beyond a narrow change
   - New revision = new file with `Supersedes: <prior path>` frontmatter
   - Prior doc's frontmatter updated: `Status: Superseded`, `Superseded by: <new path>`
   - Prior doc moved from `docs/<type>/` to `docs/archive/<type>/`
3. **Rejection workflow**: draft abandoned → archive with `Status: Rejected` + `Reason:` field. Doc-id burned.
4. **Rejected-supersession rule (new in r2)**: when a draft (`Supersedes: <prior>` frontmatter) is itself Rejected before reaching canon (Status flow: Draft → Rejected without intervening Approved/Implemented):
   - The Rejected r-N moves to `docs/archive/<type>/` with `Status: Rejected`
   - The prior file's `Status` is NOT changed to `Superseded` (since the supersession attempt failed). The `Superseded by:` field is NEITHER added NOR populated.
   - The Rejected file's `Supersedes:` field is RETAINED (preserves the historical fact that a supersession was attempted)
   - Lint validates: a doc with `Supersedes:` AND `Status: Rejected` does NOT mutate the prior doc's frontmatter
   - Effect on LLD-005 dogfood: r1 + r2 both Rejected → both move to archive; neither carries `Superseded by:`. r2 keeps its `Supersedes: r1` to preserve attempt history.
5. **Doc-id-burn policy**: new doc-id strictly greater than max(canon ∪ archive) within type. Lint enforces.
6. **Lint blocks Refs into archive (all commit types)**: `Refs: docs/archive/...` triggers commit-msg hook failure regardless of `feat:`/`fix:`/`docs:`/etc prefix.
7. **Lint blocks non-narrow in-place edit of canon-frozen docs**: HEAD comparison; allowed only narrow changes per Glossary.
8. **Lint enforces attestation path-mutation guard**: `doc_subject.path` in any attestation must resolve to a real file (either current canon path or `docs/archive/` path).
9. **Skill + STANDARDS update** to document conventions.
10. **Migration of existing 005 r1 + r2** as dogfood test case (Rejected-supersession rule applies — neither retains `Superseded by:`).

### Out of Scope (deferred to other LLDs)

- Spec-review subagent + attestation creation (LLD-007 — separate ship in v1.5 release)
- Memory architecture / 4-placement (later LLD)
- Lesson capture (later LLD)
- Backward-flow PROCESS workflow (the 8-step "halt phase X, return to phase Y" mechanic; this LLD covers only the file-level mechanic, not the process choreography)
- Skills registry (later LLD)
- AST-level drift detection
- Retroactive application of conventions to existing canon docs (001-003, ADR-001, philosophy, BUG-001..008) — they remain as-is unless and until they're revised; the new convention applies to revisions only

## Design

### Decision: Supersession path resolution mechanism

Step 3a of supersession workflow (updating prior r1's `Superseded by:` field at move time) — committed mechanism: **lint resolves `Superseded by:` paths repo-relative at lint time, with both pre-move and post-move paths permitted.**

Concretely:
- When LLD-NNN-r2 reaches canon, author updates r1's frontmatter setting `Superseded by: docs/features/NNN-name-r2.md` (canon path)
- Author then `git mv`s r1 into `docs/archive/features/`
- The `Superseded by:` field continues to reference the canon path of r2 (which is at `docs/features/`); lint accepts this
- If r2 is later itself superseded (r3 created), at THAT point the chain updates: r1's `Superseded by:` may be updated as a `narrow change` to point at archive path of r2 once r2 is moved
- Alternatively, lint may follow the supersession chain transitively via `Superseded by:` links and accept any valid path along the chain

Implementation: `lint_supersession_chain()` traverses `Superseded by:` links; accepts any path that resolves to a real file (canon or archive) AND has `Supersedes:` link back forming a valid pair.

### Archive directory convention

```
docs/
├── archive/
│   ├── features/                   # rejected + superseded LLDs
│   │   ├── 005-v1.5-enforcement-core.md
│   │   ├── 005-v1.5-enforcement-core-r2.md
│   │   └── 006-archive-and-supersession-conventions.md   # post-r2-merge, this LLD's r1 dogfood
│   ├── bugs/
│   ├── adr/
│   ├── design/
│   ├── postmortems/
│   ├── runbooks/
│   └── plans/
├── features/                        # canon LLDs (001, 002, 003, 006-r2 post-merge, ...)
├── bugs/
├── adr/
├── design/
├── postmortems/
├── runbooks/
├── plans/
├── reviews/                         # NEVER moved to archive; permanent attestation record
│                                    # (no archive/reviews/ subdir)
└── investigations/                  # scratch, NEVER archived (already non-canon)
                                    # (no archive/investigations/ subdir)
```

### Supersession workflow (file-level mechanic)

```
INITIAL STATE:
  docs/features/NNN-foo.md   (Status: Implemented)         ← canon, no -rN suffix

WHEN GAP DISCOVERED:
  1. Create docs/features/NNN-foo-r2.md with frontmatter:
       > Doc ID: NNN-foo-r2
       > Iteration: 2
       > Supersedes: docs/features/NNN-foo.md
       > Status: Draft
  2. Author + reviewer iterate on r2 (Gate 3 process — defined in LLD-007)
  3. When r2 reaches canon (Status: Approved/Implemented/Verified):
     a. Update r1 frontmatter (narrow change — permitted in-place):
          > Status: Superseded                                ← whitelisted field
          > Superseded by: docs/features/NNN-foo-r2.md         ← whitelisted field
     b. git mv r1 to docs/archive/features/
  4. The new canon (r2) stays at docs/features/NNN-foo-r2.md until ITS own supersession event

ON FURTHER REVISION (r3):
  Same pattern. r3 created with Supersedes: r2.
  When r3 reaches canon: r2's Superseded by: → r3's path; r2 moves to docs/archive/features/.
```

### Rejection workflow

```
DRAFT NEVER REACHED CANON:
  docs/features/NNN-foo.md   (Status: Draft, never advanced past review failure)

WHEN ABANDONED:
  1. Update frontmatter (narrow change permitted):
       > Status: Rejected
       > Reason: <one-line summary>
  2. git mv to docs/archive/features/
  3. Doc-id NNN burned. Next LLD uses NNN+1.

NO successor doc implied.
```

### Rejected-supersession rule (NEW, dogfood-driven)

```
WHEN DRAFT WITH `Supersedes:` IS ITSELF REJECTED:
  e.g. r2 has frontmatter `Supersedes: r1` AND `Status: Rejected`
       (r2 attempted to supersede r1 but its own review failed; both r1 + r2 are now terminal)

  RULE:
  - r2 moves to docs/archive/<type>/ with Status: Rejected
  - r2's `Supersedes:` field is RETAINED (preserves historical attempt fact)
  - r1's frontmatter is NOT mutated:
      → Status remains whatever it was (Draft / Implemented / etc — pre-supersession-attempt state)
      → `Superseded by:` field is NEITHER added NOR populated
  - If r1 was canon (Status ∈ canon-frozen) before r2 was attempted, r1 STAYS canon
  - If r1 was also itself Rejected (e.g. LLD-005 case), both move to archive separately

LINT VALIDATION:
  - For any file with `Status: Rejected` AND `Supersedes: <prior>`:
    - The prior path's frontmatter must NOT contain `Superseded by:` pointing back to the Rejected file
    - This is the rejected-supersession invariant
  - Implementation:
    `find docs/<type>/ docs/archive/<type>/ -name '*.md' -exec ...`
```

### File layout (post-LLD-006-r2 merge)

```
docs/
├── archive/
│   ├── features/
│   │   ├── 005-v1.5-enforcement-core.md           # Status: Rejected (LLD-005-r1)
│   │   ├── 005-v1.5-enforcement-core-r2.md        # Status: Rejected (LLD-005-r2; rejected-supersession of r1)
│   │   └── 006-archive-and-supersession-conventions.md  # Status: Superseded (this LLD's r1)
│   └── ... (other types empty until populated)
├── features/
│   ├── 001-design-docs-init.md
│   ├── 002-v1.2-migration-viewer-commit-msg.md
│   ├── 003-v1.3-doc-browser-mkdocs.md
│   └── 006-archive-and-supersession-conventions-r2.md  # canon LLD-006-r2 (this file)
├── reviews/
│   ├── 005-r1.review.yaml              # doc_subject.path → docs/archive/features/005-v1.5-enforcement-core.md
│   ├── 005-r2.review.yaml              # → docs/archive/features/005-v1.5-enforcement-core-r2.md
│   ├── 006-r1.review.yaml              # → docs/archive/features/006-archive-and-supersession-conventions.md
│   └── 006-r2.review.yaml              # → docs/features/006-archive-and-supersession-conventions-r2.md
└── ... (rest unchanged)
```

Note doc-id 005 is burned; doc-id 006 is canon (this r2). Next LLD = 007.

### Lint changes

Three new checks added to `cli/lint.py`:

**Check L1 (commit-msg hook):** No `Refs:` line on any commit type points into `docs/archive/`.

```python
ARCHIVE_REFS_RE = re.compile(r"^Refs:\s+docs/archive/", re.MULTILINE)

def lint_commit_no_archive_refs(commit_body: str) -> list[Finding]:
    if ARCHIVE_REFS_RE.search(commit_body):
        return [Finding("error", "commit-msg",
            "Refs: line points into docs/archive/. Archived docs are not valid references; "
            "Refs must point to canon docs in docs/<type>/ only. (Applies to all commit types.)")]
    return []
```

**Check L2 (commit-msg hook):** Canon-frozen in-place-edit narrow-change check.

```python
CANON_FROZEN_STATUSES = {"Approved", "Implemented", "Verified", "Fix Applied", "Current"}

WHITELIST_FRONTMATTER_FIELDS = {"Status", "Iteration", "Superseded by"}

def lint_commit_no_canon_inplace_edit(repo_root: Path, staged_files: list[str]) -> list[Finding]:
    findings = []
    for path in staged_files:
        if not path.startswith(("docs/features/", "docs/bugs/", "docs/adr/",
                                "docs/design/", "docs/postmortems/", "docs/runbooks/")):
            continue
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"HEAD:{path}"], cwd=repo_root, text=True
            )
        except subprocess.CalledProcessError:
            continue  # New file, no prior version
        prior_status = parse_status(prior_text)
        if prior_status in CANON_FROZEN_STATUSES:
            new_text = (repo_root / path).read_text()
            ok, why = is_narrow_change(prior_text, new_text)
            if not ok:
                findings.append(Finding("error", path,
                    f"Doc Status was {prior_status} (canon-frozen). "
                    f"In-place edit not permitted: {why}. "
                    f"Use supersession (new file with Supersedes: <prior>) instead. "
                    f"See STANDARDS.md § Supersession Workflow."))
    return findings


def is_narrow_change(prior_text: str, new_text: str) -> tuple[bool, str]:
    """Strict whitelist:
    - Frontmatter: only fields in WHITELIST_FRONTMATTER_FIELDS may differ
    - Changelog table: append-only (existing rows unchanged; only new rows allowed)
    - Body (excluding Changelog table): byte-identical
    Returns (allowed, reason_if_not).
    """
    prior_fm, prior_body = split_frontmatter(prior_text)
    new_fm, new_body = split_frontmatter(new_text)

    # 1. Frontmatter check
    fm_diff_keys = {k for k in (set(prior_fm) | set(new_fm))
                    if prior_fm.get(k) != new_fm.get(k)}
    forbidden_changes = fm_diff_keys - WHITELIST_FRONTMATTER_FIELDS
    if forbidden_changes:
        return (False, f"frontmatter fields modified outside whitelist: {sorted(forbidden_changes)}")

    # 2. Changelog table append-only check
    prior_chlog = extract_changelog_table_rows(prior_body)
    new_chlog = extract_changelog_table_rows(new_body)
    if not new_chlog[:len(prior_chlog)] == prior_chlog:
        return (False, "Changelog rows modified or removed (only append allowed)")

    # 3. Body-excluding-Changelog byte-identical
    prior_body_no_chlog = strip_changelog_table(prior_body)
    new_body_no_chlog = strip_changelog_table(new_body)
    if prior_body_no_chlog != new_body_no_chlog:
        return (False, "body content changed outside Changelog (any heading/paragraph/code-block change requires supersession)")

    return (True, "")
```

`split_frontmatter`, `extract_changelog_table_rows`, `strip_changelog_table` are testable helpers; details in implementation.

**Check L3 (lint --doc + commit-msg hook):** Attestation path-mutation guard.

```python
def lint_attestation_path_resolution(repo_root: Path, attestation_paths: list[Path]) -> list[Finding]:
    findings = []
    for ap in attestation_paths:
        attestation = yaml.safe_load(ap.read_text())
        subject_path = attestation.get("doc_subject", {}).get("path", "")
        if not subject_path:
            continue
        full = repo_root / subject_path
        if not full.exists():
            findings.append(Finding("error", str(ap),
                f"attestation doc_subject.path {subject_path!r} does not resolve to a real file. "
                f"Subject doc must exist at canon path (docs/<type>/) or archive path (docs/archive/<type>/)."))
    return findings
```

This catches silent path rewrites: if attestation YAML's `doc_subject.path` is mutated to a path that doesn't exist, lint fails.

### Doc-id-burn policy

Per type:
```python
def next_doc_id(repo_root: Path, doc_type: str) -> int:
    canon_dir = repo_root / "docs" / doc_type
    archive_dir = repo_root / "docs" / "archive" / doc_type
    ids = []
    for d in (canon_dir, archive_dir):
        if not d.exists(): continue
        for p in d.glob("*.md"):
            m = re.match(r"^(\d+)-", p.name)
            if m:
                ids.append(int(m.group(1)))
    return max(ids, default=0) + 1


def lint_doc_id_burn(new_doc_path: Path, repo_root: Path) -> list[Finding]:
    doc_type = infer_type(new_doc_path)
    expected_min = next_doc_id(repo_root, doc_type)
    actual = parse_id(new_doc_path)
    if actual < expected_min:
        return [Finding("error", str(new_doc_path),
            f"doc-id {actual} reuses an existing or burned id; "
            f"next available is {expected_min}.")]
    return []
```

### STANDARDS.md template update

`cli/templates/standards-default-7.md` adds three sections after § Spec Review Rule:

```markdown
## Archive Convention

Rejected and superseded docs live in `docs/archive/<type>/`. Canon docs live at top-level type directories. Reviews (`docs/reviews/`) and investigations (`docs/investigations/`) are append-only / scratch and never move to archive.

Lifecycle terminal states:
- **Rejected** — draft abandoned, no successor; doc-id burned.
- **Superseded** — replaced by a newer revision; new revision lives at canon path; old revision moves to archive with `Superseded by:` frontmatter link.

## Supersession Workflow

NEVER in-place edit reviewed canon docs (Status ∈ {Approved, Implemented, Verified, Fix Applied, Current}). Allowed in-place changes (a "narrow change"):
- Append a Changelog table row (no row modification or removal)
- Update Status field (lifecycle progression)
- Update `Superseded by:` field during supersession move

Anything else requires supersession:
1. Create new revision file `<type>/NNN-name-r<N+1>.md` with `Supersedes:` frontmatter
2. Iterate + review until Approved
3. Update prior file frontmatter (narrow change): `Status: Superseded`, `Superseded by:`
4. `git mv` prior file to `docs/archive/<type>/`

### Rejected-supersession (failed revision attempts)

When a draft (`Supersedes: <prior>`) is itself Rejected before reaching canon:
- The Rejected revision moves to archive with `Status: Rejected`
- The Rejected file's `Supersedes:` field is RETAINED (historical fact)
- The prior file's frontmatter is NOT mutated (no `Superseded by:` added)
- Both files exist independently — the prior remains in its pre-attempt state

## Doc-ID Burn Policy

Doc-ids never reused. New doc-id must be strictly greater than max(canon + archive) of that type. Lint enforces.

## Refs: Line Restriction

`Refs:` lines on any commit type must point to canon docs only. Refs into `docs/archive/` are rejected by lint regardless of commit prefix (`feat:`, `fix:`, `docs:`, `chore:`, etc).
```

### design-docs SKILL.md update

`skills/design-docs/SKILL.md` adds a section after the existing workflow:

```markdown
## Archive + Supersession (v1.5+)

When you need to revise a reviewed canon doc:
1. NEVER edit in place beyond a narrow change (Changelog append + Status field + Superseded by field).
2. Create new revision: `<type>/NNN-name-r<N+1>.md` with `Supersedes:` frontmatter.
3. Run review (Gate 3 — see LLD-007 when shipped).
4. After acceptance: update prior file's frontmatter (narrow change) and `git mv` to `docs/archive/<type>/`.

When abandoning a draft (no successor):
1. Set `Status: Rejected` + `Reason:` field.
2. `git mv` to `docs/archive/<type>/`.
3. Doc-id is burned.

When a revision attempt itself fails review (rejected-supersession):
- The failed revision moves to archive as Rejected.
- Its `Supersedes:` field is retained (historical fact).
- The prior file is NOT mutated.

`Refs:` lines must point to canon docs only. Lint blocks references to archive on any commit type.
```

### Migration of existing rejected docs (dogfood test)

Migration steps (post-r2-merge):

```bash
# Move LLD-005 r1 + r2 (both Rejected — rejected-supersession case)
git mv docs/features/005-v1.5-enforcement-core.md docs/archive/features/
git mv docs/features/005-v1.5-enforcement-core-r2.md docs/archive/features/

# Move LLD-006-r1 (will be Superseded by this r2 once r2 reaches canon)
# (Performed AFTER r2 attestation passes Gate 3:)
git mv docs/features/006-archive-and-supersession-conventions.md docs/archive/features/

# Update review YAMLs to reference new paths in doc_subject.path
# (Manual edits to docs/reviews/005-r{1,2}.review.yaml and docs/reviews/006-r1.review.yaml)
```

Per rejected-supersession rule:
- LLD-005-r2 keeps `Supersedes: docs/features/005-v1.5-enforcement-core.md` frontmatter (historical attempt fact)
- LLD-005-r1 does NOT get `Superseded by:` — neither r1 nor r2 reached canon
- LLD-006-r1 GETS `Superseded by: docs/features/006-archive-and-supersession-conventions-r2.md` because r2 reaches canon

## Edge Cases

- **Doc moved to archive but reviews/<doc-id>-rN.review.yaml still points at old path.** Mitigation: post-move update of `doc_subject.path` field; lint Check L3 catches stale paths.
- **Two sibling supersession candidates** (`NNN-foo-r2.md` and `NNN-foo-r2-alt.md` both drafted with same `Supersedes:` target). Lint detects via Supersedes-link analysis: if two non-superseded candidates share `Supersedes:` target, surfaces conflict; user abandons one.
- **In-place edit of canon required for typo / link-rot fix.** Disallowed under v1.5. Forces the question "is this a typo or a meaning change?" Friction is intentional. User can override via `--allow-canon-edit` flag with audit log to metrics.jsonl (deferred — `metrics.jsonl` is LLD-007+).
- **Archive folder grows large over years.** No enforced TTL; storage is cheap, history valuable. Tooling like `cli.archive --summary` deferred.
- **Doc never reached Approved (still Draft) and is being abandoned.** Rejection path applies: Status: Rejected + move to archive. Doc-id burned.
- **Lint runs on freshly-cloned repo with no git history.** Check L2 needs `git show HEAD:<path>`; falls back to "skip canon-edit check on missing prior" — first commit can't violate the rule.
- **Migration from v1.4 (no archive convention) to v1.5.** Existing rejected/superseded docs (if any) stay in place until user runs migration tool. Doc-ids in legacy positions still trigger burn-policy lint (max-id includes both top-level + archive).
- **User force-deletes an archive file.** Lint cannot detect (file simply absent). Documented as anti-pattern; git history retains.
- **Same content_hash across two doc files** (e.g. someone copies). content_hash bound to attestation, not to canon path; reviews would treat as same subject. Operationally rare; documented edge.
- **Rejected-supersession-of-Rejected-supersession** (r3 supersedes r2 which superseded r1; r3 also Rejected without r2 ever having reached canon). Recursive rejected-supersession: both r2 + r3 move to archive Rejected; r1 unchanged. Each `Supersedes:` field retained as historical chain.
- **Philosophy doc Changelog append.** Philosophy.md is canon (Status: Current). Per Glossary, Changelog table append IS a narrow change — permitted in-place. Out-of-Scope clause does NOT contradict this; Out-of-Scope means we don't restructure prior canon's body, but Changelog appends are explicitly allowed.

## Security

- **Path traversal in `Refs:`.** `Refs:` line is regex-matched; only repo-relative paths under `docs/` accepted. Absolute paths or `..` rejected by existing lint.
- **In-place-edit override flag (`--allow-canon-edit`).** Will be logged when metrics.jsonl exists (LLD-007+). For v1.5 (this LLD): flag exists but only emits stderr warning.
- **`docs/archive/` content visibility.** In-repo, version-controlled. No new exposure surface.
- **Attestation YAML path field tampering.** Lint Check L3 enforces path resolves to a real file; stale or fabricated paths fail.

## Testing

### Pytest baseline (verified 2026-05-07)

Captured directly via:
```bash
$ cd /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra
$ /Users/mohammedhassanmohiddin/Documents/Antigravity/SCALE\ APP/.venv/bin/python -m pytest tests/ 2>&1 | tail -3
tests/test_standards_generator.py ...........                            [100%]

============================== 85 passed in 6.60s ==============================
```

This output is the verification artifact. Pytest baseline = 85.

### New unit tests (≥9 binding floor; this list enumerates exactly 9)

| Test file | Test | Coverage |
|---|---|---|
| `tests/test_lint_archive_refs.py` | `test_refs_into_archive_rejected` | Refs `docs/archive/features/x.md` → exit 1 |
| `tests/test_lint_archive_refs.py` | `test_refs_into_canon_accepted` | Refs `docs/features/x.md` → exit 0 |
| `tests/test_lint_archive_refs.py` | `test_refs_archive_with_trailing_slash` | Refs `docs/archive/features/` → exit 1 |
| `tests/test_lint_canon_inplace_edit.py` | `test_inplace_body_change_rejected` | Canon-frozen doc body modified → exit 1 |
| `tests/test_lint_canon_inplace_edit.py` | `test_changelog_append_accepted` | Append Changelog row → exit 0 |
| `tests/test_lint_canon_inplace_edit.py` | `test_status_field_update_accepted` | Status field flip → exit 0 |
| `tests/test_lint_canon_inplace_edit.py` | `test_new_doc_unaffected` | New doc with no prior → exit 0 |
| `tests/test_lint_doc_id_burn.py` | `test_id_le_max_rejected` | New doc-id ≤ existing max → exit 1 |
| `tests/test_lint_doc_id_burn.py` | `test_id_max_plus_1_accepted` | New doc-id = max+1 → exit 0 |

Total new: 9 tests. Suite post-merge: 85 + 9 = 94.

Additional test (deferred to LLD-007 if simpler there): `test_attestation_path_mutation_guard` — Lint Check L3 — covered by an LLD-007 attestation test instead.

### New eval scenario

| Scenario | What |
|---|---|
| `archive-refs-blocked` | Fixture repo with `docs/archive/features/005-old.md`. Stage commit with `Refs: docs/archive/features/005-old.md`. Verify lint exits 1 with archive-rejection message. |

Path: `eval/scenarios/archive-refs-blocked.json` (integrates with existing `eval/run.py` scaffolded in LLD-001).

### Manual verification (post-migration)

- `docs/features/` lists only canonical: 001, 002, 003, 006-r2 (this file)
- `docs/archive/features/` contains: 005 r1, 005 r2, 006 r1
- `git log --follow docs/archive/features/005-v1.5-enforcement-core.md` preserves full history
- `docs/reviews/005-r{1,2}.review.yaml` + `docs/reviews/006-r1.review.yaml` `doc_subject.path` correctly points into archive

## Related Documents

- `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` — Round 1-6 research
- `docs/features/005-v1.5-enforcement-core.md` — rejected r1 (will be at `docs/archive/features/` post-merge)
- `docs/features/005-v1.5-enforcement-core-r2.md` — rejected r2 (will be at `docs/archive/features/` post-merge)
- `docs/features/006-archive-and-supersession-conventions.md` — this LLD's r1 (will be at `docs/archive/features/` post-merge as Superseded)
- `docs/reviews/005-r{1,2}.review.yaml` — LLD-005 attestations
- `docs/reviews/006-r1.review.yaml` — LLD-006-r1 attestation (FAIL with 12 findings; addressed in this r2)
- `docs/features/001-design-docs-init.md` — original `cli.lint` design (still canon)
- `docs/design/orchestra-philosophy.md` — to be updated post-merge (Changelog append, allowed under narrow-change rule)
- ADR pattern: Michael Nygard https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions ; Joel Parker Henderson collection https://github.com/joelparkerhenderson/architecture-decision-record
- Atlas roll-forward: https://atlasgo.io/blog/2024/11/14/the-hard-truth-about-gitops-and-db-rollbacks
- Temporal saga compensation: https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas

## Changelog

| Date | Change |
|---|---|
| 2026-05-07 | r2 written addressing 12 findings from r1 review (`docs/reviews/006-r1.review.yaml`). Resolves: dogfood lifecycle (rejected-supersession rule defined); 3 definitions of canon-frozen unified to {Approved, Implemented, Verified, Fix Applied, Current}; supersession path resolution committed to lint-time chain traversal; `is_narrow_change()` specified testably (frontmatter whitelist + Changelog append-only + body byte-identical); filename convention defined (first iteration no suffix; r2+ explicit); Refs scope expanded to all commit types; test count binding floor 9; version bump explained (1.4 burnt like burnt doc-ids); citations bound to URLs (Nygard, Atlas, Temporal); pytest baseline output captured inline; attestation path-mutation Check L3 added; Out-of-Scope vs philosophy Changelog append reconciled (Changelog append IS a narrow change). Status: Draft. Bootstrap subagent review pending. |
