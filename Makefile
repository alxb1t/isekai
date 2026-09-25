# The gate: this recipe is its one declaration. CI and the MinionsFactory skills
# run `make gate`; `make -n gate` prints what it runs.

.PHONY: gate

gate:
# environment, from the tracked lock; not a quality axis, hence first
	uv sync --locked
# format, in check mode (a rewrite is not the check)
	uv run ruff format --check .
# lint
	uv run ruff check .
# strict types
	uv run ty check
# strict types, in the browser: `vue-tsc --noEmit` over `ui/`, wrapped so a
# missing `ui/node_modules/` refuses by name rather than exiting 127
	bash scripts/typecheck_ui.sh
# tests
	uv run pytest
