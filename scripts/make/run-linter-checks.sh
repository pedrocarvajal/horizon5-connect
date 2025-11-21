#!/bin/bash
set -e

echo "Running linter checks..."

echo ""
echo "Running Ruff..."
uv run ruff check .

echo ""
echo "Running Pyright (Pylance)..."
uv run pyright

echo ""
echo "All linter checks passed!"
