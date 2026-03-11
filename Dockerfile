# single‑stage build, uv is installed and available at runtime
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# bring in any system packages your app needs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        firefox-esr && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy only what's needed for dependency resolution first
# (this lets Docker cache the venv when dependencies don't change)
COPY pyproject.toml uv.lock /app/
# if you have additional build-time files, copy them too

# sync the virtualenv using uv – it will be created inside /app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# now copy the application sources
COPY saboga_project /app/saboga_project
COPY manage.py /app/
COPY scripts/ /app/scripts
COPY README.md /app/

# (optional) re‑run sync in case application itself adds extras
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# make sure the venv is on PATH
ENV PATH="/app/.venv/bin:$PATH"

# run using uv or plain python – uv is still in the image so both work
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
