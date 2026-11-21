# The stage record — tasks

The cases are written first, the record comes in, the tables are read from it, and the documents say so.

## Progress

- [x] 1 — The cases · moderate
- [x] 2 — The record · moderate
- [ ] 3 — The derive · moderate
- [ ] 4 — The documents · moderate

## 1 — The cases

- [x] 1.1 **HALT CHECK** The tables stand as [D3](design.md#d3) replaces them.
  Verify: `git grep -c -e "^BUDGETS: " -e "^DESCRIPTION = " -e "^PHOTOGRAPH_VERBS = " -- isekai/foundation/failures.py isekai/foundation/names.py` prints `isekai/foundation/failures.py:1` and `isekai/foundation/names.py:2`.
- [x] 1.2 In `tests/test_run_directory.py`, add `CAPTIONS`, `PHOTOGRAPH_VERBS`, `SHEETS` and `TAGS` to the import from `isekai.foundation.run`, and add the literal-value case of [D4](design.md#d4) after `test_the_rendering_stages_budget_is_one`. It passes on today's code.
  Verify: `uv run pytest tests/test_run_directory.py -k the_stage_tables_hold_their_literal_values` exits 0.
- [x] 1.3 Run `tools.mutate` over the budget's lines, one run a range, on `tests/test_run_directory.py`, with the opening lines of [D5](design.md#d5): `isekai/foundation/failures.py:163-167`, then `:172`, then `:184-200`. A survivor is killed as `## Equivalent mutants` of [the design](design.md) says, or named there.
  Verify: `grep -c -F "## Equivalent mutants" openspec/changes/0183-the-stage-record/design.md` prints `1`.

## 2 — The record

- [x] 2.1 **HALT CHECK** No name of the record is taken in the code, the tests or the tools.
  Verify: `git grep -n -w -e Producer -e PRODUCERS -- isekai tests tools evaluation` prints nothing.
- [x] 2.2 In `tests/test_run_directory.py`, add `PRODUCERS` to the import from `isekai.foundation.run`, and add the rows case and the tables case of [D4](design.md#d4) after the case of 1.2.
  Verify: `uv run pytest tests/test_run_directory.py -k the_record` exits 2, on the import of `PRODUCERS`.
- [x] 2.3 Create `isekai/foundation/producers.py` exactly as [D1](design.md#d1) gives it.
  Verify: `grep -c -e "^class Producer" -e "^PRODUCERS" isekai/foundation/producers.py` prints `2`.
- [x] 2.4 In `isekai/foundation/run.py`, import both names of `isekai/foundation/producers.py`, add them to `__all__` and name the sibling in the docstring, as [D2](design.md#d2) says.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_layers.py` exits 0.
- [x] 2.5 In `isekai/foundation/README.md`, add the Files row and the *Imported by* row of `producers.py` after those of `names.py`, as [D7](design.md#d7) gives them, then run `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.

## 3 — The derive

- [ ] 3.1 In `isekai/foundation/failures.py`, import the record from `isekai/foundation/producers.py` and replace the comment and the `BUDGETS` literal with the block of [D3](design.md#d3), so no `: 3,` stays.
  Verify: `git grep -n -F ": 3," -- isekai/foundation/failures.py` prints nothing.
- [ ] 3.2 In `isekai/foundation/names.py`, import the record from `isekai/foundation/producers.py`, add the comment line and replace the assignments from `CAPTIONS` to `OUTPUTS`, `DESCRIPTION = (CAPTIONS, WD14, TAGS)` among them, with the block of [D3](design.md#d3).
  Verify: `git grep -n -F "= (CAPTIONS, WD14, TAGS)" -- isekai/foundation/names.py` prints nothing.
- [ ] 3.3 In `tests/mutants.json`, replace the entry `FN-1`, which names `isekai/foundation/failures.py`, with the one of [D6](design.md#d6).
  Verify: `git grep -c -F "isekai/foundation/failures.py" -- tests/mutants.json` prints `tests/mutants.json:2`.
- [ ] 3.4 Run `uv run python -m tools.derive_imported_by`: the row of `producers.py` now names `failures.py`, `names.py` and `run.py`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 3.5 Run the cases and the guards over the derived tables.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_resume.py tests/test_layers.py tests/test_ratchets.py tests/test_docs.py tests/test_spec_bindings.py` exits 0.
- [ ] 3.6 Run `tools.mutate` over `_spent` on the closing lines of [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/foundation/failures.py:137-141 --tests tests/test_run_directory.py` exits 0.
- [ ] 3.7 Run `tools.mutate` over `exhausted` on its closing line.
  Verify: `uv run python -m tools.mutate isekai/foundation/failures.py:146 --tests tests/test_run_directory.py` exits 0.
- [ ] 3.8 Run `tools.mutate` over `check_budget` on its closing lines.
  Verify: `uv run python -m tools.mutate isekai/foundation/failures.py:158-174 --tests tests/test_run_directory.py` exits 0.
- [ ] 3.9 Replay the standing mutants, `FN-1` on the record's row among them.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 4 — The documents

- [ ] 4.1 In `docs/decisions.md`, add D73 after D72 and amend D21 and D62, as [D8](design.md#d8) gives them.
  Verify: `git grep -n -F "### D73" -- docs/decisions.md` prints one line.
- [ ] 4.2 In `isekai/foundation/README.md`, replace the opening lines, where `Nothing here knows about a stage`, and the `names.py` and `failures.py` rows, as [D8](design.md#d8) says.
  Verify: `git grep -n -F "Nothing here knows about a stage" -- isekai/foundation/README.md` prints nothing.
- [ ] 4.3 In `docs/principles.md` and `ARCHITECTURE.md`, add the stage record to the foundation's bullet as [D8](design.md#d8) says.
  Verify: `git grep -c -F "the stage record" -- docs/principles.md ARCHITECTURE.md` prints `ARCHITECTURE.md:1` and `docs/principles.md:1`.
- [ ] 4.4 Check that the documents and the derived tables agree.
  Verify: `uv run pytest tests/test_docs.py tests/test_spec_prose.py` exits 0.
