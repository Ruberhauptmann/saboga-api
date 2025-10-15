SHELL:=/bin/bash

CONDA_ENV_NAME := saboga-api

# Variables to test the conda environment
ifeq (,$(shell which conda))
	HAS_CONDA=False
else
	HAS_CONDA=True
	ENV_DIR=$(shell conda info --base)
	MY_ENV_DIR=$(ENV_DIR)/envs/$(CONDA_ENV_NAME)
	CONDA_ACTIVATE=. $$(conda info --base)/etc/profile.d/conda.sh ; conda activate
endif

build:
	uv build

.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done


.PHONY: dev
dev: # Serve the site locally for testing.
	cd api-testing && docker compose -f docker-compose.yml watch

.PHONY: dev-prod
dev-prod: # Serve the site locally for testing.
	cd api-testing && docker compose -f docker-compose.yml up -d --build

.PHONY: dev-prod-monitoring
dev-prod-monitoring: # Serve the site locally for testing.
	cd api-testing && docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d --build

.PHONY: make-migrations
make-migrations: # Create migrations


.PHONY: dump-dev-db
dump-dev-db: # Dump dev database
	docker exec saboga-database mongodump -u mongoadmin -p password --authenticationDatabase admin --db boardgames
	docker cp saboga-database:/dump/boardgames/. api-testing/dump/boardgames


.PHONY: clean
clean: # Clean up build files.
	@rm -r dist/

environment: # Install the development environment.
ifeq (True,$(HAS_CONDA))
ifneq ("$(wildcard $(MY_ENV_DIR))","") # check if the directory is there
	@echo ">>> Found $(CONDA_ENV_NAME) environment in $(MY_ENV_DIR)."
	@conda env update -f conda_env.yaml -n $(CONDA_ENV_NAME)
else
	@echo ">>> Detected conda, but $(CONDA_ENV_NAME) is missing in $(ENV_DIR). Installing ..."
	@conda env create -f conda_env.yaml -n $(CONDA_ENV_NAME)
endif
	@conda run -n $(CONDA_ENV_NAME) uv sync --all-groups
	@conda run -n $(CONDA_ENV_NAME) uv run pre-commit install
	@echo ">>> Everything installed, use 'conda activate $(CONDA_ENV_NAME)' to use the environment."
ifeq ("$(wildcard api-testing/certs/*)","")
	@echo ">>> Certificates for local TLS are not installed, installing them now."
	cd api-testing && mkdir -p certs
	cd api-testing/certs && conda run -n $(CONDA_ENV_NAME) mkcert saboga.localhost
	cd api-testing/certs && conda run -n $(CONDA_ENV_NAME) mkcert traefik.localhost
	cd api-testing/certs && conda run -n $(CONDA_ENV_NAME) mkcert prometheus.monitoring.localhost
else
	@echo ">>> Certificates for local TLS are installed."
endif
else
	@echo ">>> Install conda first."
	exit
endif
