---
bump: patch
version: 0.87.24
---

# The wire derived

A stdlib tool writes the page's half of the wire, `ui/src/wire.ts`, from `shapes.py`, and a test re-derives it; the page does not read it yet.

Reading map: [design](design.md) holds the tool's grammar, the file's shape and the tests, [tasks](tasks.md) its phases: the grammar, the file, the documents.

## Why

The server's answers are declared once, in `isekai/interface/ui/shapes.py`, and held by tests ([D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests), [D64](../../../docs/decisions.md#d64--the-answers-the-record-lacks-are-a-second-table-held-by-cases-that-ask-the-server), [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own)).

The page's `types.ts` is still written by hand beside them, so it can drift again. A derived file closes that half: a test re-derives it and expects the same bytes, as the principle says of every derived copy. This version writes the file and its guard; `the-page-wire` makes the page read it.

## What Changes

- `tools/derive_wire.py` is added: stdlib and `ast` alone, `derive(root)` returns the file's text and `main()` writes `ui/src/wire.ts`.
- `ui/src/wire.ts` is added, as the tool writes it: every class `shapes.py` reaches under Python's name, each imported alias named by its module and its name, and the events map keyed as `EVENTS` is.
- `tests/test_derive_wire.py` is added: a case for each form of the tool's grammar, the refusal of a form outside it, the committed file held to what the tool writes, and the events' keys held to `EVENTS`'.
- `Makefile`'s `derive` target runs the tool; the principle's *Held by* names the re-derive test; the root README's tools line names the wire; a new decision records that the page's wire is derived and re-derived by a test.

## Capabilities

### New Capabilities

None. The change adds no requirement: it is tooling and a derived file, held by structural tests.

### Modified Capabilities

None.

## Impact

- New: `tools/derive_wire.py`, `ui/src/wire.ts`, `tests/test_derive_wire.py`.
- Edited: `Makefile`, `docs/principles.md`, `README.md`, `docs/decisions.md`.
- No file under `isekai/` changes, and under `ui/src` only `wire.ts` is added.
- No format version moves, no flow is re-pinned, no image-frozen file changes, no dependency is added.

## Not in this change

- An import of `wire.ts` by the page, and `types.ts`: that is `the-page-wire`.
- A vitest case.
- A doc comment in `wire.ts`.
- An import of `isekai` by the tool.
- A row of the page's ratchet.
- Any file under `isekai/`.
- Renaming the page's vocabulary to Python's; `api.ts`'s inline answer types and its `request<T>` casts; a tuple in Python.
- The mirrored rules — `modeOf`, the floors, the seed range; a byte-level pin; `/openapi.json`, which nothing reads.
