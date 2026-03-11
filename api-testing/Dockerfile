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
ADD saboga_project ./saboga_project
ADD manage.py ./
ADD scripts/ ./scripts
ADD api-testing ./api-testing
ADD api /app/api
ADD static/ /app/static

RUN chmod +x /app/api-testing/entrypoint.sh

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

CMD ["./api-testing/entrypoint.sh"]
