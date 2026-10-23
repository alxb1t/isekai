---
version: v0.44
backlog: [0065·R15, 0065·R17, 0061·R8, 0061·R16]
---

# 0070 — review

The Review screen as the design draws it. It has an address of its own and a rail of every sheet not yet rendered.
Approve stays on the sheet, the old header goes, a revision's pair sits on one line, ④ is one slot per image beside
the sheet, and the images open in the viewer.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the address and its head, `short`, the rail, Approve, the layout, ④, the dialogs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` · `review` |

```
/b/<batch>/review ─▶ the head ─▶ replace ─▶ /b/<batch>/review/<digest>/<flow>
                       │ none
                       ▼
               No sheet waits for review · [ Hub ]

rail │ ① PHOTOGRAPH · 1073×1406  RENDER BEING REVISED · seed 5  Side by side ⇧C │ ③ SHEET — DRAFT │ ④
○ ◐  │ [photograph]              [render]                                     │ hair_colour …   │ [−] 2 [+]
● ◌  │                                                                        │ [Discard][Appr…]│ 1 [144] 2 [random]
```

## Why

**Review is a queue.** Approve leaves the sheet for the next one, and the hub after the last. The rail drops a sheet
once it is approved, though its legend lists *approved*.

**There is no batch-level address.** The Review tab has nowhere to point, and the hub carries *Review next*.

**The old header shows file names**, and a revision's render drops below the photograph.

**④ is a list of chips.** A typed seed becomes one only on `Enter`, so nothing seems connected; two equal seeds pass
the server.

## What Changes

- **The address** — `/b/<batch>/review` opens the head; the tab counts the unapproved; *Review next* goes
  ([D1](design.md#d1)).
- **`short`** — what a cell's newest approval lacks, counted by the render stage ([D2](design.md#d2)).
- **The rail** — every sheet not yet rendered ([D3](design.md#d3)).
- **Approve stays** — the sheet stays open, read-only; Revise's queue goes ([D4](design.md#d4)).
- **The layout** — the header's parts move, the revision pair sits on one line, Discard joins the approve bar
  ([D5](design.md#d5), [D6](design.md#d6)).
- **④** — one slot per image, beside the sheet; a repeated seed refused ([D7](design.md#d7)).
- **The dialogs** — the photograph and the render in the viewer; *Side by side* ([D8](design.md#d8)).
- **The cards** — `0065·R15`, `0065·R17`, `0061·R8`, `0061·R16` ([D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - REMOVED *Review is a queue of unapproved sheets, and opening one writes its draft* — replaced below.
  - ADDED *Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the
    sheet* — the head, the empty state, the rail, `short`, Approve staying, ④'s slots, the viewer.
  - REMOVED *Revise starts from an image, and opens its drafts as a queue* — replaced below.
  - ADDED *Revise starts from an image, and opens Review on its first draft* — the rest in the rail; the pair on one
    line; Discard asks in the approve bar; *Side by side*.
  - MODIFIED *Every screen has a URL naming its batch and its run* — `/b/<batch>/review` opens the head.
  - MODIFIED *The page's save state is true to the requests in flight, and a pending edit is sent on leaving* — an
    approval waits for the save in flight.
- `review`:
  - MODIFIED *A draft carries how many images to render and which seeds, and approval checks them* — a repeated seed
    is refused.

## Impact

- **Code:** `isekai/foundation/artifacts.py`, `isekai/interface/ui/library.py`, `isekai/interface/ui/app.py`,
  `ui/src/router.ts`, `ui/src/App.vue`, `ui/src/types.ts`, `ui/src/views/Review.vue`, `ui/src/views/Hub.vue`,
  `ui/src/composables/useQueue.ts`, `ui/src/composables/useSheet.ts`, `ui/src/components/BatchRail.vue`,
  `ui/src/components/SheetHeader.vue`, `ui/src/components/SourcePanel.vue`, `ui/src/components/ApproveBar.vue`,
  `ui/src/components/RendersBlock.vue`, `ui/src/components/ImageViewer.vue`, `ui/src/app.css`; new
  `ui/src/views/ReviewHead.vue`, `ui/src/slots.ts`; deleted `ui/src/components/AppHeader.vue`,
  `ui/src/components/PhotoOverlay.vue`.
- **Tests:** `tests/test_review.py`, `tests/test_ui_library.py`, `tests/test_ui_api.py`, `tests/e2e/test_queue.py`,
  `tests/e2e/test_render.py`, `tests/e2e/test_review.py`, `ui/src/composables/useQueue.test.ts`,
  `ui/src/composables/useSheet.test.ts`; new `ui/src/slots.test.ts`.
- **Docs:** `ui/design/spec.md`, `README.md`, `isekai/interface/ui/README.md`.

## Not in this change

- **Cancel approve** — an approved, unrendered sheet back to its draft; its own change.
- **Sessions; the job runner; a second job slot.**
- **A source's own name in Review's labels** — the digest stays the run's display name.
- **`0065·R14`** — its trigger is the revise refusals.
