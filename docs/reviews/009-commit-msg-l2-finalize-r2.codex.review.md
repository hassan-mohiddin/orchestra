# Codex Adversarial Review

Target: branch diff against main
Verdict: needs-attention

No-ship: the L2-finalize design is bypassable in multiple concrete ways (fail-open control flow, mutable trust source, and path-boundary check bug), so policy enforcement can be evaded under realistic local workflows.

Findings:
- [critical] Severity source is read from mutable working tree, not staged/committed content (docs/features/009-commit-msg-l2-finalize.md:289-290)
  `_verify_finding_in_attestation` reads attestation YAML directly from filesystem text. Inference from the call flow shown in this doc: commit-msg finalize uses this helper during enforcement, so an author can keep an unstaged local edit that downgrades severity (or alters findings), pass L2-finalize, and commit without that attestation mutation landing. That breaks the trust boundary for Critical/Important gating and allows supersession-required changes to pass as narrow-change.
  Recommendation: Load attestation data from the staged index (`git show :0:<attestation_path>`) during commit-msg finalize, and reject if staged blob is missing or diverges from expected refs. Do not use working-tree bytes for enforcement decisions.
- [high] Core enforcement is explicitly fail-open when pending file is absent (docs/features/009-commit-msg-l2-finalize.md:351-353)
  The finalize entrypoint returns success immediately when the pending file is missing. The same doc explicitly treats `--no-verify` as a sanctioned path to that state. Result: the main canon-inplace guard can be skipped while still producing a successful commit, which defeats the stated enforcement model and makes bypass trivial in exactly the path attackers or rushed contributors will use.
  Recommendation: Fail closed when pending state is missing by recomputing canon-inplace candidates from staged docs at commit-msg time, or require an explicit, validated bypass token in the commit message plus CI-side enforcement that blocks silent bypass.
- [high] Path traversal boundary check is vulnerable to prefix confusion (docs/features/009-commit-msg-l2-finalize.md:273-281)
  The traversal guard uses `str(full).startswith(str(reviews_root))`. This is not a path-boundary-safe check (`/repo/docs/reviews_evil/...` passes a `/repo/docs/reviews` prefix test). Combined with regex acceptance of `docs/reviews/...` paths containing `..`, this can permit references outside the intended `docs/reviews` subtree, undermining attestation provenance controls.
  Recommendation: Replace string-prefix checks with `full.is_relative_to(reviews_root)` (or equivalent canonical path containment check) after resolving `(repo_root / attestation_path)`, and hard-reject any normalized path that escapes `docs/reviews`.

Next steps:
- Patch the trust source and containment checks first (staged attestation reads + `is_relative_to` path validation).
- Remove silent fail-open on missing pending state by adding commit-msg-time recomputation or enforced explicit bypass semantics.
- Add adversarial tests for unstaged attestation tampering, `docs/reviews/../reviews_evil/...` paths, and `--no-verify` bypass attempts to prevent regression.
