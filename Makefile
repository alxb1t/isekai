# The gate a human types and the gate the orchestrator runs, kept in one place.
#
# This recipe MIRRORS the `gate` array in .minions/minions.toml -- same commands,
# same order. Change one and you must change the other in the same commit; a
# missing, extra or reordered command is a real mismatch (gate:make-mirrors),
# because the orchestrator reads the array and the human reads this file.

.PHONY: gate

gate:
	uv sync --locked
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check
	uv run pytest
