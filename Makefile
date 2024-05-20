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
	$(CONDA_ACTIVATE) $(CONDA_ENV_NAME) && poetry build



.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done


.PHONY: serve
serve: # Serve the site locally for testing.
ifeq (True,$(HAS_CONDA))
ifneq ("$(wildcard $(MY_ENV_DIR))","") # check if the directory is there
	$(MAKE) build
	cd api-testing && docker compose up -d --build
	$(MAKE) clean
else
	@echo ">>> Please setup the environment first with 'make environment'"
endif
else
	@echo ">>> Please setup the environment first with 'make environment'"
endif

.PHONY: clean
clean: # Clean up build files.
	@rm -r dist/

create_migrations:
	cd migrations && ./create_migrations.sh


environment: # Install the development environment.
ifeq (True,$(HAS_CONDA))
ifneq ("$(wildcard $(MY_ENV_DIR))","") # check if the directory is there
	@echo ">>> Found $(CONDA_ENV_NAME) environment in $(MY_ENV_DIR)."
	conda env update -f environment.yml -n $(CONDA_ENV_NAME) --prune
else
	@echo ">>> Detected conda, but $(CONDA_ENV_NAME) is missing in $(ENV_DIR). Installing ..."
	conda env create -f environment.yml -n $(CONDA_ENV_NAME)
endif
	$(CONDA_ACTIVATE) $(CONDA_ENV_NAME) && poetry install
	$(CONDA_ACTIVATE) $(CONDA_ENV_NAME) && pre-commit install
	@echo ">>> Everything installed, use 'conda activate $(CONDA_ENV_NAME)' to use the environment."
else
	@echo ">>> Install conda first."
	exit
endif
