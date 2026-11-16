---
bump: patch
version: 0.87.10
---

# The review routes

The review's routes move out of `create_app` into one resource class in `routes/`, with behaviour unchanged.

Reading map: [design](design.md) holds the class, where each helper lands, the pre-flight and the tests' cost, [tasks](tasks.md) the reads, the writes and the documents.

## Why

`create_app` still declares the review's routes beside the library's, staging's, images' and sources', and `app.py` is a listed row of the ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)). The seams made the move possible: each of these routes reads the lock, the writers, the precondition and the file response from the surface, and none reads a name a test patches on the module.

## What Changes

- `isekai/interface/ui/routes/reviewing.py` is new. `ReviewRoutes` holds `read_input`, `read_photo`, `read_source_copy`, `put_draft`, `post_approve`, `post_cancel`, `post_discard` and `post_draft`, registered from a table. The helpers only the review reads move in with it.
- `routes/common.py` gains the helpers the review shares with the images', staging's and sources' routes, and `REFUSED`; `app.py` imports them back.
- D59's *Accepts* line, the `app.py` docstring, the interface README, `docs/modules.md` and `docs/principles.md` say where the review's routes live.
- `tests/mutants.json` takes `PB-2c`'s new path and re-anchors `UA-7` on the import block the move rewrites.
- `app.py` falls under the ceiling of long files, so `tests/test_ratchets.py` loses its row and lowers the table's count ([D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement is touched, and no scenario is added: `skip_specs` holds.

## Impact

- Code: `isekai/interface/ui/app.py` loses the moved lines; `isekai/interface/ui/routes/reviewing.py` and `isekai/interface/ui/routes/common.py` hold them.
- Documents: `docs/decisions.md`, `docs/modules.md`, `docs/principles.md` and `isekai/interface/README.md`, and each layer README's *Imported by* table, re-derived.
- Tests: `tests/mutants.json` and `tests/test_ratchets.py`, data only; no assertion changes and no record entry changes.

## Not in this change

- The images', library's, staging's and sources' routes, `read_compare`'s positional parameters, the middleware as a factory, `create_app`'s size and its rows and `read_compare`'s: when the front door's routes move.
- A record entry for a route the record lacks: when a test needs one, never a move.
- The wire's response declarations, and repointing the tests' imports from `app.py`: when the wire's declarations are planned.
- The page's review screen and its composables; any request, response or status code.
