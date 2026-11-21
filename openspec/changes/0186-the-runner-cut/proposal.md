---
bump: patch
after: [0185-the-serve-seams]
---

# The runner cut

`_per_item` in `isekai/interface/cli.py` becomes a builder per stage verb, a table keyed by the verb's name and a runner for one item, and its ratchet rows go.

Reading map: [design](design.md) holds the shapes, the order of reads and the tests, [tasks](tasks.md) its phases.

## Why

`_per_item` and its nested `work` are past the ceiling of the function ratchet: one chain of `if verb ==` branches, a branch per stage verb, each holding a nested step, then the code that reports and runs the step. Rows of `LONG_FUNCTIONS` name them ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), and [D58](../../../docs/decisions.md#d58--a-verb-is-declared-once-in-its-familys-module) reopens only when `_per_item` leaves `cli.py`. This version cuts it in place; `the-runner-move` moves it.

## What Changes

- `isekai/interface/cli.py`: the item's shared reads become one frozen `_Item`, built by `_item_of`.
- `isekai/interface/cli.py`: `caption`, `tag`, `sheet`, `review` and `approve` each get a builder, and a table `_BUILDERS` keyed by the verb's name replaces the chain.
- `isekai/interface/cli.py`: the code that reports and runs a step becomes `_run_item`.
- `tests/test_ratchets.py`: the rows of `_per_item` and `_per_item.work` go, and `FUNCTION_ROWS` follows.
- `tests/mutants.json`: `PB-2b` is re-pointed to the approve builder's line.
- `tests/test_pipeline_cli.py`: a case reaches the table's miss; further cases kill each survivor of the mutation run over `_per_item`.

No requirement changes: every printed line, progress line and exit code stays byte-equal. The change carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

The files that change are `isekai/interface/cli.py`, `tests/test_pipeline_cli.py`, `tests/test_ratchets.py` and `tests/mutants.json`. No import is added, so no derived *Imported by* row moves, and no existing test's assertion changes.

## Not in this change

- The move of the runner, its builders, `_seam`, `_assign`, `_assign_one` and `_existing_run` to `isekai/interface/verbs/runner.py`, and the amendment of D58's *Accepts*: `the-runner-move`.
- `assign` and `show` in the table: they are no stages, and a row's run is called before the flows are read, which would reorder `assign`'s refusal.
- The command builder and a refusal's fix as a field: `the-command-builder`.
- Any new verb, flag, help text or decision.
