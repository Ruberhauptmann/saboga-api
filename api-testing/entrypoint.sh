#!/bin/bash
set -e

echo "Run migrations"
uv run python manage.py migrate

# Run DB seeding
echo "Seeding database..."
uv run python manage.py runscript seed_dev_db

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

# Start Django dev server
echo "Starting Django dev server..."

exec uv run python manage.py runserver 0.0.0.0:8000
