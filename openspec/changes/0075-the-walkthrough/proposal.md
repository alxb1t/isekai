---
version: v0.48
backlog: [0070·R13, 0070·R14, 0074·R7]
---

# 0075 — the walkthrough

What the operator's manual pass over every feature after `v0.47.0` found, closed. Home's row reads as one line; the
large view sets an image beside its photograph; the hub's source cell is reachable from the keyboard; a grid keeps its
focus across a large view; a rendered hub cell shows its images and opens them in the viewer; Review's rail says where
the other flows' waiting sheets are.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each finding's fix, the cards |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
hub   [▢] 1  1.jpeg · 748×1173 │ ☑ ▰▰▰▰▰▰ rendered ×3  [v1▢][v2▢][v2▢]   ↵ view
       ↵ the photograph          └─ ↵ the viewer on the newest ── ← → h l ── ↵ the large view ── Esc back, focus kept
```

## Why

**Six findings from the manual pass.** Home's flow chips sit beside the thumbnails; the large view cannot set an
image beside its photograph; the hub's source cell has no keyboard way in; `Esc` from a large view drops the focus to
the first image or cell; a rendered hub cell is empty and `↵` leaves the hub; Review's tab counts sheets its rail does
not show.

## What Changes

- **Home's row** — a header line, the thumbnails below ([D1](design.md#d1)).
- ***Side by side* on the large view** ([D2](design.md#d2)).
- **The hub's source cell** — reached by `h`, opened by `↵` ([D3](design.md#d3)).
- **Focus kept** across a large view, Back and tab switches ([D4](design.md#d4)).
- **A rendered cell's images** — a strip, and the viewer on `↵` ([D5](design.md#d5)).
- **Review's rail head** — the other flows' waiting sheets ([D6](design.md#d6)).
- **The cards** — `0070·R13`, `0070·R14`, `0074·R7` ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *The hub shows each source's stage in each offered flow, and a tick assigns it* — the source cell from the
    keyboard; a rendered cell's images, opened in the viewer; the focus kept.
  - MODIFIED *The Renders view shows each source's images by flow and version* — `Esc` returns focused on the image
    closed.
  - MODIFIED *A version says what it was, and Compare shows a seed's two versions* — *Side by side* with the
    photograph.
  - MODIFIED *Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet* —
    the rail's head names the other flows' waiting sheets.

## Impact

- **Code:** `isekai/interface/ui/library.py`, `isekai/interface/ui/app.py`, `ui/src/types.ts`, `ui/src/stores/batch.ts`,
  `ui/src/views/Home.vue`, `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue`, `ui/src/views/RenderLarge.vue`,
  `ui/src/views/Review.vue`, `ui/src/components/ImageViewer.vue`, `ui/src/components/BatchRail.vue`,
  `ui/src/composables/useQueue.ts`, `ui/src/app.css`.
- **Tests:** `tests/test_ui_library.py`, `tests/e2e/test_render.py`, `ui/src/stores/batch.test.ts`,
  `ui/src/composables/useQueue.test.ts`.
- **Docs:** `ui/design/spec.md`.

## Not in this change

- **Renders' grid layout.**
- **A dialog besides the viewer** — the hub's images open in the one that exists.
- **What the Review tab counts** — still every flow's waiting sheets.
