install:
	uv sync
	pre-commit install

lint:
	pre-commit run --all-files
