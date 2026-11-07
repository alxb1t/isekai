---
bump: minor
debt: [0106·R1]
---

# 0111 — deleting with its approval

Deleting a render's last image takes the newest approval back to its draft, and what another flow took from an
approval holds its own copy, so nothing holds that cancel.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review`, `image-generation`, `ui`, `cli`, `run-directory` |

```
1 the cancel   only the approval's own prompt, failure records and renders hold it
2 the checks   refuse_out_of_step and --in-step-with deleted
3 the copy     approve --from and a draft from another flow: no origin recorded, the seeds copied, once
4 the delete   the last render takes the newest approval back to its draft; only its own thumbnail goes
5 the page     no "from FLOW v1"; a drafted draft shows its image while the file exists
6 the record   docs D4, D38 superseded by D49, data-flow, principles, modules, README
```

## Why

**Deleting a render leaves its approval standing.** The Hub cell still reads *approved*, and the render dialog
offers to render the deleted seed again. *Cancel approve* is no way out: it is refused while another flow's copy or
draft names the approval. A copy that names its source makes the two flows depend on each other, so neither can be
undone alone.

## What Changes

- **The delete**: a discard that empties the newest approval's group, with no draft waiting above it, deletes that
  approval's prompt and failure records and cancels it with `review.cancel`'s code ([D1](design.md#d1)).
- **The cancel**: only the approval's own prompt, failure records and renders refuse it; another flow's copy, drafted
  approval or waiting draft never does ([D2](design.md#d2)).
- **`approve --from`** records `copied: true` and no `copied_from`, copies the source's seeds into the copy's renders
  once, and writes nothing over an equal copy ([D3](design.md#d3)).
- **A draft from another flow** records no `drafted_from`; naming no image, it carries the approval's seeds
  ([D4](design.md#d4)).
- **`refuse_out_of_step`**, `generate --in-step-with` and `render`'s check before the pod go ([D5](design.md#d5)).
- **Review**: the kicker *from FLOW v1* goes; a drafted draft shows the source image while its file exists, the
  photograph alone after ([D6](design.md#d6)).
- **Thumbnails**: a delete drops only the render's own, by its image digest, read before the unlink; this closes
  `0106·R1` ([D7](design.md#d7)).
- **The record**: docs D4 gains `withdraw`; D38 is superseded by a new D49; data-flow, principles, modules and
  README follow ([D8](design.md#d8)).
- Existing files carrying `copied_from` or `drafted_from` are left as they are ([D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review` — *An approval is copied from another flow's approval, recording where it came from*: removed; added as
  *An approval is copied once from another flow's approval, its seeds with it*.
- `review` — *An approval nothing derives from can be cancelled back to its draft*: removed; added as *An approval
  nothing of its own flow derives from can be cancelled back to its draft*.
- `review` — *A draft is written from another flow's approval, its own fields from its own sheet*: removed; added as
  *A draft is written once from another flow's approval, its own fields from its own sheet*.
- `image-generation` — *A render is discarded whole, and its approval is left short*: removed; added as *A render is
  discarded whole, and the newest approval goes with its last render*.
- `image-generation` — *A flow renders on another flow's seeds when the operator names it*: removed; added as *A flow
  renders on another flow's seeds when the operator names it, reading no copy's origin*.
- `image-generation` — *A control flow equals its subject flow but for the dials it zeroes*: links D49.
- `ui` — *Draft from this starts from an image, for any flow the app offers, and opens Review on the draft*: no source
  in the kicker; the image while its file exists.
- `ui` — *The large view deletes its render after asking, and the Hub opens on its cell*: the cell reads *draft*;
  only the render's own thumbnail goes.
- `cli` — *The discard verb deletes a render named by its image path*: the last render takes its approval.
- `run-directory` — *Artifacts are append-only and numbered, and re-running a command is a no-op*: the approval goes
  with its last render.
- `run-directory` — *The run directory is the input and its photograph's description above, and each flow's work
  below*: a render records its source; a copy holds its own.

## Impact

- Code: `isekai/foundation/artifacts.py`, `isekai/pipeline/review.py`, `isekai/pipeline/generate.py`,
  `isekai/interface/cli.py`, `isekai/interface/render.py`, `isekai/interface/ui/app.py`,
  `isekai/interface/ui/library.py`.
- UI: `ui/src/types.ts`, `ui/src/views/Review.vue`.
- Tests: `tests/test_review.py`, `tests/test_generate.py`, `tests/test_render.py`, `tests/test_pipeline_cli.py`,
  `tests/test_ui_api.py`, `tests/test_ui_library.py`, `tests/e2e/test_render.py`.
- Docs: `docs/decisions.md`, `docs/data-flow.md`, `docs/principles.md`, `docs/modules.md`, `README.md`.
- `flows/`, `config/`, `gpunit.toml` and every run-file kind's version are untouched.

## Not in this change

- A confirm that says the approval goes too: the confirm stays *Delete this render?* (brief Q6).
- An approval of count above one losing one render: it stays short by one, as today (brief Q5).
- Rewriting existing files' `copied_from` or `drafted_from`: left as they are (brief Q16).
- Copying the source image into a drafted flow: the photograph alone shows once it is gone (brief Q15).
- `--seeds-from`: it stays, its seeds read at render time.
