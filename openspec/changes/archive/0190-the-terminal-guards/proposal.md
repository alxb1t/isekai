---
bump: minor
version: 0.88
after: [0189-the-page-track]
debt: [0181·S1]
---

# The terminal guards

The verbs that delete or cancel refuse beside a live render, wherever the runs root is, and a delete leaves no thumbnail behind.

Reading map: [design](design.md) holds the rule, the guard, the second drop and the documents, [tasks](tasks.md) its phases.

## Why

A render session writes its record, and holds its lock, beside any runs root it renders. The app's delete and cancel already refuse while a session holds the collection. The terminal's do not: the cancel asks nothing, and the discard's guard needs a collection.

`isekai approve --cancel` asks nothing, so it takes an approval back under a root a render is using. `render_running` of `isekai/foundation/library.py`, the guard of `isekai discard`, answers no unless the root's parent is a collection, so a discard under a plain runs root deletes beside a live render. The discard's and the edit's requirements say "collection" where the session's record says "runs root".

Card `0181·S1` rides along. The owner drops each thumbnail, then deletes the files, and a thumbnail requested in between is rebuilt and left. This version opens `isekai/foundation/discard.py`, the card's trigger, and fixes it.

No requirement demands either guard, and a patch may add none. Each is one sentence added to a requirement, with a scenario, so this is a minor.

## What Changes

- `render_running` reads the sessions beside the run's runs root, whether or not the root's parent is a collection.
- `isekai discard` refuses a render's path and an edit's path under a plain runs root while a session holds it. The sentence is today's.
- `isekai approve --cancel` refuses each run whose runs root a render session holds, with the app's sentence, before it calls the review stage's cancel. Each run is answered on its own.
- `delete_render` and `delete_edit` name each thumbnail before any file goes, drop them, delete the files, then unlink any named thumbnail that came back (card `0181·S1`).
- The `cli` spec modifies *The approve verb cancels an approval with `--cancel`* and *The discard verb deletes a render named by its image path*, each with a scenario. The `edit` spec modifies *A discard takes edits*, with a scenario.
- D74 records the guards; D72 names the second drop and the guards' new home.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: *The approve verb cancels an approval with `--cancel`* refuses a run while a render session holds its runs root. *The discard verb deletes a render named by its image path* refuses while a session holds the image's runs root, a collection's or not.
- `edit`: *A discard takes edits* refuses while a session holds the image's runs root, a collection's or not.

## Impact

- Code: `isekai/foundation/library.py`, `isekai/foundation/discard.py`, `isekai/interface/verbs/runner.py`, and the docstrings of `isekai/interface/verbs/drafts.py` and `isekai/interface/ui/__init__.py`.
- Tests: `tests/test_ui_library.py`, `tests/test_pipeline_cli.py`, `tests/test_edit_session.py`.
- Docs: `docs/decisions.md` (D72, D74), `isekai/foundation/README.md`, `isekai/interface/README.md`, `README.md`, `docs/edit-tattoo.md`.
- No format version moves. No printed text changes but the cancel's new refusal.

## Not in this change

- The app's guard, which already asks the slot or the held collection.
- The gap between a check and a delete, and the window before a session's record opens. They wait for a lock both a session and an act take, in *the session queue*'s plan.
- A lock an act holds.
- The review stage's cancel: it stays an act that decides nothing about a render.
- Any file under `ui/`, `tools/` or `evaluation/`.
