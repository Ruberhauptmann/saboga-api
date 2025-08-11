# First, build the application in the `/app` directory.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ADD src /app/src
ADD api-testing /app/api-testing
ADD pyproject.toml /app/
ADD uv.lock /app/
ADD README.md /app/
ADD .venv /app/.venv

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv sync --group test --frozen
