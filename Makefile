# OnLooker — project tasks. Run `make` or `make help` to list targets.

COMPOSE       := docker compose
PY            := .venv/bin/python
PIP           := .venv/bin/pip
MODEL         ?= llama3.2:3b

ENV_FILE      := .env
ENV_EXAMPLE   := .env.example
ENV_FILES     := $(ENV_FILE) data_ingestor/.env
UI_DIR        := ui-onlooker
UI_ENV        := $(UI_DIR)/.env.local

# Env vars that must be defined (in .env or data_ingestor/.env) before deploying.
REQUIRED_VARS := DATABASE_URL GROQ_API_KEY CENSUS_DATA_API

.DEFAULT_GOAL := help
.PHONY: help setup venv install env ui-install ui-env \
        check check-tools check-node check-env check-deps predeploy \
        build deploy up up-infra down down-v restart ps logs backend-logs ui-logs \
        schema model-pull ingest process backend ui-dev \
        dev-ingest dev-process lint clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

## ----------------------------------------------------------- preflight ------
check: check-tools check-node check-env check-deps ## Full preflight (tools + node + env + deps)
	@echo "✓ Preflight passed — ready to run/deploy."

predeploy: check-tools check-env ## Checks required before a Docker deploy (tools + env)
	@echo "✓ Predeploy checks passed."

check-tools: ## Verify core tools (python, docker, docker compose)
	@ok=1; \
	for t in python3 docker; do \
		if command -v $$t >/dev/null 2>&1; then echo "✓ $$t"; \
		else echo "✗ $$t not found — please install it"; ok=0; fi; \
	done; \
	if $(COMPOSE) version >/dev/null 2>&1; then echo "✓ docker compose"; \
	else echo "✗ docker compose v2 not found"; ok=0; fi; \
	test $$ok -eq 1 || { echo "Install the missing tools and retry."; exit 1; }

check-node: ## Verify Node.js + npm (for local frontend dev)
	@ok=1; \
	for t in node npm; do \
		if command -v $$t >/dev/null 2>&1; then echo "✓ $$t"; \
		else echo "✗ $$t not found — install Node.js 20+"; ok=0; fi; \
	done; \
	test $$ok -eq 1 || { echo "Install Node.js and retry."; exit 1; }

