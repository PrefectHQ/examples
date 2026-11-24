.PHONY: seed seed-motherduck up down serve stage2 cimd test
seed:
	uv run python scripts/seed.py
seed-motherduck:
	uv run python scripts/seed.py --motherduck
up:
	docker compose up -d --wait
down:
	docker compose down
serve:
	PYTHONPATH=src uv run python -m analytics_mcp.server
stage2: seed
	uv run python demos/stage2.py
cimd:
	uv run python demos/cimd_login.py
test:
	uv run pytest -q
