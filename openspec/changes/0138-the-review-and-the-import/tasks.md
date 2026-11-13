# The review and the import — tasks

Phases of tests and three small product fixes: the budget and the warning, an approval that is never replaced, what the reader is sent, the seal and the commit, the kinds, and the mutants that hold them. Each fix sits under a requirement that stands.

## Progress

- [x] 1 — The budget and the warning · moderate
- [x] 2 — An approval is never replaced · moderate
- [x] 3 — What the reader is sent · moderate
- [x] 4 — The seal and the commit · hard
- [x] 5 — The kinds · moderate
- [x] 6 — The mutants die · moderate

## 1 — The budget and the warning

- [x] 1.1 **HALT CHECK** The warning counts the tags alone at the line [D3](design.md#d3) replaces; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'estimate = estimate_tokens(fields, schema)' isekai/pipeline/review.py` prints `1`.
- [x] 1.2 **HALT CHECK** The CLI's `approve` call passes the schema and no flow, the shape [D3](design.md#d3) extends; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'flows[name].schema,' isekai/interface/cli.py` prints `1`.
- [x] 1.3 In `isekai/pipeline/review.py` write [D3](design.md#d3): the keyword `definition: Flow | None = None` on `approve`, the `estimate` expression, a line in `approve`'s docstring, and `token_budget`'s paragraph on `estimate_tokens` replaced as the design says.
  Verify: `git grep -c -F 'else token_budget(fields, schema, definition).total' isekai/pipeline/review.py` prints `1`.
- [x] 1.4 In `isekai/interface/cli.py` add `definition=flows[name],` after `excluded=field_map().excluded,` in `approve_flow`'s `approve(` call.
  Verify: `git grep -c -F 'definition=flows[name],' isekai/interface/cli.py` prints `1`.
- [x] 1.5 In `isekai/interface/ui/app.py` add `definition=one.flow,` after `excluded=shared.field_map().excluded,` in `post_approve`'s `approve(` call.
  Verify: `git grep -c -F 'definition=one.flow,' isekai/interface/ui/app.py` prints `1`.
- [x] 1.6 In `tests/test_ui_api.py` give the stand-in `approve_` of `_update_during_approval` the keyword-only parameter `definition: Flow | None = None` and pass `definition=definition` to `approving(...)`, importing `Flow` where the file lacks it.
  Verify: `uv run pytest tests/test_ui_api.py::test_an_update_overlapping_an_approval_is_refused tests/test_ui_api.py::test_without_the_lock_an_update_writes_after_the_approval` passes.
- [x] 1.7 In `tests/test_review.py` add `test_the_budget_of_a_known_sheet_is_its_literals`, taking `schema` and `flow`, carrying `review:budget:count-covers-the-assembled-prompt` and `review:budget:shares-and-overhead-sum-to-the-total`. It builds the sheet of [D2](design.md#d2) and asserts each literal of its table, and that an empty sheet's `total` is `20`.
  Verify: `uv run pytest tests/test_review.py::test_the_budget_of_a_known_sheet_is_its_literals` passes.
- [x] 1.8 In `tests/test_review.py` add `test_a_sheet_inside_the_window_by_its_tags_and_past_it_assembled_warns`, carrying `review:budget:a-sheet-past-the-window-only-assembled-warns`, taking `run`, `schema`, `vocabulary` and `flow`. After `review(run, FLOW)` it edits `clothes` to `every` and `accessories` to `every[:3]`, `every` being `list(vocabulary.counts)`; asserts `estimate_tokens(fields, schema) <= ENCODER_WINDOW < token_budget(fields, schema, flow).total` over the draft's fields; calls `approve(run, FLOW, schema, vocabulary, definition=flow)`, and asserts one warning holding `the assembled prompt is about` and an approved file.
  Verify: `uv run pytest tests/test_review.py::test_a_sheet_inside_the_window_by_its_tags_and_past_it_assembled_warns` passes.
- [x] 1.9 In `tests/test_pipeline_cli.py` add `test_approve_warns_on_the_assembled_prompt_and_still_approves`, carrying the key of 1.8, built as `test_approve_refuses_a_tag_the_wired_field_map_excludes` is, over the sheet of 1.8 saved with `save_draft`. It asserts the same precondition, exit `0`, `warning: ` and `the assembled prompt is about` in the error stream, and the approved file.
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_approve_warns_on_the_assembled_prompt_and_still_approves` passes.
- [x] 1.10 In `tests/test_ui_api.py` add `test_approve_answers_the_assembled_warning`, carrying the key of 1.8, over `client`, `made` and `vocabulary`: the draft update of the sheet of 1.8 answers a `budget` whose `total` is past `ENCODER_WINDOW`, and the approve route answers `200` with one `warnings` entry holding `the assembled prompt is about`.
  Verify: `uv run pytest tests/test_ui_api.py::test_approve_answers_the_assembled_warning` passes.
- [x] 1.11 The phase's files and the record agree.
  Verify: `uv run pytest tests/test_review.py tests/test_pipeline_cli.py tests/test_ui_api.py tests/test_record.py` passes.

## 2 — An approval is never replaced

- [x] 2.1 **HALT CHECK** Both approval writers publish by `write` today, the lines [D4](design.md#d4) replaces; if they read otherwise, the plan is wrong.
  Verify: `git grep -c -E 'write\((path|written), APPROVED_FILE, (approved_body|copied)\)' isekai/pipeline/review.py` prints `2`.
- [x] 2.2 **HALT CHECK** `create` refuses an occupied path, the one fact the fix leans on; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'write_atomically(path, (json.dumps(body, indent=2) + "\n").encode(), exclusive=True)' isekai/foundation/artifacts.py` prints `1`.
- [x] 2.3 In `isekai/pipeline/review.py` write [D4](design.md#d4): import `create`, add `_publish`, and end `approve` and `_copy_approval` on it as the design says, the `path.exists()` check and its sentence gone from `approve`. `_publish` takes its body as the parameter `approved` and binds `body: ReviewApproved = approved` before the `try`, as D4 shows, so `tests/test_artifact_bytes.py::test_every_write_gets_an_annotated_artifact` stays green.
  Verify: `git grep -c -F 'create(path, APPROVED_FILE, body)' isekai/pipeline/review.py` prints `1`.
- [x] 2.4 In `tests/test_review.py` add `test_an_approval_dropped_inside_the_publish_is_refused_and_its_bytes_stay`, carrying `review:approval:approved-is-not-overwritten`, with `import isekai.pipeline.review as review_module`. It wraps `review_module.create` as [D4](design.md#d4) says, dropping `b"rival\n"` at the path before the real call; approves a draft under `pytest.raises(Refusal, match=...)` holding `001.approved.json already exists`; and asserts the rival's bytes stay and the directory lists `001.approved.json` and `001.draft.json` alone.
  Verify: `uv run pytest tests/test_review.py::test_an_approval_dropped_inside_the_publish_is_refused_and_its_bytes_stay` passes.
- [x] 2.5 In `tests/test_review.py` add `test_a_copied_approval_dropped_inside_the_publish_is_refused_and_its_bytes_stay`, carrying the same key, over `_approved_source` and the same wrapper, which makes the path's folder first. `approve(run, CONTROL, schema, vocabulary, source=FLOW)` refuses the same way, the rival's bytes stay and `CONTROL`'s review directory lists `001.approved.json` alone.
  Verify: `uv run pytest tests/test_review.py::test_a_copied_approval_dropped_inside_the_publish_is_refused_and_its_bytes_stay` passes.
- [x] 2.6 The phase's file agrees with the keys.
  Verify: `uv run pytest tests/test_review.py` passes.

## 3 — What the reader is sent

- [x] 3.1 **HALT CHECK** The open reader's prompt is the briefing, stripped, and one newline, the line the mutant `PA-6` names; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'return f"{briefing.rstrip()}\n"' isekai/pipeline/caption.py` prints `1`.
- [x] 3.2 In `tests/test_caption.py` extend `test_the_open_readers_body_carries_the_photograph_and_the_pinned_sampling` in place: after its `stream` assert add `assert body["prompt"] == "Describe the person.\n"`.
  Verify: `git grep -c -F 'assert body["prompt"] == "Describe the person.\n"' tests/test_caption.py` prints `1`.
- [x] 3.3 In `tests/test_caption.py` extend `test_the_caption_records_the_options_the_reader_sent` in place: stack `@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")` above its marker and, after its last assert, add `assert sent["prompt"] == BRIEFING_PATH.read_text().rstrip() + "\n"`.
  Verify: `git grep -c -F 'assert sent["prompt"] == BRIEFING_PATH.read_text().rstrip() + "\n"' tests/test_caption.py` prints `1`.
- [x] 3.4 The phase's file agrees with the keys.
  Verify: `uv run pytest tests/test_caption.py` passes.

## 4 — The seal and the commit

- [x] 4.1 **HALT CHECK** The seal refuses on a file that is unread at the line the mutant `PA-14` names; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'if unread:' isekai/pipeline/importing.py` prints `1`.
- [x] 4.2 **HALT CHECK** The final move is one `os.rename` of the dot folder, the line [D7](design.md#d7) wraps; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'os.rename(build.parent, collection)' isekai/pipeline/importing.py` prints `1`.
- [x] 4.3 In `tests/test_importing.py` add `test_a_commit_asked_while_a_file_is_unread_is_refused_and_lands_once_it_is_read`, carrying `import:stage:a-commit-waits-for-every-file-to-be-read`. It builds `importing.Imports(library, LIMIT, publish)` as `test_a_staged_file_is_removed_alone_and_never_once_sealed` does, patches `importing._clean` with a function that waits on an `Event` up to ten seconds and then calls the real one, and puts `a.jpg`. `imports.commit(staged, "trip")` raises `Refusal` matching `0 of 1 files are read`; the event is set in a `finally`, the read is waited for, and the same commit lands `a.jpg` in `trip/sources`.
  Verify: `uv run pytest tests/test_importing.py::test_a_commit_asked_while_a_file_is_unread_is_refused_and_lands_once_it_is_read` passes.
- [x] 4.4 In `tests/test_importing.py` add `test_a_refused_commit_leaves_the_import_open_for_another_file`, carrying `import:stage:a-refused-commit-leaves-the-import-open`. After `a.jpg` is read, `(library / "taken").mkdir()` and `imports.commit(staged, "taken")` refuses; `reader.put("b.jpg", ...)` is accepted and read; `imports.commit(staged, "free").written` is `("a.jpg", "b.jpg")`.
  Verify: `uv run pytest tests/test_importing.py::test_a_refused_commit_leaves_the_import_open_for_another_file` passes.
- [x] 4.5 In `tests/test_importing.py` extend `test_an_unusable_collection_name_is_refused_and_staging_kept` in place: its parameters become `(name, message)` pairs, `("taken", "a folder of that name")` and, for `""`, `"a/b"` and `".hidden"`, `"not a collection name"`, and its `pytest.raises(Refusal)` takes `match=message`.
  Verify: `git grep -c -F 'match=message' tests/test_importing.py` prints `1`.
- [x] 4.6 In `isekai/pipeline/importing.py` write [D7](design.md#d7): the `try` around the file moves and the final rename in `commit`, and `_put_back` beside `cancel`.
  Verify: `git grep -c -F '_put_back(build, staging)' isekai/pipeline/importing.py` prints `1`.
- [x] 4.7 In `tests/test_importing.py` add `test_a_move_that_fails_puts_the_files_back`, carrying `import:stage:a-failed-move-puts-the-files-back`, parametrized over the names `.collection` and `b.jpg`. It stages `a.jpg` and `b.jpg` with `stage` and `read`, captures `real = os.rename`, and patches `importing.os.rename` with a function that raises `PermissionError(13, "denied")` when `Path(src).name` is the parameter and otherwise calls `real`. `commit(staging, library, "trip")` raises `PermissionError`; the staging folder lists `a.jpg` and `b.jpg` alone and `library / "trip"` is absent. The test restores `real`, and the same commit then writes `("a.jpg", "b.jpg")`.
  Verify: `uv run pytest tests/test_importing.py::test_a_move_that_fails_puts_the_files_back` passes.
- [x] 4.8 In `tests/test_importing.py` add `test_a_name_taken_as_the_move_lands_is_refused_and_the_files_stay`, carrying the key of 4.7 and `import:stage:an-unusable-name-is-refused`. The patched `os.rename` makes `trip` with a file `x` holding `b"rival"` and then calls `real`, when `Path(src).name` is `.collection`. `commit` raises `Refusal` matching `trip: a folder of that name is in the library; pick another`; the staging folder lists `a.jpg` and `b.jpg` alone, `x` still holds `b"rival"`, and with `real` restored a commit under `trip2` writes both files.
  Verify: `uv run pytest tests/test_importing.py::test_a_name_taken_as_the_move_lands_is_refused_and_the_files_stay` passes.
- [x] 4.9 In `tests/test_ui_api.py` add `test_a_commit_whose_name_is_taken_as_it_lands_is_refused_and_the_files_stay_staged`, carrying the key of 4.7. It opens a staging, uploads one photograph and waits until it is read, as `test_an_upload_is_answered_before_it_is_read_and_files_are_read_in_turn` does, and then patches `importing_module.os.rename` as 4.8 does. The commit post `{"collection": "trip"}` answers `409` holding `a folder of that name is in the library`, and `GET /api/staging/{staged}/files/{name}` still answers `200`.
  Verify: `uv run pytest tests/test_ui_api.py::test_a_commit_whose_name_is_taken_as_it_lands_is_refused_and_the_files_stay_staged` passes.
- [x] 4.10 The phase's files agree with the keys.
  Verify: `uv run pytest tests/test_importing.py tests/test_ui_api.py` passes.

## 5 — The kinds

- [x] 5.1 **HALT CHECK** The decode exempts an MPO from the many-image refusal, the line the mutant `PA-17a` names; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'if image.format != "MPO" and getattr(image, "n_frames", 1) > 1:' isekai/pipeline/importing.py` prints `1`.
- [x] 5.2 In `tests/images.py` add `cr2_bytes`, `dng_bytes`, `arw_bytes` and `cut_tiff_bytes` after `nef_bytes`, each returning the bytes of its row of [D8](design.md#d8)'s table.
  Verify: `git grep -c -E '^def (cr2|dng|arw|cut_tiff)_bytes' tests/images.py` prints `4`.
- [x] 5.3 In `tests/test_importing.py` add `test_a_phone_jpeg_with_a_gain_map_is_stripped_not_refused`, carrying `import:clean:a-phone-jpeg-with-a-gain-map-is-stripped`. It saves a 32 by 32 RGB image as `"MPO"` with `save_all=True` and an 8 by 8 image appended, writes it as `PXL_0001.jpg`, and `read`s it into a staging folder: the `Staged` state is `ready`, `verify` of the staged file is `[]`, and the file opens as a JPEG of one frame.
  Verify: `uv run pytest tests/test_importing.py::test_a_phone_jpeg_with_a_gain_map_is_stripped_not_refused` passes.
- [x] 5.4 In `tests/test_importing.py` add `test_a_raw_photograph_of_each_kind_is_refused_by_its_header`, carrying `import:refuse:a-raw-photograph-is-refused`, parametrized over `cr2_bytes()` as `CR2`, `dng_bytes()` as `DNG` and `arw_bytes()` as `ARW`. Each is written as `shot.bin`; `read` raises `Refusal` matching `shot.bin: a <KIND> RAW photograph` and `export it as JPEG`, and the staging folder is empty.
  Verify: `uv run pytest tests/test_importing.py::test_a_raw_photograph_of_each_kind_is_refused_by_its_header` passes.
- [x] 5.5 In `tests/test_importing.py` add `test_a_tiff_with_a_cut_header_is_refused_as_not_decoding`, carrying `import:refuse:a-file-that-does-not-decode-is-refused`: `cut_tiff_bytes()` written as `cut.tiff`, `read` raises `Refusal` matching `cut.tiff: does not decode as an image` and not holding `RAW`.
  Verify: `uv run pytest tests/test_importing.py::test_a_tiff_with_a_cut_header_is_refused_as_not_decoding` passes.
- [x] 5.6 The phase's file agrees with the keys.
  Verify: `uv run pytest tests/test_importing.py` passes.

## 6 — The mutants die

- [x] 6.1 **HALT CHECK** `0135-the-paydown` is merged: the replay mode and the target exist; if they do not, this phase has nothing to run.
  Verify: `git grep -c -F 'tools.mutate --edits tests/mutants.json' Makefile` prints `1`.
- [x] 6.2 **HALT CHECK** `0137-the-server` is merged: `tests/mutants.json` holds its entry `UB-4`, so this change appends after it.
  Verify: `grep -c -F '"finding": "UB-4"' tests/mutants.json` prints `1`.
- [x] 6.3 **HALT CHECK** The review's lines are written as [D3](design.md#d3) and [D4](design.md#d4) quote them, so the finds of [mutants.json](mutants.json) stand.
  Verify: `grep -c -F -e 'else token_budget(fields, schema, definition).total' -e 'create(path, APPROVED_FILE, body)' isekai/pipeline/review.py` prints `2`.
- [x] 6.4 **HALT CHECK** The import's lines are written as [D7](design.md#d7) quotes them, so the finds stand.
  Verify: `grep -c -F -e '_put_back(build, staging)' -e '            if collection.exists():' isekai/pipeline/importing.py` prints `2`.
- [x] 6.5 Append each entry of [mutants.json](mutants.json) to `tests/mutants.json`, keys and order unchanged, indented as the file is; each opens with `"finding":`.
  Verify: `grep -c -E '"finding": "(PB-1a|PB-1b|PB-2|PB-2b|PB-2c|PB-3a|PB-3b|PA-6|PA-14|PA-15|PA-16a|PA-16b|PA-17a|PA-17b|PA-18a|PA-18b|PA-18c|PA-18d|PA-19)"' tests/mutants.json` prints `19`.
- [x] 6.6 Run the replay. A line that names a survivor goes to 6.7.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
- [x] 6.7 For each `survivor` line 6.6 printed, add in the file its entry names a test red with the mutant in place and green without it; only where no input tells the mutant from the line, give the entry `equivalent` with the reason, proven by reading the line. Never delete an entry. Where 6.6 printed none, this task holds.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
