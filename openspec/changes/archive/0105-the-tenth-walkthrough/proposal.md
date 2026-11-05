---
bump: patch
version: 0.69.1
---

# 0105 — the tenth walkthrough

A key's move to the first or last row of the session drawer or of the import sheet's tiles brings its head or its foot
into view, by the rule the hub and the library already follow.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
1 the drawer   useEdges over the drawer in place() for a key's move · a grid's first row shows its name · test_render.py
2 the sheet    useEdges over .import__body in focusTile() for a key's move · test_import.py
```

## Why

**The drawer's head and the sheet's label hide on a key's walk.** The drawer's `place()` and the sheet's `focusTile()`
only focus, so the browser scrolls just as far as the row. On the drawer's first row the title, the timer, the bar and
the steps stay out of view, and on its last row *Stop session now*; on the sheet's first row, `sources · N · size`.

## What Changes

- **A key's move in the drawer** scrolls it to its top on the first row and to its foot on the last
  ([D1](design.md#d1)).
- **A key's move into a grid's first row** in the drawer brings that collection's name into view ([D2](design.md#d2)).
- **A key's move among the sheet's tiles** scrolls `.import__body` to its top on the first row and to its foot on the
  last ([D3](design.md#d3)).
- **An e2e step each**, in a short window ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The running render opens in a drawer every screen offers*: a key's move to an edge row shows the head or the
  foot, and a grid's first row its name; a scenario added.
- `ui` — *Sources are chosen in the file dialog, and each shows its own upload*: a key's move to an edge row of the
  tiles shows the label or the foot; a scenario added.

## Impact

- `ui/src/components/SessionDrawer.vue`, `ui/src/components/ImportSheet.vue`.
- `tests/e2e/test_render.py`, `tests/e2e/test_import.py`.
- No requirement added; `ui/src/composables/useEdges.ts` unchanged; no CSS file, no decision in force.

## Not in this change

- Renders: it is to go, with the hub taking its place.
- Compare's pick: its head sits outside its scroller, always in view.
- A click, a restored focus and the drawer's first focus: they scroll as now.
