# The hub's focus — design

The hub's focus, selection and restored spot move into one composable with its tests, then the view switches to it and loses its ratchet row. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Today `ui/src/views/Hub.vue` holds all of it:

- the focus, as the ref `focus`, and the selection, as the ref `selected`;
- `named`, `place`, `focusedCell`, `select` and `moveBy`, which move them;
- on mount, the restored spot: the cell a large view sent, else `kept` of `ui/src/grid.ts`;
- after them, the view's one `useKeys` call.

`tests/test_ratchets.py` lists the view in `BIG_UI_FILES`, and the table's count is `UI_ROWS`.

```
Hub.vue                                   Hub.vue
  focus, selected                           grid, page, useEdges        template refs stay
  named, place, focusedCell,   ───▶         useHubFocus({...})  ──────▶ focus, selected, place,
  select, moveBy                            useKeys('screen', [...])                select, moveBy
  onMounted: spots, sent, kept              onMounted: sent ─▶ restoredSpot ─▶ place
```

These facts shape the plan. A vitest test binds a scenario through `spec`, with no exempt form. `useKeys` declares a layer per call, and the newest layer answers a key first, so a second call from a composable would win over the view's. No document names the focus's code: `git grep -n -i composable -- docs ARCHITECTURE.md` prints nothing.

## Goals / Non-Goals

Goals:

- `useHubFocus` owns the focus, the selection and their moves; the spot's finder is a pure function.
- Each rule is written in its module with its test first, then the view switches to it.
- `Hub.vue` ends under the ceiling, `UI_FILE_LINES` of `tests/test_ratchets.py`, and its ratchet row goes in the same change.

Non-goals: see [proposal](proposal.md#not-in-this-change). Behaviour, classes, `data-*` hooks and keys stay as they are.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `useHubFocus` takes the sources, the flows, the grid ref, the reveal and a `remember` function, and returns `focus`, `selected`, `place`, `select` and `moveBy` | the view keeps its template refs and its store; a composable that took the store would test only with a pinia | moving `grid` and `page` into it; passing the store whole |
| [D2](#d2) | `spotName` and `restoredSpot` are pure exports of `useHubFocus.ts`; the read of `window.history.state` stays in the view | the finder needs no browser; the history is the page's | a pure file apart for these; reading the history in the composable |
| [D3](#d3) | the composable declares no keys; the view keeps its one `useKeys` call, its commands in today's order | a second call makes a newer layer that answers first, and the keys' source scans read the views alone | a `useKeys` call in the composable |
| [D4](#d4) | each test binds an existing scenario whose text covers the rule; the selection's rule moves untested | a patch adds no requirement; no scenario names `⇧↑↓` | a new scenario; an unbound test |
| [D5](#d5) | `Hub.vue`'s ratchet row and the table's count go in the phase where the view falls under the ceiling | [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets): a row goes with its offender, and the ratchet reads a row whose offender no longer offends as red | removing the row in a later phase |

### D1

The composable's options:

```ts
useHubFocus({
  sources,   // Readonly<Ref<Pick<HubSource, 'name' | 'digest'>[]>>, the view's computed
  flows,     // Readonly<Ref<string[]>>
  grid,      // Readonly<Ref<HTMLElement | null>>, the view's template ref
  reveal,    // (cell, row, rows) => void, the view's `useEdges`
  remember,  // (name: string) => void, the view's `store.focus.hub = name`
})
```

It returns `focus` (`Ref<Focus>` of `ui/src/grid.ts`), `selected` (`Ref<Set<number>>`), `place(row, column, how)`, `select(step)` and `moveBy(rows, columns)`. Each body is today's, with `store.focus.hub = named(focus.value)` as `remember(spotName(sources.value, flows.value, focus.value))`. `focusedCell` stays inside, since only `place` reads it.

### D2

```ts
spotName(sources, flows, spot)            // at(sources[row]?.name ?? '', flows[column - 1] ?? '')
restoredSpot(sources, flows, sent, held)  // the sent cell's spot, else `kept` of the spots by name
```

Both take their sources as `Pick<HubSource, 'name' | 'digest'>[]`, so a test passes `{ name, digest }` alone. `restoredSpot` builds the spots as the mount does: a row of every source by a column of the source cell and every flow. It finds the one whose source's `digest` and flow are the sent cell's, else `kept(spots, name, held)`. The view reads `window.history.state?.cell`, clears it as today and passes `sent`.

### D3

`useHubFocus.ts` holds no `useKeys` call, and `Hub.vue` keeps the one it has. The commands `left`, `down`, `up`, `right`, `select-down`, `select-up`, `tick`, `photo`, `act` and `clear` stay in today's order, and the ones that move the focus call `moveBy` and `select` from the composable.

### D4

| rule | where it lives | scenario it binds | test |
|---|---|---|---|
| a focus move clamps, writes its spot's name, focuses the cell and scrolls it | `place` | `ui:hub:an-edge-row-shows-the-head` | the `place` test |
| a restored spot is the remembered one, else the first | `restoredSpot` | `ui:hub:the-hub-keeps-its-focus` | the `restoredSpot` test |
| a cell a large view sent is the restored spot | `restoredSpot` | `ui:hub:a-rendered-cell-opens-its-newest-image` | the sent-cell test |
| `⇧↑↓` extends the selection from the focused row, which joins it, held at the grid's ends | `select` | none | none: it moves untested |

The sent-cell and edge-row scenarios are end-to-end ones. A vitest binder on such a key adds no demand and removes none: the key's own binder under `tests/e2e/` stays, and `layer_faults` asks for a binder on the key's layer alone.

### D5

The ratchet reads a row whose offender no longer offends as red, so phase 2 ends green only without the row. If the view still ends past the ceiling, this decision is wrong and the build halts at the `HALT CHECK` of phase 2 rather than keep the row.

## Tests

The change adds unit tests and no end-to-end test, since the rules need no browser. A vitest test stubs the grid as an object whose `querySelector` returns a stub cell, because vitest runs in `node` with no DOM.

| layer | added | removed | the command that counts it |
|---|---|---|---|
| unit, vitest | the tests of `ui/src/composables/useHubFocus.test.ts` | none | `grep -c "^spec(" ui/src/composables/useHubFocus.test.ts` prints `3` after phase 1 |
| structural, pytest | none; `tests/test_ratchets.py` loses the row of `Hub.vue` | none | `grep -c "Hub.vue" tests/test_ratchets.py` prints `0` after phase 2 |
| end-to-end | none | none | none to count |

No test is deleted or merged, so there is no table of removals. Every existing browser test of the hub reads the same classes, `data-row` and `data-column`, which the template keeps.

## Dependencies

None.

## Risks / Trade-offs

- **The order of the view's setup.** `useHubFocus` is called after `sources`, `flows` and `reveal` exist and before `useKeys`, so each handler the keys name is bound when they are declared. A call earlier reads an empty ref.
- **The ceiling.** The view loses the moved lines and gains the call. If it ends past the ceiling, [D5](#d5) holds the halt.
- **A cell the page does not draw.** `restoredSpot` returns the first spot when a remembered one is gone, as `kept` does today; a collection with no source returns nothing, and `place` returns at once on no rows.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the composable with its tests first, then the view's switch with its ratchet row.
