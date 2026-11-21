---
bump: patch
after: [0188-the-stage-attempt]
---

# The page track

The hub cell's stage track is typed by the verbs Prepare runs and held by vitest cases; every word and class the page shows stays as it is.

Reading map: [design](design.md) holds the union, the guard and the proof of equality, [tasks](tasks.md) its phases: cases first, then the union.

## Why

The hub cell's track is the tables `SEGMENTS`, `DONE` and `RUNNING` and the functions `wordOf` and `segmentClass`, in `ui/src/cells.ts`. `RUNNING` is keyed by `string`, so a verb Prepare does not run types as well as one it does. No vitest case reads any of them.

A union of `tag`, `caption` and `sheet` lets the type name what `RUNNING` holds. The cases come first, so the union is proven to change no word and no class.

## What Changes

- `ui/src/cells.test.ts` gains cases for `SEGMENTS`, `DONE`, `RUNNING`, `wordOf` and `segmentClass`, written first and passing on the code as it stands.
- `ui/src/cells.ts` gains `PrepareVerb`, the union of `tag`, `caption` and `sheet`; `RUNNING` is keyed by it.
- `ui/src/cells.ts` gains one guard, `isPrepareVerb`, which `wordOf` and `segmentClass` read.
- `wordOf` and `segmentClass` keep their `string | undefined` parameter and narrow it by one guard before they read `RUNNING`; a stage the table lacks reads as it did.
- No decision is added, and no requirement or scenario changes: the change carries `skip_specs`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Behaviour is unchanged, and the change carries `skip_specs`.

## Impact

- `ui/src/cells.ts` and `ui/src/cells.test.ts`.
- The page's typecheck and vitest, which the gate runs.

## Not in this change

- A wire field for the stage: a union from the wire changes `ui/src/wire.ts` and reopens [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own)'s *Accepts*, and the server sends a stage list only while a Prepare runs.
- `ui/src/views/Hub.vue`, which passes the store's `string` and stays as it is.
- Any server file, and the placement's `ui/src/stages.ts`.
- The interface's tables read from the record, until [D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy)'s *Accepts* is reopened.
- A changed word, class or segment of the track.
- Any file under `isekai/`, `tests/`, `tools/` or `evaluation/`.
