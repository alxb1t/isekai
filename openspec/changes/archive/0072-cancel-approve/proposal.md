---
version: v0.45
backlog: [0070·R11]
---

# 0072 — cancel approve

An approved sheet nothing has been made from goes back to its draft. The review stage gains `cancel` and
`cancellable`; `isekai approve --cancel` runs it; Review's approve bar offers *Cancel approve*.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | what derives, what may be cancelled, the act, the verb, the button |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review` · `cli` · `ui` |

```
review/002.approved.json ──cancel──▶ review/002.draft.json      while nothing derives from 002
        │ derives
        ├─ prompts/002…          ─┐
        ├─ outputs/002/…          ├─▶ refused, naming it and the way on
        └─ control's copy of 002 ─┘
```

## Why

**An approval cannot be taken back.** An approve pressed too early leaves `review --new-version`, a new number
above an approval that would still render.

**Approve now stays on the sheet**, so the sheet just approved is right there to take back.

## What Changes

- **What derives** from an approval, and what may be cancelled ([D1](design.md#d1), [D2](design.md#d2)).
- **The act** — the draft written from the approval, then the approval deleted ([D3](design.md#d3)).
- **`isekai approve --cancel`** ([D4](design.md#d4)).
- ***Cancel approve*** in the approve bar, with its reason when it cannot ([D5](design.md#d5)).
- **The card** — `0070·R11`, a refused discard outliving an approval ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`:
  - ADDED *An approval nothing derives from can be cancelled back to its draft* — the act and every refusal.
- `cli`:
  - ADDED *The approve verb cancels an approval with `--cancel`* — each run answered on its own.
- `ui`:
  - MODIFIED *Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet*
    — an approved sheet offers *Cancel approve*, or the reason it cannot.

## Impact

- **Code:** `isekai/pipeline/review.py`, `isekai/interface/cli.py`, `isekai/interface/ui/app.py`, `ui/src/api.ts`,
  `ui/src/types.ts`, `ui/src/views/Review.vue`, `ui/src/components/ApproveBar.vue`.
- **Tests:** `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`, `tests/e2e/test_queue.py`,
  `tests/e2e/conftest.py`.
- **Docs:** `ui/design/spec.md`, `README.md`.

## Not in this change

- **Cancelling a rendered approval** — Revise is the way on.
- **Re-opening above an approval** — `review --new-version` stays as it is.
- **A format change** — the draft and the approval keep their kinds.
