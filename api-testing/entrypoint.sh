#!/bin/bash
set -e

echo "Run migrations"
uv run alembic upgrade head

# Run DB seeding
echo "Seeding database..."
uv run python /app/api-testing/seed-dev-db.py

# Start FastAPI dev server
echo "Starting FastAPI dev server..."
exec uv run fastapi dev /app/src/sabogaapi/main.py --root-path /api --host 0.0.0.0 --proxy-headers --port 8000
