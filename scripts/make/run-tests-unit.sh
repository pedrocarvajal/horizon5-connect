#!/bin/bash
set -e

echo "Running unit tests..."
uv run python -m unittest discover -s tests/unit -p "test_*.py" -v -b --locals -f

