# Feature: orchestra v1.5 — Archive + Supersession File Conventions (LLD-006-r4)

> **Doc ID:** 006-archive-and-supersession-conventions-r4
> **Date:** 2026-05-08
> **DRI:** Hassan Mohiddin
> **Type:** Feature LLD
> **Status:** Draft
> **Iteration:** 4
> **Supersedes:** docs/features/006-archive-and-supersession-conventions.md
>
> **Note on Supersedes target:** r4's `Supersedes:` field points at r1 (the first-iteration file) as the chain-root pointer. Per promotion rule branch 2 (Glossary), since r1 was never canon-frozen, r1 + r2 + r3 ALL become Rejected when r4 reaches canon-frozen. r4 stays canon at `-r4` filename. r2's `Supersedes: r1` and r3's `Supersedes: r2` frontmatter remain as historical fact (chain audit trail). The `Supersedes:` link semantics are extended in this LLD: it is a chain-root pointer regardless of whether the prior was canon-frozen or Draft (Glossary § Supersedes link semantics, below).

## Glossary (single source of truth)

Two orthogonal axes (definitions disambiguate per r3 review):

- **canon-located doc** — doc that lives at top-level type directory (`docs/<type>/`). Pure filesystem-location concept. Includes Drafts, Proposed, and all canon-frozen statuses. Excludes anything in `docs/archive/`.
- **Refs:-eligible doc** — doc whose Status ∈ canon-frozen-statuses. Independent of location. Drafts are NEVER Refs:-eligible regardless of location.
- (Old term "canon doc" is deprecated. Use canon-located OR Refs:-eligible per intent.)

Status sets:
- **canon-statuses** — `{Draft, Proposed, Approved, In Progress, Implemented, Verified, Investigating, Fix Applied, Current}`. Statuses a canon-located doc may carry.
- **canon-frozen statuses** — `{Approved, Implemented, Verified, Fix Applied, Current}`. Post-review subset. In-place edit forbidden except narrow change.
- **archived statuses** — `{Rejected, Superseded}`. Mutually exclusive with canon-statuses; archived docs live at `docs/archive/<type>/`.

Lifecycles:
- **archived doc** — doc whose Status ∈ archived-statuses. Lives at `docs/archive/<type>/`. NOT Refs:-eligible.
- **narrow change** — modification permitted in-place to a canon-frozen doc. Exactly:
  - Append a Changelog table row (existing rows byte-identical; only NEW rows allowed at end)
  - Modify whitelisted frontmatter fields: `{Status, Iteration, Superseded by}` ONLY
  - **No** body changes outside Changelog table
  - **No** other frontmatter field additions/changes (including no `Reason:` addition)
- **rejection (Draft/Proposed only)** — abandonment of a doc that never reached canon-frozen. Status set to Rejected, `Reason:` field added (permitted because narrow-change rules apply only to canon-frozen; Drafts/Proposeds permit full edit on rejection finalization), file moved to archive, doc-id burned (first-iteration files only). Rejection of a canon-frozen doc is forbidden in-place — requires supersession.
- **rejection-finalization edit** — the one-time edit that flips a Draft/Proposed to Rejected and adds Reason:. Distinct from narrow change (which is canon-frozen-only); permitted because pre-canon-frozen docs are not yet contract-locked.
- **supersession (canon-frozen prior)** — replacement of canon-frozen doc by a new revision. New file created with `-rN` suffix and `Supersedes:` link. Prior canon-frozen doc gets `Status: Superseded` + `Superseded by:` (narrow change), then moves to archive.
- **rejected-supersession** — Draft (`Supersedes: <prior>` frontmatter) is itself Rejected before reaching canon-frozen. Rule: Rejected revision moves to archive with `Supersedes:` retained as historical fact; prior file's frontmatter NOT mutated.
- **Supersedes link semantics** — `Supersedes:` is a chain-root pointer indicating "this revision is part of the iteration chain rooted at the linked first-iteration file." It does NOT imply the linked file was canon-frozen. Both supersession (canon-frozen prior) and promotion-rule branch 2 (all-Drafts chain) use `Supersedes:` to link new revisions to the chain root. Lint validates: target exists in canon-or-archive; target is the first-iteration file matching base-name OR an intermediate `-rN` revision in the same chain.
- **promotion rule (NEW in r4)** — when a chain `r1 ← r2 ← r3 ← ... ← rN` exists (each linked by `Supersedes:`) and `rN` reaches canon-frozen, the lifecycle outcome of intermediate revisions r2..r{N-1} depends on whether r1 was canon-frozen pre-chain:
  - If r1 was canon-frozen: r1 becomes Superseded by rN (skipping intermediate Rejected revisions). r2..r{N-1} become Rejected (rejected-supersession applied retroactively to each).
  - If r1 was never canon-frozen (all of r1..r{N-1} were Drafts): r1..r{N-1} ALL become Rejected; rN is canon-frozen at its `-rN` filename with `Supersedes: r1`.

Filename + ID concepts:
- **doc-id** — the leading integer in a doc filename.
- **base-name** — the post-id slug, NOT including `-rN` suffix.
- **first-iteration filename** — file matching `^(\d+)-([a-z][a-z0-9-]*)\.md$` (NO `-rN` suffix).
- **supersession-iteration filename** — file matching `^(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$` where N≥2.
- **doc-id burn** — applies ONLY to first-iteration filenames. New first-iteration doc-id must be strictly greater than max(all first-iteration doc-ids in canon-located ∪ archive of that type). Supersession-iteration filenames EXEMPT from doc-id-burn; instead, r-suffix must be strictly greater than max existing r-suffix for that base-name (computed by glob excluding the file currently being added).
- **filename convention** — first iteration: `NNN-name.md` (no suffix). Iteration 2+: `NNN-name-r2.md`, `NNN-name-r3.md`. Iteration 1 implicit; r2+ explicit.

## Problem Statement

orchestra v1.0–1.4 has no convention for handling docs whose lifecycle ends in revision or abandonment. Three concrete defects:

