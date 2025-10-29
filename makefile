.ONESHELL:

run-dev:
	docker compose -f docker-compose.yml up

run-production:
	docker compose -f docker-compose.yml up -d