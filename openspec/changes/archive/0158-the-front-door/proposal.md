---
bump: patch
version: v0.87.14
after: [0157-the-review-actions]
---

# The front door

The images', library's, staging's and sources' routes move out of `create_app` into resource classes in `routes/`, so `create_app` falls under the function ceiling; behaviour unchanged.

Reading map: [design](design.md) holds the classes, where each helper lands, the pre-flight and the tests' cost, [tasks](tasks.md) the images, the other resources, the front door and the documents.

## Why

`create_app` is the last listed offender of the server: a closure that still declares the library's, staging's, images' and sources' routes, and holds `read_compare`, which takes more positional parameters than the ceiling. Both are rows of the ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)). The seams and the review routes made the last move possible: each of these routes reads the surface, and none reads a name a test patches on `app.py`.

This is the last version of the server. The wire's declarations are planned when it ships.

## What Changes

- `isekai/interface/ui/routes/images.py` is new. `ImageRoutes` holds the nine render and bake routes, `read_compare` with keyword-only path parameters, and `_side`, `_filled` and `_images_out`.
- `routes/hub.py`, `routes/staging.py` and `routes/sources.py` are new. `HubRoutes` holds the library's list, the hub and the assign route, `StagingRoutes` the import's routes and `SourceRoutes` a source's file and thumbnail.
- `routes/table.py`: a `Route` row may name a `status`, which the staging upload's `202` needs ([D6](design.md#d6)).
- `app.py` keeps the middleware as a module-level factory, its body unchanged, the refusal handler and the catch-alls in one helper, and mounts each resource from one table; `create_app` ends under the function ceiling ([D7](design.md#d7)).
- `tests/test_ratchets.py` loses the rows of `create_app` and `read_compare` and lowers their tables' counts.
- `tests/mutants.json` takes `UA-7`'s new path, and the replay proves it and `UA-1a`, `UA-1b` and `UA-2` die.
- D59's *Accepts* line, the `app.py` docstring, the interface README, `docs/modules.md`, `docs/principles.md` and `ARCHITECTURE.md` say where the routes live.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement is touched, and no scenario is added: `skip_specs` holds.

## Impact

- Code: `isekai/interface/ui/app.py` loses the moved lines; `images.py`, `hub.py`, `staging.py` and `sources.py` of `isekai/interface/ui/routes/` hold them; `routes/table.py` takes a field.
- Documents: `docs/decisions.md`, `docs/modules.md`, `docs/principles.md`, `ARCHITECTURE.md`, `isekai/interface/README.md`, and each layer README's *Imported by* table, re-derived.
- Tests: `tests/mutants.json` and `tests/test_ratchets.py`, data only; no assertion changes and no record entry changes.

## Not in this change

- A record entry for a route the record lacks: when a test needs one, never a move.
- The wire's response declarations, and repointing the tests' imports from `app.py`: when the wire's declarations are planned.
- The patch of `run`, `serve`'s collaborators and the jobs' factory: they stay in `app.py` until the base's seams version.
- Any request, response, status code or message; any page code.
