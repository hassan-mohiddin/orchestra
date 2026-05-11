#!/usr/bin/env bash
# orchestra commit-msg hook — Refs:-line check + L2-finalize tiered narrow-change
# (line 2 'orchestra' fingerprint required by LLD-010 A4 RAW_FINGERPRINT verify)
set -euo pipefail

MSG_FILE="$1"
SUBJECT=$(head -n1 "$MSG_FILE")

# Refs:-line check (existing)
if echo "$SUBJECT" | grep -qE '^(fix|feat)(\(.*\))?:'; then
    if ! grep -q '^Refs: docs/' "$MSG_FILE"; then
        echo "error: commit subject is fix:/feat: but message body has no 'Refs: docs/...' line." >&2
        echo "Required by orchestra commit-strategy (see docs/STANDARDS.md)." >&2
        exit 1
    fi
fi

# L2-finalize (LLD-009 r6): tiered narrow-change rule against pending file + msg
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "error: commit-msg hook requires python3 (or PYTHON env var set to a Python >=3.10 interpreter)" >&2
    exit 1
fi
"$PY" -m cli.lint --commit-msg-finalize "$MSG_FILE"
