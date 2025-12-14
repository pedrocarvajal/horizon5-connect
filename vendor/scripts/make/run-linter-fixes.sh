#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-linter-fixes"

log_title "Running Linter Fixes"

log_info "Running Ruff format..."
uv run ruff format .

log_info "Running Ruff with auto-fix..."
uv run ruff check --fix .

log_separator
log_info "All linter fixes applied!"
