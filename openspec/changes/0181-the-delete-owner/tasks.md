# The delete owner — tasks

The phases are the pre-flight, the move, the owner, the verb, the route and the documents. Each phase ends with the suite green and no existing test's assertion changed.

## Progress

- [x] 1 — The pre-flight · moderate
- [x] 2 — The move · moderate
- [x] 3 — The owner · hard
- [x] 4 — The verb · moderate
- [x] 5 — The route · moderate
- [ ] 6 — The documents · moderate

## 1 — The pre-flight

- [x] 1.1 **HALT CHECK** `0179` has landed: the draft's names are the layout's, so `withdraw` reads foundation names alone ([D1](design.md#d1)).
  Verify: `git grep -n -e "^def current_draft" -e "^def source_copy" -- isekai/foundation/layout.py` prints two lines.
- [x] 1.2 **HALT CHECK** `0180` has landed: the foundation holds the thumbnail's drop the owner calls ([D2](design.md#d2)).
  Verify: `git grep -n -e "^def thumbnail_of" -e "^def drop_thumbnails" -- isekai/foundation/library.py` prints two lines.
- [x] 1.3 Run `tools.mutate` over `discard_render`, from its `def` line to its last line, as [D5](design.md#d5) gives it. Find the range with `git grep -n -e "^def discard_render" -- isekai/pipeline/generate.py`.
  Verify: `uv run python -m tools.mutate isekai/pipeline/generate.py:337-366 --tests tests/test_generate.py tests/test_edit_session.py tests/test_edit_placement.py tests/test_pipeline_cli.py` exits 0.
- [x] 1.4 Run `tools.mutate` over `discard_edit`, on the tests of [D5](design.md#d5). Find the range with `git grep -n -e "^def discard_edit" -- isekai/pipeline/edit.py`.
  Verify: `uv run python -m tools.mutate isekai/pipeline/edit.py:329-350 --tests tests/test_edit_session.py tests/test_edit_placement.py tests/test_pipeline_cli.py` exits 0.
- [x] 1.5 Run `tools.mutate` over `_holds_render`, on the tests of [D5](design.md#d5). Find the range with `git grep -n -e "^def _holds_render" -- isekai/pipeline/review.py`.
  Verify: `uv run python -m tools.mutate isekai/pipeline/review.py:571-574 --tests tests/test_review.py tests/test_pipeline_cli.py tests/test_edit_session.py` exits 0.
- [x] 1.6 In `tests/test_review.py`, add the cases of [D5](design.md#d5)'s table that kill the survivors of `withdraw`: the first after `test_an_older_approval_whose_group_holds_failure_records_alone_goes`, the second after `test_a_flow_left_with_no_approval_keeps_only_its_assignment`. Each binds the scenario the table names.
  Verify: `uv run pytest tests/test_review.py -k "a_withdrawn_failure_only_group or a_nested_folder_under" -q` exits 0.
- [x] 1.7 Run `tools.mutate` over `withdraw`, on the tests of [D5](design.md#d5). Find the range with `git grep -n -e "^def withdraw" -- isekai/pipeline/review.py`; a survivor left is killed by a further case before 2.2.
  Verify: `uv run python -m tools.mutate isekai/pipeline/review.py:577-635 --tests tests/test_review.py tests/test_pipeline_cli.py tests/test_edit_session.py tests/test_ui_api.py tests/test_generate.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 2 — The move

- [x] 2.1 Create `isekai/foundation/discard.py` with the docstring of [D1](design.md#d1), and copy into it, character for character with their docstrings, `discard_render` from `isekai/pipeline/generate.py`, `_holds_render` and `withdraw` from `isekai/pipeline/review.py` and `discard_edit` from `isekai/pipeline/edit.py`. Import each name they read from `isekai.foundation.run`, and `EDIT_FILE` and `read` from `isekai.foundation.artifacts`.
  Verify: `grep -n -E "^def (discard_render|discard_edit|withdraw|_holds_render)" isekai/foundation/discard.py` prints four lines.
- [x] 2.2 Delete those bodies from their stages and bind each back as [D1](design.md#d1) says: `discard_render as discard_render` in `generate.py`, `discard_edit as discard_edit` in `edit.py`, `withdraw as withdraw` and `_holds_render as _holds_render` in `review.py`. Run `uv run ruff check --fix isekai/pipeline/generate.py isekai/pipeline/edit.py isekai/pipeline/review.py isekai/foundation/discard.py` for the order and each import the bodies alone read.
  Verify: `git grep -n -e "^def discard_render" -e "^def discard_edit" -e "^def withdraw" -e "^def _holds_render" -- isekai/pipeline` prints nothing.
- [x] 2.3 Run the suite over the delete's readers: no file under `tests/` changes in this phase.
  Verify: `uv run pytest tests/test_generate.py tests/test_review.py tests/test_edit_session.py tests/test_edit_placement.py tests/test_pipeline_cli.py tests/test_ui_api.py tests/test_layers.py -q` exits 0.
- [x] 2.4 In the *Imported by* table of `isekai/foundation/README.md`, add the row ``| `discard.py` | — | — |`` after the `library.py` row, then run `uv run python -m tools.derive_imported_by`; it writes the importers of `discard.py` and the rows of the files it reads.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py -q` exits 0.

## 3 — The owner

- [x] 3.1 In `tests/test_edit_session.py`, after `test_edit_discard_an_unreadable_record_in_the_chain_deletes_nothing`, add the owner's cases of [D6](design.md#d6)'s table, each `spec_exempt("structural: …")`, over a group in a collection built under `tmp_path`, importing `delete_edit` and `delete_render` from `isekai.foundation.discard` and `thumbnail_of` from `isekai.foundation.library`.
  Verify: `uv run pytest tests/test_edit_session.py -k "the_owner" -q` exits 2.
- [x] 3.2 In `isekai/foundation/discard.py`, add `Deleted` and `delete_render` and `delete_edit` as [D2](design.md#d2) gives them, importing `NamedTuple` and `drop_thumbnails`, and set the module's docstring as [D2](design.md#d2) gives it.
  Verify: `git grep -n -e "^class Deleted" -e "^def delete_render" -e "^def delete_edit" -- isekai/foundation/discard.py` prints three lines.
- [x] 3.3 In the same file, split `_chain` out of `discard_edit` and have `discard_edit` call it, as [D3](design.md#d3) gives it; its docstring and its answer stand.
  Verify: `git grep -n -e "^def _chain" -- isekai/foundation/discard.py` prints one line.
- [x] 3.4 Run the owner's cases and the suite over the delete's readers.
  Verify: `uv run pytest tests/test_edit_session.py tests/test_edit_placement.py tests/test_generate.py tests/test_review.py -q` exits 0.
- [x] 3.5 Run `uv run python -m tools.derive_imported_by`; it adds `discard.py` to the importers of `library.py`.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py -q` exits 0.

## 4 — The verb

- [x] 4.1 In `tests/test_edit_session.py`, after `test_edit_discard_the_last_render_with_an_edit_takes_the_group_and_the_approval`, add the verb's cases of [D6](design.md#d6)'s table, each bound to the scenario it names, in the collection `tmp_path / "b"` with its `sources/` made, a thumbnail written for each image they name.
  Verify: `uv run pytest tests/test_edit_session.py -k "the_verb_takes" -q` exits 1.
- [x] 4.2 In `isekai/interface/verbs/drafts.py`, make `run_discard` read the run from the ref, call `(delete_edit if edited else delete_render)(image)` and print the files, then the thumbnails, as [D4](design.md#d4) gives it. Import both from `isekai.foundation.discard`, drop the imports it no longer reads, and reword its docstring to say the owner deletes.
  Verify: `git grep -n -e "discard_render(" -e "withdraw(" -e "discard_edit(" -e "drop_thumbnails(" -- isekai/interface/verbs/drafts.py` prints nothing.
- [x] 4.3 Run the verb's cases and the delete's readers.
  Verify: `uv run pytest tests/test_edit_session.py tests/test_pipeline_cli.py -q` exits 0.
- [x] 4.4 Run `uv run python -m tools.derive_imported_by`; it moves `verbs/drafts.py` between the importers of the stages and of `discard.py`.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py -q` exits 0.

## 5 — The route

- [x] 5.1 In `tests/test_ui_api.py`, after `test_bake_detail_deleting_a_render_deletes_its_bakes_thumbnails`, add `test_the_verb_and_the_route_leave_one_cache_with_edits_seeded` as [D6](design.md#d6) gives it, `spec_exempt("structural: …")`. It is a guard, not a red-first case: it passes before the route is switched, and holds the switch after.
  Verify: `uv run pytest tests/test_ui_api.py -k "leave_one_cache" -q` exits 0.
- [x] 5.2 In `isekai/interface/ui/routes/images.py`, make `delete_render` call `delete_render(image)` from `isekai.foundation.discard` under the draft lock, after the job-slot refusal, where it chained `drop_thumbnails`, `discard_render` and `withdraw`. Drop the imports it no longer reads and reword its docstring.
  Verify: `git grep -n -e "discard_render(" -e "withdraw(" -e "discard_edit(" -e "drop_thumbnails(" -e "edit_numbers(" -- isekai/interface/ui/routes/images.py` prints nothing.
- [x] 5.3 Run the page's cases over the delete and the library's.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_library.py -q` exits 0.
- [x] 5.4 Run `uv run python -m tools.derive_imported_by`; it moves `interface/ui/routes/images.py` between the importers of the stages and of `discard.py`.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py -q` exits 0.

## 6 — The documents

- [ ] 6.1 In `docs/decisions.md`, add D72 after D71 and amend the page's [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) and D69 as [D7](design.md#d7) says; their *Made by* gain `0181`.
  Verify: `git grep -c -F "0181" -- docs/decisions.md` prints `docs/decisions.md:3`.
- [ ] 6.2 In `docs/principles.md`, delete the sentence from "The discard of a render is spelled twice" to the end of its paragraph, and the *Known breaks* bullet that names `discard_render` and `withdraw`, which ends before `### Every artifact records what shaped it`.
  Verify: `git grep -n -e "is spelled twice" -e "discard_render" -e "withdraw" -- docs/principles.md` prints nothing.
- [ ] 6.3 In `docs/modules.md`, replace the sentence that names `drop_thumbnails`, `discard_render` and `withdraw` and ends "but drops the render's thumbnails and not each edit image's" with one that names `delete_render` and `delete_edit` of `foundation/discard.py`, which `ImageRoutes` and the CLI's `discard` both call. In `docs/data-flow.md`, change "the render stage's and the library's for a deleted render" to "the foundation's `delete_render` for a deleted render", and add to the `isekai discard` paragraph that each image's thumbnail goes with it.
  Verify: `git grep -n -e "drops the render's thumbnails and not each" -e "the render stage's and" -- docs/modules.md docs/data-flow.md` prints nothing.
- [ ] 6.4 In the docstring of `isekai/interface/ui/app.py`, replace the whole span from "a render's thumbnails leave through" to "through `withdraw()`." with one sentence that names `delete_render()` of the foundation's `discard.py` as what deletes a render, its edits, their thumbnails and the approvals its last render leaves.
  Verify: `git grep -n -e "drop_thumbnails()" -e "discard_render()" -e "withdraw()" -- isekai/interface/ui/app.py` prints nothing.
- [ ] 6.5 In `isekai/foundation/README.md`, add a `discard.py` row to *Files* after `library.py`: ``a delete's one owner: `delete_render` and `delete_edit`, which drop each thumbnail, then the files, then the approval, and the bodies they call``. In `isekai/interface/README.md`, change the `verbs/drafts.py` row's "`discard` deletes a render and its thumbnails" to "`discard` deletes a render or an edit and each image's thumbnail".
  Verify: `git grep -c -F "delete_render" -- isekai/foundation/README.md` prints `isekai/foundation/README.md:1`.
- [ ] 6.6 Replay the standing mutants once, after the move.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
