install:
	uv sync

test:
	uv run pytest tests

duck:
	duckdb tests/integration/duckdb/data/duckdb.db
