---
bump: patch
after: [0196-the-child-lines-declared]
---

# The session plan

The plan of a render session — its timing, its estimate, what each approval lacks and the edit queue's reading — moves from `isekai/interface/render.py` to `isekai/interface/plan.py`. Every name is bound back in `render.py`; `quote` and `Record` stay.

Reading map: [design](design.md) holds the decisions and the names that move, [tasks](tasks.md) its phases: the estimate and the edit queue, the plan and the quote's parts, then the documents.

## Why

`render.py` holds the session's runner and, beside it, everything the runner and the app's quote read to decide what a session would do: the timing, the estimate, what each approval lacks, and the pending edits. That is a large part of a file the ratchet lists as long. The plan reads no process, no pod and no log, so it has a home of its own, and the session's later versions edit the runner without the plan beside it.

## What Changes

- `isekai/interface/plan.py` is new. It holds `Timing` and `load_timing`, `Estimate`, `recent`, `recent_edits`, `estimate` and `estimated`, `Edits`, `edits_of`, `edit_records` and `pending_edits`, `Line`, `Short`, `short` and `Quote`, with the constants and helpers they read. It imports nothing of `render.py`.
- Each moved name is bound back in `render.py`, so no test, route or verb import changes.
- `quote` and `Record` stay in `render.py` and read the names the tests patch there.
- One standing mutant in `tests/mutants.json` is found in `plan.py`.
- The interface READMEs, `isekai/README.md`, `docs/principles.md` and the boundary README name the new home.

No requirement is touched and no decision is added. The code moves as it is; every printed byte and every quoted figure stays.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

`isekai/interface/render.py` loses the code above and `isekai/interface/plan.py` is new. `tests/mutants.json` re-points one entry; no other file under `tests/` changes. `isekai/interface/README.md`, `isekai/README.md`, `docs/principles.md`, `isekai/boundary/README.md` and the derived tables of the layer READMEs name the module.

## Not in this change

- `quote` and `Record`: tests patch the names they read, `load_timing` and `session_id`, on `render`.
- The gpunit facts down to `isekai/boundary/gpu.py`, and `Record` out of `render.py`.
- A line of the moved code: no edit, no rename, no new parameter.
- `render.py`'s row among the long files: it stays until the requests leave it.
- `ui/src/wire.ts`, and any file under `ui/`, `tools/` or `evaluation/`.
- A scenario, a spec delta, a decision, and a `tools.mutate` run over the moved lines: the standing mutants are the proof.
