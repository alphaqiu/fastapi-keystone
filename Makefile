check:
	uv run black src
	uv run ruff format src
	uv run ruff check src

clean:
	@rm -rf dist
	@rm -rf src/fastapi_keystone.egg-info

build:
	# uv run bumpver update --no-commit --no-tag --no-push
	uv build

publish:
	uv run twine upload dist/*