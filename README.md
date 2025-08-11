# E-Commerce-API
E-commerce API built with FastAPI & SQLModel — A clean, production-ready REST API for managing products, categories, and orders. Includes async PostgreSQL integration, Alembic migrations, Dockerized database, GitHub Actions CI/CD, and pre-commit hooks. Designed for scalability and best practices in modern Python backend development.

## ✨Features

- FastAPI for high-performance async APIs

- SQLModel + PostgreSQL for ORM and data modeling

- Alembic migrations for database schema management

- Docker & docker-compose for containerized services (PostgreSQL + pgAdmin)

- GitHub Actions CI for linting, type-checking, migrations, and tests

- Pre-commit hooks for code quality (Ruff, mypy)

- Modular folder structure for scalability and maintainability

## 🛠 Tech Stack

- Python 3.12

- FastAPI

- SQLModel

- PostgreSQL (asyncpg)

- Alembic

- Docker & docker-compose

- GitHub Actions

## 🚀 Getting Started
1. Clone repo
```bash
git clone https://github.com/yourusername/ecommerce-api.git
cd ecommerce-api
```

2. Copy env and start DB
```bash
cp .env.example .env
```

3. Start database
```bash
docker compose up -d db pgadmin
```

3. Install deps
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

4. Run migrations
```bash
alembic upgrade head
```

5. Start API
```bash
uvicorn app.main:app --reload
```

## 🧪 Running Tests
```bash
pytest
```

## 🧩 ERD (Entity-Relationship Diagram)
```mermaid
erDiagram
    USER ||--o{ CART : "owns"
    USER ||--o{ ORDER : "places"

    CATEGORY ||--o{ PRODUCT : "has many"
    PRODUCT ||--o{ CART_ITEM : "in carts"
    PRODUCT ||--o{ ORDER_ITEM : "in orders"

    CART ||--o{ CART_ITEM : "contains"
    ORDER ||--o{ ORDER_ITEM : "contains"

    USER {
        UUID id PK
        string email UK
        string hashed_password
        timestamp created_at
        timestamp updated_at
    }

    CATEGORY {
        UUID id PK
        string name UK
        UUID parent_id FK "nullable for root"
        timestamp created_at
        timestamp updated_at
    }

    PRODUCT {
        UUID id PK
        string name
        string sku UK
        text description
        numeric price
        int stock
        UUID category_id FK
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CART {
        UUID id PK
        UUID user_id FK
        timestamp created_at
        timestamp updated_at
    }

    CART_ITEM {
        UUID id PK
        UUID cart_id FK
        UUID product_id FK
        int quantity
        numeric unit_price
        numeric subtotal
        timestamp created_at
        timestamp updated_at
    }

    ORDER {
        UUID id PK
        UUID user_id FK
        string status "pending|paid|shipped|cancelled"
        numeric total
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEM {
        UUID id PK
        UUID order_id FK
        UUID product_id FK
        int quantity
        numeric unit_price
        numeric subtotal
    }

```

## 📜 License
This project is licensed under the MIT License. See [LICENCE](/LICENSE) for details.

