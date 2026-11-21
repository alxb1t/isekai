---
bump: patch
version: 0.87.43
after: [0186-the-runner-cut]
---

# The runner move

The flow stages' runner, its builders and `_seam`, `_assign`, `_assign_one` and `_existing_run` move from `isekai/interface/cli.py` to `isekai/interface/verbs/runner.py`, and `prepare`'s run is bound in its own module.

Reading map: [design](design.md) holds the order of the moved code, the names bound back and the tests, [tasks](tasks.md) its phases.

## Why

[D58](../../../docs/decisions.md#d58--a-verb-is-declared-once-in-its-familys-module) accepts that the runs of `render`, `prepare` and `migrate` are bound in `cli.py` and reopens when `_per_item` leaves it. The runner cut (`0186-the-runner-cut`) left `_per_item` and its builders in `cli.py` at sizes the ratchet accepts. This version puts them with the verbs they run, so `prepare` no longer needs `cli.py` to hand it the runner.

## What Changes

- `isekai/interface/verbs/runner.py`: new; holds the moved code, text for text.
- `isekai/interface/cli.py`: the moved code and the imports it alone read go; `_per_item` is read through the front door; `_prepare` goes.
- `isekai/interface/verbs/__init__.py`: lists `_per_item`, no longer `run_prepare`.
- `isekai/interface/verbs/prepare.py`: `run_prepare(args, wired)` reads `_per_item` from its sibling and is the run of `PREPARE_ROW`.
- `tests/mutants.json`: `PB-2b` is re-pointed to `runner.py`.
- `docs/decisions.md`: D58's *Accepts* and *Made by* are amended; no decision is added.
- `isekai/interface/README.md`, `isekai/README.md`, `cli.py`'s docstring and each derived *Imported by* table follow the move.

No requirement changes: every printed line, progress line and exit code stays byte-equal, and the import graph `python -m isekai` loads is unchanged. The change carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

The files that change are `isekai/interface/cli.py`, `isekai/interface/verbs/__init__.py`, `isekai/interface/verbs/prepare.py`, the new `isekai/interface/verbs/runner.py`, `tests/mutants.json`, `tests/test_pipeline_cli.py` only if a survivor needs a case, `docs/decisions.md`, `isekai/interface/README.md`, `isekai/README.md` and the derived tables of the layer READMEs. No existing test's assertion changes.

## Not in this change

- `assign` and `show` as rows of the runner's table: they are no stages.
- The runs of `render` and `migrate`: they stay bound in `cli.py` with `_dispatch_argv`, `RUNS_ROOT` and `wiring`.
- The cancel's own guard, any printed text and the app's reading of the progress lines.
- The command builder and a refusal's fix as a field: `the-command-builder`.
- Any file under `ui/`, `tools/` or `evaluation/`, and any new decision.
