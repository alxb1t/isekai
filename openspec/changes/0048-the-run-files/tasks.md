# Tasks — 0048 the run files

The kind, the record's name, the sheet's failures, then the warning, per [design](design.md). The delta already
holds every new scenario; each task below adds the tests that bind them.

## Progress

- [x] 1 — The kind
- [x] 2 — The record's name
- [x] 3 — The sheet's failures
- [ ] 4 — The warning

Line numbers are `69bfd67`'s. Every new test carries `@pytest.mark.spec` with the key its task names.

## 1 — The kind

- [x] 1.1 **HALT CHECK** — `read` checks no name, the record is `<seed>.json`, the sheet records nothing, and `sheet` returns a path alone.
  Verify: `grep -c 'The name is not checked' isekai/foundation/artifacts.py` prints `1`, `grep -cF 'f"{seed}.json"' isekai/pipeline/generate.py` prints `1`, `grep -c 'record_failure' isekai/pipeline/sheet.py` prints `0`, and `grep -c ') -> Path | None:' isekai/pipeline/sheet.py` prints `1`.
- [x] 1.2 In `isekai/foundation/artifacts.py`, refuse a schema `name` other than the kind's before the version, and restate the docstrings of `read` and `require`, per [D1](design.md#d1); add `test_a_file_of_another_kind_is_refused_naming_both` (`run-directory:kind:another-kind-is-refused`) and `test_the_kind_is_checked_before_the_version` (`run-directory:kind:the-kind-is-checked-first`) to `tests/test_run_directory.py`.
  Verify: `grep -c 'The name is not checked' isekai/foundation/artifacts.py` prints `0`, `grep -c 'declares kind' isekai/foundation/artifacts.py` prints `1`, and `grep -cE '^def test_(a_file_of_another_kind_is_refused_naming_both|the_kind_is_checked_before_the_version)\(' tests/test_run_directory.py` prints `2`.
- [x] 1.3 In `isekai/foundation/artifacts.py`, restate `Frame`'s docstring per [D2](design.md#d2).
  Verify: `grep -c 'a rename leaves .id. as it was' isekai/foundation/artifacts.py` prints `1`.

## 2 — The record's name

- [x] 2.1 In `isekai/pipeline/generate.py`, name the render's record `<seed>.render.json`; in `isekai/foundation/run.py`, narrow `ARTIFACT`'s label to `draft|approved`, per [D3](design.md#d3).
  Verify: `grep -cF 'f"{seed}.render.json"' isekai/pipeline/generate.py` prints `1`, and `grep -cF '(?P<label>draft|approved)' isekai/foundation/run.py` prints `1`.
- [x] 2.2 Rename `42.json` to `42.render.json` in `tests/test_generate.py`'s `test_the_sidecar_is_written_before_its_image` and `test_a_render_on_a_pinned_pod_records_its_image_and_runtime`, and in `tests/test_resume.py`'s decoy.
  Verify: `cat tests/test_generate.py tests/test_resume.py | grep -c '"42.json"'` prints `0`.
- [x] 2.3 Add `test_a_render_record_is_never_read_as_a_version` (`run-directory:readdir:a-render-record-is-never-a-version`) to `tests/test_generate.py`: a render for seed `123` writes `123.render.json`, and `versions` of its directory is empty.
  Verify: `grep -c '^def test_a_render_record_is_never_read_as_a_version(' tests/test_generate.py` prints `1`.

## 3 — The sheet's failures

- [x] 3.1 In `isekai/pipeline/sheet.py`, record a refusal from the tagged branch's reads, entry checks and `validate` as permanent through `refusal_for`, and drop the untagged branch's `check_budget`, per [D4](design.md#d4); restate the `BUDGETS` comment in `isekai/foundation/run.py`.
  Verify: `test "$(grep -c 'record_failure' isekai/pipeline/sheet.py)" -ge 2 && echo ok` prints `ok`, `grep -c 'check_budget(STAGE' isekai/pipeline/sheet.py` prints `1`, and `grep -c 'records no failure' isekai/foundation/run.py` prints `0`.
- [x] 3.2 In `tests/test_sheet_stage.py`, restate `test_a_tag_list_missing_a_key_is_refused_naming_it` for the recorded refusal; add `test_a_sheet_failure_is_recorded_as_permanent` (`run-directory:failure:a-sheet-failure-is-permanent`), with a damaged list and a tag outside the vocabulary as its cases, and `test_an_absent_tag_list_leaves_no_record` (`run-directory:failure:an-absent-tag-list-leaves-no-record`).
  Verify: `grep -cF 'startswith("001.json: ")' tests/test_sheet_stage.py` prints `0`, and `grep -cE '^def test_(a_sheet_failure_is_recorded_as_permanent|an_absent_tag_list_leaves_no_record)\(' tests/test_sheet_stage.py` prints `2`.

## 4 — The warning

- [ ] 4.1 In `isekai/pipeline/sheet.py`, return `(path, warnings)` and warn on a tagged flow's kept path, per [D5](design.md#d5); in `isekai/interface/cli.py`, print each warning in `sheet_flow`; in `tests/stages.py`, return the path alone.
  Verify: `grep -c 'is newer' isekai/pipeline/sheet.py` prints `1`, `grep -cF 'print(f"warning: {warning}"' isekai/interface/cli.py` prints `2`, and `grep -c ') -> Path | None:' isekai/pipeline/sheet.py` prints `0`.
- [ ] 4.2 Add `test_a_newer_tag_list_is_named` (`sheet:superseded:a-newer-tag-list-is-named`), `test_a_sheet_from_the_latest_list_is_silent` (`sheet:superseded:the-latest-list-is-silent`), `test_an_untagged_flow_is_silent` (`sheet:superseded:an-untagged-flow-is-silent`) and `test_an_unreadable_kept_sheet_is_silent` (`sheet:superseded:an-unreadable-sheet-is-silent`) to `tests/test_sheet_stage.py`.
  Verify: `grep -cE '^def test_(a_newer_tag_list_is_named|a_sheet_from_the_latest_list_is_silent|an_untagged_flow_is_silent|an_unreadable_kept_sheet_is_silent)\(' tests/test_sheet_stage.py` prints `4`.
- [ ] 4.3 Add `test_sheet_prints_a_superseded_list_as_a_warning` (`sheet:superseded:a-newer-tag-list-is-named`) to `tests/test_pipeline_cli.py`: the warning on stderr, "sheet is already complete" on stdout, exit `0`.
  Verify: `grep -c '^def test_sheet_prints_a_superseded_list_as_a_warning(' tests/test_pipeline_cli.py` prints `1`.
