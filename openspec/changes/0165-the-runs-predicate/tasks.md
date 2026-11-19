# The runs predicate — tasks

The rule and its cases, then each site switched between mutation runs, then the decision and its page.

## Progress

- [x] 1 — The rule · moderate
- [x] 2 — The sites · moderate
- [x] 3 — The decision · moderate

## 1 — The rule

- [x] 1.1 Write the cases of [design Tests](design.md#tests) at the end of `tests/test_run_directory.py`, before the code. Import `run_at` and `runs_in` from `isekai.foundation.run`; each test carries `@pytest.mark.spec_exempt("structural: the one rule for which folder is a run")`.
  Verify: `git grep -l -E "^def test_(runs_in|run_at)_" -- tests/test_run_directory.py` prints `tests/test_run_directory.py`.
- [x] 1.2 Add `runs_in` and `run_at` of [D2](design.md#d2) after `assign` in `isekai/foundation/rundir.py`. Its docstring's first line becomes "`Run`, one photograph's directory and its frame, `assign`, and which folders are runs", and its body gains the sentence "`runs_in` and `run_at` decide which folder is a run."
  Verify: `git grep -n -E "^def (runs_in|run_at)" -- isekai/foundation/rundir.py` prints `2`.
- [x] 1.3 In `isekai/foundation/run.py`, import `run_at` and `runs_in` from `isekai.foundation.rundir` beside `Run, assign`, and add each to `__all__` in sorted place.
  Verify: `uv run pytest tests/test_run_directory.py -k "runs_in or run_at"` exits 0.

## 2 — The sites

- [x] 2.1 **HALT CHECK** The sites stand as the table of [D3](design.md#d3) reads them, one line each.
  Verify: `git grep -n -F "FRAME_NAME).is_file()" -- isekai/interface` prints `6`.
- [x] 2.2 Mutate `run_ids` in `isekai/interface/render.py`, lines 203-209, over `tests/test_render.py`, before the switch. A survivor that is no equivalent mutant gets its case in that file first ([D6](design.md#d6)).
  Verify: `uv run python -m tools.mutate isekai/interface/render.py:203-209 --tests tests/test_render.py` exits 0.
- [x] 2.3 Switch `run_ids` to its row of [D3](design.md#d3). In the file's import of `isekai.foundation.run`, `FRAME_NAME` goes and `runs_in` comes after `latest_artifact`.
  Verify: `git grep -n -F "runs_in(runs)" -- isekai/interface/render.py` prints `1`.
- [x] 2.4 Mutate the new lines of `run_ids`, 203-205, over the same tests.
  Verify: `uv run python -m tools.mutate isekai/interface/render.py:203-205 --tests tests/test_render.py` exits 0.
- [x] 2.5 Mutate `_runs` in `isekai/interface/compare_view.py`, lines 106-121, over `tests/test_compare.py`, before the switch. A survivor gets its case in that file first.
  Verify: `uv run python -m tools.mutate isekai/interface/compare_view.py:106-121 --tests tests/test_compare.py` exits 0.
- [x] 2.6 Switch `_runs` to its row of [D3](design.md#d3): the refusal of a collection with no runs directory stays and the list is `runs_in(root)`. In the import, `FRAME_NAME` goes and `runs_in` comes after `photo_of`.
  Verify: `git grep -n -F "return runs_in(root)" -- isekai/interface/compare_view.py` prints `1`.
- [x] 2.7 Mutate the new lines of `_runs`, 106-117, over the same tests.
  Verify: `uv run python -m tools.mutate isekai/interface/compare_view.py:106-117 --tests tests/test_compare.py` exits 0.
- [x] 2.8 Mutate the loop of `_migrate` in `isekai/interface/cli.py`, lines 191-196, over `tests/test_migrate.py`, before the switch. A survivor gets its case in that file first.
  Verify: `uv run python -m tools.mutate isekai/interface/cli.py:191-196 --tests tests/test_migrate.py` exits 0.
- [x] 2.9 Switch `_migrate` to its row of [D3](design.md#d3): `where` ends in `run.id`, and `migrate(run)` takes the listed run. In the import, `runs_in` replaces `FRAME_NAME`, after `find_run`.
  Verify: `git grep -n -F "for run in runs_in(root):" -- isekai/interface/cli.py` prints `1`.
- [x] 2.10 Mutate the new lines of the loop, 191-195, over the same tests.
  Verify: `uv run python -m tools.mutate isekai/interface/cli.py:191-195 --tests tests/test_migrate.py` exits 0.
- [x] 2.11 Mutate `run_or_photo` in `isekai/interface/verbs/common.py`, lines 289-292, over `tests/test_pipeline_cli.py`, before the switch. A survivor gets its case in that file first.
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/common.py:289-292 --tests tests/test_pipeline_cli.py` exits 0.
- [x] 2.12 Switch `run_or_photo` to its row of [D3](design.md#d3). The import of `isekai.foundation.run` gains `run_at` and keeps `FRAME_NAME` until 2.15.
  Verify: `git grep -n -F "run_at(wired.runs_root, identifier)" -- isekai/interface/verbs/common.py` prints `1`.
- [x] 2.13 Mutate the new lines of `run_or_photo`, 290-292, over the same tests.
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/common.py:290-292 --tests tests/test_pipeline_cli.py` exits 0.
- [x] 2.14 Mutate the check of `parse_cells` in the same file, lines 328-333, over `tests/test_pipeline_cli.py`, before the switch. A survivor gets its case in that file first.
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/common.py:328-333 --tests tests/test_pipeline_cli.py` exits 0.
- [x] 2.15 Switch `parse_cells` to its row of [D3](design.md#d3). The import of `isekai.foundation.run` drops `FRAME_NAME`.
  Verify: `git grep -n -F "run_at(wired.runs_root, run_id) is None" -- isekai/interface/verbs/common.py` prints `1`.
- [x] 2.16 Mutate the new lines of the check, 329-333, over the same tests.
  Verify: `uv run python -m tools.mutate isekai/interface/verbs/common.py:329-333 --tests tests/test_pipeline_cli.py` exits 0.
- [x] 2.17 Mutate `_runs` in `isekai/interface/ui/library.py`, lines 797-806, over `tests/test_ui_library.py`, before the switch. A survivor gets its case in that file first.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/library.py:797-806 --tests tests/test_ui_library.py` exits 0.
- [x] 2.18 Switch `_runs` to its row of [D3](design.md#d3), keeping the separator filter and the digest key. In the import, `runs_in` replaces `FRAME_NAME`, after `photo_of`.
  Verify: `git grep -n -F "for run in runs_in(runs)" -- isekai/interface/ui/library.py` prints `1`.
- [x] 2.19 The new lines of `_runs`, 797-803, are a bare dict comprehension: `tools.mutate` holds no mutant in them and refuses the range, so no run is made. The tests that killed every mutant of 2.17 stand as the check, and pass over the switched lines.
  Verify: `uv run pytest tests/test_ui_library.py` exits 0.
- [x] 2.20 Run the tests of the sites, of the evaluators and of the guards; no existing assertion changed.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_compare.py tests/test_migrate.py tests/test_pipeline_cli.py tests/test_render.py tests/test_ui_library.py tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_spec_bindings.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py` exits 0.

## 3 — The decision

- [x] 3.1 Add the D65 block of [D7](design.md#d7) to `docs/decisions.md`, at the end of `## Runs`, after D43.
  Verify: `git grep -n -F "### D65 · A run is a folder holding its frame file" -- docs/decisions.md` prints `1`.
- [x] 3.2 In `isekai/foundation/README.md`, change the `rundir.py` row of `## Files` to: `` `Run`, one photograph's directory and its frame, `assign`, and `runs_in` and `run_at`, which folders are runs ``.
  Verify: `git grep -n -F "runs_in" -- isekai/foundation/README.md` prints `1`.
- [x] 3.3 Replay the kept mutants: none of them names a line this change rewrote.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 3.4 Resume's `_run_for` and the evaluators are as they were ([D4](design.md#d4)): no file under `evaluation/` differs from the default branch.
  Verify: `git diff --name-only main -- evaluation` prints nothing.
