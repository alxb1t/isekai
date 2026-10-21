---
version: v0.40
backlog: [0063·R19, 0064·R4, 0064·R5]
---

# 0065 — revise

A render you mostly like goes back to a draft from the approval that made it, its seed prefilled. The operator edits
the sheet, approves, renders, and Compare shows the before and the after on the same composition.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | `revise`, the selection check, discard, the unchanged refusal, the version header, Compare |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review` · `cli` · `ui` |

```
outputs/001/1840266731.png ─▶ revise ─▶ review/003.draft.json  (fields of 001, seeds [1840266731])
                                         │ edit · approve
                                         ▼
                      outputs/003/1840266731.png ─▶ Compare: 001 ⇄ 003, the changed fields
```

## Why

**A new draft starts from the newest approval only.** An image from an older version cannot be revised from the
sheet that made it.

**A re-render draws a new seed.** The effect of one tag edit is lost in a new composition.

**Renders shows versions, not what changed.** Nothing puts two versions of one seed side by side.

## What Changes

- **`review.revise`** — a draft from the image's own approval, its seed listed ([D1](design.md#d1)).
- **`isekai revise <image.png> …`** — every draft or none ([D2](design.md#d2)).
- **`review --discard`** — the highest draft, only while unapproved ([D3](design.md#d3)).
- **Approve refuses an unchanged revision** ([D4](design.md#d4)).
- **The version header and Compare** — revision or re-roll, from the producer; the pair by seed
  ([D5](design.md#d5), [D6](design.md#d6)).
- **The UI**: Revise from the large view and the grid, its confirm and refusals, Review of a revision, the queue,
  Compare ([D7](design.md#d7)).
- **The cards**: 0063·R19's duplicate step dropped; 0064·R4 and R5's stream test made sure ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`:
  - ADDED *A revision is a draft from the approval that made the image, its seed prefilled*.
  - ADDED *Approval refuses a revision that would reproduce its images*.
  - ADDED *An unapproved draft can be discarded*.
- `cli`:
  - ADDED *The revise verb takes image paths, and writes every draft or none*.
- `ui`:
  - ADDED *Revise starts from an image, and opens its drafts as a queue*.
  - ADDED *A version says what it was, and Compare shows a seed's two versions*.

## Impact

- **Code:** `isekai/pipeline/review.py`, `isekai/interface/cli.py`, `isekai/interface/ui/app.py`,
  `ui/src/views/RenderLarge.vue`, `ui/src/views/Renders.vue`, `ui/src/views/Review.vue`, a new
  `ui/src/views/Compare.vue`, `ui/src/router.ts`.
- **Tests:** `tests/test_review.py`, `tests/test_ui_api.py`, `tests/e2e/test_render.py`.
- **Docs:** `README.md`, `docs/data-flow.md`.

## Not in this change

- **Revise from the hub** — the image is where the decision is made.
- **`control`** — its approval is copied from summon's.
- **The batch's sources on `/session`** — parked.
- **The other open cards** — a paydown patch after this.
