---
bump: patch
after: [0179-the-layout-tail]
---

# The thumbnail names

A thumbnail's path in the cache, the drop of it and the digest that names it are the library's, in `isekai/foundation/library.py`, where a delete's one owner can reach them.

Reading map: [design](design.md) holds the names, what is re-bound and the proof, [tasks](tasks.md) holds its phases.

## Why

A thumbnail is named by its image's digest, so it can be dropped only while the image is still a file. Its path is spelled twice in `isekai/interface/ui/library.py`, in `thumbnail` and in `drop_thumbnails`, and the digest is a memo in the same file, keyed by the file's stat.

The next version gives a delete one owner in the foundation. That owner drops a thumbnail before it removes the image, and a foundation module cannot import the interface. The thumbnail's names go down first, with no change to a file a run writes or a path a thumbnail takes.

## What Changes

- `isekai/foundation/library.py` gains `stat_key`, `file_digest`, `thumbnail_of` and `drop_thumbnails`. `thumbnail_of(library, run, image)` is the one spelling of a thumbnail's path.
- `isekai/interface/ui/library.py` re-binds `file_digest` as `_digest`, `stat_key` as `_key` and `drop_thumbnails` under its name. `thumbnail` calls `thumbnail_of` and still makes the JPEG.
- `isekai/interface/ui/__init__.py` loses its wrapper of `drop_thumbnails`; the `discard` verb in `isekai/interface/verbs/drafts.py` imports it from the foundation.
- The `isekai/interface/ui/library.py` row of the long files' ratchet goes, because the file falls to 800 lines or fewer.
- `tests/test_ui_library.py` holds a case for the thumbnail's path and two for the digest, written before the move.
- D68 names the moved names, and the foundation and interface READMEs say so.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change adds no requirement and changes none; `skip_specs` is set.

## Impact

- `isekai/foundation/library.py` gains names; `isekai/interface/ui/library.py`, `isekai/interface/ui/__init__.py` and `isekai/interface/verbs/drafts.py` read them.
- `tests/test_ui_library.py` gains cases and `tests/test_ratchets.py` loses a row; no existing test's assertion changes.
- `docs/decisions.md`, `isekai/foundation/README.md` and `isekai/interface/README.md` say so.
- No format version moves, no flow re-pins and no image rebuilds; every path a thumbnail takes and every line the `discard` verb prints is as it was.

## Not in this change

- A delete's one owner, the verb's thumbnails of a render's edits and of an edit, and the app's route: these are `the-delete-owner`'s.
- `thumbnail`'s making of the JPEG, `_shrunk`, and the sources' thumbnails: `source_thumbnail` and the sources' listing keep their paths and read `_digest` as they did.
- `_carries` and `_size` and their memos: they stay in `isekai/interface/ui/library.py` and read `_key`.
- `render_running` in `isekai/interface/ui/__init__.py`, which the verb still imports from there.
- The tattoo library's file kinds, and a schema block on them.
- A requirement or a scenario, and any change to what a run writes.
