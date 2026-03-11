set positional-arguments

# Help: shows all recipes with comments
help:
    @just -l

qa *args: lint type (test args)

test *args:
    uv run pytest tests/ --import-mode importlib --cov src --cov-report xml --junitxml=report.xml "$@"
    uv run coverage report -m


lint:
    uv run ruff check --fix .

format:
    uv run ruff format .

type:
    uv run ty check

migration MESSAGE:
    docker exec -it saboga-api uv run alembic revision --autogenerate -m "{{MESSAGE}}"
    docker cp saboga-api:/app/alembic ./


# Create Django migrations inside a temporary Docker container and copy them out
django-makemigrations:
	@echo "Building temporary image for migrations..."
	@docker build -f api-testing/Dockerfile -t saboga-api-migrator .
	@docker run --name saboga-api-migrator-run saboga-api-migrator python manage.py makemigrations || true
	@echo "Ensuring local migrations directory exists..."
	@mkdir -p apps/api/migrations
	@echo "Copying migrations from container to host..."
	@docker cp saboga-api-migrator-run:/app/apps/api/migrations/. apps/api/migrations/ || true
	@echo "Cleaning up temporary container and image..."
	@docker rm saboga-api-migrator-run >/dev/null 2>&1 || true
	@docker rmi saboga-api-migrator >/dev/null 2>&1 || true
	@echo "Done. Review new migration files in apps/api/migrations."

# Install the development environment
environment:
	@if command -v uv > /dev/null; then \
	  echo '>>> Detected uv.'; \
	  uv sync --all-groups; \
	  uv run pre-commit install; \
	else \
	  echo '>>> Install uv first.'; \
	  exit 1; \
	fi
