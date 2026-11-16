---
bump: patch
version: 0.87.4
---

# The render routes

The render, jobs, sessions, billing-check and events routes move out of `create_app` into resource classes in `routes/`, with behaviour unchanged.

Reading map: [design](design.md) holds the classes, where each helper goes and how the move is proved, [tasks](tasks.md) holds the phases: the render and jobs routes, the events stream, the documents.

## Why

`create_app` in `isekai/interface/ui/app.py` still declares the routes that start, quote, stop and stream the render and prepare jobs. The file and the function are listed rows of the ratchets ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), and each feature that adds a route grows both. [D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface) says a resource is a class over one `Surface`; these are the next group that reads no name a test patches.

## What Changes

- `isekai/interface/ui/routes/rendering.py` is new. `RenderRoutes` holds the prepare route, a job's stop, the render's offer, quote and `POST`, the session reads and the billing check, and the helpers `quoted`, `_held`, `short_of` and `bakes_in`. `cell_event`, `_quote`, `_quoted_row` and `_taken_out` move into the module.
- `isekai/interface/ui/routes/stream.py` is new. `StreamRoutes` holds the events stream.
- `routes/common.py` gains `_strings`, `_whole`, `_hub` and `_cell_out`; `app.py` imports them back, and binds `cell_event` under its old name.
- `create_app` mounts both resources before the catch-alls. `Jobs(`, `Billing(`, `Imports(` and `run` stay in `app.py`.
- D59's *Accepts* line, the docstring of `app.py`, the interface README and `docs/modules.md` say which routes moved.

No requirement changes: every route keeps its path, method, body, status and refusal text.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change declares `skip_specs: true`.

## Impact

- Code: `isekai/interface/ui/app.py` loses the moved lines; `routes/rendering.py`, `routes/stream.py` and `routes/common.py` hold them.
- Documents: `docs/decisions.md`, `docs/modules.md`, `isekai/interface/README.md`, the *Imported by* tables the deriver writes.
- No test's assertion, nothing under `tests/record/`, no ratchet row of `tests/test_ratchets.py`, no entry of `tests/mutants.json`, no format version and no image-frozen file changes.

## Not in this change

- The routes that read a patched name of `app.py`: when the patched names become `create_app`'s parameters.
- `Jobs(` and `run`: they stay in `app.py`, where the tests patch them.
- The draft lock, `read_compare`, the middleware and every ratchet row.
- A record entry for the routes `tests/record/routes.json` lacks.
- The library, staging, review and images routes.