1. **Filesystem clutter when revisions accumulate.** LLD-005 attempt 2026-05-07 produced 005-r1 + 005-r2; both Rejected. Both currently sit in `docs/features/` alongside canonical docs (001, 002, 003), creating confusion: a fresh reader cannot distinguish current canon from archived attempt.
2. **No supersession-vs-override decision encoded.** Override (in-place edit of canon doc) loses audit trail and breaks fresh-reviewer ability to diff. Supersession (new file with `Supersedes:` link) preserves audit but produces N files for N revisions — needs a home and a defined lifecycle.
3. **Doc-id reuse undefined.** When LLD-005 was abandoned, "doc-id 005" sat in ambiguity. Reuse erases history; burn preserves it at cost of one integer per failed attempt. The interaction with supersession (which intentionally reuses doc-ids via `-rN` suffix) was previously unhandled.

These defects are organizational. They block any further LLD work because every subsequent rejection/supersession would compound the clutter.

### Authority for the supersession-vs-override choice

Supersession over override is established practice in three reference systems:

- **ADR pattern.** Michael Nygard's original ADR proposal (2011): https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions ; widely-cited Joel Parker Henderson ADR collection: https://github.com/joelparkerhenderson/architecture-decision-record
- **Database migration roll-forward.** Atlas docs on rollbacks: https://atlasgo.io/blog/2024/11/14/the-hard-truth-about-gitops-and-db-rollbacks
- **Temporal saga compensation.** https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas

Common thread: rewind loses data + audit; corrective forward step retains both.

## Success Criteria

### Acceptance items (testable; each maps 1:1 to a test in Testing §)

- [ ] **A1.** `docs/archive/<type>/` directory convention documented in `cli/templates/standards-default-7.md` (manual verification post-merge)
- [ ] **A2.** `cli/lint.py` rejects any `Refs:` line on **any commit type** pointing into `docs/archive/` → test T1
- [ ] **A3.** `cli/lint.py` rejects in-place edit of canon-frozen docs (Status ∈ canon-frozen-statuses) when diff is not a narrow change → tests T2-T5 (4 cases: body change rejected; Changelog append accepted; Status flip accepted; new doc accepted)
- [ ] **A4.** `cli/lint.py` doc-id-burn check rejects first-iteration doc-id ≤ max(first-iteration ids in canon ∪ archive) → tests T6-T7
- [ ] **A5.** `cli/lint.py` doc-id-burn check accepts supersession-iteration filenames (`-rN` suffix) with N strictly greater than max existing N for that base-name → tests T8-T9
- [ ] **A6.** `cli/lint.py` attestation path-mutation guard: `doc_subject.path` in attestation must resolve to an existing file located at EITHER `docs/<type>/...` OR `docs/archive/<type>/...` (NOT investigations/, NOT reviews/, NOT arbitrary) → test T10
- [ ] **A7.** `skills/design-docs/SKILL.md` updated with archive + supersession + rejected-supersession workflow (manual verification post-merge)
- [ ] **A8.** `skills/design-docs/init/prompts.md` updated with terminology refresh (manual verification post-merge)
- [ ] **A9.** `cli/templates/standards-default-7.md` updated with archive + supersession + doc-id-burn + Refs sections (manual verification post-merge)
- [ ] **A10.** Migration BEFORE merge: `docs/features/005-v1.5-enforcement-core.md` and `docs/features/005-v1.5-enforcement-core-r2.md` exist at canon path. Migration AFTER merge: both moved to `docs/archive/features/`; review YAMLs at `docs/reviews/005-r{1,2}.review.yaml` updated `doc_subject.path` field to archive paths
- [ ] **A11.** Migration BEFORE merge: LLD-006 r1 + r2 + r3 + r4 exist at canon path; all Status: Draft. Migration AFTER merge (per promotion rule, since r1 was never canon-frozen): r1 + r2 + r3 ALL receive `Status: Rejected` + `Reason: <one-line>` (rejection-finalization edit permitted since all are Drafts); all moved to `docs/archive/features/`. r4 stays at canon path with `-r4` suffix. r4 retains `Supersedes: docs/features/006-archive-and-supersession-conventions.md` (which after migration resolves to `docs/archive/features/006-archive-and-supersession-conventions.md` per Lint-resolution rule below). Review YAMLs at `docs/reviews/006-r{1,2,3}.review.yaml` updated `doc_subject.path` field to archive paths.
- [ ] **A12.** Reviews stay in `docs/reviews/` (NOT moved to archive); only `doc_subject.path` field updated post-move
- [ ] **A13.** All v1.4 baseline tests pass: 85 (verified via captured pytest output in §Testing)
- [ ] **A14.** Binding floor: ≥13 new tests for v1.5 archive/supersession lint (Testing § enumerates exactly 13: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10a, T10b, T10c, T11)
- [ ] **A15.** 1 new eval scenario at `eval/scenarios/archive-refs-blocked.json` integrated with existing `eval/run.py` from LLD-001
- [ ] **A16.** Plugin version: 1.3.0 → 1.5.0. (Single rationale: v1.4 work was rolled back via `git reset --hard f88abb7` 2026-05-07 before any tag/release; semver position 1.4.0 is therefore burned by the same convention as burned doc-ids — never reused.)

### Deliverables (recorded for sign-off, not lint-checkable)

- [ ] D1. `docs/design/orchestra-philosophy.md` Changelog table appended with v1.5 entry (this IS a narrow change per Glossary, NOT supersession)
- [ ] D2. README.md updated to reference STANDARDS archive section
- [ ] D3. Post-merge dogfood: LLD-006-r1 + r2 + r3 all become Status: Rejected per promotion rule branch 2 (none reached canon-frozen); rejection-finalization edits applied via cli.lifecycle reject; all moved to `docs/archive/features/`. r4 stays canon at `-r4` filename. Aligns with A11.

## Scope

### In Scope (one principle: rule must apply consistently to its own LLD)

1. **Archive directory convention**: `docs/archive/<type>/` for rejected + superseded docs.
2. **Supersession workflow** (file-level mechanic only):
   - Never in-place edit canon-frozen doc beyond narrow change
   - New revision = new file with `-rN` suffix + `Supersedes: <prior>` frontmatter
   - Prior canon-frozen doc gets `Status: Superseded` + `Superseded by:` (narrow change permits this)
   - Prior file `git mv`'d to `docs/archive/<type>/`
