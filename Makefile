check:
	uv run black src
	uv run ruff format src
	uv run ruff check src