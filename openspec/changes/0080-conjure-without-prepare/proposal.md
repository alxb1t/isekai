---
version: v0.53
---

# 0080 — conjure without Prepare

`⇧F` on any summon image drafts conjure and opens Review, with no tick, no Prepare and no tagging first. Where conjure
holds no sheet, its sheet is filled from summon's tag list.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the sheet from another flow's tags, the drafting sequence, the page |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `sheet` · `cli` · `ui` |

```
⇧F on a summon image
   ├─ conjure holds an edited waiting draft ─▶ open it, write nothing
   ├─ conjure holds no sheet ─▶ assign · sheet from summon's tag list · draft from summon's approval
   └─ else ─────────────────────────────────▶ draft from summon's approval, as today
                                               ─▶ Review on conjure's draft
```

## Why

**Conjure from this works only where conjure was ticked and prepared.** On a batch with conjure on one source of six,
the button shows on all six and refuses five, naming a command with the library's path, then Prepare. Both flows tag
with the same pinned model, so conjure's Prepare re-runs what summon already ran.

## What Changes

- **A sheet from another flow's tags** — the sheet stage reads the named source's tag list, recording it
  ([D1](design.md#d1)).
- **The drafting sequence** — `review --from` and the page assign, fill and draft in one act ([D2](design.md#d2)).
- **An edited waiting draft is opened**, not refused, on the page ([D3](design.md#d3)).
- **Every offered sheet-alone flow is a target**, assigned or not ([D4](design.md#d4)).
- **The drafted marks stay after approve** ([D5](design.md#d5)); **the source's caption** shows where the target has
  none ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sheet`:
  - ADDED *A sheet is filled from another flow's tag list when the operator names it* — the routing and the record.
- `cli`:
  - MODIFIED *The review verb drafts from another flow's approval with `--from`* — a target with no sheet is
    assigned and filled first.
- `ui`:
  - MODIFIED *A missing caption is shown with the command that writes it* — the caption of the flow the sheet's tags
    came from.
  - MODIFIED *Conjure from this drafts from an image's approval, and opens Review on it* — every offered target; the
    sequence; an edited waiting draft opened; the marks after approve.

## Impact

- **Code:** `isekai/foundation/artifacts.py`, `isekai/pipeline/sheet.py`, `isekai/pipeline/review.py`,
  `isekai/interface/drafting.py` (new), `isekai/interface/cli.py`, `isekai/interface/ui/app.py`,
  `ui/src/types.ts`, `ui/src/views/RenderLarge.vue`, `ui/src/views/Review.vue`, `ui/src/components/SourcePanel.vue`.
- **Tests:** `tests/test_sheet_stage.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`,
  `tests/e2e/conftest.py`, `tests/e2e/test_render.py`.
- **Docs:** `README.md`, `docs/data-flow.md`, `ui/design/spec.md`.

## Not in this change

- **Ollama or the tagger for the target** — neither runs; the source's tags and caption serve.
- **The review stage's refusals** — the stage still refuses a target with no sheet; the verb fills it first. The
  CLI's `review --from` still refuses an edited waiting draft.
- **`approve --from` and *control*** — unchanged.
- **Every refusal's wording** — only the no-sheet refusal leaves the page; the rest when the spec audit reads them.
