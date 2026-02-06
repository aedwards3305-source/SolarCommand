.PHONY: up down build logs api-logs worker-logs frontend-logs db-reset seed test

# Start all services
up:
	docker compose up -d

# Start with rebuild
build:
	docker compose up -d --build

# Stop all services
down:
	docker compose down

# View all logs
logs:
	docker compose logs -f

# View individual service logs
api-logs:
	docker compose logs -f api

worker-logs:
	docker compose logs -f worker

frontend-logs:
	docker compose logs -f frontend

# Reset database (destroy volume and rebuild)
db-reset:
	docker compose down -v
	docker compose up -d --build

# Run seed data
seed:
	docker compose exec api sh -c "PGPASSWORD=solar psql -h db -U solar -d solarcommand -f /seed/seed.sql"

# Run backend tests
test:
	docker compose exec api pytest tests/ -v

# Run Alembic migration
migrate:
	docker compose exec api alembic upgrade head
