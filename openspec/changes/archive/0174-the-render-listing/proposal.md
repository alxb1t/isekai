---
bump: patch
version: 0.87.30
---

# The render listing

Move the render group's listing out of the paid stage into `isekai/foundation/layout.py`, with `run_view.rendered`, so no module above the stage imports it to list a folder. No behaviour changes.

Reading map: [design](design.md) holds the decisions, the test cost and the risks, [tasks](tasks.md) holds the phases: the listing, the importers, the documents.

## Why

`is_render`, `is_sidecar`, `rendered_seeds`, `sidecars` and `render_groups` sit in `isekai/pipeline/generate.py`, the stage that costs money. They read a seed's test, the sidecar's suffix, the outputs folder's name and a run's directory, and every one is a foundation name. `run_view.py`, `compare_view.py`, `render.py` and `ui/library.py` import the stage only to list a folder, and `review` may not import it; `rendered` in `run_view.py` lists the same folders for the evaluator.

## What Changes

- `is_render`, `is_sidecar`, `rendered_seeds`, `sidecars` and `render_groups` move from `generate.py` to `layout.py` unchanged, and `run.py` re-exports them under `__all__` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)).
- `generate.py` reads `rendered_seeds` and `render_groups` from the foundation and re-binds `is_render` and `is_sidecar`, which tests import from it.
- `run_view.py` and `compare_view.py` import nothing from the stage. `render.py` and `ui/library.py` read the listing from `isekai.foundation.run` and keep the stage's own names.
- `rendered` moves from `run_view.py` to `layout.py`; `run_view.py` reads it from `run.py`, and the evaluator's imports of it switch.
- The mutant `FN-9` names `layout.py`, its text unchanged.
- `docs/decisions.md` gains D69, the foundation README's row for `layout.py` and `layout.py`'s docstring say what the module now holds, and the *Imported by* tables are derived again.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement fits, so the change carries `skip_specs: true` and an empty `specs/`.

## Impact

- `isekai/foundation/layout.py` grows by the listing; `isekai/foundation/run.py` re-exports it.
- `isekai/pipeline/generate.py`, `isekai/interface/run_view.py`, `isekai/interface/compare_view.py`, `isekai/interface/render.py`, `isekai/interface/ui/library.py`, `evaluation/__main__.py` and `evaluation/recall.py` change their imports.
- `tests/mutants.json` changes one `path`. No other file under `tests/`, `ui/` or `tools/` changes.
- `docs/decisions.md` gains D69. `isekai/foundation/README.md` gets a new `layout.py` row text, and its derived table, `isekai/interface/README.md` and `isekai/pipeline/README.md` are re-derived.

## Not in this change

- The sites that name a render's image or record by hand, and a builder for them.
- `lacks`, `shortfall`, `duration`, `source_seeds` and `discard_render`: they read an approval or delete.
- `render_groups`' `str.isdigit`: the folder it should not list is a later change's question.
- Any other definition of "rendered".
- `rendered_at` and `edit_at`.
- The evaluator's import of `trackable`, and a layer rule for `evaluation/`.
- A scenario or a spec delta.
- Any file under `tests/` but `tests/mutants.json`.
