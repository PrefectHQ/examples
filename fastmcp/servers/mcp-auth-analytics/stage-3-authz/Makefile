# Load .env (if present) into the environment of every recipe line.
SHELL := /bin/bash
.SHELLFLAGS := -c
LOAD = set -a; [ -f .env ] && . ./.env; set +a;

.PHONY: seed seed-motherduck up down serve stage3 cimd test
seed:
	@$(LOAD) uv run python scripts/seed.py
seed-motherduck:
	@$(LOAD) uv run python scripts/seed.py --motherduck
up:
	docker compose up -d --wait
down:
	docker compose down
serve:
	@$(LOAD) PYTHONPATH=src uv run python -m analytics_mcp.server
stage3: seed
	@$(LOAD) uv run python demos/stage3.py
cimd:
	@$(LOAD) uv run python demos/cimd_login.py
test:
	uv run pytest -q
