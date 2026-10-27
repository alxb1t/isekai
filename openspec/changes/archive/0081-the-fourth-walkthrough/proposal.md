---
version: v0.54
---

# 0081 — the fourth walkthrough

A draft written from an image records that image, and Review shows it beside the photograph — a revision's whatever
its seeds become, and a conjure draft's summon image.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the `image` record, its writers and its reader |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review` · `ui` |

```
Revise v2 · seed 9423…        ─▶ draft  producer.image {summon, 2, 9423…}  ─▶ approval keeps it
Conjure from this v1 · seed 7 ─▶ draft  producer.image {summon, 1, 7}      ─▶ Review: photograph │ that image
```

## Why

**Review finds a revision's image by its current seeds, and a conjure draft names no image.** Change a revision's
seed — a legal edit — and the image it revises vanishes once approved; *Conjure from this* opens Review on the
photograph alone, the summon image left behind.

## What Changes

- **`image: {flow, version, seed}`** — an optional key on a draft's producer, carried to its approval
  ([D1](design.md#d1)).
- **Its writers** — `revise` always; `draft_from` where the page names an image ([D2](design.md#d2)).
- **Its reader** — Review's revision and drafted payloads, with today's seed match as a revision's fallback
  ([D3](design.md#d3)).
- **The page** — the large view sends the seed; the source pane shows a conjure draft's image as a revision's
  ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`:
  - MODIFIED *A revision is a draft from the approval that made the image, its seed prefilled* — records the image.
  - MODIFIED *A draft is written from another flow's approval, its own fields from its own sheet* — records the image
    the operator names.
- `ui`:
  - MODIFIED *Revise starts from an image, and opens Review on its first draft* — the recorded image, whatever the
    seeds.
  - MODIFIED *Conjure from this drafts from an image's approval, and opens Review on it* — the image named and shown.

## Impact

- **Code:** `isekai/foundation/artifacts.py`, `isekai/pipeline/review.py`, `isekai/interface/drafting.py`,
  `isekai/interface/ui/app.py`, `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/views/RenderLarge.vue`,
  `ui/src/views/Review.vue`, `ui/src/components/SourcePanel.vue`.
- **Tests:** `tests/test_review.py`, `tests/test_ui_api.py`, `tests/e2e/test_render.py`.
- **Docs:** `ui/design/spec.md`.

## Not in this change

- **`review --from --seed`** — a CLI conjure draft names no image.
- **A format version** — `image` is an optional key.
- **The multi-batch render** — cut on its own.
