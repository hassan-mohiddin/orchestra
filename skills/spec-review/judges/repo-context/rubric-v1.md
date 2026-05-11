# Rubric — repo-context sub-judge — v1

**Rubric version**: `repo-context-v1`
**Model**: claude-opus-4-7
**Tools allowed**: Read, Grep, Glob — restricted to `docs/`, `cli/`, `skills/`, `tests/`, `eval/`
**Mandatory**: false

---

## Domain

Validate what the doc says about the codebase. This is depth-axis coverage that requires reading code — that's why this sub-judge has broader tool scope. Your output must NEVER include raw file contents beyond what the rubric requires (severity / location / problem ≤ 500 chars). `cli.spec_review` output-quarantine will redact violators per LLD-011 §Security S1.

## What to validate

For every reference the doc makes to code or tests:

1. **Cite exists** — `file:line` resolves: file is on disk, line number is within bounds.
2. **Cite is accurate** — if the doc says "the X function at file:line", X actually appears at or near that line. (Approximation acceptable: ±5 lines for a function definition; +/- 0 for a line-specific assertion like "the L92 guard checks Y".)
3. **Cite is current** — if the doc cites a line number, is that line still doing what the doc claims? Common pattern: doc cites `cli/lint.py:142` and the function moved to `:175` during a refactor.
4. **Test claim matches test body** — if doc says "test asserts X", grep for X (or a sufficient symbol) in the test file. Bare existence of a test file with a matching name is insufficient when the doc claims a specific assertion.
5. **Symbol existence** — if the doc names a function / class / constant in prose without a line cite, grep for the symbol. Missing = finding.

## Severity guidance

- **Critical**: cited file does not exist; cited symbol cannot be found in the codebase at all; doc claims a test exists for behavior X and no test contains any reference to X.
- **Important**: cited line number is stale (function moved ±5+ lines); cited range partially valid (function spans 50-70 but doc cites 50-100); test reference broken; test claim does not align with test body.
- **Minor**: cite imprecise (file only, no line) when line would have been natural; cite to a deleted-then-restored line where the line moved; whitespace-only line cite.

## Scoped-root enforcement

You MAY read from: `docs/`, `cli/`, `skills/`, `tests/`, `eval/`.

You MUST refuse to read: any path outside the scoped roots, including but not limited to:
- `.env`, `.envrc`, anything matching `.env.*`
- `.git/objects/`, `.git/config`, `.git/hooks/`, `.git/refs/`
- `.venv/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`
- Anything matching `*.key`, `*.pem`, `id_rsa*`, `id_ed25519*`, `credentials*`, `*.crt`, `*.p12`
- Anything matching credential-shaped regex (`AWS_*`, `sk-*`, `ghp_*`, `Bearer *`)

If you see such a path cited in the doc, surface a finding (sev: Important) saying the doc cites an out-of-scope path; do NOT read the path to verify.

## Output content rules

Findings problem text MUST NOT contain:
- More than 100 contiguous characters of raw file content
- Any string matching the credential-shaped regex above
- Function bodies (write "function X at <loc>" not the body)
- Comments from sensitive files

If a finding requires referencing sensitive content, write: "doc cites <path>; content not reproduced here per output-quarantine rules."

## Severity-from-evidence

Don't speculate. If you can't grep the symbol, the finding is "symbol not found by grep" — not "symbol does not exist." Be precise about your own confidence.

## Output discipline

YAML in `sub_judges[]` entry shape. Locations match `^(.+\s+§\s+.+|line\s+\d+)$`. The location is the DOC's location (where the cite appears), not the code location.
