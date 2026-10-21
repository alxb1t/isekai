# The gate: this recipe is its one declaration. CI and the MinionsFactory skills
# run `make gate`; `make -n gate` prints what it runs.

.PHONY: gate browsers drift derive

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
	uv run python -m tools.typecheck_ui
# the browser's unit tests: `vitest run` over `ui/src/**/*.test.ts`, wrapped
# the same way
	uv run python -m tools.test_ui
# tests
	uv run pytest

# Fetch the Chromium the browser tests in `tests/e2e/` drive. Not part of the
# gate, because it downloads a browser; CI runs it before the gate.
browsers:
	uv run playwright install chromium

# Re-derive every fetched file and fail on a diff: a pinned source moved. Not part
# of the gate, because the manifests fetch from the network; `drift.yml` runs it
# weekly. `make` stops at, and names, the first command that fails.
drift:
	uv run python -m tools.derive_manifest
	uv run python -m tools.derive_eval_manifest
	uv run python -m tools.derive_vocabulary
	uv run python -m tools.derive_reader
	uv run python -m tools.derive_image_project
	git diff --exit-code --stat -- config/ evaluation/eval_models.json image/

# Re-derive every derived file: the field map, which needs the provisioned
# vocabulary, then the fetched ones.
derive:
	uv run python -m tools.derive_field_map
	$(MAKE) drift
