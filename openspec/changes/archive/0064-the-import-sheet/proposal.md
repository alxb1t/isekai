---
version: v0.39.1
backlog: [0061·R15, 0061·R17]
---

# 0064 — the import sheet

A patch for what `v0.39`'s metered run found on the import sheet and on Home. Each file's tile shows its upload, then
its conversion, then its preview. Home's first start reads in the design's order. Two backlog cards close.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the read after the answer, the tile's states, the preview, Home, the cards |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
choose ─▶ PUT bytes ─▶ 202 (uploading 43% … 100%) ─▶ one reader, in upload order
                                                       └▶ /events?staging=<id>: waiting → converting → ready (preview)
```

## Why

**A tile is silent while its file converts.** The upload's request also reads the file, so the bar stops at 100% and
nothing moves until a HEIC is converted.

**A tile shows no picture.** The operator cannot see what was chosen until the batch's hub.

**Home's first start reads out of order.** *New batch* sits above the heading and the privacy line, not below them.

## What Changes

- **The upload is answered when its bytes land**; the server reads staged files one at a time and reports each on
  `/events?staging=<id>` ([D1](design.md#d1)).
- **A tile's states**: uploading, waiting, converting, then ready with its preview, refused or not cleaned
  ([D2](design.md#d2), [D3](design.md#d3)).
- **Home's first start**: heading, privacy line, then *New batch* ([D4](design.md#d4)).
- **The cards**: 0061·R15's scenario, 0061·R17's docstring ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *Sources are chosen in the file dialog, and each shows its own upload* — scenarios for the preview, the
    conversion's states and the answer before the read.
  - MODIFIED *A draft update states the version of the draft it replaces* — the SHALL names the approval it already
    holds to; a scenario for it.

## Impact

- **Code:** `isekai/interface/ui/app.py`, `isekai/pipeline/importing.py`, `ui/src/components/ImportSheet.vue`,
  `ui/src/views/Home.vue`.
- **Tests:** `tests/test_ui_api.py`, `tests/e2e/test_import.py`.

## Not in this change

- **The batch's sources on `/session`** — parked until a minor touches the session view.
- **`pod_start.py`'s comment** — waits for the next image rebuild.
- **Drag-and-drop** — parked.
