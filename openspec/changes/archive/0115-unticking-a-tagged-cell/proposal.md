---
bump: patch
version: 0.75.2
---

# 0115 — unticking a tagged cell

A *tagged* cell whose flow directory is empty can be unticked, by its tick and by Discard. The server's refusal of a
directory holding work stays the guard. No format, verb or product moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision and the test cost |
| [tasks](tasks.md) | the phases, in build order |
| `specs/ui/spec.md` | the hub requirement, its untick and its click |

```
1 the untick   cells.ts: tagged ticks · pending and locked · Hub.vue's Discard and tick · the tests
2 the prose    the design spec's tick and click · the UI README · api.ts's comment
```

## Why

**A tagged cell with no work is stuck.** A cell reads *tagged* from the photograph's tag list, which every flow shares
([D17](../../../docs/decisions.md#d17--input-above-flow-below)). So a flow assigned to a tagged photograph reads
*tagged* at once, and so does a flow whose last render was deleted
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)). The
Prepare bar counts it as waiting, but neither its tick nor Discard takes it back: the page locks every cell past
*assigned*. The server would accept the untick: `assign --remove` refuses only a directory that holds files.

## What Changes

- **A click or `↵` on a tagged cell ticks**, as on an assigned one; an unreadable cell still does nothing
  ([D1](design.md#d1)).
- **`pending` and `locked` move to `ui/src/cells.ts`.** A cell is pending while assigned or tagged; a cell is locked
  past pending. The tick, Discard and the Prepare bar's count all read them ([D2](design.md#d2)).
- **Discard unticks every pending cell**, assigned or tagged, as its comment already says ([D2](design.md#d2)).
- **The tick's accent fill marks a pending cell**, so the fill still means "can be unticked" ([D3](design.md#d3)).
- **The server is unchanged.** Its refusal of a flow directory holding work is the guard ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The hub shows each source's stage in each offered flow, and a tick assigns it*: an untick, by the tick or by
  Discard, is allowed while the cell is assigned or tagged, the verb refusing a directory that holds work; a click
  ticks a tagged cell; *a prepared cell's tick stays* names a directory holding work; a scenario is added, *a tagged
  cell with no work unticks*.

The fix stays a patch: the `cli` requirement's `--remove` already deletes a flow's directory "only while it is empty",
and the Prepare bar already counts a tagged cell as waiting. The hub's rule now meets both.

## Impact

- `ui/src/cells.ts`, `ui/src/cells.test.ts`, `ui/src/views/Hub.vue`, `ui/src/app.css`.
- `tests/test_ui_api.py`.
- `ui/design/spec.md`, `isekai/interface/ui/README.md`, `ui/src/api.ts`.

## Not in this change

- **The stage word.** A tagged cell with an empty directory still reads *tagged*; showing *assigned* there is left out
  (brief Q4).
- **The delete.** Deleting a flow's last render keeps the flow assigned, per
  [D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files); one
  Discard press clears it (brief Q2).
- **The server's guard.** `assign --remove` and `POST /api/c/{collection}/assign` are unchanged.
