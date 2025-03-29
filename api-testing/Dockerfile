# First, build the application in the `/app` directory.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv sync --frozen

CMD ["uv", "run", "fastapi", "dev", "/app/src/sabogaapi/main.py", "--root-path", "/api", "--host", "0.0.0.0", "--proxy-headers", "--port", "8000"]
