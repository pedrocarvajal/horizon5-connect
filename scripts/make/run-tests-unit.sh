#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-tests-unit"

log_title "Running Unit Tests"

uv run python -m unittest discover -s tests/unit -p "test_*.py" -v -b --locals -f

