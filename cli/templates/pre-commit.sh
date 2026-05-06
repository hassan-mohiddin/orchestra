#!/usr/bin/env bash
# Orchestra pre-commit hook — runs cli.lint --pre-commit on staged docs.
# Installed by `python -m cli.install_hooks`.

set -euo pipefail

python -m cli.lint --pre-commit
