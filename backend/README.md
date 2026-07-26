# Backend

Django REST Framework API for SUPMEAL (recipes, cookbooks, planning,
messaging), backed by PostgreSQL and managed with [uv](https://docs.astral.sh/uv/).

All commands below assume they are run from the **repository root**
(where `docker-compose.dev.yml` lives), not from `backend/`.

## Summary

- [Prerequisites](#prerequisites)
- [Environment variables](#environment-variables)
- [Running the backend with PostgreSQL](#running-the-backend-with-postgresql)
- [Django migrations & initial setup](#django-migrations--initial-setup)
- [Running the tests](#running-the-tests)

---

## Prerequisites

- Docker and Docker Compose - the backend, PostgreSQL and their Python
  dependencies all run in containers, so no local Python/uv install is
  required.

## Environment variables

Copy the example file to `.env` at the repository root and fill in the
values (a working default is provided for local development):

```bash
cp .env.example .env
```

Relevant variables (see `.env.example` for the full list):

| Variable | Used by | Description |
| --- | --- | --- |
| `DATABASE_NAME` / `DATABASE_USER` / `DATABASE_PASSWORD` | `postgres`, `backend` | Database credentials, shared between the Postgres container and Django's `DATABASES` setting. |
| `DATABASE_HOST` / `DATABASE_PORT` | `backend` | Where Django connects to Postgres (`postgres`/`5432` inside the Docker network). |
| `POSTGRES_PORT` | `postgres` | Host port Postgres is published on (e.g. `5432`). |
| `BACKEND_PORT` | `backend` | Host port the Django dev server is published on (e.g. `8000`). |

The Microsoft OAuth variables (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
`AZURE_CLIENT_SECRET`, `AZURE_REDIRECT_URI`, `AZURE_AUTHORITY`) are optional
for running the backend - see [`docs/oauth.md`](../docs/oauth.md) if you
need to configure Microsoft login.

## Running the backend with PostgreSQL

To run just the API and its database (without the frontend), start only the
`postgres` and `backend` services:

```bash
docker compose -f docker-compose.dev.yml up postgres backend
```

Add `--build` the first time (or after changing `Dockerfile_dev`/dependencies):

```bash
docker compose -f docker-compose.dev.yml up --build postgres backend
```

This:

- starts PostgreSQL 16 and waits for it to be healthy (`pg_isready`);
- installs Python dependencies with `uv sync`;
- applies pending Django migrations automatically;
- starts the dev server on `http://localhost:${BACKEND_PORT}/`.

The API is then reachable at `http://localhost:${BACKEND_PORT}/api/`, with
interactive docs at `http://localhost:${BACKEND_PORT}/api/docs/` (Swagger UI)
and `http://localhost:${BACKEND_PORT}/api/schema/` (raw OpenAPI schema) - see
[`docs/api.md`](../docs/api.md) for the full route reference.

To run in the background, add `-d`; stop everything with:

```bash
docker compose -f docker-compose.dev.yml down
```

## Django migrations & initial setup

The `backend` service already runs `python manage.py migrate` on every
container start (see its `command:` in `docker-compose.dev.yml`), so a plain
`up` as above is enough after pulling changes that include new migrations.

To run Django management commands by hand instead - for example to create
the first admin account - use `exec` while the stack is running (or `run
--rm` to spin up a one-off container):

```bash
# Apply migrations manually
docker compose -f docker-compose.dev.yml exec backend uv run python manage.py migrate

# Create migration files after changing a models.py
docker compose -f docker-compose.dev.yml exec backend uv run python manage.py makemigrations

# Create a superuser for /admin/
docker compose -f docker-compose.dev.yml exec backend uv run python manage.py createsuperuser

# Open a Django shell
docker compose -f docker-compose.dev.yml exec backend uv run python manage.py shell
```

See [`docs/database.md`](../docs/database.md#running-migrations) for more
migration commands (rollbacks, previewing SQL, the `--check --dry-run`
CI check) and for the composite-primary-key gotcha that affects
`makemigrations` when adding several new interdependent apps at once.

## Running the tests

Tests use `pytest` + `pytest-django` and run inside the `backend` container,
against the same PostgreSQL instance (a separate `test_<DATABASE_NAME>`
database is created/destroyed automatically by `pytest-django` for each run).

Run the whole suite:

```bash
docker compose -f docker-compose.dev.yml exec backend uv run pytest
```

Run a single app's tests, a single file, or a single test:

```bash
docker compose -f docker-compose.dev.yml exec backend uv run pytest tests/users/
docker compose -f docker-compose.dev.yml exec backend uv run pytest tests/users/logout_test.py
docker compose -f docker-compose.dev.yml exec backend uv run pytest tests/users/logout_test.py::test_logout_blacklists_refresh_token
```

Useful flags: `-v` for verbose per-test output, `-x` to stop at the first
failure.

Lint and type-check the code (also worth running before committing):

```bash
docker compose -f docker-compose.dev.yml exec backend uv run ruff check .
docker compose -f docker-compose.dev.yml exec backend uv run basedpyright
```
