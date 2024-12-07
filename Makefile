SHELL:=/bin/bash

#CONDA_ENV_NAME := saboga-api

# Variables to test the conda environment
ifeq (,$(shell which uv))
	HAS_UV=False
else
	HAS_UV=True
	#ENV_DIR=$(shell conda info --base)
	#MY_ENV_DIR=$(ENV_DIR)/envs/$(CONDA_ENV_NAME)
	#CONDA_ACTIVATE=. $$(conda info --base)/etc/profile.d/conda.sh ; conda activate
endif

build:
	uv build

.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done


.PHONY: serve
dev: # Serve the site locally for testing.
	cd api-testing && docker compose watch

.PHONY: clean
clean: # Clean up build files.
	@rm -r dist/

environment: # Install the development environment.
ifeq (True,$(HAS_UV))
	@echo ">>> Installing "
	uv sync
	uv run pre-commit install
	@echo ">>> Everything installed."
else
	@echo ">>> Install uv first."
	exit
endif
