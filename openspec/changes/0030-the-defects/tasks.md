# Tasks — 0030 the defects

The foundation's reads first, then each area's fixes together, then every printed command once, then the docs
([design](design.md)).

## Progress

- [ ] 1 — Reading: unreadable files refused by name, the frame checked, `show` marks
- [ ] 2 — Records: the attempt number, the error record's keys, the budget and `refusal_for` messages
- [ ] 3 — Approval: one definition of a draft, the update lock, missing keys refused
- [ ] 4 — Render: the transport's kinds, the upload, the assembly and render refusals, the sidecar first
- [ ] 5 — Remedies: every printed command carries its run, and a guard holds it
- [ ] 6 — The docs drop the breaks that close

Line numbers are `e6c4278`'s; find each site by the text it names.

## 1 — Reading: unreadable files refused by name, the frame checked, `show` marks

- [ ] 1.1 **HALT CHECK** — `Run.frame` parses with a bare `json.loads`, and `read` does not guard its parse.
  Verify: `grep -c 'json.loads(self.frame_path.read_text())' isekai/foundation/run.py` prints `1`, and `grep -c 'isinstance(parsed, dict)' isekai/foundation/artifacts.py` prints `0`.
- [ ] 1.2 Make `read` refuse an unreadable file by name, with [D1](design.md#d1)'s remedy in place of *"re-run the stage that wrote it"*; follow the text in `tests/test_run_directory.py:452-453`, `:467-468`; add [D8](design.md#d8)'s test.
  Verify: `grep -c 're-run the stage that wrote it' isekai/foundation/artifacts.py` prints `0`, and `grep -c '^def test_an_unreadable_artifact_is_refused_by_name' tests/test_run_directory.py` prints `1`.
- [ ] 1.3 Read `Run.frame` through `read(…, RUN_FILE)`, per [D5](design.md#d5).
  Verify: `grep -c 'json.loads' isekai/foundation/run.py` prints `0`.
- [ ] 1.4 Make `run_view._producer_of` mark a file it cannot read, per [D5](design.md#d5), with `test_show_marks_a_file_it_cannot_read` in `tests/test_run_view.py`.
  Verify: `grep -c '^def test_show_marks_a_file_it_cannot_read' tests/test_run_view.py` prints `1`.

## 2 — Records: the attempt number, the error record's keys, the budget and `refusal_for` messages

- [ ] 2.1 Number an attempt as the highest recorded plus one in `record_failure`, per [D3](design.md#d3), with `test_a_deleted_record_is_never_overwritten` in `tests/test_run_directory.py`.
  Verify: `grep -c 'len(attempts(directory, version)) + 1' isekai/foundation/run.py` prints `0`, and `grep -c '^def test_a_deleted_record_is_never_overwritten' tests/test_run_directory.py` prints `1`.
- [ ] 2.2 Write the error record's `stage`, `seed` and `detail` by name instead of spreading the failure, per [D3](design.md#d3).
  Verify: `grep -c '\*\*failure' isekai/foundation/run.py` prints `0`.
- [ ] 2.3 Make `check_budget` take the `Run` and name the record by its path in the run; follow every caller [D2](design.md#d2) lists.
  Verify: `grep -c 'directory.name' isekai/foundation/run.py` prints `0`.
- [ ] 2.4 Give `refusal_for` [D2](design.md#d2)'s remedy for a permanent or budget-filling record, with `test_a_record_that_refuses_the_next_run_names_its_deletion` in `tests/test_run_directory.py`.
  Verify: `grep -c '^def test_a_record_that_refuses_the_next_run_names_its_deletion' tests/test_run_directory.py` prints `1`.

## 3 — Approval: one definition of a draft, the update lock, missing keys refused

- [ ] 3.1 **HALT CHECK** — the definitions [D4](design.md#d4) replaces exist.
  Verify: `grep -c '^def draft_versions' isekai/pipeline/review.py` prints `1`, and `grep -c 'latest_artifact(held.run.directory(self.flow.id, REVIEW), DRAFT)' isekai/interface/ui/batch.py` prints `1`.
- [ ] 3.2 Add `current_draft` to `isekai/pipeline/review.py` and use it in `save_draft`, `approve` and `Batch.draft_path`, per [D4](design.md#d4), with [D8](design.md#d8)'s approval test.
  Verify: `grep -c '^def draft_versions' isekai/pipeline/review.py` prints `0`, `grep -c '^def current_draft' isekai/pipeline/review.py` prints `1`, and `grep -c '^def test_approving_an_approved_flow_writes_nothing' tests/test_review.py` prints `1`.
- [ ] 3.3 Serve `read_input` by state in `isekai/interface/ui/app.py`, per [D4](design.md#d4), with [D8](design.md#d8)'s stale-draft test.
  Verify: `grep -c '^def test_a_stale_lower_draft_does_not_reopen_an_approved_input' tests/test_ui_api.py` prints `1`.
- [ ] 3.4 Hold one lock across `_precondition` and `save_draft` in `put_draft`, per [D4](design.md#d4), with [D8](design.md#d8)'s overlap test.
  Verify: `grep -c 'threading.Lock()' isekai/interface/ui/app.py` prints `1`, and `grep -c '^def test_overlapping_draft_updates_cannot_both_commit' tests/test_ui_api.py` prints `1`.
- [ ] 3.5 Refuse an approved sheet without `sheet`, and read a draft without `fields` as holding none, in `isekai/pipeline/review.py`, per [D1](design.md#d1), each with a test in `tests/test_review.py`.
  Verify: `grep -c -e '^def test_an_approved_sheet_without_its_sheet_number_is_refused' -e '^def test_a_draft_without_fields_is_refused_naming_them' tests/test_review.py` prints `2`.

## 4 — Render: the transport's kinds, the upload, the assembly and render refusals, the sidecar first

- [ ] 4.1 Replace `Unreachable` with `TransportFailure` and its `kind` in `isekai/boundary/comfy/`, `isekai/pipeline/generate.py`, `tests/test_generate.py:721` and `isekai/boundary/README.md` (with `provision.py`'s importers), per [D3](design.md#d3), [D7](design.md#d7).
  Verify: `git grep -n Unreachable -- isekai tests` prints nothing.
- [ ] 4.2 Classify in `_reported` per [D3](design.md#d3)'s table and [D1](design.md#d1)'s client row, with [D8](design.md#d8)'s status tests.
  Verify: `grep -c -e '^def test_a_rejected_graph_is_recorded_permanent' -e '^def test_a_server_error_is_recorded_transient' tests/test_generate.py` prints `2`.
- [ ] 4.3 Run the upload inside the render's guard, per [D3](design.md#d3), with [D8](design.md#d8)'s upload test.
  Verify: `grep -c '^def test_a_failed_upload_is_recorded' tests/test_generate.py` prints `1`.
- [ ] 4.4 Refuse `_submit`'s malformed history per [D1](design.md#d1), and give the render and assembly refusals [D2](design.md#d2)'s actions, the producer read inside the guard.
  Verify: `grep -c 'render again' isekai/pipeline/generate.py` prints `0`.
- [ ] 4.5 Write the sidecar before its image, and delete `prompt_artifact`'s `new_version`, per [D6](design.md#d6).
  Verify: `grep -c new_version isekai/pipeline/generate.py` prints `0`, and `grep -n -e 'write(provenance, RENDER_FILE' -e 'write_atomically(image' isekai/pipeline/generate.py | head -1 | grep -c provenance` prints `1`.

## 5 — Remedies: every printed command carries its run, and a guard holds it

- [ ] 5.1 Put the run id in every printed stage command [D2](design.md#d2) lists — `isekai/pipeline/review.py`, `generate.py`, `sheet.py`, `isekai/foundation/run.py`, `isekai/interface/ui/app.py` — keeping the substrings `tests/test_review.py:231` and `tests/test_ui.py:123` assert.
  Verify: `` cat isekai/pipeline/review.py isekai/pipeline/generate.py isekai/pipeline/sheet.py isekai/foundation/run.py isekai/interface/ui/app.py | grep -c -e '{flow}`' -e '{naming}`' -e 'new-version`' `` prints `0`.
- [ ] 5.2 Replace the `show` circle in `isekai/interface/cli.py` and `isekai/interface/ui/batch.py`, per [D2](design.md#d2).
  Verify: `` git grep -n 'show` prints' -- isekai `` prints nothing.
- [ ] 5.3 Make `tests/test_resume.py`'s command guard parse each printed command as printed and require a stage verb to name a run; update `AVAILABLE` (`:355-362`), per [D2](design.md#d2).
  Verify: `grep -c '"an-identifier"' tests/test_resume.py` prints `0`.
- [ ] 5.4 Coerce the WD14 tag in `isekai/pipeline/sheet.py:116`, per [D1](design.md#d1), with `test_a_non_string_tag_routes_nowhere` in `tests/test_sheet_stage.py`.
  Verify: `grep -c 'DanbooruTag(str(one\["tag"\]))' isekai/pipeline/sheet.py` prints `1`.

## 6 — The docs drop the breaks that close

- [ ] 6.1 Delete the known breaks this change closes from `docs/principles.md` (`:28-29`, `:127-131`, `:227`), and add *Only a front end composes*'s line for `load_vocabulary`, per [D7](design.md#d7).
  Verify: `grep -c -e 'can show an abandoned draft' -e 'errors escape as tracebacks' -e 're-approves a finished stage' docs/principles.md` prints `0`, and `grep -c load_vocabulary docs/principles.md` prints a number above `0`.
- [ ] 6.2 No live file names a retired name.
  Verify: `git grep -n -e Unreachable -e draft_versions -- ':!CHANGELOG.md' ':!openspec/changes'` prints nothing.
