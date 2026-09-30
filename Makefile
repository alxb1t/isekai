# The gate: this recipe is its one declaration. CI and the MinionsFactory skills
# run `make gate`; `make -n gate` prints what it runs.

.PHONY: gate drift derive

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
	bash tools/typecheck_ui.sh
# tests
	uv run pytest

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
