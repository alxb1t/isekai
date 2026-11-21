---
bump: patch
after: [0180-the-thumbnail-names]
---

# The delete owner

A delete has one owner, `isekai/foundation/discard.py`, which drops the thumbnail of every image it removes and returns every path it deleted; the `discard` verb and the app's delete call it and write no loop.

Reading map: [design](design.md) holds the owner, what moves and the proof, [tasks](tasks.md) holds its phases.

## Why

A render's delete is split across the paid stage's `discard_render`, review's `withdraw`, the foundation's `delete_edits` and the library's `drop_thumbnails`, and no one of them removes all of it. Each front end chains them by hand, and the chains differ.

The app drops the thumbnails of the render and of each edit image and throws both returned lists away. The `discard` verb drops the render's thumbnail alone, and on an edit's path drops none, so a likeness stays in the library's cache. The principles list that difference as a break.

A thumbnail is named by its image's digest, so it can go only while the image is still a file: an owner that deletes first cannot name it afterwards. The foundation holds the thumbnail's names since [the thumbnail names](../0180-the-thumbnail-names/proposal.md), so the owner can sit there.

## What Changes

- `isekai/foundation/discard.py` holds the bodies of `discard_render`, `withdraw`, `_holds_render` and `discard_edit`, moved unchanged and bound back at their old homes, and `Deleted`, `delete_render(image)` and `delete_edit(image)`.
- `delete_render` and `delete_edit` drop the thumbnails of every image that will go, then delete the files, then, for a render, the approval its last render leaves. They return `Deleted`, whose `files` and `thumbnails` are lists of paths.
- `run_discard` of `isekai/interface/verbs/drafts.py` calls the owner and prints the files, then the thumbnails. A render's discard drops its edits' thumbnails, and an edit's discard drops the edit's and its chain's.
- `delete_render` of `isekai/interface/ui/routes/images.py` calls the owner under the draft lock, and writes no loop.
- Requirement *The discard verb deletes a render named by its image path* gains the scenarios for a render's edits' thumbnails and for an edit's and its chain's; its text stays.
- `tests/test_review.py` gains cases that kill the survivors of `withdraw`'s pre-flight; `tests/test_edit_session.py` holds the owner's cases and the scenarios'; `tests/test_ui_api.py` holds a case that the verb and the route leave one cache.
- D72 records the owner, [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) and [D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation) name it, and the *Known breaks* of the stage principle leave `docs/principles.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: *The discard verb deletes a render named by its image path* gains the scenarios `a-render-takes-its-edits-thumbnails-with-it` and `an-edit-takes-its-own-thumbnail-and-its-chains`. No requirement's text changes.

## Impact

- `isekai/foundation/discard.py` is new; `isekai/pipeline/generate.py`, `isekai/pipeline/edit.py` and `isekai/pipeline/review.py` bind their old names from it; `isekai/interface/verbs/drafts.py` and `isekai/interface/ui/routes/images.py` call it.
- Under `tests/`: `tests/test_review.py`, `tests/test_edit_session.py` and `tests/test_ui_api.py` gain cases; no existing test's assertion changes.
- The verb's printed lines are today's lines on a tree with no edit thumbnail; with one, the verb prints it after the run's files. No file a run writes changes.
- No format version moves, no flow re-pins and no image rebuilds.
- `docs/decisions.md`, `docs/principles.md`, `docs/modules.md`, `docs/data-flow.md`, `isekai/foundation/README.md`, `isekai/interface/README.md` and the docstring of `isekai/interface/ui/app.py` say so.

## Not in this change

- `_derived` and the cancel: it answers what derives from an approval and deletes nothing, so it stays in review.
- `review.discard` and `tattoos.remove`: other deletes, other owners.
- The guards: the app's job slot, `approve --cancel`'s lack of one, a run outside a collection, and the gap between a check and a delete. The verb keeps asking the disk and the route its job slot; the acts are a later version's.
- A route that deletes an edit: the app has none.
- The making of a thumbnail, the sources' thumbnails and `render_running` in `isekai/interface/ui/__init__.py`.
- The tattoo library's file kinds and a schema block on them, which a patch may not hold.
- A requirement's text, a format version, and any file under `ui/`, `tools/` or `evaluation/`.
