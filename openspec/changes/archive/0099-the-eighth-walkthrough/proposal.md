---
bump: minor
version: v0.64
backlog: [0091·R5, 0091·R7, 0091·R8]
---

# 0099 — the eighth walkthrough

What the operator's eighth pass found, fixed in one version: `⇧A` opens the file dialog inside the import sheet, and a
key's move to the first or last row brings the hub's or the library's head or foot into view. The removal cards the
sheet's trigger reaches are paid first.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
1 the cards   0091·R5: one removal per tile · R7: the hand-off · R8: the reset — each in staging.ts, each unit-tested
2 ⇧A          add-files in the sheet's keys, off while committing · its hint on Add files… · test_import.py by ⇧A
3 the edges   useEdges: first row → top, last → foot, any other nearest · the hub's place(), the library's walk()
```

## Why

**The sheet takes its files by mouse alone, and the screens' heads hide on a key's walk.** Every other act in the
sheet has a key; *Add files…* has none. A key's move to row 0 scrolls the hub or the library only as far as the row,
so *Add sources…*, the flow names and *New collection* stay out of view.

## What Changes

- **A second press of `×` or `⌫`** on a tile whose removal is in flight does nothing ([D1](design.md#d1)).
- **The removal's hand-off and the skipped copy's reset** move into `staging.ts`, each held by a unit test
  ([D2](design.md#d2), [D3](design.md#d3)).
- **`⇧A` in the sheet** opens the file dialog, in New collection and Add sources alike; *Add files…* carries its hint
  ([D4](design.md#d4)).
- **A key's move to the first or last row** scrolls the hub or the library to its top or its foot
  ([D5](design.md#d5), [D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *Sources are chosen in the file dialog, and each shows its own upload*: `⇧A` opens the dialog from the sheet.
- `ui` — *The hub shows each source's stage in each offered flow, and a tick assigns it*: a key's move to an edge row
  shows the head or the foot.
- `ui` — *A folder in the library is a collection when it holds `sources/`*: the same on Home.

## Impact

- `ui/src/`: `staging.ts`, `staging.test.ts`, `components/ImportSheet.vue`, `views/Hub.vue`, `views/Home.vue`; a new
  `composables/useEdges.ts` and its test.
- `tests/e2e/`: `test_import.py`, `test_prepare.py`.
- `ui/design/spec.md`: the J1·4 frame and §7's dialogs row.
- No CSS file, no decision in force.

## Not in this change

- Renders, its routes and `⇧I`: their own version.
- Review's rail and the sheet's tiles: their scroll is unchanged.
- A restored focus: it still centres.
