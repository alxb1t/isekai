# The wire, complete — design

Declare the refusals and the stream's events beside the answers, hold every route by a case, and point the tests at the names' homes; no handler, route or record entry changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

[D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests) declares each JSON answer as a `TypedDict` in `isekai/interface/ui/shapes.py`. [D64](../../../docs/decisions.md#d64--the-answers-the-record-lacks-are-a-second-table-held-by-cases-that-ask-the-server) adds `UNRECORDED` for the answers the record lacks. Both left things out, which D63's *Accepts* line names: the refusals, the stream's events and the tests' imports from `app.py`.

```
                  ANSWERS     the record holds a success       held against the record
shapes.py ──────  UNRECORDED   the record lacks one             held by a case that asks the server
                  EVENTS      the stream's five kinds          held by a case that reads what is published   (new)
                  Refused     any route's refusal              held by cases, no row                          (new)
```

What the code does today, at the base:

- Each refusal is built as `{refusal}`: the guard's 403s in `app.py`, the catch-all's 404, the 409 a `Refusal` becomes, and the draft's 409, which adds `images`.
- The record holds the entries of status 400 and above for the catch-all's 404 and for stop's and propose's 409.
- The stream writes the events `snapshot`, `job`, `billing`, `cell` and `file`, and the page listens to exactly those. The snapshot is built in `StreamRoutes.read_events`, a job's by `Jobs._publish`, the billing's by `Billing.publish`, a cell's by `cell_event`, and a file's by `Imports`, to which `create_app` adds `staging`.
- `app.py` re-binds the key tuples, `RARE_BELOW` and `cell_event` in the `X as X` form and uses none of them. `Held` is a plain import that types `_precondition`.

## Goals / Non-Goals

Goals:

- Every JSON answer, refusal and event is declared in `shapes.py` and held by a test.
- A route of `create_app` with no declaration fails a case.
- A test reads a name from the module that owns it.

Non-Goals:

- Any change to a handler, a route row, a `response_model` or a record entry ([D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests)).
- Any file under `ui/src`.
- A declared set of values for a state no name declares.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A refusal is `Refused` or `DraftRefused`, and the catch-all's 404 is the row of `ANSWERS` that holds `Refused` | the record holds the 404, so the shipped case holds its row; any route answers a 403 or a 409, so no route owns one | a row per route for a 409; a table of refusals |
| [D2](#d2) | The 403s, the 409 and the draft's 409 are held by `TestClient` cases, and every recorded entry of status 400 and above is held to `Refused` by one case | a new record entry is out of scope and a changed assertion is out by the series' rules | a record entry for each refusal |
| [D3](#d3) | The stream's events are a third table, `EVENTS`, keyed by the event's name | an event is named by its kind, not by a route, so `ANSWERS`' key does not fit | rows in `UNRECORDED` keyed by `GET /events` |
| [D4](#d4) | Each `EVENTS` row is held by a case that reads what the server publishes, in the test file whose fixtures it needs | the fixtures are module-local and a shared one would be a new module | a new fixtures module |
| [D5](#d5) | A file's state, a job's state and the billing volume's state are `str` | the walker checks type names, so an inline `Literal` is a claim no test holds | a `Literal` for each |
| [D6](#d6) | A case holds that every route of `create_app` has a row, a recorded media type, or is the stream, with a twin | a route added later must be declared or named | reading the tattoo, place and render tables alone, as the shipped case does |
| [D7](#d7) | The tests read the key tuples, `RARE_BELOW` and `cell_event` from their homes, and their re-bindings leave `app.py`; `Held` stays imported there | `Held` types `_precondition`; the rest are read by no code of `app.py` | keeping the re-bindings |
| [D8](#d8) | A decision, D65, records the events' table and the refusals' rule, and D63's *Accepts* line shrinks to what remains | a decision in force is edited where it lives, in `docs/decisions.md` | a note in `design.md` alone |

### D1

`Refused` is `{refusal: str}`. `DraftRefused` extends it with `images: list[RefusedImage]`, and `RefusedImage` holds `digest`, `flow`, `version`, `seed` and `refusal: str | None`, as `_image_out` and `post_draft` build them.

The draft's 409 has no row: its route key holds the draft's success. The catch-all's 404 is the row `"GET /api/{rest:path}": Refused`, which the shipped case `test_every_answer_fits_the_record` holds.

### D2

`TestClient` cases in `tests/test_ui_api.py` ask the server for each refusal and walk `shape` of the answer through `faults`:

| case | answer | declared |
|---|---|---|
| `test_the_host_refusal_fits_refused` | the guard's 403, `not addressed here` | `Refused` |
| `test_the_origin_refusal_fits_refused` | the guard's 403, `not from this page` | `Refused` |
| `test_a_refusal_answered_as_a_conflict_fits_refused` | the 409 a `Refusal` becomes | `Refused` |
| `test_the_drafts_refusal_fits_draft_refused` | the draft's 409 | `DraftRefused` |

`tests/test_ui_shapes.py` holds `test_every_recorded_refusal_fits_refused`: every entry of `tests/record/routes.json` with a status of 400 and above has a shape that `Refused` fits. Its twin is `test_a_recorded_refusal_that_drifts_is_caught`. FastAPI's own 422 and 405 are not declared.

### D3

`EVENTS` has a row for each event the stream writes, reusing a declaration `shapes.py` already holds where one fits:

| event | declared | built by |
|---|---|---|
| `snapshot` | `Snapshot`: `jobs: dict[str, Job \| None]`, `billing: Billing`, `hub: NotRequired[HubInfo]`, `files: NotRequired[dict[str, FileState]]` | `StreamRoutes.read_events` |
| `job` | `Job` | `Jobs._publish`, from `describe()` |
| `billing` | `Billing` | `Billing.publish` |
| `cell` | `CellEvent`: `collection`, `source`, `flow`, `stage`, `state`, `message`, `cell: HubCell` | `cell_event` |
| `file` | `FileEvent`, a `FileState` with `staging` and `upload` | `Imports._set`, with `staging` added by `create_app` |

`FileState` holds `file: str` and `state: str`, with `name: str`, `carries: list[str]`, `copy_of: str | None` and `refusal: str` as `NotRequired`. The reader sends `copy_of` as `None` for a file that is no copy, so the walker needs the union. A cell's `stage`, `state` and `message` are `str | None`, as `cell_event` reads them with `line.get`.

### D4

Each row is held by a case that reads what the server publishes:

| row | case | file | read from |
|---|---|---|---|
| `snapshot` | `test_the_snapshot_fits_its_declaration` | `tests/test_ui_api.py` | the first frame of `/events?collection=…&staging=…`, read by a helper that closes the stream from a thread |
| `file` | `test_the_file_event_fits_its_declaration` | `tests/test_ui_api.py` | a subscription to the app's broadcast while an upload and a refused upload drive `Imports` |
| `job` | `test_the_job_event_fits_its_declaration` | `tests/test_ui_jobs.py` | a subscription while `POST …/prepare` runs through `_Idle`, which starts no thread |
| `billing` | `test_the_billing_event_fits_its_declaration` | `tests/test_ui_jobs.py` | a subscription while `POST /api/billing/check` runs through a wiring whose volume is a `Volume` double that answers and a window record on disk |
| `cell` | `test_the_cell_event_fits_its_declaration` | `tests/test_ui_jobs.py` | a direct call of `cell_event` |

- The billing check asks gpunit before it publishes, and every wiring of `tests/stages.py` raises there.
- The double is a `Volume` passed in the wiring, as `tests/test_ui_billing.py` passes one, and no patch.
- The window record gives `volume` a sample, so `BillingVolume` is walked.
- The snapshot case puts the run's photograph in `sources/` with `_source`, so a `HubSource` is walked, and reads an import whose file is already read, so `FileState` is walked.

### D5

A file's state, a job's state and the billing volume's state are `str`, as the plan settled. What each becomes on the page is decided when the deriver is planned.

### D6

`tests/test_ui_shapes.py` gains `test_every_route_of_the_app_has_a_row_or_a_name`.

- It builds the app as `tests/test_ui_wire.py` does and lists its routes with `tests.record.routed`.
- It asks `rowless(routes, entries)` for the routes that are in neither table, hold no recorded media type and are not `GET /events`.
- Its twin, `test_a_route_with_no_row_is_caught`, gives `rowless` a route no table holds.
- The shipped case over the tattoo, place and render tables stays as it is.

### D7

The tests change where they read from, and no assertion:

| test file | reads | from |
|---|---|---|
| `tests/test_ui_api.py` | `RARE_BELOW` | `isekai.interface.ui.routes.vocabulary` |
| `tests/test_ui_api.py` | `Held` | `isekai.interface.ui.surface` |
| `tests/test_ui_jobs.py` | `cell_event` | `isekai.interface.ui.routes.rendering` |
| `tests/test_ui_wire.py` | the `*_KEYS` tuples, by `vars` | `isekai.interface.ui.routes.keys` |

`authorities` and `create_app` stay read from `app.py`, which owns them.

### D8

`docs/decisions.md` gains D65, *The refusals are classes, and the stream's events have a table of their own*, with the rule of [D1](#d1) and [D3](#d3). D63's *Accepts* line drops the refusals, the events and the imports, and its *Made by* gains this change.

## Tests

The change adds tests at the lowest layer that can fail (`T1`). It deletes and merges none, so there is no table of removed tests. No end-to-end run is added: no case boots a browser, and none can fail for a browser's behaviour.

Each count is of the tests added, read by the command beside it after the build:

- Unit, `tests/test_ui_shapes.py`, 4 added: `git grep -c -E "^def test_(every_recorded_refusal|a_recorded_refusal|every_route_of_the_app|a_route_with_no_row)" -- tests/test_ui_shapes.py`.
- Integration through `TestClient`, `tests/test_ui_api.py`, 6 added: `git grep -c -E "^def test_(the_host_refusal|the_origin_refusal|a_refusal_answered|the_drafts_refusal|the_file_event|the_snapshot_fits)" -- tests/test_ui_api.py`.
- Integration through `TestClient`, `tests/test_ui_jobs.py`, 3 added: `git grep -c -E "^def test_the_(job|billing|cell)_event_fits" -- tests/test_ui_jobs.py`.

`tests/test_ui_wire.py` gains no test: it reads the key tuples from their home ([D7](#d7)).

Each case carries `spec_exempt("structural: …")`, and each twin `structural: twin of <its case>` (`T6`). A twin is a unit test of a pure function, so none boots a browser.

The ceiling `shapes.py` stays under is measured by `wc -l isekai/interface/ui/shapes.py`, which prints 622 at the base against the 800 the ratchet allows.

## Dependencies

None.

## Risks / Trade-offs

| risk | answer |
|---|---|
| a `NotRequired` key no sample carries is held by no case | the file case drives a refused upload, the snapshot case an import with a read file, and the billing case a window record; what remains is named in [D5](#d5) |
| the walker reads a list by its first element, so a second arm of a union is never walked | the draft case sends the untracked image first, so `RefusedImage.refusal` is sampled as `str` |
| `EVENTS`' keys can drift from the page's kinds | out of scope, and the deriver holds them when it lands |
| a double that answers makes `Billing.check` write the gpunit log under the app's root | the case's root is a temporary folder |
| the snapshot and the file cases read the stream from a thread | the helper closes the stream as the existing first-frame readers do, and a deadline ends a wait |

## Verdict

Ready to build. The change adds a declaration for each answer the wire lacked and a case for each, moves no behaviour, and ends with the tests reading names from their homes.
