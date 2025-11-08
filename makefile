.ONESHELL:
.PHONY: test test-e2e test-integration test-unit test-watch test-coverage help

test:
	uv run python -m unittest discover -s tests -p "test_*.py" -v

test-e2e:
	uv run python -m unittest discover -s tests/e2e -p "test_*.py" -v

test-integration:
	uv run python -m unittest discover -s tests/integration -p "test_*.py" -v

test-unit:
	uv run python -m unittest discover -s tests/unit -p "test_*.py" -v
