#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-tests"

log_title "Running All Tests"

uv run python -m unittest discover -s tests -p "test_*.py" -v -b --locals -f

