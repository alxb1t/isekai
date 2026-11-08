---
bump: minor
---

# 0117 — the Hub cell modal

`↵` on a rendered Hub cell opens **the cell modal**: a grid of that cell's renders at twice the thumbnail size, moved
with the arrows and `h j k l`, `↵` opening the render page. The render page's `h` `l` walk the photograph's whole row
across its flows, `Esc` from it lands on the Hub cell of the image it closed, and a Hub cell shows the renders still
pending, as Renders does. Renders stays.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision and the test cost |
| [tasks](tasks.md) | the phases, in build order |
| `specs/ui/spec.md` | the hub requirement and the Renders requirement |

```
1 the cell modal   cells.ts: the order, the grid, the ⇄ seeds, the ready tile · CellModal.vue · Hub.vue
                   · the viewer loses ⇧↵ · the unit tests
2 the walk         RenderLarge.vue: one order, Esc to the Hub cell · the detail drops `cell` · the tests
3 the prose        the e2e test · the design spec's J2, J5 and keys
```

## Why

**Images are viewed on the Hub, and it shows them one at a time.** `↵` on a rendered cell opens the viewer, one
fitted image of that cell at a time, and `⇧↵` there the render page. The only part of Renders the operator still uses
is its pending tile. The render page walks a different order by where it was opened: one flow's images by write time
from the Hub, the whole row from Renders. This change makes the Hub enough to view renders; deleting Renders waits for
the operator to try it.

## What Changes

- **The cell modal replaces the viewer for a Hub cell**, a thumbnail's click included: a click opens the modal on that
  image, `↵` on the newest. A row per version, oldest first, each its seeds in numeric order, at twice the thumbnail
  size; `h j k l` and the arrows move, `↵` or a click opens the render page, `Esc` closes
  ([D1](design.md#d1)). The viewer stays for photographs ([D6](design.md#d6)).
- **A seed rendered under more than one version is marked `⇄` in the modal**, computed in the browser
  ([D1](design.md#d1)).
- **One order** — flows as the Hub's columns, versions oldest first, seeds numeric — for the Hub cell's thumbnails,
  the modal and the render page's `h` `l`, which always walk the photograph's whole row ([D2](design.md#d2)). The
  render detail drops `cell`, the write-order copy only the Hub's walk read ([D3](design.md#d3)).
- **`Esc` and *Back to Hub* on a render page opened from the Hub open the Hub focused on the cell of the image it
  closed**, the modal not reopened ([D4](design.md#d4)).
- **A Hub cell shows the pending tile**, `ready · n images`, last in its row, from `HubCell.short`
  ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The hub shows each source's stage in each offered flow, and a tick assigns it*: a cell holding images opens
  the cell modal, its thumbnails in the one order, the pending tile last; *a rendered cell opens its newest image*
  goes through the modal; scenarios are added, *the cell modal moves by version and seed*, *a seed under two versions
  is marked* and *a cell shows what is ready*.
- `ui` — *The Renders view shows each source's images by flow and version* is removed and added as *The Renders view
  shows each source's images by flow, and a large view walks the photograph's row* ([D8](design.md#d8)): a large
  view's `h` `l` walk the photograph's row wherever it was opened, and its `Esc` lands on the Hub cell of the image it
  closed when the Hub opened it; *the large view steps through its screen's order* becomes *the large view walks the
  photograph's row*, every other scenario and key kept.

## Impact

- `ui/src/cells.ts`, `ui/src/cells.test.ts`, `ui/src/components/CellModal.vue` (new), `ui/src/views/Hub.vue`,
  `ui/src/app.css`.
- `ui/src/components/ImageViewer.vue`, `ui/src/composables/useViewer.ts`, `ui/src/components/ImageViewer.test.ts`.
- `ui/src/views/RenderLarge.vue`, `ui/src/types.ts`, `isekai/interface/ui/app.py`, `tests/test_ui_api.py`.
- `tests/e2e/test_render.py`, `ui/design/spec.md`.

## Not in this change

- **Deleting Renders** — the page, its tab and `⇧I`, the drawer's link, the list endpoint, its store slice, CSS,
  specs and tests, and *View in Hub* on `⇧H` (brief Q6). It waits until the operator has tried this change.
- **Renders' own `Esc`.** A render page opened from Renders, or from a pasted address, still goes back to Renders.
- **The server's order.** `HubCell.images` and `newest` keep the write order the server reads; the page sorts.
- **The routes.** `/renders/…` keep their names (brief Q7).
