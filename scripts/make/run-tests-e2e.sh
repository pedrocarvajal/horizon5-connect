#!/bin/bash
set -e

echo "Running E2E tests..."
uv run python -m unittest discover -s tests/e2e -p "test_*.py" -v -b --locals -f

