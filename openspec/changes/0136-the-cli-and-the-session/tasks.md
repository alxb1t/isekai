# The CLI and the session — tasks

Phases of tests and the product fixes they found: the verbs' refusals, the remedies they print, the free checks before a pod is rented, the batch that survives its refusals, and the mutants that hold them.

## Progress

- [ ] 1 — A verb's refusals · hard
- [ ] 2 — Every remedy works · moderate
- [ ] 3 — Nothing rents before the checks · moderate
- [ ] 4 — A batch survives its refusals · moderate
- [ ] 5 — The mutants die · moderate

## 1 — A verb's refusals

- [ ] 1.1 **HALT CHECK** The parser requires a verb on the line [D2](design.md#d2) rewrites; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'verbs = parser.add_subparsers(dest="verb", metavar="verb", required=True)' isekai/interface/cli.py` prints `1`.
- [ ] 1.2 In `isekai/interface/cli.py` add above `build_parser` the class `class _Verb(argparse.ArgumentParser):`, its `error(self, message: str) -> NoReturn` as [D2](design.md#d2) says: a message holding `--flow` gains `; the flows this build tracks are ` and `", ".join(tracked_flows(FLOWS_DIR)) or "(none)"`, then `super().error(message)`. Import `NoReturn` from `typing` and `FLOWS_DIR` from `isekai.foundation.flow`.
  Verify: `git grep -c -F 'class _Verb(argparse.ArgumentParser):' isekai/interface/cli.py` prints `1`.
- [ ] 1.3 In `build_parser` pass `parser_class=_Verb`, the call in the shape the formatter gives: `verbs = parser.add_subparsers(`, then `dest="verb", metavar="verb", required=True, parser_class=_Verb` on its own line, then `)`.
  Verify: `git grep -c -F 'metavar="verb", required=True, parser_class=_Verb' isekai/interface/cli.py` prints `1`.
- [ ] 1.4 In `tests/test_pipeline_cli.py` rewrite `test_no_verb_at_all_is_refused_too` in place, keeping its name and key: `build_parser().parse_args([])` under `pytest.raises(SystemExit)`, code `2`, and `the following arguments are required: verb` in `capsys.readouterr().err`.
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_no_verb_at_all_is_refused_too` passes.
- [ ] 1.5 In `tests/test_pipeline_cli.py` rewrite `test_a_stage_verb_without_a_flow_is_refused` in place, keeping its name and key: parametrize over `assign`, `sheet`, `review`, `approve` and `generate`, parse `[verb, "ada.jpg"]` under `pytest.raises(SystemExit)`, and assert code `2`, `the following arguments are required: --flow` and each name `tracked_flows(FLOWS_DIR)` returns in the message. Import both from `isekai.foundation.flow`; drop `_module` use there.
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_a_stage_verb_without_a_flow_is_refused` passes.
- [ ] 1.6 In `tests/test_pipeline_cli.py` add `test_a_count_or_a_seed_out_of_range_is_refused_at_parse_time`, carrying `cli:generate-signature:a-count-or-seed-out-of-range-is-refused`. Parametrize `(flag, value, message)`: `--count` `0` and `-1` with `a render count below 1 renders nothing`, `--count` `x` and `--seed` `x` with `is not an integer`, `--seed` `-1` and `18446744073709551616` with `is outside the sampler's unsigned 64-bit range`. Each parses `generate --flow summon-anime-wai <flag> <value>` under `pytest.raises(SystemExit)`, asserts code `2` and the message in `capsys`.
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_a_count_or_a_seed_out_of_range_is_refused_at_parse_time` passes.
- [ ] 1.7 In `tests/test_pipeline_cli.py` add `test_a_limit_below_one_second_is_refused_at_parse_time`, carrying `cli:render-limit:below-one-second-is-refused-at-parse-time`: parse `["render", "--limit", value, str(tmp_path)]` for `0` and `-1` with `a session limit below 1s ends at once` and for `x` with `is not an integer`, each under `pytest.raises(SystemExit)`, code `2`, the message in `capsys`.
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_a_limit_below_one_second_is_refused_at_parse_time` passes.
- [ ] 1.8 The record walks the parser's actions and groups, not its class, so it does not move.
  Verify: `uv run pytest tests/test_record.py` passes.

## 2 — Every remedy works

- [ ] 2.1 **HALT CHECK** The empty runs root's remedy names `tag`, as [D3](design.md#d3) says; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F "uv run python -m isekai tag {' '.join(flows)} --runs " isekai/interface/render.py` prints `1`.
- [ ] 2.2 In `isekai/interface/render.py` `_asked` change `uv run python -m isekai tag {' '.join(flows)} --runs ` to `uv run python -m isekai assign {' '.join(flows)} --runs ` in the empty-root refusal, and nothing else.
  Verify: `git grep -c -F "uv run python -m isekai assign {' '.join(flows)} --runs " isekai/interface/render.py` prints `1`.
- [ ] 2.3 In `tests/test_render.py` add `test_a_request_over_a_runs_root_with_no_run_is_refused_naming_assign`, carrying `cli:refusals:refusal-names-the-remedy`: `runs = tmp_path / "b" / "runs"` made with `runs.mkdir(parents=True)`, not through `collection()`, which always creates a run; then `session(runs, f"{FLOW}=1", opener=opener)`. Assert status `1`, `opener.opened == 0`, no `sessions/` folder beside `runs`, and in `log(runs)` the sentence `holds no run` and `isekai assign --flow {FLOW} --runs {runs}` and no `isekai tag`.
  Verify: `uv run pytest tests/test_render.py::test_a_request_over_a_runs_root_with_no_run_is_refused_naming_assign` passes.
- [ ] 2.4 In `tests/test_resume.py` `_printed` also return the command a message prints after `uv run python -m isekai ` to its end (`re.findall(r"uv run python -m isekai (\S.*)$", message)`), and `_names_its_run` return `not parsed.flows and bool(parsed.photos)` for a verb in `PHOTOGRAPH_VERBS`, which the file already imports.
  Verify: `git grep -c -F 'not parsed.flows and bool(parsed.photos)' tests/test_resume.py` prints `1`.
- [ ] 2.5 In `tests/test_resume.py` widen `test_the_command_guard_catches_a_command_that_names_no_run` in place: add `tag --flow summon-anime-wai --runs /nowhere/runs photo.jpg` printed in backticks, and the same command printed after `uv run python -m isekai ` without them, each asserted to be returned by `_unrunnable`.
  Verify: `uv run pytest tests/test_resume.py::test_the_command_guard_catches_a_command_that_names_no_run` passes.
- [ ] 2.6 In `tests/test_resume.py` add `_front_end_refusals(wired, tmp_path, photo, messages)` and call it at the end of `_every_refusal`. It appends, with its `refused: ` prefix removed, what `dispatch(build_parser().parse_args(["tag", "--flow", FLOW, "--runs", str(tmp_path / "elsewhere"), str(photo)]), aside)` prints to `aside.err`, and what `run_session(argparse.Namespace(runs=[empty], requests=[f"{FLOW}=1"]), aside, lambda argv, wired: 0, Seams())` prints over an empty `tmp_path / "empty" / "runs"`; `aside` is `dataclasses.replace(wired, err=io.StringIO())`.
  Verify: `git grep -c -F '_front_end_refusals' tests/test_resume.py` prints `2`.
- [ ] 2.7 In `tests/test_resume.py` remove from `AVAILABLE` the lines `    "delete",` and `    "rename",`, those matching `^    "(delete|rename)",$`, as [D4](design.md#d4) says.
  Verify: `git grep -L -E -e '^    "(delete|rename)",$' tests/test_resume.py` prints `tests/test_resume.py`.
- [ ] 2.8 A message the sweep then names as unhelpful gives the phrase of that message from its `delete` or `rename` to the next `;`, `,` or `.`, as printed, and that phrase is added to `AVAILABLE`. Where the sweep names none, this task holds.
  Verify: `uv run pytest tests/test_resume.py` passes.
- [ ] 2.9 The phase's files agree with each other and the keys.
  Verify: `uv run pytest tests/test_render.py tests/test_review.py tests/test_resume.py` passes.

## 3 — Nothing rents before the checks

- [ ] 3.1 In `tests/test_render.py` give the `session` helper a keyword `limit: int | None = None` and put the line `limit=limit,` into its `argparse.Namespace`.
  Verify: `git grep -c -F 'limit=limit,' tests/test_render.py` prints `1`.
- [ ] 3.2 In `tests/test_render.py` add `test_with_no_request_a_failing_free_check_rents_nothing`, carrying `pod-image:session:every-exit-tears-down`: `counted(tmp_path, schema, vocabulary, "ada", 1)`, `session(root, generate=Calls(lambda argv, wired: 1 if "--server" not in argv else 0), opener=opener, wiring=real(root, vocabulary))`. Assert status `1`, `opener.opened == 0`, and no `sessions/` folder beside `root`.
  Verify: `uv run pytest tests/test_render.py::test_with_no_request_a_failing_free_check_rents_nothing` passes.
- [ ] 3.3 In `tests/test_render.py` add `test_a_limit_below_the_floor_is_refused_before_renting`, carrying `cli:render-limit:below-the-floor-is-refused`: `session(runs, f"{FLOW}=1", limit=render.FLOOR_S - 1, opener=opener)`. Assert status `1`, `opener.opened == 0`, and `give at least --limit {render.FLOOR_S}` in `log(runs)`.
  Verify: `uv run pytest tests/test_render.py::test_a_limit_below_the_floor_is_refused_before_renting` passes.
- [ ] 3.4 In `tests/test_render.py` add `test_a_given_limit_is_the_sessions_limit`, carrying `cli:render-limit:a-given-limit-is-the-sessions`: `session(runs, f"{FLOW}=1", limit=render.FLOOR_S + 60, opener=opener)`. Assert status `0`, `opener.limits == [render.FLOOR_S + 60]` and `session limit {render.FLOOR_S + 60}s` in `log(runs)`.
  Verify: `uv run pytest tests/test_render.py::test_a_given_limit_is_the_sessions_limit` passes.
- [ ] 3.5 In `tests/test_render.py` add `test_a_lone_source_request_is_checked_free_and_planned`, carrying `cli:render-session:the-record-plans-each-photograph`: a run from `counted(tmp_path, schema, vocabulary, "ada", 2)`, `session(root, "control-anime-wai=summon-anime-wai", generate=calls)` with `Calls()`. Assert status `0`, one free line holding `--seeds-from` and `summon-anime-wai`, and the record's `planned` holding that run with `images` of the source's renders.
  Verify: `uv run pytest tests/test_render.py::test_a_lone_source_request_is_checked_free_and_planned` passes.
- [ ] 3.6 In `tests/test_render.py` add `test_a_lone_source_request_whose_free_check_fails_rents_nothing`, carrying `image-generation:seeds-from:no-source-render-is-refused-first`: the arrangement of 3.5 with `Calls(lambda argv, wired: 1 if "--seeds-from" in argv else 0)`. Assert status `1` and `opener.opened == 0`.
  Verify: `uv run pytest tests/test_render.py::test_a_lone_source_request_whose_free_check_fails_rents_nothing` passes.
- [ ] 3.7 In `tests/test_render.py` add `test_render_through_the_parser_writes_the_sessions_record`, carrying `cli:render-session:a-session-writes-its-record`: `counted(tmp_path, schema, vocabulary, "ada", 1)`, then `_dispatch_argv(["render", str(root)], dataclasses.replace(real(root, vocabulary), session=render.Seams(open_session=FakeOpen(), environ={}, connect=lambda server: FakeComfyClient(), busy=lambda port: False, kill=lambda: None)))`. Assert `0`, one record in `records(root)`, its `outcome` `done`.
  Verify: `uv run pytest tests/test_render.py::test_render_through_the_parser_writes_the_sessions_record` passes.
- [ ] 3.8 In `tests/test_render.py` add `test_a_request_with_no_collection_is_refused_at_parse_time`, carrying `cli:render-session:a-refusal-before-renting-writes-none`: `build_parser().parse_args(["render", f"{FLOW}=1"])` under `pytest.raises(SystemExit)`, code `2`, `name at least one collection's runs/` in `capsys`.
  Verify: `uv run pytest tests/test_render.py::test_a_request_with_no_collection_is_refused_at_parse_time` passes.
- [ ] 3.9 In `tests/test_render.py` add `test_edit_limit_takes_the_newest_records_when_there_are_more_than_the_window`, carrying `edit:edit-limit:a-median-above-the-figure-is-used`. In one group write `_edit_records` for seed `1` with `duration=9999.0` and for seeds `2` to `render.RECENT + 1` with `duration=1.0`, set each `{seed}.edit-1.json`'s mtime to `os.utime(path, (seed, seed))`, and assert `render.recent_edits(root, ["r1"]) == [1.0] * render.RECENT`. Import `os`.
  Verify: `uv run pytest tests/test_render.py::test_edit_limit_takes_the_newest_records_when_there_are_more_than_the_window` passes.
- [ ] 3.10 In `tests/test_render.py` replace the `spec_exempt` of `test_a_port_that_already_answers_is_refused_before_the_session` with `@pytest.mark.spec("pod-image:session:a-busy-port-is-refused-before-the-session")`.
  Verify: `git grep -c -F 'pod-image:session:a-busy-port-is-refused-before-the-session' tests/test_render.py` prints `1`.
- [ ] 3.11 In `tests/test_gpu.py` add `test_answers_is_true_while_something_listens_and_false_once_it_stops`, carrying the key of 3.10: bind a `socket.socket()` to `("127.0.0.1", 0)`, `listen()`, assert `gpu.answers(port) is True`; after the socket is closed assert `gpu.answers(port) is False`. Import `socket`.
  Verify: `uv run pytest tests/test_gpu.py::test_answers_is_true_while_something_listens_and_false_once_it_stops` passes.
- [ ] 3.12 In `tests/test_spec_bindings.py` delete the `BEHAVIOUR_EXEMPT` row of `test_a_port_that_already_answers_is_refused_before_the_session` and set `BEHAVIOUR_CEILING = 21`, as [D6](design.md#d6) says.
  Verify: `git grep -c -F 'BEHAVIOUR_CEILING = 21' tests/test_spec_bindings.py` prints `1`.
- [ ] 3.13 The phase's files agree with the table and the keys.
  Verify: `uv run pytest tests/test_render.py tests/test_gpu.py tests/test_spec_bindings.py` passes.

## 4 — A batch survives its refusals

- [ ] 4.1 **HALT CHECK** The batch is composed as one `across` over the targets plus the `broken` list, as [D7](design.md#d7) says; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'refused = across(list(targets), assemble_one) + broken' isekai/interface/cli.py` prints `1`.
- [ ] 4.2 In `tests/test_generate.py` add `test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound`, carrying the keys of the I16 table in [design](design.md#tests). Runs from `_run`: `good`; `sheet`, its `001.approved.json` rewritten to `{"schema": {"name": "review", "version": 1}}`; `header`, its photograph rewritten to `b"\x89PNG\r\n\x1a\n"`; `wide`, `body=jpeg_bytes(5000, 1000)`. Run `dispatch(build_parser().parse_args(["generate", "--flow", FLOW, "nowhere", sheet.id, header.id, wide.id, good.id]), _seeded_session(tmp_path, vocabulary, FakeComfyClient(), err))`; `nowhere` names no run, and is the target on which `assemble_one` itself raises.
  Verify: `uv run pytest tests/test_generate.py::test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound` passes.
- [ ] 4.3 In that test assert status `1`; one `refused:` line in `err` for each bad target, one holding `neither a photograph on disk nor a run`, one naming `sheet.id`, one holding `re-export the photograph`, one holding `5120`, `1024` and `str(MAX_TARGET_LONG_SIDE)`; `good`'s prompt `good.directory(FLOW, PROMPTS) / artifact_name(1)` written; and `header.directory(FLOW, PROMPTS)` holding `001.error.1.permanent.json`.
  Verify: `uv run pytest tests/test_generate.py::test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound` passes.
- [ ] 4.4 Delete the tests the I16 table names: `tests/test_generate.py::test_one_bad_sheet_does_not_stop_the_other_photographs` (`def test_one_bad_sheet_does_not_stop_the_other_photographs`), `tests/test_generate.py::test_one_unreadable_header_does_not_cost_the_batch_its_turn` (`def test_one_unreadable_header_does_not_cost_the_batch_its_turn`) and `tests/test_generate.py::test_one_photograph_past_the_bound_does_not_cost_the_batch_its_session` (`def test_one_photograph_past_the_bound_does_not_cost_the_batch_its_session`); and each import or helper only they used.
  Verify: `git grep -L -e 'def test_one_bad_sheet_does_not_stop' -e 'def test_one_unreadable_header_does_not_cost' -e 'def test_one_photograph_past_the_bound_does_not_cost' tests/test_generate.py` prints `tests/test_generate.py`.
- [ ] 4.5 In `docs/principles.md`, in the **Held by** list of *Every refusal ends with a fix that works*, replace `tests/test_generate.py::test_one_photograph_past_the_bound_does_not_cost_the_batch_its_session` with `tests/test_generate.py::test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound`; the principle's check reads the name.
  Verify: `git grep -c -F 'tests/test_generate.py::test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound' docs/principles.md` prints `1`.
- [ ] 4.6 In `tests/test_edit.py` rename `test_edit_pending_a_failed_sampling_does_not_cost_the_next_its_turn` to `def test_edit_pending_a_failed_sampling_leaves_its_request_pending`, its body and key unchanged.
  Verify: `git grep -c -F 'def test_edit_pending_a_failed_sampling_leaves_its_request_pending' tests/test_edit.py` prints `1`.
- [ ] 4.7 In `tests/test_edit.py` add `_RejectsTheFirst(RecordingComfyClient)`, built as `_RejectsTheFirst(rejects=TransportFailure("permanent", "rejected"), view_bytes=_pod().view_bytes)`, whose `submit(self, workflow: Workflow) -> str` does `failure, self.rejects = self.rejects, None` and raises `failure` when it is set, else `return super().submit(workflow)`, with `Workflow` imported from `isekai.foundation.flow`; and `test_edit_pending_a_failed_sampling_costs_the_next_edit_nothing`, carrying `edit:session:a-failed-sampling-costs-the-next-edit-nothing`. `_ask` requests on the scene with seeds `5` and `6`, then `_pending(tmp_path, client=pod)`: assert code `1`, `42.edit-2.png` written, `42.edit-1.png` not, `[path.name for path in pending(group)] == ["42.edit-1.json"]`, and `refused: 42.edit-1.json: the sampling failed (permanent) -- rejected` in `err`.
  Verify: `uv run pytest tests/test_edit.py::test_edit_pending_a_failed_sampling_costs_the_next_edit_nothing` passes.
- [ ] 4.8 In `tests/test_edit.py` add `test_edit_pending_a_chain_is_checked_before_the_pod_without_its_first_image`, carrying `edit:session:a-chain-of-pending-edits-runs-in-order`, arranged as `test_edit_sample_a_source_another_edit_will_write_is_not_yet_checked` is, up to `first.unlink()`. Then `_pending(tmp_path, client=_pod())`: assert code `1`, `42.edit-1.png` written, `refused: 42.edit-2.json: its source 42.edit-1.png has changed since the request` in `err`, and `cannot be read` not in `err`.
  Verify: `uv run pytest tests/test_edit.py::test_edit_pending_a_chain_is_checked_before_the_pod_without_its_first_image` passes.
- [ ] 4.9 In `tests/test_review.py` add to `test_an_unedited_waiting_draft_is_replaced_at_its_number`, after its last assert, `assert read(draft, DRAFT_FILE)["fields"]["hair_silhouette"] == ["very long hair"]`.
  Verify: `git grep -c -F 'hair_silhouette"] == ["very long hair"]' tests/test_review.py` prints `1`.
- [ ] 4.10 The phase's files agree with each other, the keys and the principles.
  Verify: `uv run pytest tests/test_generate.py tests/test_edit.py tests/test_review.py tests/test_principles.py` passes.

## 5 — The mutants die

- [ ] 5.1 **HALT CHECK** `0135-the-paydown` is merged: the replay mode and the target exist; if they do not, this phase has nothing to run.
  Verify: `git grep -c -F 'tools.mutate --edits tests/mutants.json' Makefile` prints `1`.
- [ ] 5.2 **HALT CHECK** Phases 1 to 4 left the lines the mutants name as [D10](design.md#d10) says: the parser's line of 1.3 holds.
  Verify: `git grep -c -F 'metavar="verb", required=True, parser_class=_Verb' isekai/interface/cli.py` prints `1`.
- [ ] 5.3 Append each entry of [mutants.json](mutants.json) to `tests/mutants.json`, keys and order unchanged, indented as the file is; each opens with `"finding":`.
  Verify: `grep -c -F '"finding":' tests/mutants.json` prints `35`.
- [ ] 5.4 Run the replay. A line that names a survivor goes to 5.5.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
- [ ] 5.5 For each `survivor` line 5.4 printed, add in the file its entry names a test red with the mutant in place and green without it; only where no input tells the mutant from the line, give the entry `equivalent` with the reason, proven by reading the line. Never delete an entry. Where 5.4 printed none, this task holds.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
