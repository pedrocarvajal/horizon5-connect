#!/bin/bash
set -e

echo "Running integration tests..."
uv run python -m unittest discover -s tests/integration -p "test_*.py" -v -b --locals -f

