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
