# The child lines pinned — design

Pin each JSON line a child prints as bytes, and read each back, in `tests/test_progress.py`, before a version moves the code that prints them. Verdict: feasible, in the phases of [tasks](tasks.md).

## Context

A child verb prints JSON lines on stdout under `--progress json`. The item line is `Reporter.item` in `isekai/interface/verbs/common.py`: `run`, `flow` when the stage has one, `stage`, `state`, what the item adds, then `message`. The session's lines are `Steps.step` and `Steps.image` in `isekai/interface/render.py`: `step`, `state`, and for an image `n`, `of`, `run`, `digest`, `flow`, `version`, `seed`, `state`.

The readers are `progress_line` and `_Images` in `isekai/interface/render.py`, and the app's job loops in `isekai/interface/ui/jobs.py`.

Every existing test parses a line with `json.loads` and compares a dict, so key order, separators and the flush are held by none. `tests/test_progress.py` already imports `Steps`, `_Images` and `progress_line` from `isekai.interface.render`; the next version binds them back there, so these tests need no edit when it moves them.

## Goals / Non-Goals

- Goal: the text of each line kind is held, key order and separators included.
- Goal: what each emitter prints, `progress_line` reads back to the dict it was built from, and a render line becomes the session's image line.
- Non-goal: any file under `isekai/`, `ui/`, `tools/`, `evaluation/` or `tests/record/`.
- Non-goal: a change to an existing test's assertion.
- Non-goal: a scenario, a spec delta or a decision in force.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Tests alone, in `tests/test_progress.py`; no record file | a pin lands before the version that leans on it; a record file is a person's own run | a file under `tests/record/` |
| [D2](#d2) | Compare the text a stream holds, never a parsed dict | a dict compares equal under any key order | `json.loads` on the samples |
| [D3](#d3) | Emit through the real emitters, on a `StringIO` | the pin must move when the printing code moves | a literal built by the test |
| [D4](#d4) | Read back through `progress_line` and `_Images` | every reader calls the first; the second turns a render line into a step | a test through `Jobs` |
| [D5](#d5) | Bind a test to the scenario it proves; exempt the rest as structural | a render, an edit and a read-back line fit no requirement | a new scenario |

### D1

The brief settled it: the version is tests alone, `skip_specs`. A byte sample of a real run would hold a person's run id, so the samples are synthetic.

### D2

`out.getvalue()` is compared with the joined text of the [samples](#samples), each line ending in a newline. Each test also asserts one flush per line: the emitters flush because a job reads a pipe as the lines happen.

### D3

`Reporter(out, err, True).item(...)` and `Steps(out, True)` are the emitters. A real `sheet` run through `dispatch` holds the verb's own start, done and refused lines, so a verb that stops passing its arguments in order fails too.

### D4

`progress_line` is the one parser the child's readers share. `_Images` is the one reader that prints: it writes an image step for each render line it is fed, holding a partial line until its newline.

The app's job loops in `isekai/interface/ui/jobs.py` read the dicts `progress_line` returns, and `tests/test_ui_jobs.py` holds them on recorded lines.

### D5

A sheet's lines prove the scenarios of `cli:progress`, and the session's lines `cli:render-progress:each-image-of-the-total`. The render and edit lines fit none, as `test_edit_pending_progress_json_prints_a_line_per_sampled_edit` already says. The read-back is structural.

## Samples

Run `0d4b7e6fb2a8_portrait`, flow `summon-anime-wai`, digest `ab12`. Each line is the whole text `out` holds, newline excluded.

| emitter call | line |
|---|---|
| `item(run, flow, "sheet", "start")` | `{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "sheet", "state": "start"}` |
| `item(run, flow, "sheet", "done")` | `{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "sheet", "state": "done"}` |
| `item(run, flow, "sheet", "refused", "no wd14 tags")` | `{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "sheet", "state": "refused", "message": "no wd14 tags"}` |
| `item(run, None, "tag", "start")` | `{"run": "0d4b7e6fb2a8_portrait", "stage": "tag", "state": "start"}` |
| `item(run, None, "caption", "refused", "no reader")` | `{"run": "0d4b7e6fb2a8_portrait", "stage": "caption", "state": "refused", "message": "no reader"}` |
| `item(run, flow, "render", "done", digest="ab12", version=2, seed="42")` | `{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "render", "state": "done", "digest": "ab12", "version": 2, "seed": "42"}` |
| `item(run, flow, "edit", "done", digest="ab12", version=1, file="42.edit-1.png")` | `{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "edit", "state": "done", "digest": "ab12", "version": 1, "file": "42.edit-1.png"}` |
| `step("pod", "starting")` | `{"step": "pod", "state": "starting"}` |
| `step("pod", "ready")` | `{"step": "pod", "state": "ready"}` |
| `step("pod", "lost")` | `{"step": "pod", "state": "lost"}` |
| `step("pod", "refused")` | `{"step": "pod", "state": "refused"}` |
| `step("teardown", "done")` | `{"step": "teardown", "state": "done"}` |
| `step("teardown", "failed")` | `{"step": "teardown", "state": "failed"}` |
| `image(<the render line as a dict>, 2, None)`, first | `{"step": "image", "n": 1, "of": 2, "run": "0d4b7e6fb2a8_portrait", "digest": "ab12", "flow": "summon-anime-wai", "version": 2, "seed": "42", "state": "done"}` |
| the same call, second | the same text with `"n": 2` |

`Steps(out, True).flag` is `("--progress", "json")` and `Steps(out, False).flag` is `()`; a `Steps(out, False)` prints nothing.

## Tests

Every added test is a unit test in `tests/test_progress.py`, and none removes or merges a test. No end-to-end run is added.

| measure | command | before | after |
|---|---|---|---|
| tests in the file | `git grep -c -e "^def test_" -- tests/test_progress.py` | `tests/test_progress.py:4` | `tests/test_progress.py:10` |

| test | proves | binding |
|---|---|---|
| `test_a_sheets_lines_are_these_bytes` | the real `sheet` verb's start, done and refused lines | `cli:progress:each-item-reports-start-and-end`, `cli:progress:a-refusal-is-a-line` |
| `test_an_items_lines_are_these_bytes` | the item lines of the [samples](#samples), a photograph's included | `cli:progress:a-photographs-line-names-no-flow`, `cli:progress:a-refusal-is-a-line` |
| `test_a_renders_and_an_edits_lines_are_these_bytes` | the render and edit lines | structural |
| `test_a_sessions_step_and_image_lines_are_these_bytes` | the step and image lines, the flag and the flush | `cli:render-progress:each-image-of-the-total` |
| `test_each_line_kind_is_read_back_as_what_built_it` | `progress_line` over every sample | structural |
| `test_a_render_line_becomes_the_sessions_image_line` | `_Images` over the item lines | structural |

Layer: each is the lowest that can fail (T1). None adds a step to an existing test, because none of those reaches an emitter on its own, and an added step would pass before it was written (T2).

## Dependencies

None.

## Risks / Trade-offs

- A call site of `Reporter.item` that passes the item's extra arguments in another order is held only for `sheet`, through the real verb. The render and edit lines are pinned at `Reporter.item` with the order the verbs use today, `isekai/interface/verbs/generate.py:84-92` and `isekai/interface/verbs/edits.py:111-119`. The next version builds the line from a declaration and holds that order by its own cases.
- A byte pin fails on a harmless reformat. That is the point: the page and the session read these bytes through a pipe.

## Verdict

Feasible. Each phase ends with the file passing.
