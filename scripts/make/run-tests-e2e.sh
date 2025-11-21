#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-tests-e2e"

log_title "Running E2E Tests"

uv run python -m unittest discover -s tests/e2e -p "test_*.py" -v -b --locals -f

