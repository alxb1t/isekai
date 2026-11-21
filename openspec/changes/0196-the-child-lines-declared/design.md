# The child lines declared — design

Declare the lines a child prints, and the flag that asks for them, once in `isekai/interface/progress.py`, and make the emitters and the readers use it. Verdict: feasible, in the phases of [tasks](tasks.md); the version before pins every line, so a moved byte fails a test.

## Context

A child verb prints JSON lines on stdout under `--progress json`. `Reporter.item` in `isekai/interface/verbs/common.py` prints the item line. `Steps` in `isekai/interface/render.py` prints the session's step and image lines, and `_Images` there reads a render line back into an image line through `progress_line`.

The app reads the same lines in `isekai/interface/ui/jobs.py`: `_Job.complete` and `Jobs._run` read an item line, `Jobs._render_child` a step line, and each calls `progress_line`. Each verb spells its stage and state as a literal. `--progress json` is spelled in the argument functions of `verbs/common.py`, `verbs/session.py` and `verbs/edits.py`, in `Steps.flag`, in `_rendered`'s argv and `_edit_argv`'s caller in `render.py`, and in `prepare_command` and `render_command` of `jobs.py`.

The module lands beside `render.py` as a leaf: it imports the standard library alone, so `python -m isekai` under `-S` still loads it, and no layer rule moves.

```
verbs/common.py  Reporter.item ──┐                       ┌── ui/jobs.py  complete, _run, _render_child
verbs/runner.py  stage, state ───┤                       │
verbs/generate.py, edits.py ─────┼─▶ interface/progress.py ◀┤
render.py  _rendered, Steps ─────┘   (stdlib only)       └── render.py  _Images
```

## Goals / Non-Goals

