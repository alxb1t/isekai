# The child lines pinned — tasks

Add tests to `tests/test_progress.py` that hold the bytes of each child line and read each back. No other file changes.

## Progress

- [x] 1 — The samples · moderate
- [ ] 2 — The read-back · moderate

## 1 — The samples

- [x] 1.1 Add `test_a_sheets_lines_are_these_bytes` to `tests/test_progress.py`, bound by `@pytest.mark.spec("cli:progress:each-item-reports-start-and-end")` and `@pytest.mark.spec("cli:progress:a-refusal-is-a-line")`. It runs `_sheet` with `--progress json` over a tagged run, and compares `out` with the text of the start and done lines of [the samples](design.md#samples) for that run and `FLOW`. Over an untagged run it holds the start line whole, and the refused line by its prefix `{"run": "<id>", "flow": "summon-anime-wai", "stage": "sheet", "state": "refused", "message": "` and its end `"}` and newline.
  Verify: `uv run pytest tests/test_progress.py -k test_a_sheets_lines_are_these_bytes` exits 0.
- [x] 1.2 Add `from isekai.interface.verbs import Reporter`, the constants `RUN = "0d4b7e6fb2a8_portrait"` and `DIGEST = "ab12"`, and `ITEM_CASES`, a `(arguments, more, line)` per item row of [the samples](design.md#samples) that is not a render or an edit. Add `test_an_items_lines_are_these_bytes`, bound by `@pytest.mark.spec("cli:progress:a-photographs-line-names-no-flow")` and `@pytest.mark.spec("cli:progress:a-refusal-is-a-line")`: it calls `Reporter(out, err, True).item(RUN, *arguments, **more)` for each case on a `_Flushes` out, asserts `out.getvalue()` is the lines joined with a newline each, and `out.flushed == len(out.getvalue().splitlines())`.
  Verify: `uv run pytest tests/test_progress.py -k test_an_items_lines_are_these_bytes` exits 0.
- [x] 1.3 Add `WORK_CASES`, the same triple for the render and edit rows of [the samples](design.md#samples), and `test_a_renders_and_an_edits_lines_are_these_bytes` with `@pytest.mark.spec_exempt("structural: a generate line and an edit line are these bytes, key order included")`. It holds `WORK_CASES` as 1.2 holds `ITEM_CASES`.
  Verify: `uv run pytest tests/test_progress.py -k test_a_renders_and_an_edits_lines_are_these_bytes` exits 0.
- [x] 1.4 Add `STEP_CASES`, a `(step, state, line)` per step row of [the samples](design.md#samples), and `IMAGE_LINES`, its image rows. Add `test_a_sessions_step_and_image_lines_are_these_bytes`, bound by `@pytest.mark.spec("cli:render-progress:each-image-of-the-total")`: `Steps(out, True).step(...)` for each case, then `Steps.image` once per image row over the render line parsed from `WORK_CASES`, with `total` 2 and `runs` `None`, on a `_Flushes` out. It asserts the text, one flush per line, `Steps(out, True).flag == ("--progress", "json")`, and that `Steps(out, False)` prints nothing and has `flag == ()`.
  Verify: `uv run pytest tests/test_progress.py -k test_a_sessions_step_and_image_lines_are_these_bytes` exits 0.

## 2 — The read-back

- [ ] 2.1 Add `test_each_line_kind_is_read_back_as_what_built_it` with `@pytest.mark.spec_exempt("structural: what an emitter prints, the reader reads back")`. For the line of each case in `ITEM_CASES`, `WORK_CASES` and `STEP_CASES` and each of `IMAGE_LINES` it asserts `progress_line(line) == json.loads(line)` and `json.dumps(progress_line(line)) == line`. It asserts `progress_line` is `None` for `"refused: no tags"`, `"[1, 2]"` and `""`.
  Verify: `uv run pytest tests/test_progress.py -k test_each_line_kind_is_read_back_as_what_built_it` exits 0.
- [ ] 2.2 Add `test_a_render_line_becomes_the_sessions_image_line` with `@pytest.mark.spec_exempt("structural: a render line is the session's image step")`. It feeds `_Images(Steps(out, True), 2, None)` the render line of `WORK_CASES` and a newline in halves, and asserts `out` is empty after the first half and the first of `IMAGE_LINES` after the second. It then writes every line of `ITEM_CASES`, the edit line and the render line rebuilt by `json.dumps` with its `state` set to `refused`, and asserts `out` is unchanged. It writes the render line again and asserts `out` ends with the second of `IMAGE_LINES`.
  Verify: `uv run pytest tests/test_progress.py -k test_a_render_line_becomes_the_sessions_image_line` exits 0.
- [ ] 2.3 Leave every test the file held untouched, and add no test but those of 1.1 to 2.2, so `tests/test_progress.py` holds what it held and those.
  Verify: `git grep -c -e "^def test_" -- tests/test_progress.py` prints `tests/test_progress.py:10`.
