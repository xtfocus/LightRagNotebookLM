# Makefile

# Load environment variables from .env file
ifneq (,$(wildcard .env))
include .env
export
endif

# Variables
BACKEND_DIR=fastapi_backend
FRONTEND_DIR=nextjs-frontend
DOCKER_COMPOSE=docker compose

# Help
.PHONY: help
help:
	@echo "Available commands:"
	@awk '/^[a-zA-Z_-]+:/{split($$1, target, ":"); print "  " target[1] "\t" substr($$0, index($$0,$$2))}' $(MAKEFILE_LIST)

test-frontend: ## Run frontend tests using npm
	cd $(FRONTEND_DIR) && pnpm run test


# Docker commands
.PHONY: docker-backend-shell docker-frontend-shell docker-build docker-build-backend \
        docker-build-frontend docker-start-backend docker-start-frontend docker-up-test-db \
        docker-migrate-db docker-db-schema docker-test-backend docker-test-frontend


docker-backend-shell: ## Access the backend container shell
	$(DOCKER_COMPOSE) run --rm backend sh

docker-frontend-shell: ## Access the frontend container shell
	$(DOCKER_COMPOSE) run --rm frontend sh

docker-build: ## Build all the services
	$(DOCKER_COMPOSE) build --no-cache

docker-build-backend: ## Build the backend container with no cache
	$(DOCKER_COMPOSE) build backend --no-cache

docker-build-frontend: ## Build the frontend container with no cache
	$(DOCKER_COMPOSE) build frontend --no-cache

docker-start-backend: ## Start the backend container
	$(DOCKER_COMPOSE) up backend

docker-start-frontend: ## Start the frontend container
	$(DOCKER_COMPOSE) up frontend

docker-up-test-db: ## Start the test database container
	$(DOCKER_COMPOSE) up db_test

docker-migrate-db: ## Run database migrations using Alembic
	$(DOCKER_COMPOSE) run --rm backend alembic upgrade head

docker-db-schema: ## Generate a new migration schema. Usage: make docker-db-schema migration_name="add users"
	$(DOCKER_COMPOSE) run --rm backend alembic revision --autogenerate -m "$(migration_name)"

docker-test-backend: ## Run tests for the backend
	$(DOCKER_COMPOSE) run --rm backend pytest

docker-test-frontend: ## Run tests for the frontend
	$(DOCKER_COMPOSE) run --rm frontend pnpm run test

# API Client Generation
.PHONY: sync-api-client sync-api-client-force sync-api-client-clean

sync-api-client: ## Generate OpenAPI client from backend (with health check)
	@echo "🔄 Starting backend..."
	$(DOCKER_COMPOSE) up backend -d
	@echo "⏳ Waiting for backend to be healthy..."
	@until curl -f http://localhost:${BACKEND_PORT:-8000}/api/v1/utils/health-check/ > /dev/null 2>&1; do \
		echo "   Backend not ready yet, waiting..."; \
		sleep 2; \
	done
	@echo "✅ Backend is healthy"
	@echo "📥 Downloading OpenAPI schema..."
	curl -s http://localhost:${BACKEND_PORT:-8000}/api/v1/openapi.json > local-shared-data/openapi.json
	@echo "🔧 Generating frontend client..."
	$(DOCKER_COMPOSE) exec frontend pnpm generate-client
	@echo "✅ API client generation complete!"

sync-api-client-force: ## Force regenerate OpenAPI client (restart backend)
	@echo "🔄 Restarting backend..."
	$(DOCKER_COMPOSE) restart backend
	@echo "⏳ Waiting for backend to be healthy..."
	@echo "🔍 Debug: Using hardcoded port 8000"
	@echo "🔍 Debug: Testing health check endpoint at http://localhost:8000/api/v1/utils/health-check/"
	@curl -v http://localhost:8000/api/v1/utils/health-check/ || echo "❌ Health check failed"
	@until curl -f http://localhost:8000/api/v1/utils/health-check/ > /dev/null 2>&1; do \
		echo "   Backend not ready yet, waiting..."; \
		echo "   🔍 Debug: Testing health check again at http://localhost:8000/api/v1/utils/health-check/"; \
		curl -v http://localhost:8000/api/v1/utils/health-check/ || echo "   ❌ Health check failed again"; \
		sleep 2; \
	done
	@echo "✅ Backend is healthy"
	@echo "📥 Downloading OpenAPI schema..."
	curl -s http://localhost:8000/api/v1/openapi.json > local-shared-data/openapi.json
	@echo "🔧 Generating frontend client..."
	$(DOCKER_COMPOSE) exec frontend pnpm generate-client
	@echo "✅ API client generation complete!"

sync-api-client-clean: ## Generate OpenAPI client and clean up containers
	@echo "🔄 Starting backend and frontend..."
	$(DOCKER_COMPOSE) up backend frontend -d
	@echo "⏳ Waiting for backend to be healthy..."
	@until curl -f http://localhost:${BACKEND_PORT:-8000}/api/v1/utils/health-check/ > /dev/null 2>&1; do \
		echo "   Backend not ready yet, waiting..."; \
		sleep 2; \
	done
	@echo "✅ Backend is healthy"
	@echo "📥 Downloading OpenAPI schema..."
	curl -s http://localhost:${BACKEND_PORT:-8000}/api/v1/openapi.json > local-shared-data/openapi.json
	@echo "🔧 Generating frontend client..."
	$(DOCKER_COMPOSE) exec frontend pnpm generate-client
	@echo "✅ API client generation complete!"
	@echo "🧹 Cleaning up containers..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Cleanup complete!"

# Cleanup commands
.PHONY: docker-clean docker-clean-all find-unused-frontend-code

docker-clean: ## Stop and remove containers, networks, and volumes
	@echo "🧹 Cleaning up Docker resources..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Cleanup complete!"

docker-clean-all: ## Stop and remove containers, networks, volumes, and images
	@echo "🧹 Cleaning up all Docker resources..."
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans
	@echo "✅ Complete cleanup finished!"

find-unused-frontend-code: ## Find and report unused files, dependencies, and exports in frontend using knip
	@echo "🔍 Scanning frontend for unused code with knip..."
	$(DOCKER_COMPOSE) exec frontend npx --yes knip
	@echo "✅ Frontend code analysis complete! Review the output above for unused items."
