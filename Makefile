.PHONY: install dev test lint fmt up down migrate

# Install dependencies
install:
	pip install -r requirements-dev.txt

# Run the application
dev:
	uvicorn app.main:app --reload

# Run tests
test:
	pytest

# Lint the code
lint:
	ruff check

# Format the code
fmt:
	ruff format

# Start the containers
up:
	docker compose up -d db pgadmin

# Stop the containers
down:
	docker compose down

# Create a new autogen migration (local dev). Pass a message: make mig.new MSG="add orders"
mig.new:
	@[ "${MSG}" ] || (echo "MSG is required, e.g. make mig.new MSG='add orders'"; exit 1)
	alembic revision --rev-id $$(date +%Y%m%d%H%M%S) --autogenerate -m "${MSG}"

# Apply migrations (dev/CI/prod)
mig.up:
	alembic upgrade head

# Roll back last migration (local only)
mig.down:
	alembic downgrade -1

# Show history
mig.history:
	alembic history --verbose

# Mark DB as up-to-date without running scripts (careful!)
mig.stamp:
	alembic stamp head

# Check current vs heads (useful in CI logs)
mig.status:
	alembic current
	alembic heads
