#!/usr/bin/env bash
# Orchestra pre-commit hook — runs cli.lint --pre-commit on staged docs.
# Installed by `python -m cli.install_hooks`.
#
# Env-portability (BUG-010 v1.6.2 fix): bare `python` not always on PATH
# (modern systems often have python3 only; venv-bin paths vary). Try
# in order: $PYTHON env override → python3 → python. Fail loudly if none.

set -euo pipefail

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PY=python3
  elif command -v python >/dev/null 2>&1; then
    PY=python
  else
    echo "error: pre-commit hook needs python (set \$PYTHON or install python3)" >&2
    exit 1
  fi
fi

"$PY" -m cli.lint --pre-commit
