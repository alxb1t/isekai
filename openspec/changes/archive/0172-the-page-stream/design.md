# The page stream — design

The live store's `listen` takes a kind of `Events` and a handler of that kind's payload, and the typecheck holds the store's `KINDS` to `Events`' keys. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`ui/src/wire.ts` is derived from `shapes.py` ([D67](../../../docs/decisions.md#d67--the-pages-wire-is-derived-from-shapespy-and-a-test-re-derives-it)) and holds `Events`, the map of the events the stream sends: `snapshot`, `job`, `billing`, `cell` and `file`. `ui/src/types.ts` re-exports the page's other wire types and none of the stream's.

`ui/src/stores/live.ts` holds its own `Snapshot`, a `KINDS` list, a `Handler` that takes `unknown` and a `Map` of handlers by kind. Each `listen` site casts its payload, in the live store and in `ui/src/stores/collection.ts`. A pytest case already holds the keys of `Events` equal to `EVENTS`' ([D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own)), and nothing holds the page's half.

```
shapes.py EVENTS ──(test_the_events_keys_are_events_keys)──▶ wire.ts Events
                                                              │ re-export
                                                          types.ts Events
                                          this change ──▶     │ keyof Events
                                                          live.ts KINDS, listen, emit
```

## Goals / Non-Goals

Goals:

- Each handler's payload is its kind's type, with no cast.
- A kind that is no key of `Events`, or a key missing from `KINDS`, fails `tools.typecheck_ui`.

Non-goals are the proposal's [Not in this change](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The stream's types the page names reach it as re-exports of `types.ts`: `Events`. The live store's own `Snapshot` goes, and the collection store stops importing it | `types.ts` stays the one page file that reads `wire.ts`, as D67's *Accepts* says | importing `./wire` in the stores |
| [D2](#d2) | The handlers are an object mapped over the kinds, each a set of handlers of that kind's payload. `listen` and `emit` are generic in the kind, and no cast is left | dispatch is the same code for every kind, so the bound cases run it; a cast inside `listen` would be the one unchecked line left | a `Map` with a cast in `listen` (kept only as the fallback in [D2](#d2)) |
| [D3](#d3) | `KINDS` is held to `Events`' keys both ways by the typecheck alone: `satisfies` for a kind that is no key, and a type-level line that fails when a key is missing. No runtime change and no test | the gate typechecks the page; the list stays a value, since the loop over it registers the listeners | a vitest case; a runtime check |
| [D4](#d4) | The page does not check a parsed event at runtime. What `JSON.parse` returns stays the one untyped edge, in the loop that registers the listeners | the server's side is held by `EVENTS`' cases; a checker is new behaviour, which a patch may not add | a checker of each payload |
| [D5](#d5) | No vitest case is added; `billing`, `cell` and `file` stay with no case, as today | no scenario covers them, and a case binds only through `spec(` | a case with no binding |
| [D6](#d6) | D66 is amended and no decision is added: its *Accepts* says the typecheck holds the page's kinds to `Events`' keys, which a test holds to `EVENTS`'; the `str` fields stay; the *Reopen* clause goes; *Made by* gains this change's id | the rule is D66's and D67's already; this change closes what D66 accepted | a new decision |
| [D7](#d7) | A patch with `skip_specs`: it closes the wire's series | no requirement fits; behaviour is unchanged | — |

### D1

`types.ts` gains one line, `export type { Events } from './wire'`, beside the other re-exports. No site names `Snapshot` or `FileEvent` once each payload is typed by its kind, so neither is re-exported. `live.ts` imports `Events` from `'../types'`.

### D2

The live store's types after this change:

```
type Handler<K extends Kind> = (data: Events[K]) => void
handlers: { [K in Kind]: Set<Handler<K>> }       one key a kind, written out
listen<K extends Kind>(kind: K, handler: Handler<K>): () => void
emit<K extends Kind>(kind: K, data: Events[K]): void
```

The loop that registers the listeners calls `emit(kind, JSON.parse(…))` with `kind` the union; `JSON.parse` returns `any`, so it needs no cast of its own. The file handler keeps its spread: `const { upload, ...state } = data`, so the stored state holds what it holds today, including `staging`.

If the typecheck refuses the generic index, the fallback is the `Map` of today with one cast inside `listen`, and this design is amended to say so. Task 1.3 is a `**HALT CHECK**` for that.

### D3

```
const KINDS = ['snapshot', 'job', 'billing', 'cell', 'file'] as const satisfies readonly (keyof Events)[]
type Kind = (typeof KINDS)[number]
const listed: [Exclude<keyof Events, Kind>] extends [never] ? true : never = true
```

`satisfies` fails on a kind that is no key. `listed` is `never` when a key is missing from `KINDS`, so `= true` fails. The builder shows each direction once, in phase 1, and puts each edit back.

### D4

No checker is added. The server's side is held by `EVENTS`' cases.

### D5

No case is added, and `ui/src/stores/live.test.ts` is unchanged.

### D6

`docs/decisions.md` D66's *Accepts* line becomes: the billing volume's state, a session's outcome and a cell event's stage and state are `str`; the typecheck holds the page's kinds to `Events`' keys, which a test holds to `EVENTS`'; FastAPI's own 422 and 405 are not declared. *Made by* reads `0166`, `0167`, `0172`. The decision's bold rule line stands.

### D7

The change is a patch: no format version moves, nothing deprecates a verb or a flag, and no requirement fits.

## Tests

Tests added and removed, and the end-to-end runs added:

| layer | added | removed | end-to-end runs added | held by |
|---|---|---|---|---|
| unit (pytest) | none | none | none | `uv run pytest tests/test_derive_wire.py` |
| vitest | none | none | none | `uv run python -m tools.test_ui` |
| typecheck | the guards of [D3](#d3) and every typed site | none | none | `uv run python -m tools.typecheck_ui` |

The count of test files this change touches is zero: `git diff --name-only a993d8a6 HEAD -- tests` and `git diff --name-only a993d8a6 HEAD -- ui/src/stores/live.test.ts` print nothing. No test is deleted or merged, so there is no `I16` table. The existing cases `ui:events:one-stream-follows-the-batch-and-the-import` and `ui:events:a-job-event-fills-its-kinds-slot` run `listen`, `emit` and the loop, and `ui:sessions:a-terminal-render-stays-live` reads the store's state; none changes.

The test rules of the repository hold: `T1` puts the guard at the lowest layer that can fail, the typecheck; `T2` to `T6` have no case to apply to.

## Dependencies

None.

## Risks / Trade-offs

- The typecheck may refuse the generic index into the mapped object. [D2](#d2) names the fallback, and task 1.3 halts first.
- A `const listed` that nothing reads is the guard's price. The gate has no unused-variable rule for `ui/`; `tsc` and `vue-tsc` are strict without `noUnusedLocals`.
- The collection store's `cell` handler reads `stage` and `state` as the wire types them, `string | null`; each reader tests truthiness, so no site changes.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the typed stream first, the documents second.
