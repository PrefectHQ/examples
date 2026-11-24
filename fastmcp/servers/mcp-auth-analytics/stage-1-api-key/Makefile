.PHONY: seed seed-motherduck stage1 test
seed:
	uv run python scripts/seed.py
seed-motherduck:
	uv run python scripts/seed.py --motherduck
stage1: seed
	uv run python demos/stage1.py
test:
	uv run pytest -q
