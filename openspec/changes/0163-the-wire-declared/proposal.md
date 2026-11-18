---
bump: patch
---

# The wire declared

The JSON answers of the hub, staging, images, vocabulary and reviewing tables are declared once in Python and held against the record by a test; no answer, handler or route moves.

Reading map: [design](design.md) holds the declarations, the walker and the documents, [tasks](tasks.md) its phases.

## Why

The page's `types.ts` is written by hand against what the server sends, and some of its types already disagree with the server. Nothing states an answer's keys once, so a test cannot hold the server and the page to one fact.

The record, `tests/record/routes.json`, holds each recorded answer's keys and type names. This change gives it a declared twin in Python and a test that holds the two equal; a later version derives the page's types from the declarations.

## What Changes

- `isekai/interface/ui/shapes.py` (new): a `TypedDict` for each answer of the hub, staging, images, vocabulary and reviewing tables, and `ANSWERS`, keyed as the record is.
- `tests/test_ui_shapes.py` (new): a walker that holds a recorded shape against a declaration, cases that show it refuses, and cases over the tables.
- `isekai/interface/README.md`: a Files row for `ui/shapes.py`.
- The *Imported by* tables of the READMEs, derived: `ui/shapes.py` imports `pipeline/review.py`.
- `docs/decisions.md`: D63, which says where the wire is declared and why a handler keeps its annotation.

No requirement changes: the change carries `skip_specs` and its new tests a `structural:` exemption.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- New: `isekai/interface/ui/shapes.py`, `tests/test_ui_shapes.py`.
- Edited: `isekai/interface/README.md`, `isekai/pipeline/README.md`, `docs/decisions.md`.
- No format version moves, no answer's bytes move, no dependency is added.

## Not in this change

- A handler's annotation, `response_model` and a route's row: the declarations live in `shapes.py` and are held by tests ([D2](design.md#d2)).
- A record entry: nothing under `tests/record/` changes.
- Any file under `ui/src`: the page's types are derived in a later version.
- The tattoos', the place and the rendering tables, a refusal's shape, the answers the record lacks and the stream's events: the next version declares them.
- A test of what the record samples empty: those parts are declared from the builders' code and named in the design ([D6](design.md#d6)).