check-env: ## Verify .env exists and required variables are defined
	@test -f $(ENV_FILE) || { echo "✗ Missing $(ENV_FILE) — run 'make env' (or 'make setup')"; exit 1; }
	@missing=0; \
	for v in $(REQUIRED_VARS); do \
		val=$$(grep -hE "^[[:space:]]*$$v=" $(ENV_FILES) 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"'); \
		if [ -z "$$val" ]; then echo "✗ $$v is not set (checked: $(ENV_FILES))"; missing=1; \
		elif echo "$$val" | grep -qiE 'your_|_here|changeme|PASSWORD@|user:password'; then \
			echo "⚠ $$v looks like a placeholder — set a real value"; \
		else echo "✓ $$v"; fi; \
	done; \
	test $$missing -eq 0 || { echo "Environment incomplete. Edit $(ENV_FILE) (see $(ENV_EXAMPLE))."; exit 1; }
	@echo "✓ Environment variables OK"

check-deps: ## Verify the Python venv and Node modules are installed
	@test -d .venv || { echo "✗ .venv missing — run 'make venv install' (or 'make setup')"; exit 1; }
	@$(PY) -c "import fastapi, sqlalchemy, marshmallow, asyncpg" 2>/dev/null \
		&& echo "✓ Python deps installed" \
		|| { echo "✗ Python deps missing — run 'make install'"; exit 1; }
	@test -d $(UI_DIR)/node_modules \
		&& echo "✓ Frontend node_modules installed" \
		|| { echo "✗ $(UI_DIR)/node_modules missing — run 'make ui-install'"; exit 1; }
	@test -f $(UI_ENV) \
		&& echo "✓ $(UI_ENV) present" \
		|| { echo "✗ $(UI_ENV) missing — run 'make ui-env'"; exit 1; }

## --------------------------------------------------------------- setup ------
setup: check-tools venv install env ui-install ui-env ## One-shot setup (venv, deps, env files)
	@echo "✓ Setup complete. Edit $(ENV_FILE) with real values, then 'make check'."

venv: ## Create the local virtualenv if missing
	@test -d .venv || python3 -m venv .venv
	@echo "✓ venv ready"

install: venv ## Install all Python dependencies into .venv
	$(PIP) install -q -r requirements.txt -r data_ingestor/requirements.txt \
		-r data_processor/requirements.txt -r backend/requirements.txt
	@echo "✓ Python dependencies installed"

env: ## Create .env from .env.example if missing
	@test -f $(ENV_FILE) && echo "✓ $(ENV_FILE) already exists" \
		|| { cp $(ENV_EXAMPLE) $(ENV_FILE) && echo "✓ Created $(ENV_FILE) from $(ENV_EXAMPLE) — fill in your values"; }

ui-install: ## Install frontend Node dependencies
	cd $(UI_DIR) && npm install

ui-env: ## Create ui-onlooker/.env.local if missing
	@test -f $(UI_ENV) && echo "✓ $(UI_ENV) already exists" || { \
		printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\nNEXT_PUBLIC_WS_URL=ws://localhost:8000\n' > $(UI_ENV); \
		echo "✓ Created $(UI_ENV)"; }

## -------------------------------------------------------------- docker ------
build: predeploy ## Build all images (apps + jobs)
	$(COMPOSE) --profile jobs build

deploy: predeploy build up ## Preflight -> build -> start the stack

up: predeploy ## Start infra + backend + ui (runs predeploy checks first)
	$(COMPOSE) up -d

up-infra: check-tools ## Start only infra (postgres, chromadb, ollama, redis)
	$(COMPOSE) up -d postgres chromadb ollama redis

down: ## Stop and remove containers
	$(COMPOSE) down

down-v: ## Stop and remove containers + volumes (wipes local DB/models)
	$(COMPOSE) down -v

restart: down up ## Restart the stack

ps: ## List running services
	$(COMPOSE) ps

logs: ## Tail logs of all services
	$(COMPOSE) logs -f

backend-logs: ## Tail backend logs
	$(COMPOSE) logs -f backend

ui-logs: ## Tail ui-onlooker logs
	$(COMPOSE) logs -f ui-onlooker

## ---------------------------------------------------------------- data ------
schema: check-env ## Apply init.sql to the cloud DB (Azure/Supabase) via DATABASE_URL
	$(PY) containers_env/postgresql-db/apply_schema.py

model-pull: ## Pull the Llama model into the ollama service
	$(COMPOSE) exec ollama ollama pull $(MODEL)

ingest: predeploy ## Run data_ingestor once (Census -> locations table)
	$(COMPOSE) run --rm data_ingestor

process: predeploy ## Run data_processor once (synthetic audience)
	$(COMPOSE) run --rm data_processor

## ------------------------------------------------ local (no docker) ---------
backend: check ## Run the FastAPI backend locally (uvicorn, repo root)
	.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

ui-dev: ## Run the frontend dev server (npm run dev)
	cd $(UI_DIR) && npm run dev

dev-ingest: check-env ## Run the ingestor on the host (uses .env)
	$(PY) -m data_ingestor.main

dev-process: ## Run the processor on the host (LLM_TRANSPORT=mock, offline)
	$(PY) -m data_processor --transport mock

lint: ## Ruff check the Python code
	.venv/bin/ruff check data_processor/ data_ingestor/ dtos/ backend/ containers_env/postgresql-db/

clean: ## Remove caches and pipeline output artifacts
	rm -rf data_processor/output data_ingestor/data/locations
	find . -name '__pycache__' -type d -not -path './.venv/*' -prune -exec rm -rf {} +
