---
bump: patch
after: [0182-the-render-guard]
---

# The stage record

A stage is declared once, in the foundation, and the foundation's tables that name a stage are read from it.

Reading map: [design](design.md) holds the record, the derivation, the cases and the documents, [tasks](tasks.md) its phases.

## Why

The foundation names a stage in several literals: `BUDGETS` in `failures.py`, and `DESCRIPTION`, `PHOTOGRAPH_VERBS` and each stage folder's word in `names.py`. No test holds that they agree, and a new stage edits each of them.

The record is `isekai/foundation/producers.py`: a frozen `Producer` per stage, in the order a run passes through them. The tables are read from it and stay bound at their old homes, so no importer changes. Behaviour is unchanged: the same values in the same order, held by cases written first.

## What Changes

- `Producer` and `PRODUCERS` join `isekai/foundation/producers.py`, standard library only: a row each for caption, wd14, tags, sheet, review, assemble and render, with key, folder, scope, verb and budget. `run.py` re-exports both names.
- `BUDGETS` in `failures.py`, and `DESCRIPTION`, `PHOTOGRAPH_VERBS` and the stage folders' words in `names.py`, are read from the record.
- Cases in `tests/test_run_directory.py` hold each table by its literal value and order, written and passing before the derive, and hold the record's rows.
- The standing mutant `FN-1` of `tests/mutants.json` is anchored on the wd14 row of the record.
- D73 records the record; D21 and D62 name it. The foundation README, `docs/principles.md`, `ARCHITECTURE.md` and `run.py`'s docstring say so.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes, so the change carries `skip_specs`.

## Impact

- Code: `isekai/foundation/producers.py` (new), `isekai/foundation/failures.py`, `isekai/foundation/names.py`, `isekai/foundation/run.py`.
- Tests: `tests/test_run_directory.py`, `tests/mutants.json`.
- Docs: `docs/decisions.md` (D21, D62, D73), `isekai/foundation/README.md`, `docs/principles.md`, `ARCHITECTURE.md`.
- No importer changes, no format version moves: the budget's key is the `stage` of a failure record on disk, and stays.

## Not in this change

- Every table above the foundation and on the page, and the hand copies of a stage's order: each is read from the record when the interface's tables are taken up.
- The sequence inside a stage and `refusal_for`.
- The pipeline's own `STAGE` constants, and the hub cell's `Stage` and `ui/src/wire.ts`: the cell's stage is the ladder's answer, no producer stage.
- The edit stage: it has no folder of its own, no budget and no row today.
- Any file under `ui/`, `tools/` or `evaluation/`.
