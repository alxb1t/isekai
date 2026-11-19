---
bump: patch
---

# The wire, rendering

The tattoos', place and rendering answers of the UI server are declared in `shapes.py` and held by tests; no handler, route, record entry or page file changes, so no answer's bytes can.

Reading map: [design](design.md) holds the decisions, each declaration and the tests, [tasks](tasks.md) holds the phases: the tattoos and place, the rendering, the rows and the documents.

## Why

[D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests) declares each JSON answer of the UI server in `isekai/interface/ui/shapes.py` and holds it against `tests/record/routes.json`. The hub, staging, images, vocabulary and reviewing tables are declared. The tattoos, place and rendering tables are not, and the page's types cannot be derived from `shapes.py` until they are.

The record holds a success for most of those routes. It holds none for prepare, render, the running sessions and a session, and holds stop and propose as a refusal alone. Those answers need a second table and a test that asks the server.

## What Changes

- `isekai/interface/ui/shapes.py`: a `TypedDict` for each answer of the tattoos', place and rendering tables, and a row for each in `ANSWERS`, where the record holds a success.
- `isekai/interface/ui/shapes.py`: `UNRECORDED`, a second table keyed as `ANSWERS` is, for prepare, render, stop, the running sessions, a session and propose.
- `tests/test_ui_propose.py`, `tests/test_ui_jobs.py` and `tests/test_ui_api.py`: a case for each row of `UNRECORDED`, which asks a `TestClient` and holds the shape of its answer to the declaration.
- `tests/test_ui_shapes.py`: a case that holds the served session to `SessionRecord`, and a case that every JSON route of the tattoos', place and rendering tables has a row in exactly one table.
- `isekai/interface/README.md`: the `shapes.py` row; the *Imported by* tables, derived; `docs/decisions.md`: D64, and D63's *Accepts* line amended to what remains.

## Capabilities

### New Capabilities

None. No requirement fits: the change carries `skip_specs`, and its tests carry a `structural:` exemption.

### Modified Capabilities

None.

## Impact

- Changed: `isekai/interface/ui/shapes.py`, `tests/test_ui_shapes.py`, `tests/test_ui_propose.py`, `tests/test_ui_jobs.py`, `tests/test_ui_api.py`, `isekai/interface/README.md`, `isekai/pipeline/README.md`, `isekai/foundation/README.md`, `isekai/shared/README.md`, `docs/decisions.md`.
- No format version moves and no new Python module is added; what stays untouched is listed below.
- `shapes.py` stays at or under the ratchet's `FILE_LINES`.

## Not in this change

- A handler's annotation, `response_model`, a route's row, a record entry, any file under `ui/src`: the declarations stay apart from the handlers ([D2](design.md#d2)).
- `app.py` and `jobs.py` stay as they are: the cases reach the jobs through `make_jobs`, a parameter of `create_app` that exists.
- The refusals, the stream's events, the catch-all's row, the case over every route of `create_app` and the tests' imports from `app.py`: the next version's.
- A `Literal` for a value set no name declares: it is `str` until the page's types are derived ([D5](design.md#d5)).
- A test of what the record samples empty ([D6](design.md#d6)).
