# The net's holes — tasks

Tests, a tool and one document alone: the silent patches and the guard, then the mutation runner. Decisions are in [design](design.md).

## Progress

- [x] 6 — No blind patch · moderate
- [x] 7 — The pre-flight · hard

## 6 — No blind patch

- [x] 6.1 In `tests/test_caption.py`, add `test_the_suites_model_records_point_at_an_empty_directory` per the first row of [D1](design.md#d1), which holds the autouse `_no_machine_records` of `tests/conftest.py` alone: `ollama.verified_build(READER)` raises `Refusal`, and its message holds `str(ollama.MODEL_RECORDS)`. It carries `spec_exempt("structural: the autouse fixture points the model records at an empty directory")`.
  Verify: `uv run pytest tests/test_caption.py -k empty_directory -q` exits 0.

- [x] 6.2 In `tests/test_caption.py`, add `test_the_model_record_tripwire_fires_for_a_caption_not_yet_made` per [D2](design.md#d2): the patch and `unreachable` of `test_a_completed_caption_reads_no_model_record`, an `OllamaReader` over `FakeTransport()`, and `caption(run, reader)` inside `pytest.raises(AssertionError, match="a model record was read")`. It carries `spec_exempt("structural: twin of test_a_completed_caption_reads_no_model_record")`.
  Verify: `uv run pytest tests/test_caption.py -k record_tripwire_fires -q` exits 0.

- [x] 6.3 In `tests/test_pipeline_cli.py`, add `test_the_wirings_reader_reaches_the_model_record_when_it_reads`: patch `ollama._verified_build` with a function raising `AssertionError("the model record was read")`, build `wiring_from(runs=tmp_path / "runs")`, and call `wired.reader().read(tmp_path / "ada.jpg", "briefing", tmp_path)` inside `pytest.raises(AssertionError, match="the model record was read")`. It carries `spec_exempt("structural: twin of test_composing_a_wiring_contacts_no_host_and_looks_up_no_binary")`.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k wirings_reader_reaches -q` exits 0.

- [x] 6.4 In `tests/test_wd14.py`, add `test_the_boundary_reaches_provisioning_at_its_first_use` per [D2](design.md#d2): the patches of `load_manifest` and `resolve` and the re-import of `test_importing_the_boundary_opens_no_file_and_computes_no_digest`, with `refuse` saying `provisioning was reached`, then `boundary.verified_paths()` inside `pytest.raises(AssertionError, match="provisioning was reached")`. It carries `spec_exempt("structural: twin of test_importing_the_boundary_opens_no_file_and_computes_no_digest")`.
  Verify: `uv run pytest tests/test_wd14.py -k reaches_provisioning_at_its_first_use -q` exits 0.

- [x] 6.5 In `tests/test_ui_api.py`, add `test_a_request_from_this_page_reads_the_photograph` per [D2](design.md#d2): the patch of `app_module.FileResponse` of `test_a_cross_site_request_without_origin_is_refused` with a recorder taking the path and any keywords, a request carrying `sec-fetch-site: same-origin`, and `read` holding the run's photograph once. It carries `spec_exempt("structural: twin of test_a_cross_site_request_without_origin_is_refused")`.
  Verify: `uv run pytest tests/test_ui_api.py -k from_this_page_reads_the_photograph -q` exits 0.

- [x] 6.6 In `test_prepare_is_refused_with_the_readers_message_and_starts_nothing` of `tests/test_ui_jobs.py`, make `Closed.open` append to a list `opened` and, after the refusal, add `assert len(opened) == 1`.
  Verify: `grep -n -F "assert len(opened) == 1" tests/test_ui_jobs.py` prints the assertion.

- [x] 6.7 In `test_serve_returns_130_for_keyboard_interrupt` of `tests/test_ui.py`, make the stand-ins for `ui.library.root` and `ui.ensure_built` append `"root"` and `"ensure_built"` to a list `asked`, and after `ui.serve` returns add `assert asked == ["root", "ensure_built"]`.
  Verify: `grep -n -F 'assert asked == ["root", "ensure_built"]' tests/test_ui.py` prints the assertion.

- [x] 6.8 In `test_chain_spline_chunks_a_large_grid_without_changing_it` of `tests/test_chain.py`, wrap `chain._kernel` after `whole` is computed with a function that appends to `calls` and returns the kernel's answer, and assert `len(calls) == math.ceil(len(grid) / 7)`; add `import math`.
  Verify: `grep -n -F "math.ceil(len(grid) / 7)" tests/test_chain.py` prints the assertion.

- [x] 6.9 In `test_the_same_bytes_are_skipped_and_a_taken_name_is_renamed` of `tests/test_importing.py`, make `cleaned_together` append its file to `cleaned` and `slow` append its path to `written`, and add `assert len(cleaned) == len(files)`, `assert len(written) >= len(files)` and `assert not together.broken`.
  Verify: `grep -n -F "assert not together.broken" tests/test_importing.py` prints the assertion.

- [x] 6.10 In `tests/test_ratchets.py`, per [D4](design.md#d4), add `PATCH_PACKAGES` and split the walk of `patched_modules` into `def resolved_patches(root, packages)`, which threads `packages` through the resolution of a target and returns `(path, line, module, name)`, the line from the call; rebuild `patched_modules` on it with `PACKAGES`, keeping its top-level-binding filter and its output.
  Verify: `grep -n -F "def resolved_patches(" tests/test_ratchets.py` prints the definition.

- [x] 6.11 In `tests/test_ratchets.py`, per [D3](design.md#d3) and [D4](design.md#d4), add `names_read(root)` and `unread_patches(root)`, and `test_a_name_is_read_by_a_load_an_attribute_or_an_import`, over a `tmp_path` tree where `isekai/m.py` binds a name loaded in a function of `m.py`, a name read as `m.name` in `isekai/n.py`, a name imported from `isekai.m` inside a function of `n.py`, and a name only stored. A test file patches each, and `unread_patches` lists the stored name alone. It carries `spec_exempt("structural: a name is read by a load, an attribute or an import, and by nothing else")`.
  Verify: `uv run pytest tests/test_ratchets.py -k a_name_is_read -q` exits 0.

- [x] 6.12 **HALT CHECK** Print the guard's scan before it is a guard: a name it lists is a silent patch the plan did not read. Edit nothing and stop.
  Verify: `uv run python -c "from pathlib import Path; from tests.test_ratchets import unread_patches; print(unread_patches(Path('.')))"` prints `[]`.

- [x] 6.13 In `tests/test_ratchets.py`, add the guard `test_every_patch_names_a_name_its_module_reads`, asserting `unread_patches(REPO_ROOT) == []` and that `resolved_patches(REPO_ROOT, PATCH_PACKAGES)` is not empty, and its twin `test_the_check_catches_a_patch_of_a_name_nothing_reads`, over a `tmp_path` tree whose test patches a name its module only stores. The guard carries `spec_exempt("structural: every patch names a name its module reads")`, the twin `spec_exempt("structural: twin of test_every_patch_names_a_name_its_module_reads")`.
  Verify: `uv run pytest tests/test_ratchets.py -k "every_patch_names or patch_of_a_name_nothing_reads" -q` exits 0.

## 7 — The pre-flight

- [x] 7.1 Create `tools/mutate.py` per [D5](design.md#d5) and [D6](design.md#d6): a module docstring with the command line, `REPO_ROOT`, `OPERATORS` as the names of the table, `LINKED` as `models`, `ui/node_modules` and `ui/dist`, `Mutant`, `Refused`, and `parse_target(text)`, which returns `(path, lo, hi)` and raises `Refused` on a form other than `<path>:<lo>[-<hi>]` or on `lo` past `hi`. Imports of the standard library alone.
  Verify: `uv run python -c "import tools.mutate"` exits 0.

- [x] 7.2 In `tools/mutate.py`, add a function for each operator of [D6](design.md#d6) on an operand — `edit_cmp`, `edit_bool`, `edit_not`, `edit_const` and `def edit_arith(` — each taking the line and the node and returning the new line, or `None`.
  Verify: `grep -n -F "def edit_arith(" tools/mutate.py` prints the definition.

- [x] 7.3 In `tools/mutate.py`, add `edit_raise`, `edit_ret` and `edit_call`, and `def sites(text, lo, hi)` per [D6](design.md#d6): the mutants on the lines, inside function bodies, a docstring and a node over several lines left alone, a node that nested functions share listed without a repeat.
  Verify: `grep -n -F "def sites(" tools/mutate.py` prints the definition.

- [x] 7.4 Create `tests/test_mutate.py` with a module docstring, `test_each_operator_makes_its_one_edit` parametrized over a table of an operator, a source line and its new line, one row for each of `OPERATORS` and a `cmp` row whose line holds a non-ASCII string before the comparison, `test_a_line_range_limits_the_sites`, `test_only_a_function_body_is_mutated`, and `test_a_statement_over_several_lines_is_left_alone`. Each carries `spec_exempt("structural: …")` naming the rule it holds.
  Verify: `uv run pytest tests/test_mutate.py -k "each_operator_makes or line_range_limits or only_a_function_body or over_several_lines" -q` exits 0.

- [x] 7.5 In `tools/mutate.py`, add `copy_tree(root, into)` per [D7](design.md#d7). In `tests/test_mutate.py`, add `build_repo(path, *, failing=False)`, which runs `git init` in `path` and adds every file but an untracked `models/` directory: `calc.py` holding `add`, `label` (`return "big" if n >= 100 else "small"`) and `drain` (`while n > 0:` then `n = n - 1`, returning `n`), and `tests/test_calc.py` asserting `add(2, 3) == 5`, `label(5) == "small"`, `label(500) == "big"` and `drain(3) == 0`, plus a failing assertion when `failing` is set. Add the fixture `small_repo`, which calls it under `tmp_path_factory`, and `test_the_copy_holds_the_tracked_files_and_links_the_ignored_ones`.
  Verify: `uv run pytest tests/test_mutate.py -k the_copy_holds -q` exits 0.

- [x] 7.6 In `tools/mutate.py`, add `pytest_args(tests, everything)`, `run_tests(copy, args, timeout)` and `verdict(code)` per [D8](design.md#d8), the run under `PYTHONDONTWRITEBYTECODE=1`. In `tests/test_mutate.py`, add `test_all_runs_the_suite_without_the_browser_tests` over `pytest_args`, and `test_a_mutant_that_cannot_run_is_invalid_not_a_survivor` over `verdict`.
  Verify: `uv run pytest tests/test_mutate.py -k "all_runs_the_suite or cannot_run" -q` exits 0.

- [x] 7.7 In `tools/mutate.py`, add `try_mutant(copy, mutant, args, timeout)`, which writes the mutant, runs, and writes the original back whatever happened, `report(results)` printing the lines of [D8](design.md#d8), and `def main(argv=None, *, root=REPO_ROOT)`, which reads `sys.argv[1:]` when `argv` is absent, with `if __name__ == "__main__": raise SystemExit(main())`. It refuses an untracked file, a range with no mutant, both or neither of `--tests` and `--all`, and a baseline that does not exit 0.
  Verify: `grep -n -F "def main(" tools/mutate.py` prints the definition.

- [x] 7.8 In `tests/test_mutate.py`, over `small_repo` and `main(argv, root=…)`, add `test_a_red_baseline_refuses_before_any_mutant` (a repository from `build_repo(tmp_path, failing=True)`, exit status 2 and no verdict line), `test_a_surviving_mutant_is_reported_with_its_operator_and_exits_one` (the `const` of `label`'s line survives and its `cmp` is killed), `test_a_run_with_no_survivor_exits_zero` (the line of `add`), `test_a_mutant_that_hangs_is_timed_out` (a `timeout` line naming `arith` on `drain`'s `n = n - 1` under `--timeout 2`, and no survivor) and `test_one_of_tests_and_all_is_required`. Each carries `spec_exempt("structural: …")` naming the rule it holds.
  Verify: `uv run pytest tests/test_mutate.py -q` exits 0.

- [x] 7.9 In `CONTRIBUTING.md`, add the paragraph of [D9](design.md#d9), after the paragraph that opens `**A change is measured as well as gated.**`.
  Verify: `git grep -n -F "A move is pre-flighted." -- CONTRIBUTING.md` prints the paragraph's first line.

- [x] 7.10 **HALT CHECK** Run the runner over a real range: the loop line of `isekai/shared/chain.py` holds one mutant, its first bound, which the chain tests kill. A baseline that is red in the copy, or a survivor, means the plan is wrong: edit nothing else and stop.
  Verify: `uv run python -m tools.mutate isekai/shared/chain.py:97 --tests tests/test_chain.py` exits 0.
