---
version: v0.56
---

# 0083 — the multi-batch render

One render session renders a **batch** drawn from many collections: one quote, one pod, collection after collection.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the session, its records, the quote, the dialog, the drawer |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `cli` · `ui` |

```
Render (any collection's bar) ─▶ one dialog: ☑ 17oct summon 4 · conjure 2   ☑ 17oct_4 summon 3
                                  one estimate · one limit · one price at most   ⌘↵
   ─▶ isekai render 17oct/runs 17oct_4/runs ─▶ one pod ─▶ 17oct's lines, then 17oct_4's ─▶ teardown
        each collection: its images in its runs, its record in its sessions/, the session in its log
```

## Why

**A session renders one collection, so a second waits for its own pod boot and volume window.** One GPU can render
every collection short of images in one session, and the operator agrees to one price for all of it.

## What Changes

- **The verb** takes many collections' runs roots, in shortfall mode ([D1](design.md#d1)).
- **One limit** — one boot over every collection's images ([D2](design.md#d2)).
- **A record per collection**, sharing the id, naming the others; the log to each ([D3](design.md#d3)).
- **The quote and the dialog** — a row per collection, ticks, the ceiling ([D4](design.md#d4), [D5](design.md#d5)).
- **The drawer** — a grid per collection, stacked, moved through as one ([D6](design.md#d6)).
- **D36's accepted risk** — rewritten for every collection's photographs ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`:
  - MODIFIED *A render with no request renders every approval short of its count* — many runs roots, one session; a
    request refused beside a second.
  - MODIFIED *A render session's limit is estimated from its work, at most the configured ceiling* — one boot over
    every collection.
  - MODIFIED *A render session writes its record into the collection, from its start to its end* — a record per
    collection, sharing the id; the log to each.
- `ui`:
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — a row per
    collection, ticks, `+n in other collections`, the ceiling.
  - MODIFIED *The running render opens in a drawer every screen offers* — a grid per collection, stacked; `⇧I` the
    focused image's collection.

## Impact

- **Code:** `isekai/interface/render.py`, `isekai/interface/cli.py`, `isekai/foundation/artifacts.py`,
  `isekai/interface/ui/app.py`, `isekai/interface/ui/jobs.py`, `ui/src/api.ts`, `ui/src/types.ts`,
  `ui/src/sessions.ts`, `ui/src/stores/live.ts`, `ui/src/stores/drawer.ts`, `ui/src/components/RenderBar.vue`,
  `ui/src/components/RenderDialog.vue`, `ui/src/components/SessionDrawer.vue`.
- **Tests:** `tests/test_render.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `ui/src/sessions.test.ts`,
  `ui/src/stores/drawer.test.ts`, `ui/src/stores/live.test.ts`, `tests/e2e/test_render.py`.
- **Docs:** `docs/decisions.md` (D36), `README.md`, `docs/data-flow.md`, `ui/design/spec.md`.

## Not in this change

- **Explicit requests across collections** — `<flow>=<count|source>` stays one runs root's.
- **gpunit, the pod's image, a flow** — unchanged.
- **Clearing ComfyUI's history between collections** — D35's boundary holds every collection alike.
