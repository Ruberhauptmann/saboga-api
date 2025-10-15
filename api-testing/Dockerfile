FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        firefox-esr

WORKDIR /app

# Copy dependency files first
ADD pyproject.toml uv.lock README.md ./
# Create venv and install deps (cached unless lockfile changes)
RUN uv sync --frozen --no-install-project

# Now copy in source (doesn't break dependency cache)
ADD src ./src
ADD api-testing ./api-testing
ADD alembic ./alembic
ADD alembic.ini ./

RUN chmod +x /app/api-testing/entrypoint.sh

CMD ["/app/api-testing/entrypoint.sh"]
