help: ## Show available commands
	@echo Available commands:
	@echo   install       - Install dependencies
	@echo   dev           - Run the application in development mode
	@echo   run           - Run the application
	@echo   test          - Run tests
	@echo   lint          - Lint the code
	@echo   fmt           - Format the code
	@echo   precommit     - Run pre-commit hooks on all files
	@echo   up            - Start db containers
	@echo   down          - Stop containers
	@echo   reset-db      - Drop and recreate database (dev only)
	@echo   mig.new       - Create a new migration (MSG=...)
	@echo   mig.up        - Apply migrations
	@echo   mig.down      - Roll back last migration
	@echo   mig.history   - Show migration history
	@echo   mig.stamp     - Stamp head (careful!)
	@echo   mig.status    - Show migration status

.PHONY: install dev test lint fmt up down reset-db mig.new mig.up mig.down mig.history mig.stamp mig.status

install: ## Install dependencies
	pip install -r requirements-dev.txt

dev: ## Run the application in development mode
	uvicorn app.main:app --reload

run: ## Run the application 
	uvicorn app.main:app

test: ## Run tests with pytest
	pytest

lint: ## Lint the code using ruff
	ruff check

fmt: ## Format the code using ruff
	ruff format

precommit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

up: ## Start the docker containers
	docker compose up -d db pgadmin

down: ## Stop the docker containers
	docker compose down

reset-db: ## Drop and recreate database (dev only)
	docker compose down -v
	docker compose up -d db
	alembic upgrade head

mig.new: ## Create a new autogen migration (local dev). Pass a message: make mig.new MSG="add orders"
ifndef MSG
	$(error MSG is required, e.g. make mig.new MSG='init DB')
endif
	alembic revision --autogenerate -m "$(MSG)"

mig.up: ## Apply migrations (dev/CI/prod)
	alembic upgrade head

mig.down: ## Roll back last migration (local only)
	alembic downgrade -1

mig.history: ## Show the migration history
	alembic history --verbose

mig.stamp: ## Mark DB as up-to-date without running scripts (careful!)
	alembic stamp head

mig.status: ## Check current vs heads (useful in CI logs)
	alembic current
	alembic heads
