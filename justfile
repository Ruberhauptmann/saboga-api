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


# Create Django migrations inside a temporary Docker container and copy them out
django-makemigrations:
	@echo "Building temporary image for migrations..."
	@docker compose -f api-testing/docker-compose.yml run --name saboga-manage saboga-manage python manage.py makemigrations || true
	@echo "Ensuring local migrations directory exists..."
	@mkdir -p api/migrations
	@echo "Copying migrations from container to host..."
	@docker cp saboga-manage:/app/api/migrations/. api/migrations/ || true
	@echo "Cleaning up temporary container and image..."
	@docker rm saboga-manage >/dev/null 2>&1 || true
	@echo "Done. Review new migration files in api/migrations."

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
