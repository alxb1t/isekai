# The thumbnail names — tasks

The phases are the path and the digest, the drop and the documents; each moving phase opens with its pre-flight. Each phase ends with the suite green and no existing test's assertion changed.

## Progress

- [x] 1 — The path and the digest · moderate
- [x] 2 — The drop · moderate
- [ ] 3 — The documents · moderate

## 1 — The path and the digest

- [x] 1.1 Before any edit, run `tools.mutate` over `thumbnail` and over `_key` with `_digest` in `isekai/interface/ui/library.py`, one run a range from the `def` line to the last line, with the command and tests of [D5](design.md#d5). Find the ranges with `git grep -n -e "^def thumbnail" -e "^def _key" -e "^def _digest" -- isekai/interface/ui/library.py`; kill a survivor by a case in `tests/test_ui_library.py` before 1.6.
  Verify: `grep -c -F "3 killed, 0 survived" openspec/changes/0180-the-thumbnail-names/design.md` prints `2`.
- [x] 1.2 **HALT CHECK** The foundation already holds the names the moved bodies read, so they import no layer above ([D1](design.md#d1)).
  Verify: `git grep -n -e "^CACHE = " -e "^RUNS = " -e "^def is_collection" -- isekai/foundation/library.py` prints three lines.
- [x] 1.3 **HALT CHECK** `0179` has landed: `ui/library.py` no longer imports `current_draft` from the review stage, so the measure of [D6](design.md#d6) holds.
  Verify: `git grep -n -F "review import Status, came_from, current_draft" -- isekai/interface/ui/library.py` prints nothing.
- [x] 1.4 In `tests/test_ui_library.py`, add the cases of [D5](design.md#d5)'s table after `test_one_source_at_one_seed_in_two_collections_has_two_thumbnails`, written against `library.thumbnail` and `library._digest`. The first binds `ui:renders:a-thumbnail-is-its-own-images`; the other two carry `@pytest.mark.spec_exempt("structural: …")` with the reason after the colon, one sentence each.
  Verify: `uv run pytest tests/test_ui_library.py -k "a_thumbnail_is_named or a_files_digest"` passes.
- [x] 1.5 In `isekai/foundation/library.py`, import `ID_DIGEST_CHARS`, `Run` and `digest_of` from `isekai.foundation.run` in one line, set the docstring as [D3](design.md#d3) gives it, and add `_DIGESTS`, `stat_key`, `file_digest` and `thumbnail_of` after `_session`, as [D1](design.md#d1) and [D2](design.md#d2) give them.
  Verify: `git grep -n -e "^def stat_key" -e "^def file_digest" -e "^def thumbnail_of" -- isekai/foundation/library.py` prints three lines.
- [x] 1.6 In `isekai/interface/ui/library.py`, delete `_DIGESTS`, `_key` and `_digest`. Import `thumbnail_of` plain and `file_digest as _digest` and `stat_key as _key` from `isekai.foundation.library`, drop `digest_of` from the import from `isekai.foundation.run`, reword the comment above `_CARRIES` and `_SIZES` as [D2](design.md#d2) says, and make `thumbnail` read `cached = thumbnail_of(library, run, image)` as [D1](design.md#d1) says. Run `uv run ruff check --fix isekai/interface/ui/library.py` for the order and any unread import.
  Verify: `git grep -n -e "^def _digest" -e "^def _key" -e "^_DIGESTS" -- isekai/interface/ui/library.py` prints nothing, and `uv run pytest tests/test_ui_library.py tests/test_pipeline_cli.py` exits 0.
- [x] 1.7 In `tests/test_ui_library.py`, switch the cases of 1.4 to the foundation's names: add `from isekai.foundation.library import file_digest, thumbnail_of` to its imports, assert the thumbnail's path with `thumbnail_of` and that `library.thumbnail` returns it, and read the digest through `file_digest`.
  Verify: `git grep -c -F "from isekai.foundation.library import" -- tests/test_ui_library.py` prints `tests/test_ui_library.py:1`, and `uv run pytest tests/test_ui_library.py -k "a_thumbnail_is_named or a_files_digest"` passes.
- [x] 1.8 **HALT CHECK** `ui/library.py` has 800 lines or fewer, so its row in the long files' ratchet no longer offends ([D6](design.md#d6)). A longer file means the plan is wrong: move nothing more to pass under.
  Verify: `wc -l isekai/interface/ui/library.py` prints a number of 800 or fewer.
- [x] 1.9 In `tests/test_ratchets.py`, delete the `"isekai/interface/ui/library.py": 881,` row of `LONG_FILES` and set `FILE_ROWS = 4`.
  Verify: `uv run pytest tests/test_ratchets.py` passes.

## 2 — The drop

- [x] 2.1 Before any edit, run `tools.mutate` over `drop_thumbnails` in `isekai/interface/ui/library.py`, one run from its `def` line to its last line, with the command and tests of [D5](design.md#d5). Find the range with `git grep -n -e "^def drop_thumbnails" -- isekai/interface/ui/library.py`; kill a survivor by a case in `tests/test_ui_library.py` before 2.3.
  Verify: `grep -c -F "9 killed, 0 survived" openspec/changes/0180-the-thumbnail-names/design.md` prints `1`.
- [x] 2.2 In `isekai/foundation/library.py`, add `drop_thumbnails` after `thumbnail_of`, its docstring unchanged and its path from `thumbnail_of`, as [D3](design.md#d3) gives it.
  Verify: `git grep -n -e "^def drop_thumbnails" -- isekai/foundation/library.py` prints one line.
- [x] 2.3 In `isekai/interface/ui/library.py`, delete `drop_thumbnails` and import it as `drop_thumbnails as drop_thumbnails` from `isekai.foundation.library`, in the sorted place of the `X as X` lines. Run `uv run ruff check --fix isekai/interface/ui/library.py` for any unread import.
  Verify: `git grep -n -e "^def drop_thumbnails" -- isekai/interface/ui/library.py` prints nothing, and `uv run pytest tests/test_ui_library.py tests/test_ui_api.py` exits 0.
- [x] 2.4 In `isekai/interface/ui/__init__.py`, delete the wrapper `drop_thumbnails`; `render_running` stays ([D4](design.md#d4)).
  Verify: `git grep -n -e "^def drop_thumbnails" -- isekai/interface/ui/__init__.py` prints nothing.
- [x] 2.5 In `isekai/interface/verbs/drafts.py`, import `drop_thumbnails` from `isekai.foundation.library` between the imports of `flow` and `refusal`, and change the handler's `from isekai.interface.ui import drop_thumbnails, render_running` to import `render_running` alone ([D4](design.md#d4)).
  Verify: `git grep -n -F "isekai.interface.ui import drop_thumbnails" -- isekai` prints nothing, and `uv run pytest tests/test_pipeline_cli.py` exits 0.
- [x] 2.6 Run `uv run python -m tools.derive_imported_by`; it rewrites the derived row of `library.py` in `isekai/foundation/README.md` to name `interface/verbs/drafts.py`, and no other file.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py` passes.
- [x] 2.7 Run `tools.mutate` over `stat_key` and `file_digest` at their closing range of [D5](design.md#d5).
  Verify: `uv run python -m tools.mutate isekai/foundation/library.py:153-164 --tests tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [x] 2.8 Run `tools.mutate` over `thumbnail_of` at its closing range, on the same tests.
  Verify: `uv run python -m tools.mutate isekai/foundation/library.py:167-177 --tests tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [x] 2.9 Run `tools.mutate` over `drop_thumbnails` at its closing range, on the same tests.
  Verify: `uv run python -m tools.mutate isekai/foundation/library.py:180-196 --tests tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [x] 2.10 Run `tools.mutate` over `thumbnail` at its closing range, on the same tests.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/library.py:447-459 --tests tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [x] 2.11 Replay the standing mutants once, after the move.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 3 — The documents

- [ ] 3.1 In `docs/decisions.md`, amend D68 as [D7](design.md#d7) says: its bold paragraph names `stat_key`, `file_digest`, `thumbnail_of` and `drop_thumbnails`, its *Accepts* line drops the clause that `ui/library.py` stays a listed long file and says `thumbnail` and the sources' thumbnails stay in it and `render_running` stays wrapped by `ui/__init__.py`, and its *Made by* gains `0180`. The heading stays.
  Verify: `git grep -c -F "thumbnail_of" -- docs/decisions.md` prints `docs/decisions.md:1`, and `git grep -n -F "stays a listed long file" -- docs/decisions.md` prints nothing.
- [ ] 3.2 In `isekai/foundation/README.md`, extend the `library.py` row of *Files* with ``, and where a thumbnail sits in the cache and what names it: `stat_key`, `file_digest`, `thumbnail_of` and `drop_thumbnails` ``.
  Verify: `git grep -c -F "thumbnail_of" -- isekai/foundation/README.md` prints `isekai/foundation/README.md:1`.
- [ ] 3.3 In `isekai/interface/README.md`, in the `ui/__init__.py` row change ``and `drop_thumbnails` and `render_running` for the `discard` verb`` to ``and `render_running` for the `discard` verb``; in the `ui/library.py` row change ``the collection's names and its session records' read side are `foundation/library.py`'s, re-bound here (D68)`` to ``the collection's names, its session records' read side and a thumbnail's path, drop and digest are `foundation/library.py`'s, re-bound here (D68)``.
  Verify: `git grep -c -F "a thumbnail's path, drop and digest" -- isekai/interface/README.md` prints `isekai/interface/README.md:1`, and `git grep -n -F "drop_thumbnails" -- isekai/interface/README.md` prints nothing.
