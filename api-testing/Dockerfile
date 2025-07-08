FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        firefox-esr

ADD . /app

WORKDIR /app
RUN uv sync --frozen

RUN chmod +x /app/api-testing/entrypoint.sh

CMD ["/app/api-testing/entrypoint.sh"]
