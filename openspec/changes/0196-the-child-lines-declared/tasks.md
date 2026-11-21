# The child lines declared — tasks

Declare a child's lines and `--progress json` once in `isekai/interface/progress.py`, move `Steps`, `_Images` and `progress_line` there, and make the emitters and the readers use it. No printed byte changes.

## Progress

- [x] 1 — The module · moderate
- [x] 2 — The emitters · moderate
- [x] 3 — The readers · moderate
- [ ] 4 — The decision and the docs · moderate

## 1 — The module

- [x] 1.1 **HALT CHECK** Pin the two branches of `Steps` the version before leaves free, then run `tools.mutate` over `Steps` and `Reporter.item` before any line moves. The first run, at `15d39a55`, printed "19 killed, 2 survived": `return self.out` → `return None` in `Steps.child`, and `and` → `or` in `Steps.image`'s record test. First add to `tests/test_progress.py`, after `test_a_render_line_becomes_the_sessions_image_line`, `test_a_quiet_session_hands_its_child_its_own_stream` with `@pytest.mark.spec_exempt("structural: a quiet session with no record hands its child its own stream")`, asserting `Steps(out, False).child() is out`; and `test_a_session_records_an_image_only_with_a_record_and_its_runs` with `@pytest.mark.spec_exempt("structural: an image reaches the record only when both are given")`, asserting that `Steps(out, True).image(render, 2, runs)` with no record prints the image line and raises nothing, and that a stand-in record kept on a `Steps` is handed no image when `runs` is `None`. Neither changes a line of `isekai/`. The ranges are `isekai/interface/render.py:412-456` and `isekai/interface/verbs/common.py:212-238` after 0195's merge; if `git grep -n -e "^class Steps" -e "^class _Images" -- isekai/interface/render.py` prints other lines, the range runs from the `Steps` line to the line above the blank lines over `_Images`. A survivor left now is a line the pins still miss: halt.
  Verify: `uv run python -m tools.mutate isekai/interface/render.py:412-456 isekai/interface/verbs/common.py:212-238 --tests tests/test_progress.py tests/test_render.py tests/test_pipeline_cli.py` exits 0.
