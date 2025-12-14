.PHONY: run-tests run-tests-e2e run-tests-integration run-tests-unit run-linter-checks run-linter-fixes run-submodules-synchronization run-submodules-push

run-tests:
	./vendor/scripts/make/run-tests.sh

run-tests-e2e:
	./vendor/scripts/make/run-tests-e2e.sh

run-tests-integration:
	./vendor/scripts/make/run-tests-integration.sh

run-tests-unit:
	./vendor/scripts/make/run-tests-unit.sh

run-linter-checks:
	./vendor/scripts/make/run-linter-checks.sh $(if $(FILE),--file $(FILE)) $(if $(FOLDER),--folder $(FOLDER))

run-linter-fixes:
	./vendor/scripts/make/run-linter-fixes.sh

run-submodules-synchronization:
	./vendor/scripts/make/run-submodules-synchronization.sh

run-submodules-push:
	./vendor/scripts/make/run-submodules-push.sh
