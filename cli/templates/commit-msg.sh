#!/usr/bin/env bash
# Orchestra commit-msg hook — verify Refs: line on fix:/feat: commits at message-author time.
# Installed by `python -m cli.install_hooks --commit-msg`.

set -euo pipefail

MSG_FILE="$1"
SUBJECT=$(head -n1 "$MSG_FILE")

if echo "$SUBJECT" | grep -qE '^(fix|feat)(\(.*\))?:'; then
    if ! grep -q '^Refs: docs/' "$MSG_FILE"; then
        echo "error: commit subject is fix:/feat: but message body has no 'Refs: docs/...' line." >&2
        echo "Required by orchestra commit-strategy (see docs/STANDARDS.md)." >&2
        exit 1
    fi
fi

exit 0
