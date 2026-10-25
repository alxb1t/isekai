---
version: v0.49
backlog: [0069·R12]
---

# 0076 — the second walkthrough

What the operator's second manual pass after `v0.48.0` found, closed. Review's panes move from a field on macOS;
Compare takes any two images of a cell; the hub's source cell is a column that keeps long names in; the Render dialog
closes when its page is left; a `?` button replaces the key bars; Renders' source cell is reachable and `h j k l` move
as the arrows do; the session page is a grid of flows over the originals, from the keyboard.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each finding's fix, the card |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` · `cli` |

```
session page          00003          16_01          IMG_0412
summon-anime-wai      [v2·10]        [v1·7]         ·
conjure-anime-wai     [v1·4]         [▨ waiting]    [v1·7]
originals             [00003]        [16_01]        [IMG_0412]       h l between photographs · j k between rows
```

## Why

**Nine findings from the second pass.** A field holds Review's pane keys; Compare reaches one same-seed version alone;
long source names spill out of the hub's column and its photograph sits off its renders' line; the Render dialog
outlives its page; two lines of key bar repeat the key list; Renders' photograph takes no focus and its letters and
arrows differ; the session page shows every photograph of the batch, unpaired with its renders, and none from the
keyboard.

## What Changes

- **Review's panes from a field, on macOS** — `⌃H` `⌃L` ([D1](design.md#d1)).
- **Compare any two images of a cell** — a pick in the viewer ([D2](design.md#d2)).
- **The hub's source cell** — a column; long names wrap everywhere ([D3](design.md#d3)).
- **The Render dialog** — closed on leaving ([D4](design.md#d4)).
- **No key bars** — a `?` button ([D5](design.md#d5)).
- **Renders' keys** — the source cell; `h j k l` as the arrows ([D6](design.md#d6)).
- **The session grid** — the record's plan, the flows over the originals, the keys ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *Every command has one key, declared once, and none fires while typing* — no key bar, the app bar's `?`;
    `⌃H` `⌃L` in a field on macOS; Renders' moves.
  - MODIFIED *The Renders view shows each source's images by flow and version* — the source cell from the keyboard.
  - MODIFIED *A version says what it was, and Compare shows a seed's two versions* — any two images of a cell.
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — the dialog
    closes when its page is left.
  - MODIFIED *Each batch's render sessions are listed and shown from their records* — the grid, its photographs, its
    keys.
- `cli`:
  - MODIFIED *A render session writes its record into the batch, from its start to its end* — the plan per photograph
    and flow.

## Impact

- **Code:** `isekai/interface/render.py`, `isekai/foundation/artifacts.py`, `isekai/interface/ui/library.py`,
  `isekai/interface/ui/app.py`, `ui/src/stores/keys.ts`, `ui/src/grid.ts`, `ui/src/router.ts`, `ui/src/App.vue`,
  `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/views/Compare.vue`,
  `ui/src/views/Review.vue`, `ui/src/views/SessionPage.vue`, `ui/src/views/Home.vue`, `ui/src/views/Sessions.vue`,
  `ui/src/views/Billing.vue`, `ui/src/components/ImageViewer.vue`, `ui/src/components/RenderDialog.vue`,
  `ui/src/components/BatchRail.vue`, `ui/src/stores/batch.ts`, `ui/src/sessions.ts`, `ui/src/app.css`; deleted
  `ui/src/components/KeyBar.vue`.
- **Tests:** `tests/test_render.py`, `tests/test_ui_api.py`, `tests/e2e/test_render.py`, `ui/src/stores/keys.test.ts`,
  `ui/src/grid.test.ts`, `ui/src/sessions.test.ts`.
- **Docs:** `ui/design/spec.md`, `docs/decisions.md` (D25).

## Not in this change

- **A conjure draft from summon** — *conjure from this*, its own change.
- **Linux's pane keys** — `Esc`, then `h` `l`, as today.
- **A dialog besides the viewer.**
