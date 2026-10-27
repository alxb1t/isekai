---
version: v0.58
---

# 0085 — draft from

From an image, a draft for any flow the app offers: its own flow is a revision, another a draft from its approved
sheet. *Draft from this* on `⇧D` and `isekai draft --flow` fold Revise and *Conjure from this* into one act.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the stage, the verb, the dialog, the waiting draft |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review` · `cli` · `ui` |

```
large view ⇧D ─▶ Draft from this: ▸ summon-anime-wai (revise) · summon-flat-anime-wai · conjure-anime-wai
   ↵ ─▶ isekai draft --flow <target> <image> ─▶ Review: the photograph │ the image it came from
```

## Why

**Revise and *Conjure from this* are one act with two names, two keys, two verbs and two routes.** Flat summon has a
photograph and summon's schema, so neither reaches it: Revise drafts its own flow alone, and *Conjure from this* only
a flow that reads a sheet alone. Every flow to come would need a third path.

## What Changes

- **The stage** — a revision replaces an unedited waiting draft; a draft from an image prefills its seed
  ([D1](design.md#d1), [D2](design.md#d2)).
- **The verb** — `isekai draft --flow FLOW <image>…`; `revise` and `review --from` go ([D3](design.md#d3)).
- **The page** — *Draft from this* `⇧D` and its dialog, every flow the app offers; one route; `⇧E` and `⇧F` go
  ([D4](design.md#d4), [D5](design.md#d5)).
- **The waiting draft** — an edited one opened on the page and refused by the verb, an unedited one replaced
  ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`:
  - MODIFIED *A revision is a draft from the approval that made the image, its seed prefilled* — an unedited waiting
    draft replaced.
  - MODIFIED *A draft is written from another flow's approval, its own fields from its own sheet* — the image's seed
    prefilled.
- `cli`:
  - REMOVED *The revise verb takes image paths, and writes every draft or none*.
  - REMOVED *The review verb drafts from another flow's approval with `--from`*.
  - ADDED *The draft verb drafts a flow from image paths, and writes every draft or none*.
- `ui`:
  - REMOVED *Revise starts from an image, and opens Review on its first draft*.
  - REMOVED *Conjure from this drafts from an image's approval, and opens Review on it*.
  - ADDED *Draft from this starts from an image, for any flow the app offers, and opens Review on the draft*.

## Impact

- **Code:** `isekai/pipeline/review.py`, `isekai/interface/drafting.py`, `isekai/interface/cli.py`,
  `isekai/interface/ui/app.py`, `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/views/RenderLarge.vue`,
  `ui/src/views/Renders.vue`, `ui/src/components/DraftDialog.vue` (new, replacing `ReviseConfirm.vue`).
- **Tests:** `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`, `tests/e2e/test_render.py`.
- **Docs:** `README.md`, `docs/data-flow.md`, `ui/design/spec.md`.

## Not in this change

- **`approve --from` and *control*** — a copied approval is another act.
- **A flow** — none changes; flat summon becomes a target as every offered flow does.
- **A format version** — the producer's keys are unchanged.
