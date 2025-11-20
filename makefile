.PHONY: run-tests run-tests-e2e run-tests-integration run-tests-unit run-submodules-synchronization run-submodules-push

run-tests:
	./scripts/make/run-tests.sh

run-tests-e2e:
	./scripts/make/run-tests-e2e.sh

run-tests-integration:
	./scripts/make/run-tests-integration.sh

run-tests-unit:
	./scripts/make/run-tests-unit.sh

run-submodules-synchronization:
	./scripts/make/run-submodules-synchronization.sh

run-submodules-push:
	./scripts/make/run-submodules-push.sh
