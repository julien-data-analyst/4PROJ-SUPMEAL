FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Installs straight into the system Python instead of the .venv `uv sync`
# creates by default - there's no "activate" step needed in a container that
# only ever runs this one project, and --no-dev drops ruff/pytest/etc, which
# have no reason to ship in the production image.
ENV UV_PROJECT_ENVIRONMENT=/usr/local

COPY . .

# collectstatic can't run here: settings.py requires DATABASE_NAME (no
# default) as soon as Django's settings module is imported, and real
# credentials aren't available at build time (only via env_file at
# container start) - it runs from docker-compose.prod.yml's command
# instead, alongside migrate.
RUN uv sync --locked --no-dev

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
