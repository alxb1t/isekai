---
version: v0.42
backlog: [0064·R3, 0064·R2, 0064·R10, 0067·R10, 0067·R11, 0067·R12, 0067·R13, 0067·R14]
---

# 0068 — the store

One owner of the page's event stream, and one owner of the open batch's state, on Pinia. Every screen of a batch
reads the same hub, and sees its cells change as Prepare runs.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the live store, the stream it watches, the batch store, the upload id, the cards |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
route batch ──┐                      ┌─▶ live store   job · billing · now · files
open import ──┴─▶ /events?batch&staging ─┤
                  (one per page)         └─▶ batch store  hub · running · refusals · renders · offer
                                                 ▲
                              hub · Review · Renders · AppHeader · BatchRail
```

## Why

**A page holds up to three event streams.** The shell, the hub and the import sheet each open their own. A browser
allows six connections per host, so two tabs with an import open stall.

**The batch is fetched in three places.** The hub, Review and Renders each hold their own copy, and only the hub's
follows Prepare live.

**Two uploads of one name share one state**, and an upload can land while Import commits (`0064·R3`, `0064·R2`).

## What Changes

- **Pinia** — the dependency, pinned ([D1](design.md#d1)).
- **The live store** — the job slot, billing, the clock, the actions on them, and the only `EventSource`
  ([D2](design.md#d2)).
- **The stream follows the page** — the route's batch and the open import, one connection ([D3](design.md#d3)).
- **The batch store** — the hub, its running cells and refusals, the renders, the Render offer ([D4](design.md#d4)).
- **What stays per screen** ([D5](design.md#d5)).
- **The upload id** — each upload's own state; no upload once a commit begins ([D6](design.md#d6)).
- **The cards** — `0064·R10`, `0067·R10`–`R14` ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *The page is told of a job as it runs* — a page holds one event stream, following its batch and its
    open import.
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — the bar
    shows the newest offer asked for, whatever order the answers arrive in.
  - MODIFIED *Sources are chosen in the file dialog, and each shows its own upload* — each upload has its own state;
    an upload after Import is pressed is refused; a failed read refuses its file alone.
  - MODIFIED *The Renders view shows each source's images by flow and version* — an image Pillow cannot read is
    refused, naming it.

## Impact

- **Code:** `ui/package.json`, `ui/package-lock.json`, `ui/src/main.ts`, `ui/src/App.vue`, `ui/src/bars.ts`,
  `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue`, `ui/src/views/Review.vue`, `ui/src/views/Session.vue`,
  `ui/src/components/ImportSheet.vue`, `ui/src/components/RenderBar.vue`, `ui/src/components/RenderDialog.vue`,
  `ui/src/composables/useQueue.ts`; new `ui/src/stores/live.ts`, `ui/src/stores/batch.ts`; deleted
  `ui/src/composables/useLive.ts`, `ui/src/composables/useRenderOffer.ts`; `isekai/pipeline/importing.py`,
  `isekai/interface/ui/app.py`, `isekai/shared/image.py`.
- **Tests:** new `ui/src/stores/live.test.ts`, `ui/src/stores/batch.test.ts`; `ui/src/composables/useQueue.test.ts`,
  `tests/test_importing.py`, `tests/test_ui_api.py`, `tests/test_ui_library.py`.
- **Docs:** `ui/design/spec.md`, `isekai/interface/ui/README.md`.

## Not in this change

- **The key registry** — the per-view listeners and the `⌥` keys stay.
- **Review's layout, rail and dialogs.**
- **Sessions** — the session record, its tab, a running indicator.
- **The job runner** — `0063·R17` waits for the next change to it.
- **A second job slot.**
- **The server's stream** — it already takes a batch and an import on one connection.
