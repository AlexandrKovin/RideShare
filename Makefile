SERVICES=postgres redis minio vault vault-init rabbitmq

services-down:
	docker compose -f docker-compose.yaml stop $(SERVICES)
	docker compose -f docker-compose.yaml rm -f $(SERVICES)

services-up: services-down
	docker compose -f docker-compose.yaml up -d $(SERVICES)

makemigrate:
	alembic revision --autogenerate

migrate:
	alembic upgrade head

lint:
	ruff format
