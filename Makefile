duckdb_cmd=duckdb
ifeq ($(READONLY),1)
	duckdb_cmd+= -readonly
endif

install:
	uv sync

lint:
	pre-commit run --all-files

unit:
	uv run pytest tests/unit -svx

integration:
	uv run pytest tests/integration -sv

test: unit integration

duck:
	$(duckdb_cmd) tests/integration/duckdb/data/duckdb.db
