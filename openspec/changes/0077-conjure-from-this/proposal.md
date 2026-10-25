---
version: v0.50
---

# 0077 — conjure from this

A conjure draft starts from the summon approval that made an image, so its tags are not corrected twice. The review
stage gains `draft_from`; `isekai review --from` runs it; the large view offers *Conjure from this*.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the draft, its producer, the refusals, the verb, the button, Review's marks |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review` · `cli` · `ui` |

```
summon-anime-wai/review/001.approved.json ─┐ every field both flows hold
conjure-anime-wai/sheets/001.json ─────────┤ conjure's own fields
                                           ▼
conjure-anime-wai/review/NNN.draft.json   producer: source sheets, drafted_from {summon-anime-wai, 1}
        │ the operator finishes it, then approves
        ▼
conjure-anime-wai/review/NNN.approved.json   an ordinary approval, not a copy
```

## Why

**The operator corrects summon's sheet, then corrects the same tags again in conjure.** Conjure's schema holds every
summon field by name, and adds its own. `approve --from` copies a whole approval and leaves no draft to finish, so it
cannot carry conjure's own fields.

## What Changes

- **A draft from another flow's approval** — the shared fields from the source, the target's own from its sheet
  ([D1](design.md#d1)).
- **Its producer** names the source in `drafted_from`; its approval is ordinary ([D2](design.md#d2)).
- **The refusals** — no sheet, a waiting edited draft, no such approval, the source as a target
  ([D3](design.md#d3)).
- **`isekai review --from FLOW [--version N]`** ([D4](design.md#d4)).
- ***Conjure from this*** `f` on the large view, for each flow drafted from a sheet alone ([D5](design.md#d5),
  [D6](design.md#d6)).
- **Review's marks** against the target's sheet, and *Discard draft* on such a draft ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`:
  - ADDED *A draft is written from another flow's approval, its own fields from its own sheet* — the fields, the
    producer, every refusal.
- `cli`:
  - ADDED *The review verb drafts from another flow's approval with `--from`* — the default approval, the options it
    refuses.
- `ui`:
  - ADDED *Conjure from this drafts from an image's approval, and opens Review on it* — the targets, the act, the
    marks.

## Impact

- **Code:** `isekai/foundation/artifacts.py`, `isekai/pipeline/review.py`, `isekai/interface/cli.py`,
  `isekai/interface/ui/app.py`, `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/views/RenderLarge.vue`,
  `ui/src/views/Review.vue`.
- **Tests:** `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`, `tests/e2e/conftest.py`,
  `tests/e2e/test_render.py`.
- **Docs:** `README.md`, `docs/data-flow.md`, `ui/design/spec.md`.

## Not in this change

- **`approve --from` and *control*** — they stay as they are.
- **Conjure into summon from the UI** — summon reads a photograph, so it is no target; the verb still takes it.
- **A format version** — `drafted_from` is an optional key of the producer.
- **A confirm before the draft** — the draft is one *Discard draft* away, and costs nothing.
