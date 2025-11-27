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

- **Purpose**: Provide a modular API to manage users (and upcoming auth features) for the JAFEPA application.
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
  - `CORS_ORIGINS` (comma-separated list; defaults to `http://localhost:3000`)
- Required keys to JWT and auth:
  - `JWT_SECRET`
  - `JWT_EXPIRES_IN`

> Missing required variables raise `ValueError` at startup, ensuring misconfigurations are detected early.

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

```bash
# Launch services defined in docker-compose.yml (e.g., PostgreSQL)
# build postgres service
docker-compose up -d --build postgres 
# build api service
docker-compose up -d --build api

# Stop services
docker-compose down
```

Update `docker-compose.yml` as additional services are introduced.

## 9. Database Management

- Tables are auto-created at startup via `SQLModel.metadata.create_all(engine)` in `main.py`.
- For schema changes, modify models in `src/shared/models/` and restart the application.
- Consider adding Alembic for versioned migrations once the schema grows.

Place tests under a `tests/` directory and add fixtures for SQLModel sessions.

## 10. Linting & Formatting

```bash
# Lint with Ruff
ruff check .

# Format with Black
black .
```

Adopt additional tools (`isort`, `mypy`) as required by team standards.

## 11. API Summary

- **Router aggregator**: `src/modules/router.py` exposes `api_router`.
- **Users module** (`src/modules/users/users_router.py`):
  - `PUT /users/list` <- Get all users with pagination and optional filters
  - `GET /users/{guid}` <- Get user by guid
  - `GET /users/me` <- Get context user by token
  - `POST /users/create` <- Create user
  - `POST /users/create-admin` <- Create admin
  - `PATCH /users/update/{guid}` <- Update user
  - `DELETE /users/{guid}` <- Delete user
- Future modules (e.g., `auth`) should be registered in `src/modules/router.py`.

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
