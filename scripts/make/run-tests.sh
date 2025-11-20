#!/bin/bash
set -e

echo "Running all tests..."
uv run python -m unittest discover -s tests -p "test_*.py" -v -b --locals -f

