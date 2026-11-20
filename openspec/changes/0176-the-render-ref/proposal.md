---
bump: patch
---

# The render ref

`rendered_at` and `edit_at` return named types, and a version is read off an artifact's name by one function.

Reading map: [design](design.md) holds the types, the sites and the proof, [tasks](tasks.md) holds the phases: the types, the readers, the versions and the documents.

## Why

`rendered_at` returns a tuple of run, flow, approval and seed, and `edit_at` one that adds the edit's number. Callers read a field by its place, with an index, a slice or a star-unpack, so a reader must know the order by heart.

Review's `Revision` is the same tuple written as a type alias, and a route builds one by hand. A version is read off an artifact's name by slicing its first characters at several sites, each repeating the width of a name.

A named type reads by field and keeps the tuple's order, so every caller that unpacks holds. One function that reads a version leaves the width in one place.

## What Changes

- `isekai/foundation/layout.py` gains `RenderRef(run, flow, version, seed)` and `EditRef(run, flow, version, seed, k)`, `NamedTuple`s, and `version_of(path)`. `run.py` re-exports all three.
- `rendered_at` returns a `RenderRef` and `edit_at` an `EditRef`.
- The sites that index, slice or star-unpack a result read it by field name: `_located` and `request_placed` in `isekai/pipeline/edit.py`, `discard_render` in `isekai/pipeline/generate.py`, and `run_discard` in `isekai/interface/verbs/drafts.py`.
- Review's `Revision` is `RenderRef`, and the route that builds one by hand builds a `RenderRef`.
- The sites that slice a name's first characters call `version_of`: `current_draft`, `_waiting_number`, `discard`, `withdraw` and `approve` in `isekai/pipeline/review.py`, `_drafted` in `isekai/interface/ui/routes/reviewing.py` and `refusal_for` in `isekai/foundation/run.py`.
- A decision, D70, records the types and the function; the foundation README's row and `layout.py`'s docstring say so.
- No requirement changes, so there is no spec delta.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change carries `skip_specs: true`: every path names the same run, flow, approval, seed and number as today, and the suite holds it as it stands.

## Impact

- Code: `isekai/foundation/layout.py`, `isekai/foundation/run.py`, `isekai/pipeline/edit.py`, `isekai/pipeline/generate.py`, `isekai/pipeline/review.py`, `isekai/interface/verbs/drafts.py`, `isekai/interface/ui/routes/reviewing.py`.
- Tests: cases for each type and for `version_of` are added to `tests/test_edit.py` and `tests/test_run_directory.py`; no existing assertion changes.
- Documents: `docs/decisions.md` (D70), `isekai/foundation/README.md`, the docstring of `isekai/foundation/layout.py`.
- No format version moves and no run file changes.

## Not in this change

- A function whose signature takes a ref: it would edit many test calls, and the routes cannot take one.
- A method on a ref.
- The folder climbs by `parents[n]` and the `int(group.name)` reads.
- The server's check of a seed, a version or a bake's number in a path.
- The page's address types.
- A scenario or a spec delta.
