---
bump: minor
---

# 0104 — the ninth walkthrough

What the operator's ninth pass found, fixed in one version: the Render dialog shows the photographs it renders as
thumbnails, grouped by flow, and the tag list opens above an input near the sheet's foot.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
1 the thumbnails  thumbs.ts: a 96×128 thumbnail per source by flow, ×N above one, 15 then +n, the left-out by reason
                  RenderDialog: the groups, the photoUrl fallback, the collections in a max height · new classes only
2 the flip        placement.ts: below if it fits, else above if it fits, else the larger · TagInput measures .rows · .drop--above mirrored
3 the record      ui/design/spec.md: the J4·1 frame drawn with thumbnails
```

## Why

**The Render dialog reads as text, and the tag list hides past the sheet's foot.** The dialog names each photograph
by file name, version and count, so the operator reads names to know what will render. On Review's last rows the
tag list opens below its input, past the foot of the scrolling sheet, where its matches cannot be seen.

## What Changes

- **Each photograph the dialog renders is a thumbnail** at the hub's tile size, under its flow's name and count; `×N`
  only when it renders more than once; its file name and version on hover ([D1](design.md#d1), [D2](design.md#d2)).
- **The photographs left out are thumbnails too**, dimmed, grouped by reason and flow ([D1](design.md#d1)).
- **A flow shows 15 thumbnails, then `+n`**; the collections scroll in a max height, the estimate, the price and the
  buttons kept in view ([D1](design.md#d1), [D3](design.md#d3)).
- **A run that is not among the hub's sources** falls back to the run's own photograph ([D2](design.md#d2)).
- **The tag list opens above its input** when the room below it, to the sheet's foot, cannot hold it and the room
  above can, or is the larger; mirrored, row 1 nearest the input, the footer on top; the keys unchanged ([D4](design.md#d4), [D5](design.md#d5)).
- **The J4·1 frame** is drawn with thumbnails ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *Render is confirmed in a dialog that quotes what renders, its limit and its price at most*: the dialog
  shows what renders and what is left out as thumbnails grouped by flow, and gains a scenario.
- `ui` — *Tag suggestions are answered by the pipeline's own search*: the list opens above its input near the
  sheet's foot, and gains a scenario.

## Impact

- `ui/src/`: `components/RenderDialog.vue`, `components/TagInput.vue`, `components/TagAutocomplete.vue`,
  `views/ReviewHead.vue`, `app.css`; new `thumbs.ts`, `placement.ts`, `placement.test.ts` and
  `components/RenderDialog.test.ts`.
- `tests/e2e/`: `test_render.py`, `test_review.py`.
- `ui/design/spec.md`: the J4·1 frame.
- No backend, payload or type change; no decision in force; no dependency.

## Not in this change

- The estimate, the price, the keep-volume box and the keys: unchanged.
- The quote's payload and the backend.
- Removing a photograph from the session: its own version.
- The `.render-dialog` base rules `DraftDialog` and `ThemeDialog` share: untouched.
