---
bump: patch
version: 0.87.28
---

# The page stream

The live store's `listen` is typed by the wire's `Events` map, so each handler's payload is its kind's type and every cast on the stream goes; behaviour is unchanged.

Reading map: [design](design.md) holds the typed store, the guards on `KINDS` and the test cost, [tasks](tasks.md) its phases.

## Why

`ui/src/wire.ts` declares the events the stream sends as `Events`, and `ui/src/types.ts` reads it. The live store still types its handler as `(data: unknown) => void` and casts the payload at each `listen` site, so the stream is the one half of the wire the typecheck cannot hold. A kind added to the server's `EVENTS` reaches the page with no check.

## What Changes

- `ui/src/types.ts` re-exports `Events` from the wire, so it stays the one page file that reads `wire.ts`.
- `ui/src/stores/live.ts`: `KINDS` is held to `Events`' keys both ways by the typecheck. The handlers become an object mapped over the kinds. `listen` and `emit` are generic in the kind. The store's own `Snapshot` goes, and every `as` cast on a payload with it.
- `ui/src/stores/collection.ts` stops importing `Snapshot` from the live store, and drops the casts of its listeners.
- `docs/decisions.md` D66: *Accepts* says the typecheck holds the page's kinds to `Events`' keys, which a test holds to `EVENTS`'; *Reopen* goes; *Made by* gains this change's id.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement fits, so the change carries `skip_specs`.

## Impact

- Only `ui/src/types.ts`, `ui/src/stores/live.ts`, `ui/src/stores/collection.ts` and `docs/decisions.md` change, and the changelog gains its entry.
- The same listeners register and the same handlers run in the same order. No existing test's assertion changes, and no vitest case is added.
- The stored state of a file event keeps what it holds today: the handler keeps its spread.

## Not in this change

- A runtime check of a parsed event: what `JSON.parse` returns stays the one untyped edge, in the loop that registers the listeners.
- A vitest case for `billing`, `cell` or `file`.
- A new decision.
- `api.ts`'s `request<T>` casts.
- The fields D66 leaves a `str`: the billing volume's state, a session's outcome and a cell event's stage and state.
- Any file under `isekai/`, `tools/` or `tests/`, and `wire.ts`.