- [x] 1.2 Create `isekai/interface/progress.py`: a docstring with an example of each line and who writes and reads it, the standard-library imports of [D1](design.md#d1), then in this order the names of [the names table](design.md#names) down to `LANDED`, the `TypedDict`s of [D3](design.md#d3), `Recorder`, and `emit` of [D4](design.md#d4). Each class and function carries a docstring and its annotations, as `ruff` asks of `isekai/`.
  Verify: `uv run python -c "from isekai.interface.progress import ItemLine, StepLine, ImageLine, Recorder, emit"` exits 0.
- [x] 1.3 Move `progress_line`, `Steps` and `_Images` from `isekai/interface/render.py` into `progress.py`, after `emit`, in that order: `_Images` annotates `Steps`, so `Steps` comes first. Apply the changes of [D2](design.md#d2); their docstrings and behaviour stay.
  Verify: `uv run python -c "from isekai.interface.progress import Steps, _Images, progress_line"` exits 0.
- [x] 1.4 In `isekai/interface/render.py` delete those definitions, and import `Steps` plainly and `_Images` and `progress_line` as `_Images as _Images` and `progress_line as progress_line` from `isekai.interface.progress`, with a comment that the tests import them here.
  Verify: `git grep -n -e "^class Steps" -e "^class _Images" -e "^def progress_line" -- isekai/interface/render.py` prints nothing.
- [x] 1.5 Drop each import `render.py` no longer reads and each `progress.py` does not, as `ruff` names them. `progress.py` imports nothing from `isekai`.
  Verify: `uv run ruff check isekai/interface/render.py isekai/interface/progress.py` exits 0.
- [x] 1.6 In `isekai/interface/ui/jobs.py` import `progress_line` with `from isekai.interface.progress import`, not from `isekai.interface.render`. Each name tasks 3.1 to 3.3 take joins that one statement.
  Verify: `git grep -c -F "from isekai.interface.progress import" -- isekai/interface/ui/jobs.py` prints `isekai/interface/ui/jobs.py:1`.
- [x] 1.7 In `tests/test_progress.py` add `test_the_progress_module_imports_the_standard_library_alone` with `@pytest.mark.spec_exempt("structural: the lines' module loads under -S")`. It parses `isekai/interface/progress.py` with `ast` and asserts each imported top-level module is in `sys.stdlib_module_names`, and that no import is from `isekai`.
  Verify: `uv run pytest tests/test_progress.py -k test_the_progress_module_imports_the_standard_library_alone` exits 0.
- [x] 1.8 Add `test_the_declared_names_are_the_words_the_lines_print` with `@pytest.mark.spec_exempt("structural: the declared names are the words printed")`. It asserts the value of each constant of [the names table](design.md#names), `RENDER == STAGE_RENDER` of `isekai.pipeline.generate`, `Steps(out, True).flag == ARGUMENT` and `Steps(out, False).flag == ()`.
  Verify: `uv run pytest tests/test_progress.py -k test_the_declared_names_are_the_words_the_lines_print` exits 0.
- [x] 1.9 Add `test_each_sample_line_is_the_shape_it_declares` with `@pytest.mark.spec_exempt("structural: each sample line is its declared shape")`. For each line of `ITEM_CASES` and `WORK_CASES` it asserts the parsed keys are an ordered subsequence of the keys of `ItemLine.__annotations__`, `run`, `stage` and `state` among them, `stage` is in `get_args(Stage)` and `state` in `get_args(ItemState)`. It asserts, for `STEP_CASES`, keys equal to those of `StepLine` and `step` and `state` in `get_args(StepName)` and `get_args(StepState)`, and, for `IMAGE_LINES`, keys equal to those of `ImageLine`.
  Verify: `uv run pytest tests/test_progress.py -k test_each_sample_line_is_the_shape_it_declares` exits 0.
- [x] 1.10 Leave every test the file held untouched, and add no test but the two of 1.1, which pin the survivors of its first run, those of 1.7 to 1.9, and the one of 4.4, which pins the survivor of its first run. The file holds 15 tests at the end of phase 1 and 16 at the end of phase 4.
  Verify: `git grep -c -e "^def test_" -- tests/test_progress.py` prints `tests/test_progress.py:15` at the end of phase 1 and `tests/test_progress.py:16` once 4.4 is done.

## 2 — The emitters

- [x] 2.1 In `isekai/interface/verbs/common.py` make `Reporter.item` end on `emit(self.out, line)`, replacing the `print(json.dumps(line), …)` and its comment, and import `emit` from `isekai.interface.progress`. Drop the `json` import, which nothing else there reads.
  Verify: `git grep -n -F "json.dumps" -- isekai/interface/verbs/common.py` prints nothing.
- [x] 2.2 In `progress_flag` of `isekai/interface/verbs/common.py`, in `render_arguments` of `isekai/interface/verbs/session.py` and in the argument of `isekai/interface/verbs/edits.py`, add `FLAG` of `isekai/interface/progress.py` with `choices=[FORMAT]` in place of the literals `"--progress"` and `"json"`. Each help text stays.
  Verify: `git grep -n -F '"--progress"' -- isekai/interface/verbs` prints nothing.
- [x] 2.3 In `isekai/interface/verbs/runner.py` replace `"start"`, `"refused"` and `"done"` in `_reported` and in the unopened-run refusal with `START`, `REFUSED` and `DONE`; in `isekai/interface/verbs/prepare.py` replace `"sheet", "refused"` with `SHEET, REFUSED`. Both import them from `isekai/interface/progress.py`.
  Verify: `git grep -n -e '"start"' -e '"refused"' -e '"done"' -- isekai/interface/verbs/runner.py isekai/interface/verbs/prepare.py` prints nothing.
- [x] 2.4 In `isekai/interface/verbs/generate.py` replace `STAGE_RENDER` and `"done"` with `RENDER` and `DONE`, and drop the `STAGE_RENDER` import; in `isekai/interface/verbs/edits.py` replace `"edit"` and `"done"` in `sample_one` with `EDIT` and `DONE`. Both import them from `isekai/interface/progress.py`.
  Verify: `git grep -n -F "STAGE_RENDER" -- isekai/interface/verbs/generate.py` prints nothing.
- [x] 2.5 In `isekai/interface/render.py` spread `*ARGUMENT` of `isekai/interface/progress.py` in `_rendered`'s `generate` argv in place of `"--progress", "json"`, and pass `ARGUMENT` to `_edit_argv` in place of `("--progress", "json")`.
  Verify: `git grep -n -F '"--progress"' -- isekai/interface/render.py` prints nothing.

- [x] 2.6 Replace `== "json"` with `== FORMAT` of `isekai/interface/progress.py` where the parsed argument is tested: in `isekai/interface/verbs/prepare.py`, `isekai/interface/verbs/edits.py`, `isekai/interface/verbs/generate.py`, `isekai/interface/verbs/runner.py` and `json_lines` of `isekai/interface/render.py`. Each file adds `FORMAT` to its import from `isekai/interface/progress.py`, or one such import if it has none.
  Verify: `git grep -n -F '== "json"' -- isekai/interface` prints nothing.

## 3 — The readers

- [x] 3.1 In `isekai/interface/ui/jobs.py` delete `PREPARE` and its comment, and import `PREPARE` from `isekai/interface/progress.py`; key `REACHED` by `TAG` and `SHEET` of that module.
  Verify: `git grep -n -e "^PREPARE" -- isekai/interface/ui/jobs.py` prints nothing.
- [x] 3.2 In `isekai/interface/ui/jobs.py`, in `_Job.complete` compare `line.get("state")` with `DONE`; in `Jobs._render_child` replace `== "image"` with `== IMAGE` and take `LANDED` for the image's keys in place of the names it spells. Both come from `isekai/interface/progress.py`.
  Verify: `git grep -n -F '== "image"' -- isekai/interface/ui/jobs.py` prints nothing.
- [x] 3.3 In `isekai/interface/ui/jobs.py`, in `prepare_command` and `render_command`, spread `*ARGUMENT` of `isekai/interface/progress.py` in place of `"--progress", "json"`. Each command's list is otherwise as it was.
  Verify: `git grep -n -F '"--progress"' -- isekai/interface/ui/jobs.py` prints nothing.

## 4 — The decision and the docs

- [ ] 4.1 In `docs/decisions.md` add `### D76 · The child's lines are declared in isekai/interface/progress.py` after D73, with the bold sentence, the *Why* and *Accepts* bullets and the *Made by* bullet naming `0196`, all as [D7](design.md#d7) gives them.
  Verify: `git grep -c -F "### D76" -- docs/decisions.md` prints `docs/decisions.md:1`.
- [ ] 4.2 In `isekai/interface/README.md` add a `progress.py` row after `render.py` in `## Files`, saying it declares the lines and the flag, holds `emit`, `progress_line`, `Steps` and `_Images`, and **imports the standard library alone**. Add a `progress.py` row after `render.py` in `## Imported by` with `—` in its other cells, then run `uv run python -m tools.derive_imported_by`, which fills it.
  Verify: `git grep -c -e "^| .progress.py. |" -- isekai/interface/README.md` prints `isekai/interface/README.md:2`.
- [ ] 4.3 In `isekai/README.md` add `progress.py` after `render.py` in the `interface/` row; in `docs/modules.md`, where the sentence "`--progress json` is `Reporter` of `interface/verbs/common.py`" wraps after `--progress json`, make it read "`--progress json` is the lines `interface/progress.py` declares, which `Reporter` of `interface/verbs/common.py` and `Steps` write", keeping the wrap.
  Verify: `git grep -n -F "interface/progress.py" -- docs/modules.md` prints one line.
- [ ] 4.4 Pin `_Images.write`'s return, then run `tools.mutate` over the whole of `isekai/interface/progress.py`, the lines `Steps` and `_Images` now hold included, one range a run. The first run, at `8647358f`, printed "21 killed, 1 survived": `return len(text)` → `return None` in `_Images.write` (`isekai/interface/progress.py:176`). It is not equivalent: `write` of a text stream returns the count of characters it took, and `print` merely ignores it. First add to `tests/test_progress.py`, after `test_a_render_line_becomes_the_sessions_image_line`, `test_an_images_stream_returns_the_characters_it_took` with `@pytest.mark.spec_exempt("structural: a stream's write returns the characters it took")`, asserting that `_Images(Steps(out, True), 2, None)` returns `len(text)` from `write` for a whole line and for a partial line with no newline. It changes no line of `isekai/`. A survivor left after it is a line the pins still miss: halt.
  Verify: `uv run python -m tools.mutate isekai/interface/progress.py:1-600 --tests tests/test_progress.py tests/test_render.py tests/test_pipeline_cli.py` exits 0.
- [ ] 4.5 Run `tools.mutate` over `Reporter.item` again. The edit of 2.1 shortens it by a line, so the range stops at line 237 when the imports of 2.1 and 2.2 add one statement and drop one. If `git grep -n -e "    def item" -e "^def say" -- isekai/interface/verbs/common.py` prints other lines, the range runs from the `def item` line to the line above the blank lines over `say`.
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/common.py:212-237 --tests tests/test_progress.py tests/test_render.py tests/test_pipeline_cli.py` exits 0.
- [ ] 4.6 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 4.7 Confirm `isekai/interface/progress.py` names nothing of `isekai.interface.render`, which would close a cycle.
  Verify: `git grep -n -F "isekai.interface.render" -- isekai/interface/progress.py` prints nothing.
