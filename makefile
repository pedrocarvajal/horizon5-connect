.ONESHELL:

run-dev:
	docker compose -f docker-compose.yml down -v
	docker compose -f docker-compose.yml build --no-cache
	docker compose -f docker-compose.yml up

run-production:
	docker compose -f docker-compose.yml up -d