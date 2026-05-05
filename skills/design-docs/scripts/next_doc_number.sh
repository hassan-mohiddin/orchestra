#!/bin/bash
# next_doc_number.sh — Get the next auto-incremented doc number
# Usage: ./next_doc_number.sh <type>
#   type: features | bugs | adr | research | postmortem

set -e

TYPE="${1:?Usage: next_doc_number.sh <features|bugs|adr|research|postmortem>}"
DOCS_DIR="$(git rev-parse --show-toplevel)/docs"

case "$TYPE" in
  features)
    DIR="$DOCS_DIR/features"
    PREFIX=""
    ;;
  bugs)
    DIR="$DOCS_DIR/bugs"
    PREFIX="BUG-"
    ;;
  adr)
    DIR="$DOCS_DIR/adr"
    PREFIX="ADR-"
    ;;
  research)
    DIR="$DOCS_DIR/research"
    PREFIX=""
    ;;
  postmortem)
    # Postmortems are date-prefixed, not numbered. Emit today's date in expected format.
    DATE_PREFIX="$(date +%Y-%m-%d)"
    printf "POSTMORTEM-%s\n" "$DATE_PREFIX"
    exit 0
    ;;
  *)
    echo "Error: Unknown type '$TYPE'. Use: features, bugs, adr, research, postmortem" >&2
    exit 1
    ;;
esac

# Create dir if it doesn't exist
mkdir -p "$DIR"

# Find the highest number
HIGHEST=$(ls "$DIR" 2>/dev/null | grep -oE '^[A-Z]*-?[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)

if [ -z "$HIGHEST" ]; then
  NEXT=1
else
  # Force base-10 — without 10# prefix, bash treats leading-zero numbers (008, 012)
  # as octal and silently miscounts (012 → 10 instead of 12).
  NEXT=$((10#$HIGHEST + 1))
fi

# Pad to 3 digits
printf "%s%03d\n" "$PREFIX" "$NEXT"
