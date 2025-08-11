FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        firefox-esr

ADD src /app/src
ADD api-testing /app/api-testing
ADD pyproject.toml /app/
ADD uv.lock /app/
ADD README.md /app/
ADD .venv /app/.venv

WORKDIR /app
RUN uv sync --frozen

RUN chmod +x /app/api-testing/entrypoint.sh

CMD ["/app/api-testing/entrypoint.sh"]
