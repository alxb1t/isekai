# Green main — tasks

Tests and the workflow alone: the reds of `main`, then the tests that fail under load. Decisions are in [design](design.md).

## Progress

- [x] 1 — The reds · moderate
- [ ] 2 — The load-bound tests · moderate

## 1 — The reds

- [x] 1.1 In `tests/e2e/test_import.py`, hand Playwright a lambda as the file chooser's handler: replace `page.on("filechooser", chosen.append)` with `page.on("filechooser", lambda chooser: chosen.append(chooser))`. Keep the `chosen` list and the `assert not chosen` below it.
  Verify: `git grep -n -F 'lambda chooser: chosen.append(chooser)' -- tests/e2e/test_import.py` prints the edited line.

- [x] 1.2 In `tests/test_chain.py`, change the last line of `test_chain_spline_chunks_a_large_grid_without_changing_it` per [D2](design.md#d2): replace `assert np.array_equal(spline(grid), whole)` with `np.testing.assert_allclose(spline(grid), whole, rtol=0, atol=1e-9)`. Keep the test's name and its `spec_exempt` mark.
  Verify: `git grep -n -F 'atol=1e-9' -- tests/test_chain.py` prints the edited line.

- [x] 1.3 In `.github/workflows/ci.yml`, add the line `        if: always()` under `      - name: Browser tests`, above its `run: make e2e`. Reword the comment above the step, `# cannot run them; CI holds them on every push.`, to `# cannot run them; CI runs them after the gate, red or green.`
  Verify: `git grep -n -F 'if: always()' -- .github/workflows/ci.yml` prints one line, in the step named *Browser tests*.

- [x] 1.4 **HALT CHECK** The workflow's guards in `tests/test_infra.py` hold with the edited step, and the spline's test passes: a failure in `tests/test_infra.py` means `if: always()` breaks a guard the plan says it keeps. Edit nothing.
  Verify: `uv run pytest tests/test_chain.py tests/test_infra.py -q` exits 0.

## 2 — The load-bound tests

- [ ] 2.1 In `_overlap` of `tests/test_ui_api.py`, keep each update's body with its status: `put` stores `(reply.status_code, reply.json())` in `answers`, with `reply` the `client.put(...)` result, and `answers` and the return type are `dict[str, tuple[int, dict[str, Any]]]`.
  Verify: `git grep -n -F 'reply.status_code, reply.json()' -- tests/test_ui_api.py` prints the edited line.

- [ ] 2.2 In `test_overlapping_draft_updates_cannot_both_commit`, assert `(answers["first"][0], answers["second"][0]) == (200, 409)` and that `answers["second"][1]["refusal"]` holds `changed since this page last read it`. In `test_without_the_lock_overlapping_updates_both_commit`, assert the same pair is `(200, 200)`.
  Verify: `git grep -n -F 'answers["second"][1]["refusal"]' -- tests/test_ui_api.py` prints the edited line.

- [ ] 2.3 In `_overlap`, order `check` as in [the lock pair](design.md#load-bound-tests): call `precondition(one, payload)` first, then set `reached` when the payload is the second update's (`["black hair"]`). Keep the docstring and the `Waited` lock as they are.
  Verify: `uv run pytest tests/test_ui_api.py -k overlapping -q` exits 0.

- [ ] 2.4 In `tests/test_ui_api.py`, add `def _until_each_read(feed, uploads: Mapping[str, set[str]]) -> dict[str, list[Any]]` before `_until_read`, `feed` typed as there: one loop over the feed, keeping each listed import's `file` events and ending when every upload of every import is read. Make `_until_read` return `_until_each_read(feed, {staged: uploads})[staged]`.
  Verify: `git grep -n -F 'def _until_each_read' -- tests/test_ui_api.py` prints the definition.

- [ ] 2.5 In `test_the_imports_stream_reports_a_file_waiting_converting_then_converted`, replace the `_until_read` calls for `staged` and for `other` with `_until_each_read(feed, {staged: {plain["upload"]}, other: {away["upload"]}})`.
  Verify: `uv run pytest tests/test_ui_api.py -k imports_stream -q` exits 0.

- [ ] 2.6 In `tests/test_ui_jobs.py`, make `SLEEP` `"import time\nwhile True: time.sleep(0.05)"`, and replace the last line, the thirty-second sleep, of `SLOW_TEARDOWN` and of the scripts in `test_a_stop_whose_wait_runs_out_names_the_command_that_closes_the_window` and `_stop_with_window` with `"while True: time.sleep(0.05)\n"`.
  Verify: `git grep -n -F 'while True: time.sleep(0.05)' -- tests/test_ui_jobs.py` prints each edited line.

- [ ] 2.7 In `tests/test_ui_jobs.py`, replace `"; import time; time.sleep(30)"` in the children of `test_stopping_the_surface_interrupts_both_and_closes_the_window_first` and `test_stop_interrupts_the_stage_and_starts_no_later_one` with `"\nimport time\nwhile True: time.sleep(0.05)"`.
  Verify: `git grep -c -F 'time.sleep(30)' -- tests/test_ui_jobs.py` prints nothing and exits 1.

- [ ] 2.8 In `tests/test_ui.py`, make the idle child of `test_sigint_ends_streams_without_cancellation_output` `[sys.executable, "-c", "import time\nwhile True: time.sleep(0.05)"]`, in place of `"import time; time.sleep(30)"`. Leave `sleep 60` of the build-timeout test's stand-in as it is ([D1](design.md#d1)).
  Verify: `git grep -c -F 'time.sleep(30)' -- tests/test_ui.py` prints nothing and exits 1.

- [ ] 2.9 In `_stop_with_window` of `tests/test_ui_jobs.py`, settle in ten seconds: replace `settle=lambda: 2,` with `settle=lambda: 10,`. Keep `jobs.shutdown(timeout=2)`.
  Verify: `git grep -n -F 'settle=lambda: 10' -- tests/test_ui_jobs.py` prints the edited line.

- [ ] 2.10 Run phase 2's test files together, as the load-bound tests are read: edit nothing.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui.py -q` exits 0.
