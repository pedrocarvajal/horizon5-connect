.ONESHELL:
.PHONY: run-tests run-tests-e2e run-tests-integration run-tests-unit help

run-tests:
	uv run python -m unittest discover -s tests -p "test_*.py" -v

run-tests-e2e:
	uv run python -m unittest discover -s tests/e2e -p "test_*.py" -v

run-tests-integration:
	uv run python -m unittest discover -s tests/integration -p "test_*.py" -v

run-tests-unit:
	uv run python -m unittest discover -s tests/unit -p "test_*.py" -v