3. **Rejection workflow** (Draft/Proposed only — canon-frozen rejection requires supersession): set Status: Rejected, add Reason: field, move to archive, burn doc-id (if first-iteration).
4. **Rejected-supersession rule**: Draft `Supersedes: <prior>` itself Rejected → revision moves to archive Rejected; `Supersedes:` retained; prior NOT mutated.
5. **Doc-id-burn policy** (first-iteration files only): new first-iteration doc-id strictly > max first-iteration ids. Supersession-iteration filenames exempt from burn — instead require strict-greater r-suffix per base-name.
6. **Refs lint**: `Refs:` on any commit type points to Refs:-eligible doc only. Lint rejects Refs into `docs/archive/`, `docs/investigations/`, `docs/reviews/`, or any path outside `docs/<canon-type>/<id>-name.md` pattern.
7. **In-place edit lint**: canon-frozen docs reject non-narrow changes via HEAD diff.
8. **Attestation path-mutation lint**: `doc_subject.path` in any `docs/reviews/*.yaml` must resolve to existing file at `docs/<type>/` OR `docs/archive/<type>/`.
9. **Skill + STANDARDS update**.
10. **Dogfood migration** of LLD-005 (rejected-supersession case) + LLD-006 r1/r2 (supersession case) post-merge.

### Out of Scope (deferred)

- Spec-review subagent + attestation creation logic (LLD-007)
- Memory architecture / 4-placement (later)
- Lesson capture (later)
- Backward-flow PROCESS workflow (later — this LLD is file-level only)
- Skills registry (later)
- AST-level drift detection
- Retroactive convention application to existing canon docs (001-003 LLDs, ADR-001, philosophy, BUG-001..008) — applies on next revision only
- `metrics.jsonl` event logging (LLD-007+)

## Design

### Decision: Supersession path resolution (committed; no alternatives)

Lint resolves `Superseded by:` paths repo-relative at lint time. Specifically:

