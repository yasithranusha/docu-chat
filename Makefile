.PHONY: help dev start test lint format install migrate migrate-create clean docker-build docker-run docker-stop

# Default target - show help
help:
	@echo "Available commands:"
	@echo "  make dev           - Run development server with auto-reload"
	@echo "  make start         - Run production server with workers"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make install       - Install dependencies"
	@echo "  make migrate       - Apply database migrations"
	@echo "  make migrate-create MSG='message' - Create new migration"
	@echo "  make clean         - Remove Python cache files"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo "  make docker-stop   - Stop Docker container"

# Development server with auto-reload
dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server with workers
start:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Run tests
test:
	poetry run pytest -v

# Run tests with coverage
test-cov:
	poetry run pytest --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	poetry run ruff check app/

# Format code
format:
	poetry run black app/

# Type checking
typecheck:
	poetry run mypy app/

# Install dependencies
install:
	poetry install

# Apply database migrations
migrate:
	poetry run alembic upgrade head

# Create new migration
migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a migration message. Usage: make migrate-create MSG='your message'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(MSG)"

# Rollback last migration
migrate-rollback:
	poetry run alembic downgrade -1

# Clean Python cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

# Build Docker image
docker-build:
	docker build -t docu-chat:latest .

# Run Docker container
docker-run:
	docker run -d --name docu-chat -p 8000:8000 --env-file .env docu-chat:latest

# Stop Docker container
docker-stop:
	docker stop docu-chat
	docker rm docu-chat

# Docker Compose up
docker-up:
	docker-compose up -d

# Docker Compose down
docker-down:
	docker-compose down

# Show logs
logs:
	docker logs -f docu-chat

# All quality checks (lint, format, typecheck)
check: lint typecheck
	@echo "All checks passed!"

# Setup project (install + migrate)
setup: install migrate
	@echo "Project setup complete!"
