#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-linter-checks"

TARGET=""
FILE_PATH=""
FOLDER_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --file)
            FILE_PATH="$2"
            shift 2
            ;;
        --folder)
            FOLDER_PATH="$2"
            shift 2
            ;;
        *)
            log_error "Unknown argument: $1"
            log_info "Usage: $0 [--file <path>] [--folder <path>]"
            exit 1
            ;;
    esac
done

if [[ -n "$FILE_PATH" && -n "$FOLDER_PATH" ]]; then
    log_error "Cannot specify both --file and --folder"
    exit 1
fi

if [[ -n "$FILE_PATH" ]]; then
    TARGET="$FILE_PATH"
    log_title "Running Linter Checks on file: $TARGET"
elif [[ -n "$FOLDER_PATH" ]]; then
    TARGET="$FOLDER_PATH"
    log_title "Running Linter Checks on folder: $TARGET"
else
    TARGET="."
    log_title "Running Linter Checks on entire project"
fi

EXIT_CODE=0

log_info "Running Ruff format check..."
uv run ruff format --check "$TARGET" || EXIT_CODE=$?

log_info "Running Ruff..."
uv run ruff check "$TARGET" || EXIT_CODE=$?

log_info "Running Pyright (Pylance)..."
if [[ "$TARGET" == "." ]]; then
    uv run pyright || EXIT_CODE=$?
else
    uv run pyright "$TARGET" || EXIT_CODE=$?
fi

log_info "Running pydocstyle (PEP 257 Docstring Conventions)..."
uv run pydocstyle "$TARGET" || EXIT_CODE=$?

log_separator
if [ $EXIT_CODE -eq 0 ]; then
    log_info "All linter checks passed!"
else
    log_error "Some linter checks failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
