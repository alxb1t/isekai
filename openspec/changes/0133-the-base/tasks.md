# The base — tasks

Phases of tests: the retry rule, a run's names, the session record's ends, every path a delete removes, "rendered" where every site agrees, and a refusal that leaves the tree whole.

## Progress

- [x] 1 — The retry rule · moderate
- [x] 2 — A run's names · moderate
- [x] 3 — The record's every end · moderate
- [x] 4 — Every path removed · moderate
- [x] 5 — Rendered, where all agree · moderate
- [x] 6 — Refused, whole · moderate

## 1 — The retry rule

- [x] 1.1 **HALT CHECK** The retry rule reads the budget by the stage's name, as [D1](design.md#d1) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'return "budget" if len(recorded) >= BUDGETS[stage] else None' isekai/foundation/run.py` prints `1`.
- [x] 1.2 In `tests/test_run_directory.py` add `test_a_stage_attempts_until_its_budget_and_refuses_at_it`, parametrized over `("caption", 3)`, `("wd14", 1)` and `("tags", 3)` as [D1](design.md#d1) says. It carries `run-directory:budget:at-budget-the-stage-refuses` and `tagging:budget:each-tagger-has-its-own-budget`.
  Verify: `git grep -c -F test_a_stage_attempts_until_its_budget_and_refuses_at_it tests/test_run_directory.py` prints `1`.
- [x] 1.3 In `tests/test_run_directory.py` delete `test_a_tagger_below_its_budget_attempts_again_rather_than_raising_keyerror`, mapped in the [Tests](design.md#tests) table to the test of 1.2.
  Verify: `git grep -c -F rather_than_raising_keyerror tests/test_run_directory.py` exits 1.
- [x] 1.4 In `tests/test_run_directory.py` add `test_a_stages_records_are_read_one_version_at_a_time`: a budget of transient `caption` records against version 1, then `attempts(directory, 2) == []` and `check_budget("caption", directory, 2, Run("aunt-ada", tmp_path))` returns. It carries `run-directory:budget:at-budget-the-stage-refuses`.
  Verify: `git grep -c -F test_a_stages_records_are_read_one_version_at_a_time tests/test_run_directory.py` prints `1`.

## 2 — A run's names

- [x] 2.1 **HALT CHECK** The instruction record names a file outside the repository by its name alone, as [D2](design.md#d2) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'if inside else resolved.name,' isekai/foundation/run.py` prints `1`.
- [x] 2.2 In `tests/test_run_directory.py` add to the parameters of `test_the_slug_keeps_nothing_that_could_leave_the_directory` the cases `("a_b", "a-b")`, `("a" * 31 + "-" + "b" * 8, "a" * 31)` and `("a" * 40, "a" * 32)`, each stem and its slug.
  Verify: `git grep -c -F '("a_b", "a-b")' tests/test_run_directory.py` prints `1`.
- [x] 2.3 In `tests/test_caption.py`, in `test_the_producer_records_the_briefings_path_and_digest`, after the assertion on `one["path"]` add `assert two["path"] == "other.md"`.
  Verify: `git grep -c -F 'assert two["path"] == "other.md"' tests/test_caption.py` prints `1`.
- [x] 2.4 In `tests/test_resume.py` import `tree` beside `snapshot` from `tests.conftest`. In `test_a_second_full_pass_changes_nothing_and_calls_nothing` read the runs root with `tree` in place of `snapshot`: `after_first = tree(wired.runs_root)` and `assert tree(wired.runs_root) == after_first`.
  Verify: `git grep -c -F 'after_first = tree(wired.runs_root)' tests/test_resume.py` prints `1`.
- [x] 2.5 In `tests/test_migrate.py` import `tree` beside `snapshot` from `tests.conftest`. In `test_a_second_run_changes_nothing` read the library with `tree` in place of `snapshot`: `first = tree(library.root)` and `assert tree(library.root) == first`.
  Verify: `git grep -c -F 'first = tree(library.root)' tests/test_migrate.py` prints `1`.

## 3 — The record's every end

- [x] 3.1 **HALT CHECK** A lost create and a failed teardown end the record through `refuse`, as [D3](design.md#d3) says; if `refuse` does not end it, the plan is wrong.
  Verify: `git grep -c -F 'record.end("failed", message)' isekai/interface/render.py` prints `1`.
- [x] 3.2 In `tests/test_render.py` read the record back in `test_a_flow_that_raises_closes_the_session` and `test_a_sigterm_inside_the_session_closes_it_and_exits_143` with `(record,) = records(runs)`. Assert the rows of [D3](design.md#d3): `(record["outcome"], record["message"]) == ("failed", "a flow raised")` in the first and `== ("stopped", None)` in the second, and teardown `done` in both.
  Verify: `git grep -c -F '== ("failed", "a flow raised")' tests/test_render.py` prints `1`.
- [x] 3.3 In `tests/test_render.py` read the record back in `test_the_ceiling_writes_its_refusal_and_ends_the_session_with_143` and `test_the_limits_retry_keeps_each_without`. Assert `record["outcome"] == "stopped"`, that `record["message"]` opens with `the session reached its` and that `record["message"].endswith("renders only the rest")`.
  Verify: `git grep -c -F 'endswith("renders only the rest")' tests/test_render.py` prints `2`.
- [x] 3.4 In `tests/test_render.py` read the records back in `test_a_lost_create_exits_3_and_a_failed_teardown_names_gpunit_down` with `lost, torn = records(runs)` and in `test_a_failed_body_is_named_beside_a_failed_teardown`. Assert `(lost["steps"]["pod"], lost["outcome"]) == ("lost", "failed")` with a message opening `the provider's answer was lost`, and for `torn` teardown `failed`, outcome `failed` and a message opening `the session's teardown failed`; each record has `ended` set. Keep both exemptions and add no key.
  Verify: `git grep -c -F '== ("lost", "failed")' tests/test_render.py` prints `1`.
- [x] 3.5 In `tests/test_edit_session.py` read `ended = json.loads(opened.read_text())` in `test_edit_render_a_session_may_hold_edits_alone` and assert `(ended["outcome"], ended["message"]) == ("done", None)`. In `test_edit_render_a_rejected_graph_fails_the_session_and_leaves_the_edit_pending` read `(held,) = (root.parent / SESSIONS).glob("*.json")` as `json.loads(held.read_text())` and assert `("failed", "a flow failed; the collection's log names it")`.
  Verify: `git grep -c -F "a flow failed; the collection's log names it" tests/test_edit_session.py` prints `1`.

## 4 — Every path removed

- [x] 4.1 **HALT CHECK** A discard of an edit deletes the chain in number order through `delete_edits`, as [D4](design.md#d4) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'return delete_edits(group, seed, sorted(taken))' isekai/pipeline/edit.py` prints `1`.
- [x] 4.2 In `tests/test_generate.py`, in `test_discarding_a_groups_last_render_removes_the_group`, replace `assert deleted[-1] == group` with the whole list: the image, then `group.absolute() / "42.render.json"`, then `group.absolute()`.
  Verify: `git grep -c -F 'group.absolute() / "42.render.json"' tests/test_generate.py` prints `1`.
- [x] 4.3 In `tests/test_review.py` import `tree` beside `snapshot` from `tests.conftest`. In `test_a_flow_left_with_no_approval_keeps_only_its_assignment` and `test_a_flows_own_description_goes_where_photo_holds_it` take `before` and `after` as `tree(run.path)` around each `withdraw`, set `gone = sorted(str(p.relative_to(run.path.absolute())) for p in went)` from its return `went`, and assert `assert gone == sorted(set(before) - set(after))`.
  Verify: `git grep -c -F 'assert gone == sorted(set(before) - set(after))' tests/test_review.py` prints `3`.
- [x] 4.4 In `tests/test_edit_session.py` and `tests/test_edit_placement.py` replace the sorted names asserted of `discard_edit` with the ordered list of `group / "<name>"` in the order of [D4](design.md#d4), without a file the case does not write. The placement case ends on `group / "42.edit-2.placement.json",` and `group / "42.edit-2.composite.png",`.
  Verify: `git grep -c -F 'group / "42.edit-2.placement.json",' tests/test_edit_placement.py` prints `1`.
- [x] 4.5 In `tests/test_edit_session.py`, in `test_edit_discard_the_last_render_with_an_edit_takes_the_group_and_the_approval`, import `tree` from `tests.conftest`, take `before = tree(run.path.parent)` before `_discard` and `after` after it, and assert `sorted(out.splitlines()) == sorted(f"discard deleted {name}" for name in set(before) - set(after))`.
  Verify: `git grep -c -F 'f"discard deleted {name}" for name in set(before) - set(after)' tests/test_edit_session.py` prints `1`.
- [x] 4.6 In `tests/test_ui_api.py`, in `test_deleting_a_render_deletes_its_files_and_thumbnail`, import `tree` from `tests.conftest`, `bare_wiring` from `tests.stages` and `build_parser`, `dispatch` from `isekai.interface.cli`. Before the first `client.delete` copy `made.path.parents[1]` with `shutil.copytree` to `tmp_path / "twin"`, run `dispatch` of `discard` on `twin_run / FLOW / "outputs" / "001" / "11.png"` with `bare_wiring(runs_root=tmp_path)`, and right after that route delete assert `set(tree(made.path)) == set(tree(twin_run))`, `twin_run` is `tmp_path / "twin" / "runs" / made.path.name`.
  Verify: `git grep -c -F 'set(tree(made.path)) == set(tree(twin_run))' tests/test_ui_api.py` prints `1`.

## 5 — Rendered, where all agree

- [x] 5.1 **HALT CHECK** `refuse_revision` reads a render as the sidecar of the seed, as [D5](design.md#d5) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'if not (group_of(run, flow, version) / f"{seed}{SIDECAR}").is_file():' isekai/pipeline/review.py` prints `1`.
- [x] 5.2 In `tests/test_review.py` add `test_a_revision_of_a_seed_no_render_wrote_is_refused`, parametrized on `failure`: true writes `record_failure(group, 1, "permanent", {"stage": "render", "seed": SEED, "detail": "x"})` into the group `run.directory(FLOW, "outputs", "001")`, false leaves it absent, after `_approved(run, schema, vocabulary)` wrote approval 1. `revise(run, FLOW, 1, SEED)` raises `Refusal` matching `rendered no seed`, and the snapshot of `run.path` is unchanged. It carries `@pytest.mark.spec_exempt("structural: a revision refuses a seed no render wrote")`.
  Verify: `uv run pytest tests/test_review.py::test_a_revision_of_a_seed_no_render_wrote_is_refused` passes.
- [x] 5.3 In `tests/test_review.py` add `test_a_revision_whose_seed_no_render_wrote_is_approved`, parametrized on `failure`: `revise` over a rendered `SEED`, the image and its sidecar unlinked, then the group holds the failure record of 5.2 when `failure` is true and is removed when false, and `approve` returns an approval. It carries `review:revise:new-seeds-alone-are-a-change`.
  Verify: `uv run pytest tests/test_review.py::test_a_revision_whose_seed_no_render_wrote_is_approved` passes.
- [x] 5.4 In `tests/test_review.py` add `test_a_copy_of_a_group_holding_no_render_keeps_the_approvals_own_renders`, parametrized on `failure` as in 5.2: `approve(run, CONTROL, schema, vocabulary, source=FLOW)` over `_approved_source` writes `renders` equal to `{"count": 1, "seeds": []}`, the default of an approval that lists none. It carries `review:copy-from:the-copy-carries-the-seeds`.
  Verify: `uv run pytest tests/test_review.py::test_a_copy_of_a_group_holding_no_render_keeps_the_approvals_own_renders` passes.
- [x] 5.5 In `tests/test_ui_library.py` add `test_a_cells_stage_reads_rendered_only_where_a_render_is_written`: an approved cell over a group holding an image and its sidecar is `rendered`, and over a group holding a failure record alone, and over no group, is `approved`, each read with `newest` true and with `newest` false. It carries `ui:hub:a-cells-stage-comes-from-its-run`.
  Verify: `uv run pytest tests/test_ui_library.py::test_a_cells_stage_reads_rendered_only_where_a_render_is_written` passes.

## 6 — Refused, whole

- [x] 6.1 **HALT CHECK** The CLI's `discard` refuses on a running session before it deletes anything, as [D6](design.md#d6) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'if render_running(run):' isekai/interface/cli.py` prints `1`.
- [x] 6.2 In `tests/test_pipeline_cli.py` import `tree` from `tests.conftest`. In `test_discard_deletes_the_render_and_its_thumbnail` take `before = tree(lib)` inside the held lock, before the refused `dispatch`, and assert `assert tree(lib) == before` after it.
  Verify: `git grep -c -F 'assert tree(lib) == before' tests/test_pipeline_cli.py` prints `1`.
- [x] 6.3 In `tests/test_edit_session.py`, in `test_edit_discard_a_running_session_refuses_an_edits_path`, take `before = tree(tmp_path)` inside the held lock, before `_discard`, and assert `assert tree(tmp_path) == before` after it.
  Verify: `git grep -c -F 'assert tree(tmp_path) == before' tests/test_edit_session.py` prints `1`.
