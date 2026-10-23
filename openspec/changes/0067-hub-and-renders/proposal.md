---
version: v0.41.0
backlog: [0062·R12, 0064·R6, 0061·R18]
---

# 0067 — hub and Renders

Home, the hub and Renders, finished as the design spec draws them. Every source shows as a thumbnail with its size.
A hub cell does its one thing on a click. A Render bar says what is ready. The Renders grid reads oldest to newest.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the source routes, the viewer, cell actions, the Render bar, the ready tile, the grid, motion |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
Home   2026-09-17  [▢▢▢▢▢▢▢ +5]  summon 2/5 approved …          [ New batch ⌥N ] in the header row
hub    [▢] 00003  00003.png · 832×1216 │ ☑ ▰▰▰▰▰▰ rendered ×1  ↵ view   ── click ──▶ the large view
                                        ┌ 1 ready to render                        [ Render ⌥R ] ┐
Renders  [▢] 00003 │ [v1 ⇄] [v2 ⇄] [▨ ready · 2 images]                      ── Esc ──▶ where it opened
```

## Why

**Nothing serves a source's image.** Home and the hub show no thumbnail. An unassigned source shows no size, because
its size is read from a run it does not have yet.

**A cell opens only on a double-click, and only Review.** A rendered cell cannot reach its image.

**Render is a header button.** Its disabled reason repeats what the grid already shows. Renders has no way to render
an approval short of its count.

**The Renders grid stacks versions newest first under a heading each.** Their labels overlap, and a cell reads right
to left in time.

## What Changes

- **Source images** — a thumbnail and the whole file, served by name; the size read from the source
  ([D1](design.md#d1)).
- **The viewer dialog** — one image, fitted, click for 1:1 ([D2](design.md#d2)).
- **Home and the hub's source cell** — thumbnails, the stem as the name, *New batch* in the header row
  ([D3](design.md#d3)).
- **Cell actions** — a click and `↵` follow the cell's stage; each cell names its newest image
  ([D4](design.md#d4)).
- **The large view returns to where it was opened** ([D5](design.md#d5)).
- **The Render bar** — replaces the header's Render button on the hub, and joins Renders ([D6](design.md#d6)).
- **The ready tile** — what the newest approval still lacks, from the render stage's own count
  ([D7](design.md#d7)).
- **The Renders grid** — a row per cell, oldest to newest; the version heading moves to the large view
  ([D8](design.md#d8)).
- **Motion** — one set of running signals, stopped by reduced motion ([D9](design.md#d9)).
- **The cards** — `0062·R12`, `0064·R6`, `0061·R18` ([D10](design.md#d10)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *A folder in the library is a batch when it holds `sources/`* — a row names its first sources; Home's
    header row holds *New batch*; first start keeps it under the privacy line.
  - MODIFIED *The hub shows each source's stage in each offered flow, and a tick assigns it* — the source's thumbnail
    and size from its file; a click follows the stage; each cell names its newest image.
  - MODIFIED *The page is told of a job as it runs* — a hub opened after a failed Prepare shows its message.
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — Render is
    offered from a bar that counts the images short and is absent when none is.
  - MODIFIED *The Renders view shows each source's images by flow and version* — oldest to newest; a source's
    thumbnail, upright, opening the viewer; the ready count; `Esc` back to where the large view opened.
  - MODIFIED *A version says what it was, and Compare shows a seed's two versions* — the heading moves to the
    large view.

## Impact

- **Code:** `isekai/interface/ui/library.py`, `isekai/interface/ui/app.py`, `ui/src/views/Home.vue`,
  `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/api.ts`,
  `ui/src/types.ts`, `ui/src/app.css`, `ui/src/components/BatchRail.vue`; new `ui/src/components/ImageViewer.vue`,
  `ui/src/components/RenderBar.vue`, `ui/src/bars.ts`, `ui/src/cells.ts`.
- **Tests:** `tests/test_ui_library.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/e2e/test_render.py`,
  `tests/e2e/test_routes.py`, `tests/e2e/test_import.py`; new `ui/src/bars.test.ts`, `ui/src/cells.test.ts`.
- **Docs:** `ui/design/spec.md`, `isekai/interface/ui/README.md`.

## Not in this change

- **The store and the key registry** — `useLive` and the per-view listeners stay; the `⌥` keys stay.
- **Review** — its layout, rail, dialogs, header and route; `PhotoOverlay` stays; Review next stays.
- **Sessions** — the session record, its tab, the running indicator, the session view's motion.
- **A second job slot.**
- **Home's running-render row** — J7·1's accent edge.
- **`0065·R17`** — the design spec's *Discard revision*, changed where Discard moves.
