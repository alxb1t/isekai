---
version: v0.60
---

# 0087 — the fifth walkthrough

What the operator's fifth pass over the UI found, fixed in one version: the Render bar while a session runs, a
restored focus scrolled into view, `⇧C` for Compare, the pick's captions, Compare as big as the window, and `h` `l`
on the large view.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
1 the bar and the scroll   the session's totals while it runs · a restored focus in view
2 the keys and the pick    ⇧C · a plain letter moves, a command is ⇧ + a letter · captions vN, the head the full name
3 compare                  the pair and its heads alone, as big as the window, centred
4 the large view's steps   h l through the screen's renders, 2 of 5
```

## Why

**A pass over every screen found what reads wrong or costs a step.** The bar says *ready* of images already
rendering; a return lands scrolled away from its focus; Compare is the last plain-letter command; a 64-bit seed breaks
the pick; Compare's text crowds its images; the large view cannot step to the next image.

## What Changes

- **The Render bar** while a session runs ([D1](design.md#d1)); **a restored focus** scrolled into view
  ([D2](design.md#d2)).
- **`⇧C`** and the key rule ([D3](design.md#d3)); **the pick's captions and head** ([D4](design.md#d4)).
- **Compare** — the pair and its heads alone ([D5](design.md#d5)).
- **`h` `l` on the large view** ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — the bar
    while a session runs.
  - MODIFIED *The Renders view shows each source's images by flow and version* — `h` `l` on the large view; a
    restored focus centred.
  - MODIFIED *The hub shows each source's stage in each offered flow, and a tick assigns it* — a restored focus
    centred.
  - MODIFIED *Every command has one key, declared once, and none fires while typing* — a plain letter moves, a command
    is `⇧` + a letter.
  - MODIFIED *A version says what it was, and Compare sets an image beside any image of its source* — `⇧C`; the pick's
    captions and head; the pair alone.

## Impact

- **Code:** `isekai/interface/ui/app.py`, `ui/src/bars.ts`, `ui/src/cells.ts`, `ui/src/app.css`,
  `ui/src/components/RenderBar.vue`, `ui/src/components/ComparePick.vue`, `ui/src/views/Renders.vue`,
  `ui/src/views/Hub.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/views/Compare.vue`, `ui/src/types.ts`.
- **Tests:** `tests/test_ui_api.py`, `ui/src/bars.test.ts`, `ui/src/cells.test.ts`, `tests/e2e/test_render.py`.
- **Docs:** `docs/decisions.md` (D25), `ui/design/spec.md`.

## Not in this change

- **`isekai ui` from any directory** — the isekai command, a version of its own.
- **The render job, the drawer, the CLI** — unchanged.
