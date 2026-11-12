---
bump: patch
after: [0129-the-refactors-rails]
---

# The record

The whole outputs of the pipeline are pinned in `tests/record/`: every flow's graph and the edit's, the run's every path, the verbs' flags, the routes' answers and the child's done line, written by a program a test re-derives.

Reading map: [design](design.md) holds the decisions, how each output is pinned and the cost of the tests, [tasks](tasks.md) the graphs, the run, the verbs, the routes and the wire.

## Why

The refactor that follows moves code between files and must not move an output; the suite pins one flow's graph by a digest and each run file kind by a hand-kept golden. It pins no other flow's graph, no verb's flags, no route's answer and no line the child writes to the job that reads it. A move that changes any of them passes the gate.

```
today                                       after

one flow's graph: a digest                  every flow's graph and the edit's: whole
goldens: kept by hand, one kind each        the run's every path: one program writes them
verbs, routes, the child's lines: unpinned  flags walked, answers shaped, the done line read by each reader
```

## What Changes

Edits to tests alone. No `.py` under `isekai/` or `evaluation/` moves, and no document is edited.

- `tests/record.py` runs one offline pass over every flow, on the suite's doubles through `ISEKAI_WIRING`, and writes `tests/record/*.json`; `python -m tests.record` is its command.
- `tests/test_record.py` re-derives each file into a temporary directory and compares it with the committed one, and holds the writer's own functions with twins.
- `tests/record/graphs.json` holds every flow's graph and the edit's, whole.
- `tests/record/run.json` holds every path the pass writes: a JSON file with its duration normalised, a PNG by its pixels, any other file by its bytes.
- `tests/record/verbs.json` holds each verb's flags, walked from the parser, its runs root repo-relative.
- `tests/record/routes.json` holds each route reachable without a running child: its status and the shape of its answer.
- `tests/record/wire.json` holds the lines the CLI prints for the child's wire, and `tests/test_progress.py` and `tests/test_ui_jobs.py` feed them to the session's, the cell's and the job's readers.
- `tests/test_resume.py` holds that a second pass over the same runs moves nothing.

No requirement is touched, so the delta is empty and `.openspec.yaml` carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Added: `tests/record.py`, `tests/test_record.py` and the files of `tests/record/`.
- Edited, each with one test added: `tests/test_resume.py`, `tests/test_progress.py` and `tests/test_ui_jobs.py`.
- Read and not edited: `tests/e2e/wiring.py`, whose factory the pass builds on; `tests/test_edit_session.py` and `tests/test_ui_api.py`, whose edit request and app client the pass restates; `flows/`, whose graphs the pass renders; `isekai/interface/cli.py`, `isekai/interface/render.py`, `isekai/interface/ui/app.py` and `isekai/interface/ui/jobs.py`, whose outputs and readers the record pins.
- No format version moves, no verb or flag is deprecated, and the product is the same for the same inputs, so the change meets each condition of a patch in [CONTRIBUTING.md](../../../CONTRIBUTING.md).
- No dependency is added.

## Not in this change

- The routes that need a running child — Prepare, render, the session routes and the event stream: the version that hardens the jobs.
- The silent patches and the guard that every patch names a name its module reads, and the mutation runner: the next version of this series.
- The mis-bound scenarios — the *spec audit* — and the tattoo screens' browser tests — *e2e tattoo*.
- A change to a product file to make an output stable: a value that varies is normalised in the record, never in the product.
