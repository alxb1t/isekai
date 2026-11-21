---
bump: patch
---

# The layout tail

The layout names each kind of an edit's file once, and the draft's and the source copy's names live in the foundation, where the code that reads them can reach them.

Reading map: [design](design.md) holds the tuple, the moved names, the importers that switch and the proof, [tasks](tasks.md) holds its phases.

## Why

An edit's image, record, placement and composite are listed by hand in `is_edit_file`, `edit_numbers` and `delete_edits` of `isekai/foundation/layout.py`, each in its own order, and the edit stage spells the composite's suffix again. A new kind would be added at each of them, and a loop that misses it fails silently.

The draft's label and the source copy's path belong to the layout, and each body reads foundation names alone. They sit in the review stage, so the render verb, the app's surface, the library and the review routes import the stage to build a path, and a delete owner cannot move into the foundation without them ([D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation) already says a module above the pipeline reads the layout from the foundation).

Both halves are one rule: the layout says each file kind once. Nothing a run writes changes.

## What Changes

- `EDIT_SUFFIXES` in `isekai/foundation/layout.py`: the suffixes of an edit's files in the order a delete takes them. `is_edit_file`, `edit_numbers` and `delete_edits` read it.
- `_ready` in `isekai/pipeline/edit.py` names the composite by `EDIT_COMPOSITE`, not by a string.
- `DRAFT` moves to `isekai/foundation/names.py`; `current_draft` and `source_copy` move to `isekai/foundation/layout.py`. `isekai/foundation/run.py` re-exports them.
- `isekai/pipeline/review.py` imports `DRAFT`, `current_draft` and `source_copy` from `isekai.foundation.run` and keeps them bound, so every test that imports them from review holds.
- `isekai/interface/render.py`, `isekai/interface/ui/surface.py`, `isekai/interface/ui/library.py` and `isekai/interface/ui/routes/reviewing.py` read them from the foundation.
- `tests/test_run_directory.py` holds a case for `current_draft` and one for `source_copy`, written before the move.
- D69 names the moved names, and the foundation README, the pipeline README's derived row and `layout.py`'s docstring say so.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change adds no requirement and changes none; `skip_specs` is set.

## Impact

- `isekai/foundation/layout.py`, `isekai/foundation/names.py` and `isekai/foundation/run.py` gain names.
- `isekai/pipeline/review.py` and `isekai/pipeline/edit.py` read them.
- `isekai/interface/render.py`, `isekai/interface/ui/surface.py`, `isekai/interface/ui/library.py` and `isekai/interface/ui/routes/reviewing.py` stop importing the review stage for them.
- `tests/test_run_directory.py` gains cases; no existing test's assertion changes.
- `docs/decisions.md`, `isekai/foundation/README.md` and `isekai/pipeline/README.md` say so.
- No format version moves, no flow re-pins and no image rebuilds.

## Not in this change

- The thumbnail's path, its drop and its digest, which are `the-thumbnail-names`'.
- A delete's one owner and the verb's thumbnails of an edit, which are `the-delete-owner`'s.
- `edit_files` and `placement_file`: `edit_files` keeps its paths and `placement_file` its one.
- The image's own suffix as a named constant, and `edit_at`'s test of `.png`.
- `OUTPUT_SUFFIX`'s home: `source_copy` reads it from the flow module as it did.
- A requirement or a scenario, and any change to what a run writes.
