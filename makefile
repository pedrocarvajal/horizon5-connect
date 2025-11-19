.ONESHELL:
.PHONY: run-tests run-tests-e2e run-tests-integration run-tests-unit run-submodules-synchronization run-submodules-push help

run-tests:
	@echo "Running all tests..."
	$(MAKE) run-tests-e2e
	$(MAKE) run-tests-integration
	$(MAKE) run-tests-unit

run-tests-e2e:
	@echo "Running E2E tests..."
	uv run python -m unittest discover -s tests/e2e -p "test_*.py" -v -b --locals

run-tests-integration:
	@echo "Running integration tests..."
	uv run python -m unittest discover -s tests/integration -p "test_*.py" -v -b --locals

run-tests-unit:
	@echo "Running unit tests..."
	uv run python -m unittest discover -s tests/unit -p "test_*.py" -v -b --locals

run-submodules-synchronization:
	git submodule update --remote --recursive

run-submodules-push:
	@if [ -z "$$(git submodule status 2>/dev/null)" ]; then \
		echo "No submodules found"; \
	else \
		git submodule foreach 'if [ -n "$$(git status --porcelain)" ]; then echo "Pushing changes in $$name..."; git add . && git commit -m "Update submodule" && git push; else echo "No changes in $$name"; fi'; \
	fi
