# The wire, complete — tasks

The phases declare the refusals, declare the stream's events, hold every route, then point the tests at the names' homes and amend the documents. Each new case is a test of `tests/` that carries `spec_exempt("structural: …")` and asks the server, as the declarations of [design](design.md) say.

## Progress

- [x] 1 — The refusals · moderate
- [x] 2 — The stream's events · moderate
- [x] 3 — Every route · moderate
- [x] 4 — The imports and the documents · moderate

## 1 — The refusals

- [x] 1.1 In `isekai/interface/ui/shapes.py` add `RefusedImage`, `Refused` and `DraftRefused` per [D1](design.md#d1),
  each with a one-line docstring. Place them after `RunningSessions`.
  Verify: `git grep -n -E "^class (RefusedImage|Refused|DraftRefused)" -- isekai/interface/ui/shapes.py` prints three lines.
- [x] 1.2 In `ANSWERS` of `shapes.py` add the row `"GET /api/{rest:path}": Refused`, after the row of `GET /api/library`.
  Verify: `git grep -n -F '"GET /api/{rest:path}": Refused' -- isekai/interface/ui/shapes.py` prints one line, and `uv run pytest tests/test_ui_shapes.py -k test_every_answer_fits_the_record` exits 0.
- [x] 1.3 In `tests/test_ui_shapes.py` add `refusal_faults(entries)`, a line per recorded entry of status 400 and above that `Refused` does not fit, its case and its twin ([D2](design.md#d2));
  the twin feeds a shape with an undeclared key `extra`.
  Verify: `uv run pytest tests/test_ui_shapes.py -k recorded_refusal` exits 0.
- [x] 1.4 In `tests/test_ui_api.py` import `Refused` and `DraftRefused` beside `UNRECORDED`, and add `test_the_host_refusal_fits_refused` and `test_the_origin_refusal_fits_refused`.
  Each sends `GET /api/library`, the first with a foreign `host`, the second with a foreign `origin`, asserts the 403 and walks `faults(Refused, shape(answered.json()), "")` to `[]`.
  Verify: `uv run pytest tests/test_ui_api.py -k "host_refusal or origin_refusal"` exits 0.
- [x] 1.5 In `tests/test_ui_api.py` add `test_a_refusal_answered_as_a_conflict_fits_refused`, which posts `DRAFT_ROUTE` with no images, and `test_the_drafts_refusal_fits_draft_refused`,
  set up as `test_a_revision_of_an_untracked_flow_is_refused_and_nothing_is_written` is, the `nope` image first; each asserts the 409, the first walks `Refused`, the second `DraftRefused`.
  Verify: `uv run pytest tests/test_ui_api.py -k "answered_as_a_conflict or drafts_refusal"` exits 0.

## 2 — The stream's events

- [x] 2.1 In `shapes.py` add `FileState`, `FileEvent`, `Snapshot` and `CellEvent` per [D3](design.md#d3), each with a one-line docstring,
  the fields and types of the table and of `FileState`'s paragraph in [D3](design.md#d3). Place them after `Refused`'s classes.
  Verify: `git grep -n -E "^class (FileState|FileEvent|Snapshot|CellEvent)" -- isekai/interface/ui/shapes.py` prints four lines.
- [x] 2.2 In `shapes.py` add `EVENTS: dict[str, Any]` after `UNRECORDED`, with the rows `snapshot`, `job`, `billing`, `cell` and `file`,
  and add the table to the docstring of `shapes.py` as the line that says `UNRECORDED` keys the answers the record lacks does.
  Verify: `git grep -n -E "^(ANSWERS|UNRECORDED|EVENTS): dict" -- isekai/interface/ui/shapes.py` prints three lines.
- [x] 2.3 In `tests/test_ui_jobs.py` add `test_the_job_event_fits_its_declaration` ([D4](design.md#d4)): build the app with `_held_client(..., make_jobs=_Idle)`,
  subscribe to `app.state.broadcast`, post the prepare, take the `job` event with `_until` and walk `shape` of its data against `EVENTS["job"]`. Import `EVENTS` beside `UNRECORDED`.
  Verify: `uv run pytest tests/test_ui_jobs.py -k the_job_event_fits` exits 0.
- [x] 2.4 In `tests/test_ui_jobs.py` add `test_the_billing_event_fits_its_declaration`: a local `Volume` double over a `.gpunit` folder holding a window record, the app built by `create_app` and
  `bare_wiring(volume=…)` as `tests/test_ui_billing.py` does; subscribe, post `/api/billing/check`, walk the `billing` event against `EVENTS["billing"]`.
  Verify: `uv run pytest tests/test_ui_jobs.py -k the_billing_event_fits` exits 0.
- [x] 2.5 In `tests/test_ui_jobs.py` add `test_the_cell_event_fits_its_declaration`: call `cell_event(folder, grid, {FLOW: load_flow(FLOW)})` as
  `test_a_stage_reporting_an_item_done_sends_that_cells_new_stage` does, on a `done` line naming a run and `FLOW`, and walk the event against `EVENTS["cell"]`.
  Verify: `uv run pytest tests/test_ui_jobs.py -k the_cell_event_fits` exits 0.
- [x] 2.6 In `tests/test_ui_api.py` add `test_the_file_event_fits_its_declaration`: subscribe with `_broadcast`, open a staging, `_upload` a photograph and a file the reader refuses,
  collect each with `_until_each_read`, and walk every `file` event against `EVENTS["file"]`. Import `EVENTS` beside `UNRECORDED`.
  Verify: `uv run pytest tests/test_ui_api.py -k the_file_event_fits` exits 0.
- [x] 2.7 In `tests/test_ui_api.py` add `_first_frame(client, url)`, which reads the stream's first frame and closes the stream from a thread once it is open,
  and `test_the_snapshot_fits_its_declaration`: `_source(made)`, an upload read through `_until_read`, then `/events?collection=…&staging=…` walked against `EVENTS["snapshot"]`.
  Verify: `uv run pytest tests/test_ui_api.py -k the_snapshot_fits` exits 0.

## 3 — Every route

- [x] 3.1 **HALT CHECK** The record holds a `media_type` for each route that answers a file, which `rowless` of 3.2 reads in place of a row.
  Verify: `git grep -c -F '"media_type"' -- tests/record/routes.json` prints `14`.
- [x] 3.2 In `tests/test_ui_shapes.py` add `rowless(routes, entries)`, which returns the routes that are in neither `ANSWERS` nor `UNRECORDED`,
  hold no `media_type` in `entries`, and are not `GET /events`, and the twin `test_a_route_with_no_row_is_caught`, which gives it a route no table holds.
  Verify: `uv run pytest tests/test_ui_shapes.py -k a_route_with_no_row` exits 0.
- [x] 3.3 In `tests/test_ui_shapes.py` add `test_every_route_of_the_app_has_a_row_or_a_name` ([D6](design.md#d6)): build the app as `_routes` of `tests/test_ui_wire.py` does
  with `bare_wiring` and `Seams(environ={})`, list its routes with `tests.record.routed`, and assert `rowless(routed(app), _routes())` is `[]`.
  Verify: `uv run pytest tests/test_ui_shapes.py -k every_route_of_the_app` exits 0.

## 4 — The imports and the documents

- [x] 4.1 In `tests/test_ui_api.py` read `RARE_BELOW` from `isekai.interface.ui.routes.vocabulary` and `Held` from `isekai.interface.ui.surface` ([D7](design.md#d7));
  the import of `app` keeps `authorities` and `create_app`.
  Verify: `git grep -n -E "^    (RARE_BELOW|Held),$" -- tests/test_ui_api.py` prints nothing.
- [x] 4.2 In `tests/test_ui_jobs.py`, before: `from isekai.interface.ui.app import cell_event, create_app`; after: `create_app` from `app` and `cell_event` from
  `isekai.interface.ui.routes.rendering`.
  Verify: `git grep -n -F "from isekai.interface.ui.app import cell_event" -- tests/test_ui_jobs.py` prints nothing.
- [x] 4.3 In `tests/test_ui_wire.py` import `isekai.interface.ui.routes.keys` as `keys_module`, a name `wire_faults`' `keys` local does not shadow, and read the tuples with
  `vars(keys_module)`, where `vars(app_module)` read them; drop the `app_module` import.
  Verify: `git grep -n "app_module" -- tests/test_ui_wire.py` prints nothing, and `uv run pytest tests/test_ui_wire.py` exits 0.
- [x] 4.4 In `isekai/interface/ui/app.py` delete each `X_KEYS as X_KEYS` import, the `cell_event as cell_event` import and the `RARE_BELOW as RARE_BELOW` import;
  `Held` stays imported.
  Verify: `git grep -n -E "_KEYS as [A-Z0-9_]+_KEYS" -- isekai/interface/ui/app.py` prints nothing, and `git grep -n -E "import (cell_event|RARE_BELOW) as" -- isekai/interface/ui/app.py` prints nothing.
- [x] 4.5 In `app.py`'s docstring, before: "import FastAPI and are reached through this module alone", after: "import FastAPI and this module mounts them"; delete "the `rare` threshold -- which
  exists nowhere else in this repository --". In the `ui/routes/` row of `isekai/interface/README.md`, before: "are reached through `ui/app.py` alone", after: "are mounted by `ui/app.py`".
  Verify: `git grep -n -e "are reached through" -e "exists nowhere else" -- isekai/interface/ui/app.py isekai/interface/README.md` prints nothing.
- [x] 4.6 In `isekai/interface/README.md` name the refusals and `EVENTS` in the `ui/shapes.py` row, and add the `file` event and the snapshot to the `ui/events.py` row.
  Verify: `git grep -n -F "EVENTS" -- isekai/interface/README.md` prints a line.
- [x] 4.7 In `docs/decisions.md` add D65, *The refusals are classes, and the stream's events have a table of their own* ([D8](design.md#d8)), after D64 in D63's shape.
  In D63's *Accepts*, before: "the refusals, the stream's events and the tests' imports from `app.py` are declared by the next version, and"; after: nothing. Add `0166` to its *Made by*.
  Verify: `git grep -n -E "^### D65" -- docs/decisions.md` prints a line, and `git grep -n -F "the refusals, the stream's events and the tests' imports" -- docs/decisions.md` prints nothing.
- [x] 4.8 Run `uv run python -m tools.derive_imported_by` and keep what it writes: removing the imports of `app.py` may change a derived *Imported by* row.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
