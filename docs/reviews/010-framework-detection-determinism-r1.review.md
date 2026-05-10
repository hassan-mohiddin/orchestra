# Orchestra Judge-1 Review (LLD-010 r1; off-schema)

> Reviewer: subagent:general-purpose+spec-review-v1
> Date: 2026-05-11
> NOTE: subagent used non-standard gate names (technical_correctness, contract_completeness, scope_alignment, documentation_quality) instead of schema {completeness, evidence, clarity, consistency}. Saved as .md companion rather than piped through cli.spec_review.

```yaml
schema_version: "1.0"
doc_subject:
  path: docs/features/010-framework-detection-determinism.md
  content_hash: "sha256:a76f2e16c4f3284acc198ce929f3e5d94004ac7ba52fb9eced61692321af8b32"
  iteration: 1
review:
  reviewer: claude-opus-4-7-1m
  role: judge-1
  iteration: 1
  date: 2026-05-11
verdict: needs_attention
summary: |
  LLD-010 architectural shape is sound (separate snippet file, framework-detection
  with tailoring, --apply opt-in, --verify entrypoint, hard-fail). However the
  load-bearing technical claim driving the entire LLD — that pass_filenames: false
  on a commit-msg hook causes the framework to withhold the msg-file path — is
  INVERTED relative to authoritative pre-commit.com docs. commit-msg hooks ALWAYS
  receive the msg-file path regardless of pass_filenames. This invalidates the
  Problem Statement defect #2, the Glossary entry, A1's central rationale, the
  snippet's IMPORTANT comment, and the codex r2 high #1 attribution. Several
  secondary defects: pseudocode has a real fsync bug (fsync on closed fd / wrong
  fd), atomic-write also re-opens tmp which discards the just-written buffer in
  some Python versions, A3 "shorter snippet" implementation is undefined (only
  `...` stub), A8 reconciliation does not address the LLD-008 A3 inventory
  asymmetry (LLD-008 keeps precommit-yaml-patch.txt in cli/templates/, LLD-010
  ships new file in skills/commit/templates/ — split rationale absent), edge case
  for two `- repo: local` blocks may break duplicate-id detection (A3 only
  scans for {orchestra-lint, orchestra-commit-msg} ⊆ ids across-all-local;
  partial-config edge 2 contradicts itself on whether `--apply` errors or just
  emits manual-merge guidance).
gates:
  technical_correctness:
    verdict: fail
    findings:
      - severity: Critical
        location: "Glossary § pass_filenames"
        finding: |
          Glossary states: "For `commit-msg` stage: when `true`, framework passes
          commit-msg-file path; when `false`, no positional arg." This is wrong.
          pre-commit.com authoritative docs: "commit-msg hooks will be passed a
          single filename -- this file contains the current contents of the
          commit message to be validated." The msg-file is passed regardless of
          pass_filenames. pass_filenames controls the OTHER (matched) filenames
          arg flow, not the special commit-msg arg.
        evidence: |
          pre-commit.com /index.html § hooks: "For commit-msg stage hooks: this
          file is passed as a mandatory argument to validate the message,
          regardless of the pass_filenames setting." Verified 2026-05-11.
        recommendation: |
          Rewrite Glossary entry: "commit-msg stage hooks ALWAYS receive the
          commit-msg-file as their first positional argument (pre-commit
          framework contract). The pass_filenames key for commit-msg stage
          controls only auxiliary matched filenames (typically none), not the
          msg-file path itself. pass_filenames: false is therefore a valid and
          arguably more correct setting for orchestra-commit-msg because no
          file-matching is performed." Then re-derive A1 default with the
          corrected semantics.
      - severity: Critical
        location: "Problem Statement § defect #2 + A1 + line 30 + line 113-115"
        finding: |
          Defect #2 ("Snippet pass_filenames wrong for commit-msg stage. Naive
          snippet sets pass_filenames: false ... framework does NOT pass
          msg-file path") is incorrect per pre-commit framework contract.
          The LLD's entire pass_filenames: true mandate (A1, snippet line 138,
          snippet IMPORTANT comment lines 112-115) is built on this inverted
          premise. If codex r2 high #1 actually claimed this — codex's claim is
          wrong and should be re-litigated, NOT propagated forward.
        evidence: |
          Same source as above. Cross-check: a quick repro is reading pre-commit
          source `pre_commit/commands/hook_impl.py` — commit-msg stage execution
          unconditionally prepends the commit-msg-file argv before invoking
          entry. pass_filenames affects the OTHER filenames list (which is
          empty for commit-msg by design).
        recommendation: |
          Either (a) verify directly via integration test before locking the
          design — write a test repo with pass_filenames: false and confirm
          `cli.lint --commit-msg-finalize` still receives sys.argv[1] = msg
          file path; if confirmed → defect #2 is invalid, retract that prong
          of the Problem Statement, mark snippet pass_filenames as
          implementation-author-choice with brief rationale; OR (b) if codex's
          original observation arose from a real bug (e.g. some pre-commit
          version did honor pass_filenames: false for commit-msg), pin the
          version range and cite the source. Without one of these, A1 is
          shipping a documented-but-unverified mandate that may be no-op.
      - severity: Important
        location: "Design § --apply auto-merge — lines 243-245"
        finding: |
          fsync pseudocode is bugged. `os.fsync(open(tmp).fileno())` opens a
          NEW read fd, fsyncs it (which on POSIX flushes nothing since the
          write happened via a different fd that was closed by write_text),
          and leaks the fd. Standard durable-write pattern requires fsyncing
          the SAME fd the write went through. Path:
            with open(tmp, "w") as f:
                f.write(yaml.safe_dump(...))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, cfg_path)
          Additionally for true durability fsync the containing directory after
          os.replace (POSIX requirement for rename atomicity to survive crash).
        evidence: |
          Python docs: write_text closes the file. Re-opening with open() in
          read mode produces a new fd whose buffer is empty; fsyncing it is
          effectively no-op for the write that already occurred (kernel may
          have written to disk via the closed fd, but no guarantee). This is a
          well-known pitfall (see python-trio / sqlite write-ahead patterns).
        recommendation: |
          Replace pseudocode with the with-block pattern above; add dirfsync
          step. Update T5d test description to assert fsync(dir) is also called
          (or that the chosen idiom matches a vetted helper such as
          `os.replace` after `fsync(fd)` on an explicit write-mode fd).
      - severity: Important
        location: "Design § Framework detection + tailoring — lines 209-218"
        finding: |
          `_emit_tailored_snippet` body is `...` (stub) where the actual
          stripping logic should live. "strip lines between marker comments"
          is hand-waved — the snippet file as written has no marker comments
          delimiting the directive block. T3a ("shorter snippet emitted")
          is therefore unimplementable as specified.
        evidence: |
          Read lines 104-140 of the snippet body — comments are free-form
          prose, not delimited by a parsable marker (e.g. `# BEGIN
          default_install_hook_types` / `# END default_install_hook_types`).
        recommendation: |
          Either (a) define explicit BEGIN/END markers in the snippet file
          and document the strip mechanism; OR (b) drop the "shorter snippet"
          tailoring entirely and always emit the full snippet — the user
          already has the directive in their config so the recommendation
          comment is a no-op, not a conflict. (b) is simpler; tailoring
          complexity buys little. Update A3 + T3a/T3b accordingly.
      - severity: Important
        location: "Edge Cases § 2 (lines 300) vs § 11 (line 309)"
        finding: |
          Edge case 2 says `--apply` with partial config "would create
          duplicate orchestra-lint id" and mitigation is "check for
          orchestra-lint id presence; if present alone: emit error suggesting
          manual merge." But A3 detection at line 198 only returns True if
          BOTH ids are present (subset check). So `--apply` with partial
          config CURRENTLY falls through the "orchestra not configured"
          branch and appends a new local block, producing the duplicate.
          The "Mitigation" sentence describes desired behavior but no
          acceptance item / test enforces it. The implementation contract
          is silent on this state.
        evidence: |
          Line 198 `_orchestra_ids_configured`: `{"orchestra-lint",
          "orchestra-commit-msg"}.issubset(ids)`. Line 300 mitigation:
          "checks for orchestra-lint id presence" — different predicate.
          No A-item codifies this; no T-case asserts it.
        recommendation: |
          Add A3b (or extend A3) explicitly: "If user config has orchestra-lint
          OR orchestra-commit-msg but not both → exit non-zero with
          partial_config error message suggesting manual merge. `--apply` MUST
          NOT proceed in this state." Add test T3e for this case.
      - severity: Important
        location: "A8 + Related Documents — lines 62, 360, 365"
        finding: |
          A8 reconciliation says `precommit-yaml-patch.txt` "stays in
          cli/templates/" (per LLD-008 A3) while LLD-010 ships new file in
          `skills/commit/templates/precommit-framework-snippet.yaml`. This
          creates an asymmetric layout (template files split between two
          directories with no shared rationale documented). LLD-008 A3
          rationale was "cli/templates/ retains init-related artifacts" —
          but the new framework-snippet IS init-related (init-time framework
          detection). Why does this file live under skills/commit/templates/
          but precommit-yaml-patch.txt does not?
        evidence: |
          LLD-008 A3 (line 52): "cli/templates/ retains 11 init-related
          artifacts ... precommit-yaml-patch.txt stays — different purpose
          (BUG-007 yaml-checker --unsafe)." LLD-010 A1 (line 40):
          "skills/commit/templates/precommit-framework-snippet.yaml (NEW)."
          No criterion distinguishes the two beyond "BUG-007 vs LLD-010
          purpose," which is post-hoc.
        recommendation: |
          Add one paragraph in A8 (or LLD-008 A3 amendment) stating the
          canonical placement rule: "Framework-integration artifacts (consumed
          by cli.install_hooks framework-detection path) live under
          skills/commit/templates/. Init-time framework-orthogonal patches
          (consumed by cli.init or by user-manual edit of mkdocs.yml etc.)
          live under cli/templates/." Then test T8 should assert BOTH files
          live at their canonical paths and that the rule is reflected in a
          docstring or README under each directory.
      - severity: Minor
        location: "A3 (line 45) + A6 (line 56)"
        finding: |
          A6 says framework detection is integrated into existing
          `cli.install_hooks` (NOT new entrypoint), but A3 + A4 + A5 all
          describe new flags (--apply, --verify, --force-raw) and behaviors
          that materially change the existing CLI shape. Calling this "not
          a new entrypoint" is accurate but misleading — the CLI surface
          area is roughly doubled.
        recommendation: |
          Rephrase A6: "Framework detection extends the existing cli.install_hooks
          entrypoint with new flags (--apply, --verify, --force-raw) and new
          conditional code paths; no new top-level CLI tool added."
      - severity: Minor
        location: "A11 + LLD-009 A16"
        finding: |
          A11 says pytest target post-LLD-010 = 219 (197 LLD-009 + 22 LLD-010).
          LLD-009 A16 says 197 (161 LLD-008 + 36). The math depends on
          LLD-008/009 actually landing in sequence with stated test counts.
          T8 is described as testing "both files exist with documented
          contents" — one test function or two? T8 description in Testing
          table conflates assertions. T1+T2 also overlap T8 (T8 reasserts
          T1's snippet existence). Count of 22 is plausible but soft.
        recommendation: |
          Tighten T8 description: "T8a: cli/templates/precommit-yaml-patch.txt
          exists. T8b: skills/commit/templates/precommit-framework-snippet.yaml
          exists. T8c: each file's docstring/comment header references its
          BUG / LLD source-of-truth." That's 3 sub-tests. Update total
          accordingly. Either accept the LLD-008/009 dependency in writing
          (preferred) or guard against ordering with an interim-baseline
          fallback.
  contract_completeness:
    verdict: conditional_pass
    findings:
      - severity: Important
        location: "A4 verify-hooks-active + § Hard-fail invariant"
        finding: |
          A4 fingerprint check uses head -n5. But pre-commit framework hook
          header (line 1: `#!/usr/bin/env <pre-commit-runner-path>`; line 2-N:
          generated comment block) may exceed 5 lines depending on pre-commit
          version. Some pre-commit versions emit the marker at line 6+. A
          legitimate framework-mode install could fail A4 → A7 hard-fail →
          user sees remediation telling them to do exactly what they already
          did, breaking trust.
        recommendation: |
          Either widen the head check to head -n20 (still constant-time,
          covers known versions), OR check for fingerprint anywhere in the
          file (not just head). Update T4e accordingly. Document the pre-commit
          version floor that the fingerprint string is stable at (cite the
          source file generating it: pre_commit/commands/install_uninstall.py).
      - severity: Minor
        location: "A13 integration test T13 (line 67)"
        finding: |
          T13 names "stage a canon-inplace violation" but does not specify
          how the violation is constructed. End-to-end test requires fixture
          for canon-frozen markdown + corresponding HEAD state. Without this
          fixture spec, T13 is unimplementable.
        recommendation: |
          Add to T13 description: "Fixture: docs/features/test-canon-froz.md
          committed at HEAD with Status: Implemented + Iteration: 1; test
          modifies a non-whitelist Acceptance section; stages; commits with
          no Addresses: line. Expected: commit-msg hook rejects via LLD-009
          L2-finalize path." Pull this fixture from LLD-009 if reusable.
  scope_alignment:
    verdict: pass
    findings:
      - severity: Minor
        location: "Out of Scope (lines 87-97)"
        finding: |
          Auto-uninstall deferral noted. "Manual procedure documented" but
          no pointer to where (runbook, README, etc.). Reader has no path
          to find the manual procedure post-ship.
        recommendation: |
          Add reference to D2 (CONTRIBUTING.md) covering both install and
          uninstall framework procedures; or file follow-up doc with explicit
          path before LLD-010 ship.
  documentation_quality:
    verdict: pass
    findings:
      - severity: Minor
        location: "Mermaid diagram lines 144-166"
        finding: |
          Diagram labels orchestra-frame ("auto-merge: append local repo
          entry") but does not show the orchestra-ids-detected branch where
          one id is present without the other (partial config edge case
          from § Edge Cases 2). Diagram understates the decision space.
        recommendation: |
          After the F decision node, add a "partial config" branch leading
          to exit non-zero with manual-merge guidance (per recommended A3b
          above). Or update diagram caption to note "partial config branch
          not shown — see Edge Cases § 2 / proposed A3b."
      - severity: Minor
        location: "Changelog (line 372)"
        finding: |
          Single Changelog row covers r1 filing; mentions "5 Q&A locked"
          but the questions/answers are not enumerated in the LLD body
          (only A3-A7 reference "QN grill answer" by number). Reader cannot
          trace grilling-session reasoning.
        recommendation: |
          Either inline a "Grilling session decisions" subsection summarizing
          each Q with the locked answer, OR link to the grilling-session
          scratch note (if one exists in docs/investigations/). Otherwise
          Q-references in A-items are unresolvable.
unverified_claims:
  - location: "Problem Statement § defect #2 + A1"
    claim: "pass_filenames: false on commit-msg hook prevents framework from passing msg-file path"
    status: "REFUTED by pre-commit.com documentation. See technical_correctness Critical finding 1+2."
  - location: "A4 fingerprint head -n5"
    claim: "framework-generated hooks contain `# generated by pre-commit` in first 5 lines for all supported versions ≥3.0"
    status: "UNVERIFIED — no source citation. Recommend version-pin or widen window."
  - location: "Edge case 8 (line 306)"
    claim: "pre-commit framework version floor ≥3.0 documented in Out-of-Scope"
    status: "PARTIAL — floor stated but not verified that all behaviors required (commit-msg msg-file pass, header fingerprint, default_install_hook_types support) actually exist at the 3.0 boundary. Recommend confirm against pre-commit 3.0 release notes."
process_notes:
  iteration_plateau_signal: |
    LLD-008 r1+r2 + LLD-009 r1 + LLD-010 r1 all share lineage with codex r2
    high findings. If LLD-010 r1 is rejected on the pass_filenames inversion,
    LLD-009 inherits NO direct impact (LLD-009 reads sys.argv[1] regardless
    of framework pass_filenames setting, since the framework always passes
    it). However A1's snippet emission is THE deliverable; getting this
    inverted invalidates the snippet T1 will lock in. Recommend pause before
    iteration 2: verify pass_filenames behavior with an actual pre-commit
    repro (5 min) before redrafting. If repro confirms framework always
    passes msg-file: defect #2 retracts, A1 keeps pass_filenames: false
    (matches no-other-filenames-to-pass intent), Glossary corrects, codex r2
    high #1 attribution should be re-examined.
recommended_disposition: |
  needs_attention with mandatory pre-iteration-2 step: hands-on repro of
  pre-commit framework commit-msg arg behavior. Two outcomes possible:
  (a) framework always passes msg-file → retract defect #2, fix Glossary,
  set pass_filenames per author taste with brief justification, redraft
  A1+A12. (b) framework honors pass_filenames: false → keep current design
  but cite the source (pre-commit version + file:line) to make the
  contract verifiable. Either way, the fsync pseudocode bug + A3 stub +
  A3b partial-config gap + A8 placement rule + fingerprint head-window
  should be fixed in r2.
```