- `Superseded by:` field value is parsed as a repo-relative path string
- Lint checks: path resolves to an existing file in either `docs/<type>/<id>-...-rN.md` OR `docs/archive/<type>/<id>-...-rN.md`
- Lint follows the supersession chain transitively (r1 → r2 → r3 → ... → current-canon) by reading `Superseded by:` of each archived file
- Lint rejects: cycles (r2 superseded by r3 which is superseded by r2), broken links (path doesn't exist), self-supersession

Single mechanism. No "alternatively." (P3 checklist item.)

### Archive directory convention

```
docs/
├── archive/
│   ├── features/
│   │   ├── 005-v1.5-enforcement-core.md         # Status: Rejected (LLD-005 r1)
│   │   ├── 005-v1.5-enforcement-core-r2.md      # Status: Rejected (LLD-005 r2; rejected-supersession)
│   │   ├── 006-archive-and-supersession-conventions.md     # Status: Rejected (LLD-006 r1; promotion rule branch 2)
│   │   ├── 006-archive-and-supersession-conventions-r2.md  # Status: Rejected (LLD-006 r2; promotion rule branch 2)
│   │   └── 006-archive-and-supersession-conventions-r3.md  # Status: Rejected (LLD-006 r3; promotion rule branch 2)
│   └── ... (other types empty until populated)
├── features/
│   ├── 001-design-docs-init.md
│   ├── 002-v1.2-migration-viewer-commit-msg.md
│   ├── 003-v1.3-doc-browser-mkdocs.md
│   └── 006-archive-and-supersession-conventions-r4.md  # canon LLD-006-r4 (this file, post-merge)
├── reviews/                                       # NEVER moved; permanent attestations
└── investigations/                                # scratch; NEVER archived
```

### Supersession workflow (file-level mechanic)

```
INITIAL STATE:
  docs/features/NNN-foo.md   (Status: Implemented)         ← canon-frozen, no -rN suffix

WHEN GAP DISCOVERED:
  1. Create docs/features/NNN-foo-r2.md frontmatter:
       Doc ID: NNN-foo-r2
       Iteration: 2
       Supersedes: docs/features/NNN-foo.md
       Status: Draft
  2. Author + reviewer iterate on r2 (Gate 3 process — LLD-007)
  3. r2 reaches canon-frozen (Status: Approved/Implemented/Verified):
     a. Update r1 frontmatter (narrow change):
          Status: Superseded
          Superseded by: docs/features/NNN-foo-r2.md
     b. git mv r1 to docs/archive/features/
  4. r2 stays at docs/features/ until ITS own supersession event

ON FURTHER REVISION (r3):
  Same pattern. Create r3 with Supersedes: r2.
  When r3 reaches canon-frozen: r2's Superseded by: → r3's path; r2 → archive.
```

### Rejection workflow (Draft / Proposed only)

```
PRECONDITION: doc Status ∈ {Draft, Proposed} (NOT canon-frozen).

WHEN ABANDONED:
  1. Update frontmatter (NOT a narrow change because doc was not canon-frozen;
     full edit is allowed as the rejection of a Draft/Proposed):
       Status: Rejected
       Reason: <one-line summary>
  2. git mv to docs/archive/<type>/
  3. If file is first-iteration: doc-id burned. If supersession-iteration: r-suffix burned for that base-name.

REJECTION OF CANON-FROZEN: forbidden in-place. To "reject" a canon-frozen doc, supersede it
with a successor that explicitly notes the deprecation. (Edge case; rare.)
```

### Rejected-supersession rule

```
WHEN: r2 has frontmatter `Supersedes: <prior>` AND `Status: Rejected`
       (i.e. r2 attempted to supersede r1 but its own review failed)

RULE:
  - r2 moves to docs/archive/<type>/ with Status: Rejected
  - r2's `Supersedes:` field is RETAINED (historical fact)
  - r1 frontmatter NOT mutated:
      → Status remains pre-attempt value (Draft / Implemented / etc)
      → `Superseded by:` field NEITHER added NOR populated
  - If r1 was canon-frozen pre-attempt: r1 STAYS canon
  - If r1 was also Rejected (e.g. LLD-005): both move to archive separately

LINT INVARIANT:
  For any file with Status: Rejected AND Supersedes: <prior>:
    Prior file's frontmatter must NOT contain Superseded by: pointing back at the Rejected file.
```

### Lint changes (4 new checks)

**Check L1 (commit-msg hook):** Refs:-eligibility check — ALL commit types.

```python
REFS_ELIGIBLE_PREFIXES = (
    "docs/features/", "docs/bugs/", "docs/adr/",
    "docs/design/", "docs/postmortems/", "docs/runbooks/",
)
# Plans EXCLUDED — plans are mutable working documents, not canon-frozen contract surfaces.
# Refs to plans are ALWAYS rejected per v1.5 convention.

CANON_FROZEN_STATUSES = {"Approved", "Implemented", "Verified", "Fix Applied", "Current"}


def lint_commit_refs_eligible(commit_body: str, repo_root: Path) -> list[Finding]:
    """Refs: line must point to a Refs:-eligible doc.
    Eligible: docs/{features,bugs,adr,design,postmortems,runbooks}/<id>-name(-rN)?.md
              with Status ∈ canon-frozen-statuses.
    REJECTED: docs/plans/, docs/archive/, docs/investigations/, docs/reviews/,
              any path outside REFS_ELIGIBLE_PREFIXES.
    """
    findings = []
    for line in commit_body.splitlines():
        m = re.match(r"^Refs:\s+(\S+)$", line)
        if not m: continue
        ref = m.group(1)
        if not ref.startswith(REFS_ELIGIBLE_PREFIXES):
            findings.append(Finding("error", "commit-msg",
                f"Refs: {ref} — not in Refs:-eligible prefix list. "
                f"Refs must point to canon-frozen docs in {REFS_ELIGIBLE_PREFIXES}. "
                f"Plans, archive, investigations, reviews are NOT Refs:-eligible."))
            continue
        ref_path = repo_root / ref
        if not ref_path.exists():
            findings.append(Finding("error", "commit-msg",
                f"Refs: {ref} — file does not exist."))
            continue
        status = parse_status(ref_path.read_text())
        if status not in CANON_FROZEN_STATUSES:
            findings.append(Finding("error", "commit-msg",
                f"Refs: {ref} — Status is {status}, not in canon-frozen-statuses {sorted(CANON_FROZEN_STATUSES)}. "
                f"Drafts and archived docs are not Refs:-eligible."))
    return findings
```

**Check L2 (commit-msg hook):** Canon-frozen narrow-change check.

```python
WHITELIST_FRONTMATTER_FIELDS = {"Status", "Iteration", "Superseded by"}

def lint_commit_no_canon_inplace_edit(repo_root: Path, staged_files: list[str]) -> list[Finding]:
    findings = []
    for path in staged_files:
        if not path.startswith(("docs/features/", "docs/bugs/", "docs/adr/",
                                "docs/design/", "docs/postmortems/", "docs/runbooks/")):
            continue
        try:
            prior_text = subprocess.check_output(
                ["git", "show", f"HEAD:{path}"], cwd=repo_root, text=True)
        except subprocess.CalledProcessError:
            continue  # New file
        prior_status = parse_status(prior_text)
        if prior_status in CANON_FROZEN_STATUSES:
            new_text = (repo_root / path).read_text()
            ok, why = is_narrow_change(prior_text, new_text)
            if not ok:
                findings.append(Finding("error", path,
                    f"Doc Status was {prior_status} (canon-frozen). Non-narrow change: {why}. "
                    f"Use supersession (new file with -rN suffix and Supersedes:) instead."))
    return findings


def is_narrow_change(prior_text: str, new_text: str) -> tuple[bool, str]:
    """Strict whitelist using python-frontmatter library + line-based table parsing.

    Permitted changes:
      1. Frontmatter: only WHITELIST_FRONTMATTER_FIELDS may differ
      2. Changelog table: append-only (existing rows byte-identical; only NEW rows allowed at end)
      3. Body excluding Changelog table: byte-identical

    Implementation:
      - Parse frontmatter via python-frontmatter (https://pypi.org/project/python-frontmatter/)
        which handles the standard YAML-frontmatter convention used by Jekyll, Hugo, Obsidian.
      - Locate Changelog table via `^## Changelog\\s*$` heading line followed by `| Date | Change |`
        marker line. Take the contiguous block of `^|` lines as the table body.
      - For body comparison: byte-compare prior body and new body, ignoring (a) the frontmatter
        and (b) the Changelog table block (rows). Everything else must be byte-identical.

    Edge: multiple `## Changelog` headings → reject (use first; unusual case).
    Edge: Changelog inside fenced code block → ignored (fenced code starts with ```).
    """
    import frontmatter
    prior = frontmatter.loads(prior_text)
    new = frontmatter.loads(new_text)

    # 1. Frontmatter check
    fm_diff_keys = {k for k in (set(prior.keys()) | set(new.keys()))
                    if prior.get(k) != new.get(k)}
    forbidden = fm_diff_keys - WHITELIST_FRONTMATTER_FIELDS
    if forbidden:
        return (False, f"frontmatter fields modified outside whitelist: {sorted(forbidden)}")

    # 2 + 3. Body sectioning
    prior_chlog_rows, prior_body_no_chlog = extract_changelog_and_strip(prior.content)
    new_chlog_rows, new_body_no_chlog = extract_changelog_and_strip(new.content)

    # Body excluding Changelog must be byte-identical
    if prior_body_no_chlog != new_body_no_chlog:
        return (False, "body content outside Changelog table modified (any heading/paragraph/code-block change requires supersession)")

    # Changelog table append-only
    if new_chlog_rows[:len(prior_chlog_rows)] != prior_chlog_rows:
        return (False, "Changelog rows modified or removed (only append allowed)")

    return (True, "")


def extract_changelog_and_strip(body: str) -> tuple[list[str], str]:
    """Locate ## Changelog table; return (list of row lines, body with table block replaced by sentinel).

    Algorithm:
      - Find first line matching ^## Changelog\\s*$
      - Skip blank lines + the `|---|---|` separator line
      - Capture contiguous lines starting with `|` as table rows
      - Replace the captured block with a sentinel string in the body for comparison
    """
    lines = body.split("\n")
    changelog_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Changelog\s*$", line):
            changelog_idx = i
            break
    if changelog_idx is None:
        return ([], body)
    rows = []
    j = changelog_idx + 1
    # Skip blank lines + header row + separator row
    while j < len(lines) and not lines[j].startswith("|"):
        j += 1
    # Now lines[j] should be header row "| Date | Change |", lines[j+1] separator
    if j + 1 < len(lines) and lines[j].startswith("|") and lines[j+1].startswith("|---"):
        # Skip header + separator
        j += 2
        while j < len(lines) and lines[j].startswith("|"):
            rows.append(lines[j])
            j += 1
    # Replace block lines [changelog_idx..j-1] with sentinel
    sentinel = "<<CHANGELOG_BLOCK>>"
    body_no_chlog = "\n".join(lines[:changelog_idx] + [sentinel] + lines[j:])
    return (rows, body_no_chlog)
```

Helpers fully specified above (no "details in implementation"). `python-frontmatter` is the cited parser library. (P2 checklist item.)

**Check L3 (lint --doc + commit-msg hook):** Attestation path-mutation guard — enforces documented two-locations rule.

```python
ALLOWED_ATTESTATION_PATH_PREFIXES = (
    "docs/features/", "docs/bugs/", "docs/adr/", "docs/design/",
    "docs/postmortems/", "docs/runbooks/",
    "docs/archive/features/", "docs/archive/bugs/", "docs/archive/adr/",
    "docs/archive/design/", "docs/archive/postmortems/", "docs/archive/runbooks/",
)

def lint_attestation_path_resolution(repo_root: Path, attestation_paths: list[Path]) -> list[Finding]:
    findings = []
    for ap in attestation_paths:
        attestation = yaml.safe_load(ap.read_text())
        subject_path = attestation.get("doc_subject", {}).get("path", "")
        if not subject_path:
            continue
        # Two-locations rule: must be under canon-type/ or archive/canon-type/
        if not subject_path.startswith(ALLOWED_ATTESTATION_PATH_PREFIXES):
            findings.append(Finding("error", str(ap),
                f"attestation doc_subject.path {subject_path!r} not under canon-type or archive/canon-type. "
                f"Allowed prefixes: {ALLOWED_ATTESTATION_PATH_PREFIXES}"))
            continue
        # Existence check
        full = repo_root / subject_path
        if not full.exists():
            findings.append(Finding("error", str(ap),
                f"attestation doc_subject.path {subject_path!r} does not resolve to a real file."))
    return findings
```

Now enforces BOTH "allowed location" AND "exists." (Fixes r2 review L3 finding.)

**Check L4 (commit hook on new doc files):** Doc-id-burn check — first-iteration vs supersession-iteration handling.

```python
FIRST_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)\.md$")
SUPERSESSION_ITERATION_RE = re.compile(r"^(\d+)-([a-z][a-z0-9-]*)-r(\d+)\.md$")


def lint_doc_id_burn(new_doc_path: Path, repo_root: Path) -> list[Finding]:
    name = new_doc_path.name
    doc_type = infer_type(new_doc_path)
    canon_dir = repo_root / "docs" / doc_type
    archive_dir = repo_root / "docs" / "archive" / doc_type

    m_first = FIRST_ITERATION_RE.match(name)
    m_super = SUPERSESSION_ITERATION_RE.match(name)

    if m_first:
        # First-iteration filename: strict-greater than all first-iteration ids
        new_id = int(m_first.group(1))
        existing_ids = []
        for d in (canon_dir, archive_dir):
            if not d.exists(): continue
            for p in d.glob("*.md"):
                m = FIRST_ITERATION_RE.match(p.name)
                if m:
                    existing_ids.append(int(m.group(1)))
        max_id = max(existing_ids, default=0)
        if new_id <= max_id:
            return [Finding("error", str(new_doc_path),
                f"first-iteration doc-id {new_id} reuses existing or burned id (max={max_id}). "
                f"Next available: {max_id + 1}.")]

    elif m_super:
        # Supersession-iteration filename: corresponding first-iteration must exist;
        # r-suffix must be strictly greater than max existing r-suffix for that base-name
        new_id = int(m_super.group(1))
        base_name = m_super.group(2)
        new_r = int(m_super.group(3))
        # Verify first-iteration sibling exists in canon or archive
        first_iter_name = f"{m_super.group(1)}-{base_name}.md"
        first_exists = ((canon_dir / first_iter_name).exists() or
                        (archive_dir / first_iter_name).exists())
        if not first_exists:
            return [Finding("error", str(new_doc_path),
                f"supersession-iteration {name} references base {first_iter_name} which "
                f"does not exist in canon or archive. Cannot supersede a non-existent doc.")]
        # r-suffix must be strictly greater than existing.
        # CRITICAL: exclude the file currently being added from the glob, otherwise the
        # check rejects the very file it's evaluating (r3 review caught this self-defeating bug).
        new_doc_resolved = new_doc_path.resolve()
        existing_rs = []
        for d in (canon_dir, archive_dir):
            if not d.exists(): continue
            for p in d.glob(f"{m_super.group(1)}-{base_name}-r*.md"):
                if p.resolve() == new_doc_resolved:
                    continue  # Skip the file currently being added
                m = SUPERSESSION_ITERATION_RE.match(p.name)
                if m and m.group(2) == base_name:
                    existing_rs.append(int(m.group(3)))
        max_r = max(existing_rs, default=1)  # r=1 implicit (the first-iteration file)
        if new_r <= max_r:
            return [Finding("error", str(new_doc_path),
                f"supersession-iteration r{new_r} reuses or precedes existing r-suffix (max r={max_r}). "
                f"Next available: r{max_r + 1}.")]

    else:
        return [Finding("error", str(new_doc_path),
            f"filename {name!r} does not match first-iteration or supersession-iteration pattern.")]

    return []
```

Self-check applied to LLD-006-r4 (this file): `006-archive-and-supersession-conventions-r4.md` matches SUPERSESSION_ITERATION_RE (id=6, base=archive-and-supersession-conventions, r=4). Sibling `006-archive-and-supersession-conventions.md` (r1) exists in canon → first_exists=True. Existing r-suffixes (excluding self): r2 + r3 (both currently at canon path; both Draft). max_r = 3. New r = 4. 4 > 3 → PASSES. (P6 checklist verified: rule applied to this LLD itself does not break, with the glob-exclusion fix from r3 review.)

### STANDARDS.md template update

`cli/templates/standards-default-7.md` adds three sections after § Spec Review Rule:

```markdown
## Archive Convention

Rejected and superseded docs live in `docs/archive/<type>/`. Canon docs live at top-level type directories. Reviews (`docs/reviews/`) and investigations (`docs/investigations/`) are append-only / scratch and never move to archive.

Lifecycle terminal states:
- **Rejected** — draft abandoned, no successor; doc-id burned (first-iteration only).
- **Superseded** — replaced by newer revision; new revision lives at canon path; old revision moves to archive with `Superseded by:` frontmatter link.

## Supersession Workflow

NEVER in-place edit canon-frozen docs (Status ∈ {Approved, Implemented, Verified, Fix Applied, Current}). Allowed in-place changes (a "narrow change"):
- Append a Changelog table row (no row modification or removal)
- Modify whitelisted frontmatter fields ONLY: Status, Iteration, Superseded by

Anything else requires supersession:
1. Create new revision file `<type>/NNN-name-r<N+1>.md` with `Supersedes:` frontmatter
2. Iterate + review until canon-frozen
3. Update prior file frontmatter (narrow change): `Status: Superseded`, `Superseded by:`
4. `git mv` prior file to `docs/archive/<type>/`

### Rejected-supersession (failed revision attempts)

When a draft (`Supersedes: <prior>`) is itself Rejected before reaching canon-frozen:
- The Rejected revision moves to archive with Status: Rejected
- The Rejected file's `Supersedes:` field is RETAINED (historical fact)
- The prior file's frontmatter is NOT mutated

### Rejection of Draft / Proposed docs

Drafts that have not reached canon-frozen may be rejected by setting Status: Rejected and adding Reason: field (full edit allowed since narrow-change rules apply only to canon-frozen docs). Move to archive. Doc-id burned (first-iteration) or r-suffix burned (supersession-iteration).

## Doc-ID Burn Policy

- First-iteration filenames (`NNN-name.md`): doc-id never reused. New first-iteration doc-id must be strictly greater than max(first-iteration ids in canon ∪ archive of same type).
- Supersession-iteration filenames (`NNN-name-rN.md`): EXEMPT from doc-id burn (reuse same id by design); instead, r-suffix must be strictly greater than max existing r-suffix for that base-name.

## Refs: Line Restriction

`Refs:` lines on any commit type must point to Refs:-eligible canon docs only. A Refs:-eligible doc:
- Lives at `docs/<canon-type>/<id>-name(-rN)?.md` where canon-type ∈ {features, bugs, adr, design, postmortems, runbooks}
- Has Status ∈ canon-frozen-statuses

Lint rejects Refs into:
- `docs/archive/` (archived docs)
- `docs/investigations/` (scratch)
- `docs/reviews/` (attestations, not docs)
- `docs/plans/` (plans are mutable working documents, NOT canon-frozen contract surfaces; never Refs:-eligible)
- Any path outside the 6 canon-type directories
- Any canon doc whose Status is not canon-frozen (e.g. Drafts)
```

Whitelist (Status, Iteration, Superseded by) consistent with Glossary. (P4 checklist.)

### Migration of existing rejected docs (dogfood)

**BEFORE merge** (current state, 2026-05-07):
- `docs/features/005-v1.5-enforcement-core.md` (Status: Rejected; canon path)
- `docs/features/005-v1.5-enforcement-core-r2.md` (Status: Rejected; canon path)
- `docs/features/006-archive-and-supersession-conventions.md` (r1; Status: Draft → will become Rejected per promotion rule; canon path)
- `docs/features/006-archive-and-supersession-conventions-r2.md` (r2; Status: Draft → will become Rejected per promotion rule; canon path)
- `docs/features/006-archive-and-supersession-conventions-r3.md` (r3; Status: Draft → will become Rejected per promotion rule; canon path)
- `docs/features/006-archive-and-supersession-conventions-r4.md` (r4 = this file; Status: Draft → will become canon-frozen on review pass; canon path)

**AFTER merge** (target state, post-Gate-3-pass on r4):

Migration is fully executable (no bash comments carrying load-bearing rules). Per promotion rule, since r1 was never canon-frozen, r1..r3 ALL become Rejected; r4 stays canon at `-r4` filename.

```bash
set -e
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

# 1. LLD-005 r1 + r2 — both Rejected. Frontmatter Status already set 2026-05-07.
git mv docs/features/005-v1.5-enforcement-core.md docs/archive/features/
git mv docs/features/005-v1.5-enforcement-core-r2.md docs/archive/features/

# 2. LLD-006 r1 + r2 + r3 — all Rejected per promotion rule (none reached canon-frozen).
#    Apply rejection-finalization edits (Status: Rejected + Reason: field) via cli.lifecycle.
python -m cli.lifecycle reject \
  --file docs/features/006-archive-and-supersession-conventions.md \
  --reason "Promotion rule: r4 reached canon-frozen first; r1 was never canon-frozen → Rejected"
python -m cli.lifecycle reject \
  --file docs/features/006-archive-and-supersession-conventions-r2.md \
  --reason "Rejected on r2 review fail (10 findings); promotion rule applies on r4 canon-pass"
python -m cli.lifecycle reject \
  --file docs/features/006-archive-and-supersession-conventions-r3.md \
  --reason "Rejected on r3 review fail (11 findings); promotion rule applies on r4 canon-pass"

git mv docs/features/006-archive-and-supersession-conventions.md docs/archive/features/
git mv docs/features/006-archive-and-supersession-conventions-r2.md docs/archive/features/
git mv docs/features/006-archive-and-supersession-conventions-r3.md docs/archive/features/

# 3. Update review YAMLs (doc_subject.path → archive paths)
python -m cli.lifecycle update-attestation-paths \
  --reviews docs/reviews/005-r1.review.yaml \
  --reviews docs/reviews/005-r2.review.yaml \
  --reviews docs/reviews/006-r1.review.yaml \
  --reviews docs/reviews/006-r2.review.yaml \
  --reviews docs/reviews/006-r3.review.yaml
```

`cli.lifecycle` is a small new helper (in scope of v1.5 implementation; spec below): `reject` adds Status: Rejected + Reason: + (optional) doc-id-burn marker; `update-attestation-paths` reads each review.yaml, determines current location of subject, rewrites `doc_subject.path` field. Both deterministic + scriptable.

**Per promotion rule:** r1 was never canon-frozen (Status: Draft throughout). r4 is the first revision to reach canon-frozen. Therefore r1 + r2 + r3 all Rejected; r4 keeps `Supersedes: docs/features/006-archive-and-supersession-conventions.md` (chain root). LLD-005 r1 + r2 are independently Rejected (separate chain that never produced a canon-frozen successor).

### Supersedes/Superseded-by path resolution after archive

Lint resolves `Supersedes:` and `Superseded by:` paths by checking BOTH canon-located and archive locations:

```python
def resolve_supersession_link(repo_root: Path, link_value: str) -> Path | None:
    """Given a Supersedes: or Superseded by: link value, return the actual file path
    by checking canon-located first, then archive. Returns None if not found.

    Example: link_value = 'docs/features/006-archive-and-supersession-conventions.md'
    Lint checks:
      1. {repo_root}/docs/features/006-archive-and-supersession-conventions.md (canon)
      2. {repo_root}/docs/archive/features/006-archive-and-supersession-conventions.md (archive)
    Returns the first that exists.
    """
    canon_path = repo_root / link_value
    if canon_path.exists():
        return canon_path
    parts = Path(link_value).parts
    if parts and parts[0] == "docs" and len(parts) >= 2:
        archive_path = repo_root / "docs" / "archive" / "/".join(parts[1:])
        if archive_path.exists():
            return archive_path
    return None
```

Effect: r4's `Supersedes: docs/features/006-archive-and-supersession-conventions.md` resolves to canon BEFORE migration and to archive AFTER migration. No path rewrite needed in frontmatter; resolution is location-aware.

### cli.lifecycle helper spec (v1.5 implementation, in scope)

Subcommands:

- `python -m cli.lifecycle reject --file <path> --reason <one-line>`
  - Reads file frontmatter via python-frontmatter
  - Sets `Status: Rejected`
  - Adds `Reason: <one-line>` field
  - **Iteration field unchanged.** Iteration reflects the file's chain position (1, 2, 3, ...) at time of authoring; rejection does not alter chain position. Iteration is preserved as historical fact.
  - Writes file back
  - Idempotent (re-running on already-Rejected with same reason is no-op)

- `python -m cli.lifecycle update-attestation-paths --reviews <path> [--reviews <path>]...`
  - For each review.yaml: parse, read `doc_subject.path`, locate the actual file via `resolve_supersession_link`, update `doc_subject.path` to current location, write back
  - Validates content_hash matches subject doc (unchanged hash means valid path update; changed hash = error)
  - Idempotent

## Edge Cases

- **Doc moved to archive but reviews/<doc-id>-rN.review.yaml still points at canon path.** Mitigation: post-move update of `doc_subject.path`; lint Check L3 catches stale paths via two-locations rule.
- **Two sibling supersession candidates** (`NNN-foo-r2.md` and `NNN-foo-r2-alt.md` — name collision). Lint Check L4 r-suffix uniqueness rejects the second; only one r2 per base-name allowed.
- **In-place edit of canon-frozen for typo / link-rot fix.** Disallowed. Forces "is this a typo or a meaning change?" Friction intentional. Override flag deferred to LLD-007+ (with metrics.jsonl audit).
- **Archive folder grows large over years.** No enforced TTL. `cli.archive --summary` deferred.
- **Doc never reached canon-frozen and is being abandoned.** Rejection workflow applies; Reason: field added (allowed because doc was not canon-frozen).
- **Lint runs on freshly-cloned repo with no git history.** Check L2 needs `git show HEAD:<path>`; falls back to "skip canon-edit check on missing prior" — first commit can't violate the rule.
- **Migration from v1.4 (no archive convention) to v1.5.** Existing docs in canon path stay until user revises or rejects. Doc-id-burn lint includes both top-level + archive in max-id calculation, so legacy state doesn't break new-doc-id flow.
- **User force-deletes an archive file.** Lint cannot detect (file simply absent). Anti-pattern; git history retains.
- **Rejected-supersession-of-Rejected-supersession** (r3 supersedes r2 which superseded r1; r3 also Rejected). Recursive: each Rejected revision moves to archive independently; `Supersedes:` chain retained; no `Superseded by:` populated for any since none reached canon-frozen.
- **Philosophy doc Changelog append.** Philosophy.md is canon-frozen (Status: Current). Per Glossary, Changelog table append IS narrow change. Out-of-Scope clause does NOT contradict this; Changelog appends explicitly allowed.
- **Refs to Draft canon doc.** Lint Check L1 rejects (Status not in canon-frozen-statuses). Fresh reader writing `Refs: docs/features/<id>-name.md` BEFORE the doc reaches canon-frozen will fail lint. Post-Gate-3-pass, Status flips to canon-frozen, lint accepts.
- **Refs target migrated to archive after commit landed.** Once a `feat:` / `fix:` commit with `Refs: docs/features/006-foo.md` is committed and that doc is later superseded → archived, the original commit's Refs line still references the now-archived path. Resolution: Lint runs only on NEW commits (not retroactively); old commits are immutable git history. New commits adding Refs to a now-archived path are rejected by L1. To reference the archived doc's content, the new commit should use `Refs: docs/features/<id>-foo-rN.md` (the current canon revision). git history preserves the link via `git log --follow`.
- **A canon-frozen doc with a Reason: field added without supersession.** Forbidden — Reason is not in narrow-change whitelist. To add Reason, supersede.

## Security

- **Path traversal in `Refs:` / `Superseded by:`.** Regex-matched repo-relative paths only; absolute paths and `..` rejected.
- **In-place-edit override.** Deferred to LLD-007+ when metrics.jsonl exists.
- **`docs/archive/` content visibility.** In-repo, version-controlled. No new exposure.
- **Attestation YAML path field tampering.** Lint Check L3 enforces two-locations + existence; stale or fabricated paths fail.
- **Lint check L4 file enumeration.** Reads filesystem under `docs/<type>/` and `docs/archive/<type>/`; no traversal beyond.

## Testing

### Pytest baseline (verified 2026-05-07)

Captured directly:
```bash
$ cd /Users/mohammedhassanmohiddin/Documents/Antigravity/orchestra
$ /Users/mohammedhassanmohiddin/Documents/Antigravity/SCALE\ APP/.venv/bin/python -m pytest tests/ 2>&1 | tail -3
tests/test_standards_generator.py ...........                            [100%]

============================== 85 passed in 6.60s ==============================
```

Baseline = 85.

### New unit tests (binding floor: ≥13; this list enumerates exactly 13)

Each test maps 1:1 to an Acceptance item per P5 checklist:

| Test ID | Test file::function | Maps to | Coverage |
|---|---|---|---|
| T1 | `tests/test_lint_archive_refs.py::test_refs_into_archive_rejected` | A2 | Refs `docs/archive/features/x.md` → exit 1 |
| T2 | `tests/test_lint_canon_inplace_edit.py::test_inplace_body_change_rejected` | A3 | Canon-frozen doc body modified → exit 1 |
| T3 | `tests/test_lint_canon_inplace_edit.py::test_changelog_append_accepted` | A3 | Append Changelog row → exit 0 |
| T4 | `tests/test_lint_canon_inplace_edit.py::test_status_field_update_accepted` | A3 | Status field flip → exit 0 |
| T5 | `tests/test_lint_canon_inplace_edit.py::test_new_doc_unaffected` | A3 | New doc with no prior → exit 0 |
| T6 | `tests/test_lint_doc_id_burn.py::test_first_iter_id_le_max_rejected` | A4 | First-iter id ≤ existing max → exit 1 |
| T7 | `tests/test_lint_doc_id_burn.py::test_first_iter_id_max_plus_1_accepted` | A4 | First-iter id = max+1 → exit 0 |
| T8 | `tests/test_lint_doc_id_burn.py::test_supersession_r_suffix_le_max_rejected` | A5 | Supersession r-suffix ≤ existing max r → exit 1 |
| T9 | `tests/test_lint_doc_id_burn.py::test_supersession_r_suffix_max_plus_1_accepted` | A5 | Supersession r-suffix = max r+1 → exit 0 |
| T10a | `tests/test_lint_attestation_path.py::test_path_under_non_allowed_prefix_rejected` | A6 | doc_subject.path under `docs/investigations/...` → exit 1 |
| T10b | `tests/test_lint_attestation_path.py::test_path_under_canon_accepted` | A6 | doc_subject.path under `docs/features/...` (exists) → exit 0 |
| T10c | `tests/test_lint_attestation_path.py::test_path_under_archive_accepted` | A6 | doc_subject.path under `docs/archive/features/...` (exists) → exit 0 |
| T11 | `tests/test_lint_canon_inplace_edit.py::test_reason_field_added_rejected` | A3 | Canon-frozen doc with `Reason:` field added (non-whitelisted) → exit 1 |

Total new: 13 tests. Suite post-merge: 85 + 13 = 98.

### New eval scenario

| Scenario | Path |
|---|---|
| `archive-refs-blocked` | `eval/scenarios/archive-refs-blocked.json`. Integrates with `eval/run.py` (LLD-001 scaffolding). Fixture: repo with `docs/archive/features/005-old.md`. Stage commit with `Refs: docs/archive/features/005-old.md`. Verify lint exits 1 with archive-rejection message. |

### Manual verification (post-migration)

- `docs/features/` lists only canon: 001, 002, 003, 006-r4 (this file)
- `docs/archive/features/` contains: 005 r1, 005 r2, 006 r1, 006 r2, 006 r3
- `git log --follow docs/archive/features/<any>` preserves full history
- `docs/reviews/{005-r1,005-r2,006-r1,006-r2}.review.yaml` `doc_subject.path` correctly points into archive

## Related Documents

- `docs/investigations/2026-05-07-workflow-spec-review-brainstorm.md` — Round 1-6 research; pre-dispatch checklist
- `docs/features/005-v1.5-enforcement-core.md` — rejected r1 (BEFORE merge: at canon path; AFTER merge: at archive)
- `docs/features/005-v1.5-enforcement-core-r2.md` — rejected r2 (BEFORE merge: at canon path; AFTER merge: at archive)
- `docs/features/006-archive-and-supersession-conventions.md` — this LLD's r1 (BEFORE merge: at canon path; AFTER merge: at archive, Status: Rejected)
- `docs/features/006-archive-and-supersession-conventions-r2.md` — this LLD's r2 (BEFORE merge: at canon path; AFTER merge: at archive, Status: Rejected)
- `docs/features/006-archive-and-supersession-conventions-r3.md` — this LLD's r3 (BEFORE merge: at canon path; AFTER merge: at archive, Status: Rejected)
- `docs/reviews/005-r{1,2}.review.yaml`, `006-r{1,2,3}.review.yaml` — attestations (stay in `docs/reviews/`)
- `docs/features/001-design-docs-init.md` — original cli.lint design (still canon)
- `docs/design/orchestra-philosophy.md` — Changelog appended post-merge (narrow change; permitted)
- ADR pattern: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions ; https://github.com/joelparkerhenderson/architecture-decision-record
- Atlas roll-forward: https://atlasgo.io/blog/2024/11/14/the-hard-truth-about-gitops-and-db-rollbacks
- Temporal saga: https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas
- python-frontmatter parser: https://pypi.org/project/python-frontmatter/

## Changelog

| Date | Change |
|---|---|
| 2026-05-07 | r3 written addressing all 10 r2 review findings via pre-dispatch checklist (P1-P9). Resolves: (1) doc-id-burn vs supersession conflict — burn applies to first-iteration only; supersession-iteration uses r-suffix uniqueness rule; (2) supersession path resolution — single mechanism (lint chain traversal); (3) L3 acceptance now mapped 1:1 to T10; (4) is_narrow_change() helpers fully specified using python-frontmatter; (5) narrow-change whitelist single source of truth in Glossary; (6) Reason: field clarification; (7) Refs:-eligibility check enforces canon-frozen Status; (8) version bump rationale single sentence; (9) BEFORE/AFTER merge labels added; (10) all design decisions committed. Status: Draft. r3 bootstrap review FAILED (`docs/reviews/006-r3.review.yaml` — 11 findings, 2 critical: L4 self-check glob bug + plans Refs ambiguity). |
| 2026-05-08 | r4 written addressing all 9 r3 review findings. Resolves: (1) L4 self-check glob — explicit exclusion of file currently being added (`p.resolve() == new_doc_resolved` skip); self-check verified against r4 itself: max_r=3 (excluding r4), new_r=4, 4>3 PASSES; (2) plans Refs handling — plans REMOVED from REFS_ELIGIBLE_PREFIXES; plans NEVER Refs:-eligible per v1.5; (3) Supersedes/Superseded-by path resolution — `resolve_supersession_link()` checks both canon and archive locations; no frontmatter rewrite needed on migration; (4) r1/r2/r3 dogfood lifecycle — promotion rule defined: r1 was never canon-frozen → r1+r2+r3 ALL Rejected (not Superseded); r4 stays canon at -r4 filename with Supersedes: r1; (5) Reason-field test added (T11) to lint floor; floor now 13; (6) T10 split into T10a/b/c (3 distinct test functions); (7) "canon doc" disambiguated into canon-located vs Refs:-eligible; (8) Migration block fully executable via `cli.lifecycle reject` + `cli.lifecycle update-attestation-paths` helpers; cli.lifecycle spec in scope; (9) "full edit" replaced by "rejection-finalization edit" defined in Glossary. Status: Draft. r4 bootstrap subagent review pending. |
