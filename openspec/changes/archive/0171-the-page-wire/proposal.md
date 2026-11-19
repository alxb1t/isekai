---
bump: patch
version: 0.87.27
---

# The page wire

`ui/src/types.ts` re-exports `ui/src/wire.ts` under the page's names, so the page's types are the server's declaration and no longer a hand-written copy. Behaviour is unchanged.

Reading map: [design](design.md) holds the decisions, the test cost and the acceptance, [tasks](tasks.md) its phases.

## Why

`types.ts` is a hand-written copy of what the server sends, and `SessionRecord`, `RunningSession`, `Billing`, `QuoteSource`, `CellEvent` and `TattooList` disagree with the server. `wire.ts` is derived from `shapes.py` and a test holds it equal ([D67](../../../docs/decisions.md#d67--the-pages-wire-is-derived-from-shapespy-and-a-test-re-derives-it)), but no page file reads it yet. Until the page reads it, a field the server adds reaches the page by hand.

## What Changes

- `types.ts` re-exports each wire type the page uses, under the page's present name, one line a type; every page file goes on importing `types.ts`.
- Overlay types narrow a pair to the page's `Point` and `Pair`: `Tattoo`, `Outline`, `Stage1`, `Proposal` and `TattooList`.
- `Billing`, `CellEvent`, `SessionRecord` and `RunningSession` become the wire's; `QuoteSource` is the wire's `QuotedSource` without `images`.
- The collection store stores a cell event's stage only when it is set.
- The session fixtures of `sessions.test.ts`, `SessionDrawer.test.ts` and `live.test.ts` gain the fields the wire's types require. No assertion changes and no case is added.
- `types.ts` loses its doc comments; two that state a rule of the page move to the site that applies it.
- D67's *Accepts* line says the page reads `wire.ts` through `types.ts`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement is touched, so the change carries `skip_specs`.

## Impact

- `ui/src/types.ts` shrinks to the re-exports, the overlays and the types only the page holds.
- `ui/src/stores/collection.ts`, `ui/src/components/SourcePanel.vue` and `ui/src/stores/live.ts` change a line or a comment each.
- `ui/src/sessions.test.ts`, `ui/src/components/SessionDrawer.test.ts` and `ui/src/stores/live.test.ts` gain fixture fields.
- `docs/decisions.md` amends D67.
- `ui/src` holds the page's other files, which import `types.ts` and change no import line.

## Not in this change

- Renaming the page's vocabulary to Python's.
- `api.ts`'s inline answer types and its `request<T>` casts.
- A tuple in Python.
- The typed `listen`, the snapshot's type, `KINDS` and the stream's casts, which come with the page's stream.
- A `Pick` for the running session.
- A narrowing by the page of a field Python holds as `str`.
- A vitest case.
- Any file under `isekai/`, `tools/` or `tests/`, and `wire.ts`.
