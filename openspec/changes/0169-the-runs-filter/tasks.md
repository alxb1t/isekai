# The runs filter — tasks

The phases: the helper's predicate with its cases, the library's call with the hub's case, and D65's text. Each case is written before the line it holds.

## Progress

- [ ] 1 — The helper · moderate
- [ ] 2 — The library · moderate
- [ ] 3 — The decision · moderate

## 1 — The helper

- [ ] 1.1 Add the helper's cases of [D5](design.md#d5) to `tests/test_run_directory.py`, after `test_runs_in_holds_none_of_a_root_that_is_no_directory`. Run them: each fails with `TypeError`, since `named` is unknown.
  Verify: `git grep -n -e "def test_runs_in_leaves_out_a_framed_folder_its_name_predicate_rejects" -e "def test_runs_in_does_not_probe_a_child_its_name_predicate_rejects" -- tests/test_run_directory.py` prints two lines.
- [ ] 1.2 Write `runs_in` in `isekai/foundation/rundir.py` exactly as [D1](design.md#d1) gives it, and add `Callable` to the `collections.abc` import. No other line of the file changes.
  Verify: `uv run pytest tests/test_run_directory.py` exits 0.
- [ ] 1.3 Run the mutator over `runs_in`'s lines as 1.2 leaves them, as [D7](design.md#d7) says. A survivor gets a case in `tests/test_run_directory.py` that kills it.
  Verify: `uv run python -m tools.mutate isekai/foundation/rundir.py:154-165 --tests tests/test_run_directory.py` exits 0.

## 2 — The library

- [ ] 2.1 Add the hub's case of [D5](design.md#d5) to `tests/test_ui_library.py`, after `test_an_unreadable_run_file_marks_its_cell_alone`, bound to `ui:hub:a-folder-that-is-no-run-is-ignored`. Run it: it fails with `PermissionError`.
  Verify: `git grep -n "ui:hub:a-folder-that-is-no-run-is-ignored" -- tests/test_ui_library.py` prints one line.
- [ ] 2.2 Write `_runs` in `isekai/interface/ui/library.py` exactly as [D2](design.md#d2) gives it: the separator test goes to `runs_in` as `named`, and the `if` of the comprehension goes.
  Verify: `git grep -n "named=" -- isekai/interface/ui/library.py` prints one line.
- [ ] 2.3 Run the tests that hold the helper, the library and the bindings.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_ui_library.py tests/test_spec_bindings.py tests/test_spec_prose.py tests/test_ratchets.py tests/test_layers.py` exits 0.

## 3 — The decision

- [ ] 3.1 In `docs/decisions.md`, D65's *Why* ends with the sentence of [D6](design.md#d6) in place of its last, and its *Made by* reads `0165`, `0169`. No decision is added and no other line of the page changes.
  Verify: `git grep -n -E "passes its separator filter to|Made by:.{4}0165.{4}0169" -- docs/decisions.md` prints two lines.
- [ ] 3.2 Leave the other sites, `run_at` and `_run_for` as they are.
  Verify: `git grep -n "runs_in(" -- isekai/interface/render.py isekai/interface/compare_view.py isekai/interface/cli.py` prints three lines.
- [ ] 3.3 Run the gate's documents and layer tests.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_ratchets.py` exits 0.
