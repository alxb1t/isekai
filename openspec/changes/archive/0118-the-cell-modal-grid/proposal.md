---
bump: minor
version: 0.78
---

# 0118 — the cell modal as a grid

The cell modal lays a cell's renders out as **one grid**, at most three to a row, its rows balanced, each image badged
with its version and fitted to the window. **Renders is deleted**: the hub's cells and their modal are where images are
viewed, and every large view goes back to the hub.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision and the test cost |
| [tasks](tasks.md) | the phases, in build order |
| `specs/ui/spec.md` | the hub, Render, drawer and Draft requirements; the large view's and the keys' requirements, renamed |

```
1 the grid       cells.ts: cellGrid in balanced rows, moveCell · CellModal.vue: the badge, the fit · app.css
                 · the unit tests · the e2e step
2 Renders gone   the page, its route, tab and ⇧I · the drawer's View in Hub on ⇧H · the large view's way back
                 · the store slice, api and types · the list endpoint and `lacking` · the CSS · the tests
3 the prose      the design spec · the READMEs and data-flow · the comments that name Renders
```

## Why

**A row per version reads as no layout at all.** The operator tried `v0.77.0`: a cell rendered under a few versions shows a
short row for each, a ragged staircase. One grid in the one order, balanced, shows them as a set. **And
Renders is left with nothing to do**: `v0.77.0` gave the hub its pending tile and a modal of every render, so the
operator asked to fold its deletion — the second half of the hub-takes-Renders plan — into this version.

## What Changes

- **One grid, no version rows.** Every render of the cell in the one order — versions oldest first, seeds numeric —
  at most three columns, rows balanced: rows = ⌈n/3⌉, columns = ⌈n/rows⌉ ([D1](design.md#d1)).
- **The version is a `vN` badge on the image**, as on the hub's thumbnails; the caption is `seed N`, then `⇄` when the
  seed was rendered under another version too ([D3](design.md#d3)).
- **2D moves.** `h j k l` and the arrows; `j` onto a missing tile lands on the last; `l` at a row's end goes on to the
  next row's first, `h` at a row's start back to the previous row's last ([D2](design.md#d2)).
- **Fit the window.** Up to three rows show whole, tiles scaled down from twice a thumbnail as needed; past nine renders
  the grid scrolls ([D4](design.md#d4)).
- **BREAKING (UI) — Renders is deleted**: the page, its route, its tab and `⇧I`, the list endpoint and `lacking`,
  `RendersInfo`, the store slice, its CSS, its specs and tests ([D5](design.md#d5)). The `/renders/…` routes of the
  large view and Compare keep their names.
- **Every large view goes back to the hub**, on the cell of the image it closed ([D6](design.md#d6)).
- **The drawer's link is *View in Hub*, on `⇧H`**; `⇧I` is freed ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The hub shows each source's stage in each offered flow, and a tick assigns it*: the cell modal is one
  balanced grid, badged, fitted, moved in 2D; *the cell modal moves by version and seed* and *a thumbnail opens the
  cell modal on it* rewritten; *the cell modal balances its rows* and *the hub keeps its focus* added.
- `ui` — *Render is confirmed in a dialog that quotes what renders, its limit and its price at most*: the bar is the
  hub's alone.
- `ui` — *The running render opens in a drawer every screen offers*: `⇧H` opens the focused image's collection's hub;
  tiles at a thumbnail's size; *a key's move to an edge row shows the drawer's head* names *View in Hub*.
- `ui` — *Draft from this starts from an image, …*: offered from the large view alone.
- `ui` — *The Renders view shows each source's images by flow, and a large view walks the photograph's row* is removed
  and added as *An image's large view shows its sheet and walks the photograph's row, and its thumbnail is made once*
  ([D9](design.md#d9)): the Renders view and its scenarios go; the large view, thumbnail and serving scenarios carry
  their keys.
- `ui` — *Every command has one key, declared once, and none fires while typing* is removed and added as *Each command
  has one key, declared once, and none fires while typing* ([D9](design.md#d9)): *Renders moves by cell and by image*
  goes; *a row move keeps the column* is read on the cell modal.

## Impact

- `ui/src/cells.ts`, `ui/src/cells.test.ts`, `ui/src/components/CellModal.vue`, `ui/src/app.css`,
  `tests/e2e/test_render.py`.
- Deleted: `ui/src/views/Renders.vue`. Edited: `ui/src/router.ts`, `ui/src/App.vue`,
  `ui/src/components/SessionDrawer.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/views/Compare.vue`,
  `ui/src/views/Hub.vue`, `ui/src/components/ComparePick.vue`, `ui/src/components/DeleteDialog.vue`,
  `ui/src/stores/collection.ts`, `ui/src/stores/collection.test.ts`, `ui/src/grid.ts`, `ui/src/grid.test.ts`,
  `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/bars.ts`.
- `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`, `tests/test_ui_api.py`, `tests/e2e/conftest.py`.
- `ui/design/spec.md`, `README.md`, `isekai/interface/ui/README.md`, `isekai/interface/README.md`, `docs/data-flow.md`,
  `docs/principles.md`.

## Not in this change

- **The routes' names.** `/c/<collection>/renders/…` stays for the large view and Compare (brief Q7 of `0117`).
- **The draft endpoint's several images.** It still takes a list; only the page's selection goes.
- **The server's order.** `HubCell.images` and `newest` keep their write order; the page sorts.
- **The pending tile, the large view's `h` `l` and Compare** stay as `v0.77.0` shipped them.
