set positional-arguments

# Help: shows all recipes with comments
help:
    @just -l

qa *args: lint type (test args)

test *args:
    docker run --rm --name pytest-mongodb -d -p 27017:27017 -v ./api-testing/init_db.sh:/docker-entrypoint-initdb.d/init_db.sh -v ./api-testing/dump:/dump mongo:8.0-noble
    uv run pytest tests/ --import-mode importlib --cov --cov-report xml --junitxml=report.xml "$@"
    uv run coverage report
    docker stop pytest-mongodb

lint:
    uv run ruff check --fix .

type:
    uv run mypy --ignore-missing-imports src/

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
