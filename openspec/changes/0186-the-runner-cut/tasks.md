# The runner cut — tasks

Pin `_per_item` by mutation, cut it into builders, a table and a runner in [`isekai/interface/cli.py`](../../../isekai/interface/cli.py), then replay the mutation over the new code.

## Progress

- [x] 1 — Pin `_per_item` by mutation · moderate
- [x] 2 — Cut `_per_item` into builders, a table and a runner · hard
- [x] 3 — Replay the mutation over the new code · moderate

## 1 — Pin `_per_item` by mutation

- [x] 1.1 **HALT CHECK** The premise of [D8](design.md#d8) stands: `_per_item` is in `isekai/interface/cli.py`, where the mutation run of 1.3 reads it.
  Verify: `git grep -n -e '^def _per_item' -- isekai/interface/cli.py` prints one line.

- [x] 1.2 In `tests/test_pipeline_cli.py`, add `test_per_item_refuses_a_verb_that_is_no_stage` and `test_per_item_opens_the_run_before_it_refuses_a_verb`, as [D3](design.md#d3) says. Both import `_per_item` beside `_flows_for` from `isekai.interface.cli`, call `_per_item("draft", argparse.Namespace(progress="json"), wired, {}, [])` on the file's own wiring and run the work it returns. The first runs it on a photograph the file's fixtures write, asserts a `Refusal` whose text is `'draft' is not a stage this build runs` and asserts `wired.out` holds nothing. The second runs it on an identifier that names no photograph and no run, and asserts the `Refusal` is not the miss. Mark both `spec_exempt("structural: the table's miss is reached by no verb")`.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k test_per_item_` exits 0.

- [x] 1.3 Run the mutation over the lines of `_per_item` before any line moves, per [D8](design.md#d8): `uv run python -m tools.mutate isekai/interface/cli.py:372-582 --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_resume.py tests/test_tagging.py tests/test_assign.py tests/test_review.py`. Kill each survivor with a case in `tests/test_pipeline_cli.py`; a survivor no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run python -m tools.mutate isekai/interface/cli.py:372-582 --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_resume.py tests/test_tagging.py tests/test_assign.py tests/test_review.py` exits 0.

## 2 — Cut `_per_item` into builders, a table and a runner

- [x] 2.1 In `isekai/interface/cli.py`, between `_seam` and `_per_item`, add `_Item` and `_item_of(args, wired, flows, collected)` as in [D1](design.md#d1) and [D6](design.md#d6): the reporter, `new_version`, the memoised `vocabulary` and `field_map`, and the `tagger` thunk move out of `_per_item` with their docstrings, and `_item_of` returns the `_Item`.
  Verify: `git grep -n -e '^class _Item' -e '^def _item_of' -- isekai/interface/cli.py` prints a line for each.

- [x] 2.2 After them, add the builders `_caption_step`, `_tag_step`, `_sheet_step`, `_review_step` and `_approve_step`, each `(run: Run, item: _Item)` returning the step its branch of `_per_item` defined, the body unchanged but for reading its context as `item.<name>`, per [D2](design.md#d2). The approve step reads `flow = item.flows[name]` after its `--cancel` branch has returned and passes `definition=flow,` on a line of its own.
  Verify: `git grep -n -e '^def _caption_step' -e '^def _tag_step' -e '^def _sheet_step' -e '^def _review_step' -e '^def _approve_step' -- isekai/interface/cli.py` prints a line for each.

- [x] 2.3 After the builders, add `_BUILDERS` as in [D3](design.md#d3), then `_reported(item, run, verb, name, step)` and `_run_item(verb, run, item)` as in [D4](design.md#d4); `_reported` is today's nested `reported`, and `_run_item` ends with the `across` loop, over `[None]` for a photograph's verb and over the flows otherwise.
  Verify: `git grep -n -e '^_BUILDERS' -e '^def _reported' -e '^def _run_item' -- isekai/interface/cli.py` prints a line for each.

- [x] 2.4 Rewrite `_per_item` to build its `_Item` with `_item_of` and to return a `work` that holds `assign`, the opening of the run with its refusal reported for each name, `show` and a call of `_run_item`, as in [D5](design.md#d5). Delete the chain, each `elif verb ==` branch of it, and every closure it held.
  Verify: `git grep -n -F "elif verb ==" -- isekai/interface/cli.py` prints nothing.

- [x] 2.5 In `tests/mutants.json`, re-point `PB-2b` per [D8](design.md#d8): its `find` becomes `definition=flow,\n` and its `replace` stays `definition=None,\n`; its `path`, `tests` and `why` stand.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

- [x] 2.6 In `tests/test_ratchets.py`, delete the rows `"isekai/interface/cli.py::_per_item": 214,` and `"isekai/interface/cli.py::_per_item.work": 154,` from `LONG_FUNCTIONS`, per [D7](design.md#d7).
  Verify: `git grep -n -F "cli.py::_per_item" -- tests/test_ratchets.py` prints nothing.

- [x] 2.7 In `tests/test_ratchets.py`, set `FUNCTION_ROWS = 8` to `FUNCTION_ROWS = 6`, per [D7](design.md#d7).
  Verify: `git grep -n -e '^FUNCTION_ROWS = 6' -- tests/test_ratchets.py` prints one line.

## 3 — Replay the mutation over the new code

- [x] 3.1 Find the lines of the new code, from `_Item` to the line before `_assign`.
  Verify: `git grep -n -e '^@dataclasses.dataclass' -e '^def _assign(' -- isekai/interface/cli.py` prints two lines: the line of the decorator over the item class, then the line of the assign function's definition.

- [x] 3.2 Run `uv run python -m tools.mutate isekai/interface/cli.py:<first>-<last> --tests tests/test_pipeline_cli.py tests/test_progress.py tests/test_resume.py tests/test_tagging.py tests/test_assign.py tests/test_review.py`, with `<first>` the line of `_Item`'s decorator and `<last>` one less than the line of `def _assign(`, both from 3.1. Kill each survivor with a case in `tests/test_pipeline_cli.py`; a survivor no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
