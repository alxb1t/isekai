---
bump: patch
after: [0146-the-billing-watch]
---

# The surface

`create_app` hands what its routes share to a `Surface`, and the vocabulary, tattoo library and place routes to routers, with behaviour unchanged.

Reading map: [design](design.md) holds the shape, where each name goes and the test cost, [tasks](tasks.md) holds the phases: the surface, vocabulary and the tattoo library, place, the documents.

## Why

`create_app` in `isekai/interface/ui/app.py` is one closure holding every route, helper, middleware and the lifespan, and its nested functions read its names throughout. The file and the function are listed rows of the ratchets ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), and each feature that adds a route grows both.

This version proves the shape on the routes no test patches and no lock guards: what the routes share becomes a `Surface`, and a resource becomes a class registered from a table. The later versions of the server move the rest the same way.

## What Changes

- `isekai/interface/ui/surface.py` is new. It imports no web framework and holds `Surface`: the folders, the wiring, the flows, the jobs, billing, imports, the broadcast, the shared vocabulary and the upload limit, and the shared closures of `create_app` as methods. `Held`, `_Shared`, `_version`, `_flow` and their constants move into it.
- `isekai/interface/ui/routes/` is new: a class for the vocabulary routes, the tattoo library routes and the place routes, each registered from a table of method, path and handler. The `*_KEYS` tuples move to `routes/keys.py`; `_dimensions` and `_needs` to `routes/common.py`.
- `create_app` builds a `Surface`, binds its methods under today's names and includes the routers before the catch-alls. No other route's line changes.
- `docs/decisions.md` gains a decision for the shape. `app.py`'s docstring, the interface's README, `docs/modules.md` and `ARCHITECTURE.md` are amended.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes: the change declares `skip_specs: true` in `.openspec.yaml` and holds `specs/.gitkeep`.

## Impact

- Code: `isekai/interface/ui/app.py` loses the moved lines; `surface.py` and `routes/` hold them.
- Tests: none changes an assertion, and nothing under `tests/record/` changes. The mutation replay of `tests/mutants.json` proves the app's entries still hold.
- Documents: `docs/decisions.md`, `isekai/interface/README.md`, `docs/modules.md`, `ARCHITECTURE.md`, and the *Imported by* tables, re-derived in every phase.
- A patch by [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves, no behaviour fix, nothing deprecated, nothing changes the product.

## Not in this change

- The routes that read a name a test patches, and the render, jobs and events routes: later versions of the server.
- The draft lock, `read_compare`'s keyword-only parameters and the middleware factory.
- Every ratchet row: none is added, removed or lowered.
- `tests/test_ui_wire.py` and the page's types: the `*_KEYS` tuples stay bound in `app.py` until the wire's version repoints the test.
- What a check that raises shows on the page.
