---
bump: patch
version: 0.87.22
---

# The wire, complete

Declare what the UI server's wire still lacks, the refusals and the stream's events, hold every route by a case, and point the tests at the names' homes. Behaviour is unchanged.

Reading map: [design](design.md) holds the decisions, the tests' cost and the risks, [tasks](tasks.md) its phases: the refusals, the stream's events, every route, the imports and the documents.

## Why

`shapes.py` declares each JSON answer of the tattoo, place and render route tables, held against the record or by a case that asks the server. A refusal, an event of the stream and the catch-all's 404 have no declaration yet. No case holds that every route of `create_app` has a row somewhere, so a route added later can skip the wire.

Names are re-bound in `app.py` for the test files that read them and used by none of its own code: the key tuples, `RARE_BELOW` and `cell_event`. They keep a test reading a module's name through a module that does not own it.

The wire is the base the page's derived types build on. A half-declared wire derives half a file.

## What Changes

- `shapes.py` gains `Refused` and `DraftRefused`, with the catch-all's 404 as the row of `ANSWERS` that holds `Refused`. The 403s and the 409s, which any route answers, get no row.
- `TestClient` cases hold the guard's 403s, a 409 and the draft's 409 to their declarations. One case holds every recorded entry of status 400 and above to `Refused`, with a twin.
- `shapes.py` gains `EVENTS`, a table keyed by the event's name: `snapshot`, `job`, `billing`, `cell` and `file`. A case holds each row against what the server publishes.
- One case holds that every route of `create_app` has a row in `ANSWERS` or `UNRECORDED`, or is a media type the record holds, or is the stream. Its twin shows a route with no row is caught.
- The tests read the key tuples, `RARE_BELOW`, `cell_event` and `Held` from their homes. The re-bindings leave `app.py`; `Held` stays imported there, since it types `_precondition`.
- The lines of `app.py`'s docstring that say the routes are reached through it alone and that the `rare` threshold lives there are corrected, and so is the interface README's matching line. The README rows name the refusals, the events and the `file` event. A decision records the third table.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement fits a declaration the tests hold, so the change carries `skip_specs` and each new test a `structural:` exemption.

## Impact

- `isekai/interface/ui/shapes.py` grows. It stays under the 800-line ceiling.
- `isekai/interface/ui/app.py` loses its re-binding imports and corrects its docstring.
- `tests/test_ui_shapes.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py` and `tests/test_ui_wire.py` gain cases or repoint imports. No existing assertion changes.
- `isekai/interface/README.md` and `docs/decisions.md` change. A derived *Imported by* table changes if the deriver says so.
- No handler, route row, `response_model`, record entry or file of the page changes, so no answer's bytes can.

## Not in this change

- FastAPI's own 422 and 405 answers: isekai builds no `{detail}` answer and the page reads `refusal` alone.
- A handler's annotation, `response_model`, or a route's row.
- A record entry: the record cannot run a child and gains none.
- Any file under `ui/src`. The page's types are derived from the declarations when the deriver is planned.
- A `Literal` for a set no name declares: a file's state, a job's state and the billing volume's state stay `str`.
- A patch of a module's name.
- `app.py`'s own names a test reads through it: `authorities`, `_precondition`, `run` and `Server`.
- A test that holds `EVENTS`' keys equal to the page's list of kinds: the deriver holds them when it lands.
