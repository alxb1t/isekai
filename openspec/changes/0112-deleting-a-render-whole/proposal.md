---
bump: minor
---

# 0112 — deleting a render whole

Deleting an approval's last render deletes the approval and what it alone held, down to the sheet once no approval is
left, and every flow holds its own files: a draft from another flow's image keeps a copy of that image, and a copy of an
approval sits on the target's own sheet.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review`, `image-generation`, `ui`, `cli`, `run-directory`, `sheet` |

```
1 the source copy   a draft from another flow's image copies it into the flow's own sources/
2 the page          Review shows that copy, headed "the image it was drafted from"
3 the discard       a discard takes the draft and its copy alone; no tags_from, no undo of the flow
4 the copy's sheet  approve --from fills the target's sheet first, and the copy names it
5 the delete        the last render takes its approval, older render-less ones and a waiting draft; none left, the sheets
6 the record        docs D4, D49 and a new D50; data-flow, principles, README
```

## Why

**Under `0111`, deleting a render left the flow on show.** The last render cancelled its approval back to a draft, so
the Hub read *draft* and Review offered *Approve sheet*; older approvals with no render kept the cell at *approved*;
and discarding a drafted flow's draft left empty `prompts/` and `outputs/` behind. The operator expects a deleted render
to leave nothing to review, and no flow to reference another's files.

## What Changes

- **The delete**: an approval's last render deletes that approval, its prompt, its failure records and its source copy,
  every older approval with no render left, and, when it was the newest, the draft waiting above it. Nothing goes back
  to a draft ([D1](design.md#d1)).
- **A flow with no approval left** loses its sheets, prompts, reviews and source copies too, and keeps its empty
  directory: the assignment. The photograph's tags and caption stay ([D1](design.md#d1)).
- **The source copy**: *Draft from this* into another flow copies the image into that flow's `sources/`, named by the
  draft's number. It is never one of the flow's renders, and the draft records no image of another flow
  ([D2](design.md#d2)).
- **Review** shows the source copy beside the photograph, headed *the image it was drafted from*, served by a new route
  ([D3](design.md#d3)).
- **The discard** of a draft deletes it and its source copy alone; the flow stays, and its sheet with it
  ([D4](design.md#d4)).
- **No cross-flow record**: a sheet no longer records `tags_from`; old files keep it, unread, and a drafted sheet is
  weighed against a newer tag list like any other ([D5](design.md#d5)).
- **`approve --from`** fills a target with no sheet from the photograph's tags first, and the copy names the target's
  newest sheet, so a revision of the copy compares against it ([D6](design.md#d6)).
- **The record**: docs D4 and D49 edited, D50 added; data-flow, principles, README and `interface/README.md` follow
  ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation` — *A render is discarded whole, and the newest approval goes with its last render*: removed; added
  as *A render is discarded whole, and its approval goes with its last render*.
- `review` — *An unapproved draft can be discarded*: removed; added as *An unapproved draft can be discarded, with its
  source copy and nothing else*: no flow is unassigned.
- `review` — *An approval is copied once from another flow's approval, its seeds with it*: the copy names the target's
  own sheet; the verb fills a target with none first.
- `review` — *A draft is written once from another flow's approval, its own fields from its own sheet*: removed; added
  as *A draft is written once from another flow's approval, holding its own fields, seeds and image*: a named image is
  copied into the target's sources, never recorded.
- `ui` — *Draft from this starts from an image, for any flow the app offers, and opens Review on the draft*: Review
  shows the source copy, which outlives the source image.
- `ui` — *The large view deletes its render after asking, and the Hub opens on its cell*: the cell reads *tagged* once
  the flow's last approval goes.
- `cli` — *The discard verb deletes a render named by its image path*: the last render takes its approval, and the
  flow's sheets once none is left.
- `cli` — *The draft verb drafts a flow from image paths, and writes every draft or none*: the target holds a copy of
  the image.
- `run-directory` — *Artifacts are append-only and numbered, and re-running a command is a no-op*: the approval goes
  with its last render; nothing returns to a draft.
- `run-directory` — *The run directory is the input and its photograph's description above, and each flow's work
  below*: a flow's `sources/`; no flow names another's files.
- `sheet` — *The stage fills fields from the tag list of a flow that declares the tagger, and leaves them empty for a
  flow that declares none*: removed; added as *…, leaves them empty for a flow that declares none, and names no other
  flow*: a first sheet a draft writes records no source.
- `sheet` — *A kept sheet filled from a tag list older than the photograph's newest is named*: removed; added as *…,
  whoever filled it*: a sheet a draft wrote is weighed like any other.

## Impact

- Code: `isekai/foundation/run.py`, `isekai/foundation/artifacts.py`, `isekai/pipeline/review.py`,
  `isekai/pipeline/sheet.py`, `isekai/interface/drafting.py`, `isekai/interface/cli.py`,
  `isekai/interface/run_view.py`, `isekai/interface/ui/app.py`.
- UI: `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/views/Review.vue`, `ui/src/components/SourcePanel.vue`.
- Tests: `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`, `tests/test_sheet_stage.py`,
  `tests/test_run_view.py`, `tests/test_resume.py`, `tests/test_generate.py`, `tests/e2e/test_render.py`.
- Docs: `docs/decisions.md`, `docs/data-flow.md`, `docs/principles.md`, `README.md`, `isekai/interface/README.md`.
- `flows/`, `config/`, `gpunit.toml` and every run-file kind's version are untouched.

## Not in this change

- Copying the image of each existing *Draft from this* approval into its flow's `sources/` (brief Q14b): a one-off
  after release, its dry run first. Until then such an approval shows the photograph alone.
- Running the new delete over today's leftovers (brief Q17): a one-off after release, its dry run first.
- Rewriting old files' `tags_from`, `drafted_from`, `copied_from` or cross-flow `image`: left as they are, unread
  (brief Q15).
- A change to the confirm dialog: it stays *Delete this render?* (brief Q12).
- Removing a flow on a discard (brief Q13).
