# The layout tail — tasks

The phases are the edit kinds, the draft's names, the importers and the documents. Each phase ends with the suite green and no existing test's assertion changed.

## Progress

- [x] 1 — The edit kinds · moderate
- [x] 2 — The draft's names · moderate
- [x] 3 — The importers · moderate
- [x] 4 — The documents · moderate

## 1 — The edit kinds

- [x] 1.1 Before any edit, run `tools.mutate` over `is_edit_file`, `edit_numbers` and `delete_edits` in `isekai/foundation/layout.py`, one run a range from the `def` line to the last line, on `tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py`. Find each range with `git grep -n -e "^def is_edit_file" -e "^def edit_numbers" -e "^def delete_edits" -- isekai/foundation/layout.py`; kill a survivor by a case in `tests/test_run_directory.py` before 1.3, per [D5](design.md#d5).
  Verify: `grep -n -F "3 killed, 0 survived" openspec/changes/0179-the-layout-tail/design.md` prints one line.
- [x] 1.2 **HALT CHECK** The composite's suffix is spelled by hand once outside the layout, in `_ready`: no other line of `isekai/` builds a name from `}.composite.png` ([D2](design.md#d2)).
  Verify: `git grep -n -F "}.composite.png" -- isekai` prints one line, in `isekai/pipeline/edit.py`.
- [x] 1.3 In `isekai/foundation/layout.py`, add `EDIT_SUFFIXES` after `EDIT_PLACEMENT`, one blank line between them, with its comment as [D1](design.md#d1) gives them. `is_edit_file` and `edit_numbers` loop `for suffix in EDIT_SUFFIXES:` and `delete_edits` takes each path from `edit_stem` and the suffix, as the block of [D1](design.md#d1) reads.
  Verify: `git grep -c -F "in EDIT_SUFFIXES:" -- isekai/foundation/layout.py` prints `isekai/foundation/layout.py:3`.
- [x] 1.4 In `isekai/foundation/layout.py`, no loop lists the suffixes by hand any more: the tuple `(EDIT_COMPOSITE, EDIT_PLACEMENT, EDIT_RECORD, ".png")` that `is_edit_file` held is gone.
  Verify: `git grep -n -F "(EDIT_COMPOSITE, EDIT_PLACEMENT, EDIT_RECORD" -- isekai/foundation/layout.py` prints nothing.
- [x] 1.5 In `isekai/foundation/run.py`, import `EDIT_SUFFIXES` from `isekai.foundation.layout` and add `"EDIT_SUFFIXES"` to `__all__` after `"EDIT_STEM"`.
  Verify: `git grep -c -F "EDIT_SUFFIXES" -- isekai/foundation/run.py` prints `isekai/foundation/run.py:2`.
- [x] 1.6 In `isekai/pipeline/edit.py`, add `EDIT_COMPOSITE` to the import from `isekai.foundation.run` before `EDIT_RECORD`, and make `_ready` name the composite `f"{record.name.removesuffix(EDIT_RECORD)}{EDIT_COMPOSITE}"`, so the string `EDIT_RECORD)}.composite` is gone ([D2](design.md#d2)).
  Verify: `git grep -n -F "EDIT_RECORD)}.composite" -- isekai/pipeline/edit.py` prints nothing.

## 2 — The draft's names

- [x] 2.1 In `tests/test_run_directory.py`, add the cases of [D5](design.md#d5)'s table after `test_deciding_approval_reads_no_file`, the `current_draft` cases bound to `review:approval:draft-is-not-done` and the `source_copy` case to `review:draft-from:a-draft-from-an-image-copies-it`. Add `current_draft` and `source_copy` to the file's import from `isekai.pipeline.review`; the `source_copy` case builds `Run("run", tmp_path)`.
  Verify: `uv run pytest tests/test_run_directory.py -k "a_draft_above or a_draft_at_or_below or a_draft_copy"` passes.
- [x] 2.2 Before `review.py` changes, run `tools.mutate` over `current_draft` and `source_copy` in `isekai/pipeline/review.py`, one run each from the `def` line to the last line, on `tests/test_review.py tests/test_run_directory.py`; kill a survivor by a case in `tests/test_run_directory.py` before 2.5 ([D5](design.md#d5)).
  Verify: `grep -n -F "6 killed, 0 survived" openspec/changes/0179-the-layout-tail/design.md` prints one line.
- [x] 2.3 **HALT CHECK** `OUTPUT_SUFFIX`, which `source_copy` reads, is a foundation name in the flow module, so the moved body imports no stage ([D3](design.md#d3)).
  Verify: `git grep -n -e "^OUTPUT_SUFFIX = " -- isekai/foundation/flow.py` prints one line.
- [x] 2.4 In `isekai/foundation/names.py`, add `DRAFT = "draft"` after `APPROVED` and word the comment above them as [D3](design.md#d3) says.
  Verify: `git grep -n -e "^DRAFT = " -- isekai/foundation/names.py` prints one line.
- [x] 2.5 In `isekai/foundation/layout.py`, set the docstring as [D3](design.md#d3) gives it, import `OUTPUT_SUFFIX`, `DRAFT` and `SOURCES`, and append `current_draft` and then `source_copy` after `approved_versions`, their text copied from `review.py` unchanged.
  Verify: `git grep -n -e "^def current_draft" -e "^def source_copy" -- isekai/foundation/layout.py` prints two lines.
- [x] 2.6 In `isekai/foundation/run.py`, import `DRAFT` from `isekai.foundation.names` and `current_draft` and `source_copy` from `isekai.foundation.layout`, and add the three to `__all__` in sorted place.
  Verify: `git grep -c -E "current_draft|source_copy|DRAFT" -- isekai/foundation/run.py` prints `isekai/foundation/run.py:6`.
- [x] 2.7 In `isekai/pipeline/review.py`, delete `DRAFT = "draft"`, `current_draft` and `source_copy`, and import the three from `isekai.foundation.run` in sorted place; every other line of the file stays, and its other imports stay while a line reads them.
  Verify: `git grep -n -e "^def current_draft" -e "^def source_copy" -e "^DRAFT = " -- isekai/pipeline/review.py` prints nothing.
- [x] 2.8 In `tests/test_run_directory.py`, take `current_draft` and `source_copy` out of `from isekai.pipeline.review import approve, current_draft, review, source_copy` and add them to the file's import from `isekai.foundation.run`.
  Verify: `git grep -n -F "review import approve, current_draft" -- tests/test_run_directory.py` prints nothing.
- [x] 2.9 Run `tools.mutate` over `is_edit_file` at its closing range of [D5](design.md#d5), on the edit tests of 1.1.
  Verify: `uv run python -m tools.mutate isekai/foundation/layout.py:249-259 --tests tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py` exits 0.
- [x] 2.10 Run `tools.mutate` over `edit_numbers` at its closing range, on the same tests.
  Verify: `uv run python -m tools.mutate isekai/foundation/layout.py:291-306 --tests tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py` exits 0.
- [x] 2.11 Run `tools.mutate` over `delete_edits` at its closing range, on the same tests.
  Verify: `uv run python -m tools.mutate isekai/foundation/layout.py:315-330 --tests tests/test_run_directory.py tests/test_edit.py tests/test_edit_placement.py tests/test_edit_session.py` exits 0.
- [x] 2.12 Run `tools.mutate` over the moved `current_draft` and `source_copy` at their closing range, on the tests of 2.2.
  Verify: `uv run python -m tools.mutate isekai/foundation/layout.py:415-435 --tests tests/test_review.py tests/test_run_directory.py` exits 0.
- [x] 2.13 Replay the standing mutants once, after the move.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 3 — The importers

- [x] 3.1 In `isekai/interface/render.py`, delete the import of `current_draft` from `isekai.pipeline.review`, the file's only import from the stage, and add `current_draft` to its import from `isekai.foundation.run` ([D4](design.md#d4)).
  Verify: `git grep -n -F "isekai.pipeline.review" -- isekai/interface/render.py` prints nothing.
- [x] 3.2 In `isekai/interface/ui/surface.py`, delete the import of `current_draft` from `isekai.pipeline.review`, the file's only import from the stage, and add it to the import from `isekai.foundation.run`.
  Verify: `git grep -n -F "isekai.pipeline.review" -- isekai/interface/ui/surface.py` prints nothing.
- [x] 3.3 In `isekai/interface/ui/library.py`, drop `current_draft` from the import from `isekai.pipeline.review`, which keeps `Status` and `came_from`, and add it to the import from `isekai.foundation.run`.
  Verify: `git grep -n -e "review import.*current_draft" -- isekai/interface` prints nothing.
- [x] 3.4 In `isekai/interface/ui/routes/reviewing.py`, drop `source_copy` from the multi-line import from `isekai.pipeline.review` and add it to the import from `isekai.foundation.run` after `sheet_of`.
  Verify: `git grep -n -e "^    source_copy,$" -- isekai/interface/ui/routes/reviewing.py` prints `41:    source_copy,`.
- [x] 3.5 Run `uv run python -m tools.derive_imported_by`; it rewrites `isekai/pipeline/README.md`'s derived row for `review.py` without `interface/render.py` and `interface/ui/surface.py`, and no other file.
  Verify: `uv run pytest tests/test_docs.py` passes.

## 4 — The documents

- [x] 4.1 In `docs/decisions.md`, amend D69's bold paragraph to say the draft being worked on, `current_draft(directory)`, and the draft's source copy, `source_copy(run, flow, version)`, are in `layout.py`, and `DRAFT` in `names.py`, each read through `run.py`; its heading stays, and its *Made by* gains `0179`.
  Verify: `git grep -c -F "current_draft" -- docs/decisions.md` prints `docs/decisions.md:1`.
- [x] 4.2 In `isekai/foundation/README.md`, extend the `layout.py` row of the Files table with the draft being worked on and its source copy, and the `names.py` row with the draft's label.
  Verify: `git grep -c -F "the draft being worked on" -- isekai/foundation/README.md` prints `isekai/foundation/README.md:1`.
