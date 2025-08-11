# E-Commerce-API
E-commerce API built with FastAPI & SQLModel — A clean, production-ready REST API for managing products, categories, and orders. Includes async PostgreSQL integration, Alembic migrations, Dockerized database, GitHub Actions CI/CD, and pre-commit hooks. Designed for scalability and best practices in modern Python backend development.

## Features

- FastAPI for high-performance async APIs

- SQLModel + PostgreSQL for ORM and data modeling

- Alembic migrations for database schema management

- Docker & docker-compose for containerized services (PostgreSQL + pgAdmin)

- GitHub Actions CI for linting, type-checking, migrations, and tests

- Pre-commit hooks for code quality (Ruff, mypy)

- Modular folder structure for scalability and maintainability

## Tech Stack

- Python 3.12

- FastAPI

- SQLModel

- PostgreSQL (asyncpg)

- Alembic

- Docker & docker-compose

- GitHub Actions

## Getting Started
### Clone repo
git clone https://github.com/yourusername/ecommerce-api.git
cd ecommerce-api

### Copy env and start DB
cp .env.example .env
docker compose up -d db pgadmin

### Install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

### Run migrations
alembic upgrade head

### Start API
uvicorn app.main:app --reload
