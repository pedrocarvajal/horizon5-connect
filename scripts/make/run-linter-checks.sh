#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-linter-checks"

log_title "Running Linter Checks"

EXIT_CODE=0

log_info "Running Ruff format check..."
uv run ruff format --check . || EXIT_CODE=$?

log_info "Running Ruff..."
uv run ruff check . || EXIT_CODE=$?

log_info "Running Pyright (Pylance)..."
uv run pyright || EXIT_CODE=$?

log_info "Running pydocstyle (PEP 257 Docstring Conventions)..."
uv run pydocstyle . || EXIT_CODE=$?

log_separator
if [ $EXIT_CODE -eq 0 ]; then
    log_info "All linter checks passed!"
else
    log_error "Some linter checks failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
