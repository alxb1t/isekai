---
version: v0.44.1
backlog: [0070·R3, 0070·R4, 0070·R5, 0070·R6, 0070·R7, 0070·R16, 0070·R18, 0070·R19, 0070·R21]
---

# 0071 — the review patch

The cards `v0.44.0` shipped with open past their *before release* trigger, paid. The living spec, the README and
three comments say what the code does; Revise's promise about the rail is narrowed to one flow; and a test opens a
batch's Review address.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each card's fix, the erratum, the route steps |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` · `review` |

## Why

**The text and the code disagree.** The spec says the page names the approved artifact, that the rail holds "only"
unrendered sheets, that a closing page always asks, and that Revise's other drafts wait in the rail; a `review` SHALL
lost its "or". The README and comments describe the queue and the header line `v0.44.0` removed.

**`/b/<batch>/review` is untested.** Its replace and its empty page run in no test.

## What Changes

- **The living spec** — the approved input, the save state, Revise and the seeds requirement say what holds
  ([D1](design.md#d1)).
- **The README and comments** — Approve stays; refusals land in the approve bar ([D2](design.md#d2)).
- **The route test** — the reload test opens a batch's Review, then one with nothing waiting ([D3](design.md#d3)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *An approved input is read-only on the surface until it is re-opened* — the page states the approval and
    when, no path; the rail holds the unrendered sheets and the one open (`0070·R3`, `0070·R18`).
  - MODIFIED *The page's save state is true to the requests in flight, and a pending edit is sent on leaving* — a
    closing page asks only while an edit waits behind a save in flight (`0070·R19`).
  - MODIFIED *Revise starts from an image, and opens Review on its first draft* — the others of its flow in the rail
    (`0070·R6`).
  - MODIFIED *Every screen has a URL naming its batch and its run* — the reload scenario covers the replace and the
    empty page (`0070·R16`).
- `review`:
  - MODIFIED *A draft carries how many images to render and which seeds, and approval checks them* — its "or"
    restored (`0070·R7`).

## Impact

- **Code:** comments in `ui/src/composables/useSheet.ts`, `ui/src/views/Review.vue`, `ui/src/components/TagInput.vue`.
- **Tests:** `tests/e2e/test_routes.py`.
- **Docs:** `README.md`.

## Not in this change

- **Revise across flows** — the rail still holds one flow; the promise is narrowed instead.
- **The other `0070` cards** — their triggers are later changes.
