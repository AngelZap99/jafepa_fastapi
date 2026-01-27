<!-- JAFEPA Backend README -->

# JAFEPA Backend

Backend service for the JAFEPA platform built with FastAPI and SQLModel.

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Environment Variables](#environment-variables)
6. [Installation](#installation)
7. [Running the Project](#running-the-project)
8. [Docker Support](#docker-support)
9. [Database Management](#database-management)
10. [Linting & Formatting](#linting--formatting)
11. [API Summary](#api-summary)
12. [Recommended Workflow](#recommended-workflow)
13. [Troubleshooting](#troubleshooting)

## 1. Overview

- **Purpose**: Provide a modular API for the JAFEPA application (users/auth + catalog, inventory, invoices and sales).
- **Architecture**: Service/repository pattern with centralized error handling via `src/shared/error_handler.py`.
- **Entry point**: `main.py` wires dependencies, middlewares, handlers, and exposes routers through `api_router`.

## 2. Tech Stack

- **Language**: Python 3.13
- **Framework**: FastAPI (`fastapi`, `uvicorn`)
- **ORM**: SQLModel (SQLAlchemy 2.x)
- **Database**: PostgreSQL (default) with connection pooling
- **Validation**: Pydantic v2
- **Security**: Password hashing using `passlib[bcrypt]` (auth module in progress)

## 3. Project Structure

```text
JAFEPA-backend/
├── main.py                      # FastAPI application instance
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Optional local services
├── src/
│   ├── modules/
│   │   ├── router.py            # Aggregates module routers into api_router
│   │   └── users/
│   │       ├── domain/
│   │       │   ├── users_repository.py
│   │       │   └── users_service.py
│   │       ├── users_router.py
│   │       └── users_schema.py
│   └── shared/
│       ├── database/            # Engine creation & dependencies
│       ├── error_handler/       # Exception classes & handlers
│       └── models/              # SQLModel models
├── .env.example                 # Sample environment configuration
└── README.md
```

## 4. Prerequisites

- **Python** 3.13 or higher
- **PostgreSQL** 14+
- **pip** / **virtualenv** for dependency management
- **Docker & Docker Compose** (optional, for containerized setup)

## 5. Environment Variables

- Copy the sample file: `cp .env.example .env`
- Required keys (validated in `src/shared/database/database_config.py`):
  - `DB_DIALECT`
  - `DB_DIALECT_DRIVER`
  - `DB_HOST`
  - `DB_PORT`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
- Optional keys:
  - `PYENV` (defaults to `development`; enables SQL logging in dev)
  - `ALLOWED_CORS_ORIGINS` (comma-separated list; e.g. `http://localhost:3000,http://localhost:5173`)
- JWT/auth keys (used by `src/shared/config/env_config.py`):
  - `JWT_SECRET_KEY`
  - `JWT_ALGORITHM` (default `HS256`)
  - `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`)
  - `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default `7`)
  - `JWT_ENCRYPTION_KEY` (optional)

> Missing required variables raise `RuntimeError` at startup, ensuring misconfigurations are detected early.

## 6. Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate        # Windows (PowerShell)

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## 7. Running the Project

```bash
# Ensure PostgreSQL is running and .env is configured

# Start FastAPI with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

`main.py` registers global exception handlers and pulls in all routes via `api_router`.

## 8. Docker Support

### Run local in Dockers

```bash
# Launch services defined in docker-compose.yml (e.g., PostgreSQL)
# build postgres service
docker-compose up -d --build postgres
# build api service
docker-compose up -d --build api

# Stop services
docker-compose down

### !Important
Set .env variable $DB_HOST=postgres
# this is the docker's name service
```

### Run local

```bash
# Launch services defined in docker-compose.yml (e.g., PostgreSQL)
# build postgres service
docker-compose up -d --build postgres

# Stop services
docker-compose down

### !Important
Set .env variable $DB_HOST=localhost / $DB_HOST=127.0.0.1
# this is the host of the postgres service
```

Update `docker-compose.yml` as additional services are introduced.

## 9. Database Management

- Tables are auto-created at startup via `SQLModel.metadata.create_all(engine)` in `main.py`.
- For schema changes, modify models in `src/shared/models/` and restart the application.
- Consider adding Alembic for versioned migrations once the schema grows.

## 10. Linting & Formatting

```bash
# Lint with Ruff
ruff check .

# Format with Black
black .
```

Adopt additional tools (`isort`, `mypy`) as required by team standards.

## 11. API Summary

All module routes are mounted under the `/api` prefix in `main.py` (example: `GET /api/users/list`). Swagger/ReDoc include the full paths.

### Auth

- Login: `POST /api/auth/login` → returns `{ access_token, refresh_token, token_type }`
- Refresh: `POST /api/auth/refresh` → returns a new token pair
- Protected endpoints expect: `Authorization: Bearer <access_token>`

### Endpoints (by module)

- **Users** (`src/modules/users/users_router.py`)
  - `GET /api/users/list`
  - `GET /api/users/me` (requires auth)
  - `GET /api/users/{user_id}`
  - `POST /api/users/createUser`
  - `POST /api/users/createAdmin`
  - `PUT /api/users/update/{user_id}`
  - `DELETE /api/users/delete/{user_id}`

- **Clients** (`src/modules/client/client_router.py`, requires auth)
  - `GET /api/clients/list`
  - `GET /api/clients/{client_id}`
  - `POST /api/clients/create`
  - `PUT /api/clients/update/{client_id}`
  - `DELETE /api/clients/delete/{client_id}`

- **Warehouses** (`src/modules/warehouse/warehouse_router.py`, requires auth)
  - `GET /api/warehouses/list`
  - `GET /api/warehouses/{warehouse_id}`
  - `POST /api/warehouses/create`
  - `PUT /api/warehouses/update/{warehouse_id}`
  - `DELETE /api/warehouses/delete/{warehouse_id}`

- **Categories** (`src/modules/category/category_router.py`)
  - `GET /api/categories/list`
  - `GET /api/categories/{category_id}`
  - `POST /api/categories/create`
  - `PUT /api/categories/update/{category_id}`
  - `DELETE /api/categories/delete/{category_id}`

- **Brands** (`src/modules/brand/brand_router.py`)
  - `GET /api/brands/list`
  - `GET /api/brands/{brand_id}`
  - `POST /api/brands/create`
  - `PUT /api/brands/update/{brand_id}`
  - `DELETE /api/brands/delete/{brand_id}`

- **Products** (`src/modules/product/product_router.py`)
  - `GET /api/products/list`
  - `GET /api/products/{product_id}`
  - `POST /api/products/create` (multipart/form-data, optional `image_file`)
  - `PUT /api/products/update/{product_id}` (multipart/form-data, optional `image_file`)
  - `DELETE /api/products/delete/{product_id}`

- **Invoices** (`src/modules/invoice/invoice_router.py`)
  - `GET /api/invoices/list?skip=0&limit=100`
  - `GET /api/invoices/{invoice_id}`
  - `POST /api/invoices/create`
  - `PUT /api/invoices/update/{invoice_id}`
  - `PUT /api/invoices/update-status/{invoice_id}`
  - `DELETE /api/invoices/delete/{invoice_id}`

- **Invoice lines** (`src/modules/invoice_line/invoice_line_router.py`)
  - `GET /api/invoice-lines/list/{invoice_id}?skip=0&limit=100`
  - `POST /api/invoice-lines/create/{invoice_id}`
  - `PUT /api/invoice-lines/update/{invoice_id}/{line_id}`
  - `DELETE /api/invoice-lines/delete/{invoice_id}/{line_id}`

- **Inventory** (`src/modules/inventory/inventory_router.py`)
  - `GET /api/inventory/list`
  - `GET /api/inventory/{inventory_id}`
  - `POST /api/inventory/create`
  - `PUT /api/inventory/update/{inventory_id}`
  - `DELETE /api/inventory/delete/{inventory_id}`
  - `GET /api/inventory/movements` (filters + pagination: `skip`, `limit`)
  - `GET /api/inventory/pdf/all` (query filters like `categoria`, `subcategoria`, `marca`, `buscar`, `ids`)

- **Sales** (`src/modules/sale/sale_router.py`)
  - `GET /api/sales/report` (requires `from_date` + `to_date`; optional filters)
  - `GET /api/sales/list?skip=0&limit=100`
  - `GET /api/sales/{sale_id}`
  - `POST /api/sales/create`
  - `PUT /api/sales/update/{sale_id}`
  - `PUT /api/sales/update-status/{sale_id}`
  - `DELETE /api/sales/delete/{sale_id}`
  - `POST /api/sales/{sale_id}/lines`
  - `PUT /api/sales/{sale_id}/lines/{line_id}`
  - `DELETE /api/sales/{sale_id}/lines/{line_id}`

### Non-API (dev/test)

- `GET /test-cors` (not under `/api`)

## 12. Recommended Workflow

- **Define schemas** in the module's schema file (e.g., `users_schema.py`).
- **Implement repository methods** (e.g., `users_repository.py`).
- **Add business logic** in services (`users_service.py`).
- **Expose endpoints** via routers and include them in `src/modules/router.py`.
- **Document and test** updates; keep `.env.example` and README current.

## 13. Troubleshooting

- **Missing env vars** → `ValueError: Missing required environment variables` at startup.
- **Database connection errors** → ensure PostgreSQL is running and credentials match `.env`.
- **Import errors** → activate the virtual environment and reinstall dependencies.
- **Hashing issues** → verify `passlib` and `bcrypt` are installed (`requirements.txt`).

---

Document future decisions (auth strategy, migrations, CI/CD) here for team alignment.
