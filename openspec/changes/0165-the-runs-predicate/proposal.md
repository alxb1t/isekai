---
bump: patch
---

# The runs predicate

One rule for which folder is a run, in the foundation, called by the front-end sites that each wrote it in their own words; behaviour unchanged.

Reading map: [design](design.md) holds the rule, the sites and the tests, [tasks](tasks.md) its phases: the rule, the sites, the decision.

## Why

A run is a folder holding its frame file. The render's `run_ids`, the compare page's `_runs`, the CLI's `_migrate`, the verbs' `run_or_photo` and `parse_cells`, and the library's `_runs` each ask that of a folder in their own words. A change to the rule would be an edit in each, and a site that missed it would list a folder the others refuse.

## What Changes

- `isekai/foundation/rundir.py` gains `runs_in(root)` and `run_at(root, id)`; `run.py` re-exports both.
- Each site calls one of them. The library's `_runs` keeps its separator filter and its key, so the hub is unchanged.
- `docs/decisions.md` gains D65, the rule and its exceptions; the foundation README's `rundir.py` row names the functions.
- Requirements touched: none. No scenario is added and no delta is written (`skip_specs`), because no behaviour changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Code: `isekai/foundation/rundir.py`, `isekai/foundation/run.py`, `isekai/interface/render.py`, `isekai/interface/compare_view.py`, `isekai/interface/cli.py`, `isekai/interface/verbs/common.py` and `isekai/interface/ui/library.py`.
- Tests: `tests/test_run_directory.py` gains the rule's cases. The mutation runs read `tests/test_render.py`, `tests/test_compare.py`, `tests/test_migrate.py`, `tests/test_pipeline_cli.py` and `tests/test_ui_library.py`, which gain a case only for a survivor. No existing assertion changes.
- Docs: `docs/decisions.md`, `isekai/foundation/README.md`.
- No module is added, no derived *Imported by* row changes and no ratchet row moves. No file under `evaluation/` changes.

## Not in this change

- Resume's `_run_for`: it finds a run by its photograph's digest and passes over a folder with no frame, so `open_run` writes one in place. It changes when resume stops creating a frame in place.
- Evaluation's `runs_in` and every file under `evaluation/`: it lists a folder whose frame is no file, so that a frame that does not read is a row. It changes when the evaluators list by the rule and their recall scenario says so.
- `_laid_out` and the remedy `rendered_at` picks: each asks about one path, not a listing.
- A scenario or a spec delta, and a ratchet's row.
