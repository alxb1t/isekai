---
bump: patch
debt: [0165·S1]
---

# The runs filter

`runs_in` takes a keyword-only name predicate, `named`, and the library passes its separator test through it, so a folder that is no run is never probed.

Reading map: [design](design.md) the helper, the library's call, the tests and the mutation run, [tasks](tasks.md) its phases.

## Why

The library's `_runs` used to drop a folder whose name lacks the identifier separator before it looked inside. It now calls `runs_in`, which probes every child's `run.json` first and filters the name after. A folder that is no run and cannot be read, such as `private` at mode `000`, raises `PermissionError` from that probe on Python 3.12.

The server handles `Refusal` and no other error, so Home, the hub and the run lookup fail for an operator who did nothing wrong. Debt card `0165·S1` records it.

## What Changes

- `isekai/foundation/rundir.py`: `runs_in(root, *, named=None)`. A child whose name `named` rejects is left out before its frame is probed; with `None` every child is probed, as today.
- `isekai/interface/ui/library.py`: `_runs` passes the separator test as `named` and drops its own filter.
- `tests/test_run_directory.py`: cases hold the predicate, one of them with a real `chmod(0o000)` folder.
- `tests/test_ui_library.py`: one case reads the hub with such a folder beside a run.
- `docs/decisions.md`: D65's *Why* says the library's filter goes through `named`, and its *Made by* gains this change.
- `ui` requirement *The hub shows each source's stage in each offered flow, and a tick assigns it*: gains the scenario `ui:hub:a-folder-that-is-no-run-is-ignored`; its prose and every other scenario are unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: the hub's requirement gains one scenario, under the clause that the rest of the grid is still shown.

## Impact

- Code: `isekai/foundation/rundir.py`, `isekai/interface/ui/library.py`.
- Tests: `tests/test_run_directory.py`, `tests/test_ui_library.py`.
- Docs: `docs/decisions.md`. The living `ui` spec takes the scenario at release.
- No format version moves, no flow is re-pinned, no file frozen into the pod image changes, and no dependency is added.

## Not in this change

- A folder named like a run that cannot be read: it stays an error, as it was before the shared helper.
- `run_at`, and a catch of the filesystem's error inside the helper.
- The other sites: `run_ids` in `isekai/interface/render.py`, the compare page's `_runs`, the CLI's listing, and the verbs' lookups.
- Resume's `_run_for` and evaluation's `runs_in`, and every file under `evaluation/`.
- A handler for an error that is no `Refusal`.
- A new decision.
