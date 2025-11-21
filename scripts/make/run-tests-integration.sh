#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-tests-integration"

log_title "Running Integration Tests"

uv run python -m unittest discover -s tests/integration -p "test_*.py" -v -b --locals -f

