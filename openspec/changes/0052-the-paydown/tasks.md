# Tasks — 0052 the paydown

The records first, then `show`, the guard, and the words, per [design](design.md). The delta already holds both new
scenarios; phase 2 adds their tests.

## Progress

- [ ] 1 — The records
- [ ] 2 — What `show` hid
- [ ] 3 — The guard
- [ ] 4 — The words

Line numbers are `4fd5d99`'s. Every new test carries `@pytest.mark.spec` with the key its task names. No existing
test turns red: `show`'s legend test asserts with `in`, and the guard's twin only gains cases.

## 1 — The records

- [ ] 1.1 **HALT CHECK** — no decision carries an `Accepts:` bullet, and *A component is a contract* has no *Known breaks*.
  Verify: `grep -c 'Accepts:' docs/decisions.md` prints `0`, and `grep -c 'MODEL_RECORDS' docs/principles.md` prints `0`.
- [ ] 1.2 In `docs/decisions.md`, add the `Accepts:` bullets to D6, D27, D35 and D36, and `0052` to each one's `Made by`, per [D1](design.md#d1).
  Verify: `grep -c '^- \*\*Accepts:\*\*' docs/decisions.md` prints `4`, and `grep -c '0052' docs/decisions.md` prints `4`.
- [ ] 1.3 In `docs/principles.md`, add *A component is a contract*'s *Known breaks* per [D1](design.md#d1), and `_once` to *Only a front end composes*'s per [D2](design.md#d2).
  Verify: `grep -c 'MODEL_RECORDS' docs/principles.md` prints `1`, and `grep -c '_once' docs/principles.md` prints `1`.
- [ ] 1.4 Add `refusal_for`'s docstring sentence in `isekai/foundation/run.py`, and `tests/test_tagging.py` to the `ollama.py` row in `isekai/boundary/README.md`, per [D2](design.md#d2).
  Verify: `grep -c 'did not fail' isekai/foundation/run.py` prints `1`, and `grep '^| .ollama.py.' isekai/boundary/README.md | grep -c test_tagging` prints `1`.

## 2 — What `show` hid

- [ ] 2.1 **HALT CHECK** — the failure pattern is private, and `show` imports it nowhere.
  Verify: `grep -c '_ERROR' isekai/foundation/run.py` prints `2`, and `grep -c 'ERROR' isekai/interface/run_view.py` prints `0`.
- [ ] 2.2 Rename `_ERROR` to `ERROR` in `isekai/foundation/run.py`; in `isekai/interface/run_view.py`, add `Listing.failures`, `render_failures` and the `!` lines and legend, per [D3](design.md#d3).
  Verify: `grep -c '_ERROR' isekai/foundation/run.py` prints `0`, `grep -c '^def render_failures(' isekai/interface/run_view.py` prints `1`, and `grep -c 'marks a failure record' isekai/interface/run_view.py` prints `1`.
- [ ] 2.3 In `tests/test_run_view.py`, add `test_failure_records_are_listed_under_their_stage`, `test_a_stage_holding_only_failures_is_not_reported_empty` and `test_render_failures_are_listed_under_their_group` (`cli:show:failure-records-are-listed`).
  Verify: `grep -c '^def test_failure_records_are_listed_under_their_stage(\|^def test_a_stage_holding_only_failures_is_not_reported_empty(\|^def test_render_failures_are_listed_under_their_group(' tests/test_run_view.py` prints `3`.
- [ ] 2.4 In `isekai/interface/run_view.py`, add `unread` and its `not read` lines, per [D4](design.md#d4).
  Verify: `grep -c '^def unread(' isekai/interface/run_view.py` prints `1`, and `grep -c 'f"  not read  ' isekai/interface/run_view.py` prints `1`.
- [ ] 2.5 In `tests/test_run_view.py`, add `test_a_name_show_does_not_read_is_named` (`cli:show:an-unread-name-is-named`), parametrised over the places in [D4](design.md#d4).
  Verify: `grep -c '^def test_a_name_show_does_not_read_is_named(' tests/test_run_view.py` prints `1`.
- [ ] 2.6 In `_producer_of`, say `declares no kind` when `schema.name` is absent, and add that case to `test_show_marks_a_file_it_cannot_read`'s parameters, per [D5](design.md#d5).
  Verify: `grep -c 'declares no kind' isekai/interface/run_view.py` prints `1`, and `grep -c 'declares no kind' tests/test_run_view.py` prints `1`.

## 3 — The guard

- [ ] 3.1 **HALT CHECK** — `ADD_GIT` has no ssh alternative.
  Verify: `grep -c 'bssh://' tools/derive_image_project.py` prints `0`.
- [ ] 3.2 Widen `ADD_GIT` in `tools/derive_image_project.py`, and add the `an-ssh-add` and `an-scp-add` cases to `test_the_count_catches_a_clone_with_a_flag_and_another_host` in `tests/test_infra.py`, per [D6](design.md#d6).
  Verify: `grep -c 'bssh://' tools/derive_image_project.py` prints `1`, and `grep -o 'an-s[sc][hp]-add' tests/test_infra.py | wc -l` prints `2`.

## 4 — The words

- [ ] 4.1 Reword `Batch.wd14_path`'s docstring in `isekai/interface/ui/batch.py`, the run button in `ui/src/components/BatchRail.vue`, and the `beforeunload` comment in `ui/src/ReviewApp.vue`, per [D7](design.md#d7).
  Verify: `grep -c 'every list after it' isekai/interface/ui/batch.py` prints `0`, `grep -c 'in the manifest' ui/src/components/BatchRail.vue` prints `1`, and `grep -c 'can lose the last edit' ui/src/ReviewApp.vue` prints `1`.
