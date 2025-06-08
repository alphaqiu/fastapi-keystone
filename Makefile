check:
	uv run black src
	uv run ruff format src
	uv run ruff check src
	uv run black examples
	uv run ruff format examples

clean:
	@rm -rf dist
	@rm -rf src/fastapi_keystone.egg-info

build:
	# uv run bumpver update --no-commit --no-tag --no-push
	uv build

publish:
	uv run twine upload dist/*

test:
	uv run --python 3.10 pytest
	uv run --python 3.11 pytest
	uv run --python 3.12 pytest
	uv run pytest

coverage:
	uv run pytest --cov=src