- Goal: each line shape, stage, state and step name, and the flag, is spelled in one module.
- Goal: `Steps`, `_Images` and `progress_line` live there and stay importable from `isekai.interface.render`.
- Goal: every line a child prints stays byte-equal, key order and flush included.
- Non-goal: a change to a line, a flag's help text or a printed word.
- Non-goal: `ui/src/wire.ts`, `shapes.py`, or any file under `tests/record/`, `ui/`, `tools/` or `evaluation/`.
- Non-goal: a scenario, a spec delta or a change to an existing test's assertion.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai/interface/progress.py`, standard library only | the lines are the interface's own wire between its verbs and its job loops; the foundation has no reader of them | the foundation, which nothing below the interface reads |
| [D2](#d2) | `Steps`, `_Images` and `progress_line` move there and are bound back in `render.py` | the emitters and their reader sit with the shapes; no test import changes | repointing the tests |
| [D3](#d3) | The shapes are `TypedDict`s, the vocabularies `Literal`s, and an emitter's parameters stay `str` | `ty` checks the tests, whose cases pass plain `str`; a test holds the samples to the declaration | `Literal` parameters, which fail the version before's cases |
| [D4](#d4) | One writer, `emit`, and one reader, `progress_line` | the encoding is spelled once, and a test of either holds every line | each class printing for itself |
| [D5](#d5) | The flag is `FLAG`, `FORMAT` and `ARGUMENT`; each use reads them | the flag is spelled where the child is asked and where it is read | a literal per site |
| [D6](#d6) | The stage names a verb or a reader spells are constants, and `PREPARE` moves | the readers compare these words against what the verbs print | leaving `PREPARE` in `jobs.py` |
| [D7](#d7) | One decision in force, docs `D74`, is added to `docs/decisions.md` | the page says what holds; this file says how it came about | none |

### D1

The module imports `io`, `json`, `collections.abc`, `pathlib` and `typing`, and nothing of `isekai`. `shapes.py` does not name the line's type, so the wire's deriver reads nothing new and `ui/src/wire.ts` is unchanged.

### D2

`render.py` imports `Steps` as itself and re-exports `_Images` and `progress_line` as `from isekai.interface.progress import _Images as _Images`, the form `record_running` already takes there. Those definitions leave `render.py` whole, with the changes below:

- `Steps.record` is typed `Recorder | None`. `Recorder` is a `Protocol` in `progress.py` with `step(step: str, state: str) -> None` and `image(item: Mapping[str, Any], runs: Path) -> None`, which `Records` meets. `progress.py` cannot name `Records`: it imports nothing of `isekai`.
- `Steps._line` calls `emit` and prints nothing itself.
- `Steps.flag` is `ARGUMENT` when enabled, else `()`.
- `Steps.image` names `IMAGE` and `DONE`, and its `named` keys are `("run", *LANDED)`.
- `_Images.write` compares a line's `stage` with `RENDER` and its `state` with `DONE`.

### D3

| shape | keys, in print order |
|---|---|
| `ItemLine` | `run`, `flow`, `stage`, `state`, `digest`, `version`, `seed`, `file`, `message` |
| `StepLine` | `step`, `state` |
| `ImageLine` | `step`, `n`, `of`, `run`, `digest`, `flow`, `version`, `seed`, `state` |

`ItemLine` requires `run`, `stage` and `state`; every other key is `NotRequired`. A render line holds `digest`, `version` and `seed`; an edit line holds `digest`, `version` and `file`; no line holds `seed` and `file` together, so one order serves both. `message` is last.

`Stage`, `ItemState`, `StepName` and `StepState` are `Literal`s of the words in [the names](#names). The emitters keep `str` parameters, so a test case that passes a `str` still type-checks. `tests/test_progress.py` holds each sample line of the version before to these declarations.

### D4

`emit(out, line)` is `print(json.dumps(line), file=out, flush=True)`, with the comment that a job reads a pipe line by line as it happens. `Reporter.item` builds its dict as it does and calls `emit`; `Steps._line` calls `emit`. `progress_line` moves unchanged.

### D5

`FLAG` is `"--progress"`, `FORMAT` is `"json"`, and `ARGUMENT` is `(FLAG, FORMAT)`. Each argument function adds `FLAG` with `choices=[FORMAT]` and keeps its help text. `_rendered` and `render_command` and `prepare_command` spread `ARGUMENT`, and `_edit_argv` is passed it. Where a verb or the session tests the parsed argument, it compares with `FORMAT`.

### D6

`STAGE_RENDER` of `isekai/pipeline/generate.py` is the failure record's key, and D73 keeps the pipeline's own constants. `verbs/generate.py` stops importing it and names `RENDER`; a test holds the two equal.

The `steps.step("pod", …)` and `steps.step("teardown", …)` calls in `render.py` stay literals: `tests/mutants.json` finds them by their text. `REACHED` in `jobs.py` keeps its sets and keys them by `TAG` and `SHEET`.

### D7

Docs `D74` reads: **`isekai/interface/progress.py` declares a child's lines — the item line, and the session's step and image lines — their stage, state and step names, and `--progress json`; `Reporter.item`, `Steps` and `_Images` write and read them there, and `progress_line` is the one reader.** The bullets under it:

- **Why:** a line was spelled by its emitter, again in each verb that names its stage and state, and again in each reader, and no test held them to agree. One module says what a line is, and a test holds each sample to it.
- **Accepts:** the `steps.step` literals in `render.py`, the emitters' `str` parameters, the pipeline's `STAGE_RENDER` and the app's `cell` event stay as they are. Reopen when an emitter is typed by a shape.
- **Made by:** `0196`.

## Names

What `progress.py` declares, in this order after its docstring and imports.

| name | value | read by |
|---|---|---|
| `FLAG`, `FORMAT`, `ARGUMENT` | `"--progress"`, `"json"`, `(FLAG, FORMAT)` | each argument function, `Steps.flag`, `_rendered`, `_edit_argv`'s caller, `prepare_command`, `render_command` |
| `TAG`, `CAPTION`, `SHEET`, `RENDER`, `EDIT` | `"tag"`, `"caption"`, `"sheet"`, `"render"`, `"edit"` | `PREPARE`, `REACHED`, `_Images`, the verbs |
| `Stage` | `Literal` of those five and `"review"`, `"approve"` | the test of the samples |
| `PREPARE` | `(TAG, CAPTION, SHEET)` | `_Job.describe` |
| `START`, `DONE`, `REFUSED` | `"start"`, `"done"`, `"refused"` | `runner.py`, `prepare.py`, `generate.py`, `edits.py`, `_Images`, `_Job.complete` |
| `ItemState` | `Literal` of those | the test of the samples |
| `POD`, `TEARDOWN`, `IMAGE` | `"pod"`, `"teardown"`, `"image"` | `Steps.image`, `_render_child` |
| `StepName`, `StepState` | `Literal` of those, and of `"starting"`, `"ready"`, `"lost"`, `"refused"`, `"done"`, `"failed"` | the test of the samples |
| `LANDED` | `("digest", "flow", "version", "seed")` | `Steps.image`, `_render_child` |
| `ItemLine`, `StepLine`, `ImageLine` | the [shapes](#d3) | the test of the samples |
| `Recorder` | a `Protocol` | `Steps.record` |
| `emit`, `progress_line`, `Steps`, `_Images` | as [D2](#d2) and [D4](#d4) say | `Reporter.item`, `render.py`, `jobs.py` |

`POD` and `TEARDOWN` are declared for the vocabulary and the test; no call site reads them.

## Tests

Every added test is a unit test in `tests/test_progress.py`, and none removes or merges a test. No end-to-end run is added.

| measure | command | before | after |
|---|---|---|---|
| tests in the file | `git grep -c -e "^def test_" -- tests/test_progress.py` | `tests/test_progress.py:10` | `tests/test_progress.py:13` |

| test | proves |
|---|---|
| `test_the_progress_module_imports_the_standard_library_alone` | `progress.py` imports no module outside `sys.stdlib_module_names` |
| `test_the_declared_names_are_the_words_the_lines_print` | each constant's value, `STAGE_RENDER == RENDER`, and `Steps(out, True).flag == ARGUMENT` |
| `test_each_sample_line_is_the_shape_it_declares` | each sample line's keys are its shape's keys in order, its words are declared |

The proof the move changes no byte is the version before's tests, and `tools.mutate` over the moved lines. Layer: each new test is the lowest that can fail (T1); none adds a step to an existing test, because none of those holds a declaration (T2).

## Dependencies

None.

## Risks / Trade-offs

- A `TypedDict` does not fix the order an emitter prints. The test of the samples holds the order, so a reordered emitter fails it.
- No emitter is typed by a shape: `Reporter.item` takes `**more` and `Steps._line` takes keywords. The byte samples and the test of the samples hold what `ty` does not.
- The mutation ranges name lines of the tree at the cut. A version merged since moves them, and the tasks say how to print the new ones.

## Verdict

Feasible. Each phase ends with its tests passing.
