#!/usr/bin/env bash
set -e

echo "Running Alembic migrations..."
cd /app && alembic upgrade head

echo "Starting FastAPI..."
fastapi run /app/src/sabogaapi/main.py --root-path /api --host 0.0.0.0 --proxy-headers --port 8000
