---
version: v0.59
---

# 0086 — compare any image

`c` on a render's large view compares the image with any image of its source — any flow's, or the photograph — picked
in a grid of the source. *Side by side* folds in as the photograph's compare.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the pick, the route, the view |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
large view · summon v2 · seed 9423   c ─▶  photo                  [▣]
                                           summon-anime-wai       [v1][v2·][v3]
                                           summon-flat-anime-wai  [v1]
                                       ↵ ─▶ Compare: the image picked │ summon v2 · seed 9423
```

## Why

**Compare reaches one cell, and the photograph is a separate act.** With a draft from any flow, the comparison the
operator wants is across flows — summon beside flat summon — and Compare cannot make it.

## What Changes

- **The pick** — a grid of the source: the photograph's row, a row per flow; `h j k l` and the arrows
  ([D1](design.md#d1), [D2](design.md#d2)).
- **The route** — names the image picked by flow, version and seed, or the photograph ([D3](design.md#d3)).
- **The view** — the image picked left, the one compare started from right; shared fields across flows; the
  photograph's pair alone ([D4](design.md#d4)).
- ***Side by side* leaves the large view** ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - REMOVED *A version says what it was, and Compare shows a seed's two versions*.
  - ADDED *A version says what it was, and Compare sets an image beside any image of its source* — the pick of the
    source, the order, across flows, the photograph.

## Impact

- **Code:** `isekai/interface/ui/app.py`, `ui/src/router.ts`, `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/cells.ts`,
  `ui/src/views/RenderLarge.vue`, `ui/src/views/Compare.vue`, `ui/src/components/ComparePick.vue`.
- **Tests:** `tests/test_ui_api.py`, `ui/src/cells.test.ts`, `tests/e2e/test_render.py`.
- **Docs:** `ui/design/spec.md`.

## Not in this change

- **Across sources** — one source's images only.
- **Review's `⌃P` *Side by side*** — unchanged.
- **A flow** — none changes.
