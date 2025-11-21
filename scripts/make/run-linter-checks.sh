#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-linter-checks"

log_title "Running Linter Checks"

log_info "Running Ruff..."
uv run ruff check .

log_info "Running Pyright (Pylance)..."
uv run pyright

log_separator
log_info "All linter checks passed!"
