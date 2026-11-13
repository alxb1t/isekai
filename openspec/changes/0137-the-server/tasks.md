# The server — tasks

Phases of tests alone: the jobs' slots, the guard that answers before a handler and the bodies it refuses, Prepare and Stop over HTTP, the billing poll and the event stream, the page's request bodies, and the mutants that hold them.

## Progress

- [x] 1 — A job's slot · moderate
- [x] 2 — A route answers before its handler · moderate
- [x] 3 — Prepare and Stop · hard
- [ ] 4 — The poll and the stream · moderate
- [ ] 5 — The page's bodies · moderate
- [ ] 6 — The mutants die · moderate

## 1 — A job's slot

- [x] 1.1 **HALT CHECK** The refusal of a second job reads as [D8](design.md#d8)'s mutant `UB-4` expects; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'if job is not None and self._slots[kind].running:' isekai/interface/ui/jobs.py` prints `1`.
- [x] 1.2 In `tests/test_ui_jobs.py` add `def _failing_close(record: Path) -> Volume:`; its `run(argv, say)` appends `" ".join(argv)` to `record` and returns `GpunitExit(1 if "down" in argv else 0)`, and it returns `Volume(run=run, records=record.parent / ".gpunit")`.
  Verify: `git grep -c -F 'def _failing_close' tests/test_ui_jobs.py` prints `1`.
- [x] 1.3 In `tests/test_ui_jobs.py` add `test_a_failed_close_after_a_render_raises_the_volume_alert`, carrying `ui:render-job:a-failed-close-raises-the-volume-alert`. `record = tmp_path / "acts"`, `command = _order(record)[1]`, `Jobs(events.Broadcast(), lambda: None, volume=_failing_close(record), render=command, raise_volume=lambda: raised.append(True), now=lambda: "ended")`, then `render({"b": folder}, limit=1500, total=1, keep_open=False)` and `wait("render", WAIT)`. Assert `raised == [True]`, the slot's `session["steps"]["volume down"] == "failed"` and `record.read_text().splitlines()` is `volume up --yes`, `render 1500 <session id>`, `volume down`.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_a_failed_close_after_a_render_raises_the_volume_alert` passes.
- [x] 1.4 In `tests/test_ui_jobs.py` extend `test_a_render_job_opens_the_window_renders_at_the_limit_and_closes_it` in place: `raised: list[bool] = []`, `raise_volume=lambda: raised.append(True)` in its `Jobs`, and after its last assert `assert raised == []`, the twin of 1.3.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_a_render_job_opens_the_window_renders_at_the_limit_and_closes_it` passes.
- [x] 1.5 In `tests/test_ui_jobs.py` add `test_a_job_of_a_kind_starts_once_the_one_before_it_has_ended`, carrying `ui:prepare:a-job-follows-an-ended-one`. `volume, command = _order(tmp_path / "acts")`, `script = _Script("pass")`, `Jobs(events.Broadcast(), lambda: None, command=script, volume=volume, render=command, now=lambda: "ended")`; ask `prepare("b", folder, _steps(run), lambda line: [])` and `wait("prepare", WAIT)`, then again; ask `render({"b": folder}, limit=1500, total=1, keep_open=False)` and `wait("render", WAIT)`, then again. Assert `script.asked == [[f"{run.id}/{FLOW}"], [f"{run.id}/{FLOW}"]]` and that the record holds a `render` line for each session.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_a_job_of_a_kind_starts_once_the_one_before_it_has_ended` passes.
- [x] 1.6 In `tests/test_ui_jobs.py` add the constant `STEPS = (` and its closing `)`, a script printing, each with `flush=True`, `json.dumps({"step": "pod", "state": "done"})` and `json.dumps({"step": "image", "digest": "d1", "flow": "summon-anime-wai", "version": 1, "seed": "7"})`, then `raise SystemExit(1)`.
  Verify: `git grep -c -F 'STEPS = (' tests/test_ui_jobs.py` prints `1`.
- [x] 1.7 In `tests/test_ui_jobs.py` add `test_the_verbs_step_and_image_lines_are_the_sessions_steps_and_images`, carrying `ui:render-job:the-verbs-lines-are-the-sessions-steps`. `Jobs(..., volume=_order(tmp_path / "acts")[0], render=lambda limit, roots, session: [sys.executable, "-c", STEPS])` renders and ends. Assert the slot is `failed`, `session["steps"]["pod"] == "done"`, `session["images"] == [{"digest": "d1", "flow": FLOW, "version": 1, "seed": "7"}]`, and a message that starts `render ended with exit 1;` and holds `b/log.txt` and not `before reporting`. A second `Jobs` whose child is `[sys.executable, "-c", "raise SystemExit(1)"]` ends with `render ended with exit 1 before reporting; read b/log.txt`.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_the_verbs_step_and_image_lines_are_the_sessions_steps_and_images` passes.
- [x] 1.8 The phase's file agrees with the keys.
  Verify: `uv run pytest tests/test_ui_jobs.py` passes.

## 2 — A route answers before its handler

- [x] 2.1 **HALT CHECK** The guard's refusal of a foreign host reads as `UA-1a` expects; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'return JSONResponse({"refusal": "not addressed here"}, FORBIDDEN)' isekai/interface/ui/app.py` prints `1`.
- [x] 2.2 In `tests/test_ui_api.py` rewrite `test_a_request_carrying_someone_elses_host_is_refused` in place, keeping its name and key and its read: add `fields = client.get(_at(made)).json()["fields"]`, `fields["hair_colour"] = ["blonde"]`, `before = snapshot(made.path)`, and a `client.put(_at(made, "/draft"), json={"fields": fields}, headers={"host": f"evil.example:{PORT}"})`. Assert status `403`, `{"refusal": "not addressed here"}` and `snapshot(made.path) == before`.
  Verify: `uv run pytest tests/test_ui_api.py::test_a_request_carrying_someone_elses_host_is_refused` passes.
- [x] 2.3 In `tests/test_ui_api.py` rewrite `test_a_write_carrying_another_pages_origin_is_refused` in place the same way: the body of 2.2's `fields` in place of `{"fields": {}}`, `before = snapshot(made.path)` ahead of the request, and `snapshot(made.path) == before` after its `403` and `{"refusal": "not from this page"}`.
  Verify: `uv run pytest tests/test_ui_api.py::test_a_write_carrying_another_pages_origin_is_refused` passes.
- [x] 2.4 In `tests/test_ui_api.py` extend `test_every_loopback_alias_of_the_bound_port_is_answered` in place, adding the parameters `client: TestClient, made: Run` and keeping its asserts. For each `Host` of `localhost:{PORT}` and `[::1]:{PORT}` assert `client.get("/api/library", headers={"host": host}).status_code == 200`; then assert a draft update of `hair_colour` `["blonde"]` with `headers={"host": f"localhost:{PORT}", "origin": f"http://localhost:{PORT}"}` answers `200` and `client.get(_at(made)).json()["fields"]["hair_colour"] == ["blonde"]`.
  Verify: `uv run pytest tests/test_ui_api.py::test_every_loopback_alias_of_the_bound_port_is_answered` passes.
- [x] 2.5 In `tests/test_ui_api.py` add `_WRONG`, the ids `assign-flow`, `assign-sources`, `commit`, `quote-collections`, `quote-without`, `draft-flow`, `draft-images`, `renders-object` and `renders-seeds`, and `def _wrong(made: Run, staged: str, fields: dict[str, Any])` returning each id's `(method, path, json, text)` as the table of [D3](design.md#d3) gives it, the `renders` rows over `_at(made, "/draft")` with `fields`.
  Verify: `git grep -c -F 'def _wrong(' tests/test_ui_api.py` prints `1`.
- [x] 2.6 In `tests/test_ui_api.py` add `test_a_body_of_the_wrong_shape_is_refused_naming_what_it_lacks`, carrying `ui:damage:a-body-of-the-wrong-shape-is-refused-naming-what-it-lacks`, parametrized over `_WRONG`. It opens `staged = client.post("/api/staging").json()["id"]`, reads `fields`, takes `before = snapshot(made.path)`, sends the row with `client.request`, and asserts status `409`, the row's `text` in the answer's `refusal`, and `snapshot(made.path) == before`.
  Verify: `uv run pytest tests/test_ui_api.py::test_a_body_of_the_wrong_shape_is_refused_naming_what_it_lacks` passes.
- [x] 2.7 In `tests/test_ui_api.py` add `test_an_upload_past_its_declared_length_is_refused_before_its_body_is_read`, carrying `import:refuse:a-file-over-the-limit-is-refused`. Patch `importing_module.upload_limit` to `lambda *args, **kwargs: 1024 * 1024` and `importing_module.Reader.put` to a function that raises `AssertionError("the body was handed to the reader")`; build the client with `_client(wired, made, tmp_path)` after the first patch; open a staging, `client.put(f"/api/staging/{staged}/files/big.jpg", content=b"x" * (1024 * 1024 + 1))`. Assert status `409` and `big.jpg` and `past the 1 MB limit` in its `refusal`.
  Verify: `uv run pytest tests/test_ui_api.py::test_an_upload_past_its_declared_length_is_refused_before_its_body_is_read` passes.
- [x] 2.8 In `tests/test_ui_jobs.py` add `test_a_confirmation_that_names_no_collections_limit_images_or_bakes_is_refused`, carrying the key of 2.6. `_quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})`, `_approved(folder, "ada.jpg", FLOW, schema, vocabulary)`, `asked = {"collections": ["b"]}`, `shown` the quote's `estimate["limit_s"]`; post `/api/render` with `{"keep_open": False}`, `asked`, `{**asked, "limit_s": shown}` and `{**asked, "limit_s": shown, "images": 1}`, and assert each answers `409` holding in turn `names no collections`, `names no quoted limit`, `names no quoted images` and `names no quoted bakes`, and the quote's `disabled` is still `None`.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_a_confirmation_that_names_no_collections_limit_images_or_bakes_is_refused` passes.
- [x] 2.9 The phase's files agree with the keys.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_ui_jobs.py` passes.

## 3 — Prepare and Stop

- [x] 3.1 **HALT CHECK** The browser tests' wiring holds the Prepare reader on a collection named `hub-prepare`; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'runs.parent.name == "hub-prepare"' tests/e2e/wiring.py` prints `1`.
- [x] 3.2 In `tests/test_ui_jobs.py` give `_collection` the keyword `collection: str = "b"` after `*names`, naming the folder `tmp_path / "lib" / collection`; each caller stays as it is.
  Verify: `git grep -c -F 'collection: str = "b"' tests/test_ui_jobs.py` prints `1`.
- [x] 3.3 In `tests/test_ui_jobs.py` add `def _held_client(tmp_path, monkeypatch, vocabulary)`, returning `(app, client, folder, run)`: `monkeypatch.setenv("ISEKAI_WIRING", "tests.e2e.wiring:fake")`, `_collection(tmp_path, "ada.jpg", collection="hub-prepare")`, and the wiring, `dist` stub and `create_app(...)` of `test_a_stream_opened_for_a_collection_starts_with_both_slots_and_its_hub`. Add `_slot(app, client, kind)`, which reads `/events` as that test's `first_frame` does: a daemon thread waits up to `WAIT` for `app.state.broadcast._queues` to be non-empty and then publishes `events.CLOSE`, which ends only that call's stream; it returns `json.loads(first data)["jobs"][kind]`.
  Verify: `git grep -c -F 'def _held_client' tests/test_ui_jobs.py` prints `1`.
- [x] 3.4 In `tests/test_ui_jobs.py` add `def test_prepare_over_http_is_refused_while_it_runs_and_stop_interrupts_it`, carrying `ui:prepare:one-job-at-a-time` and `ui:prepare:stop-interrupts-the-job` as stacked markers, run inside `with client:` so its exit stops the surface and a child left running. Post `/api/c/hub-prepare/prepare`: status `200`, the answer's `job` `kind` `prepare` and `state` `running`; a second post is `409` holding `a job is running: Prepare on hub-prepare`; poll `/api/c/hub-prepare/hub` until the cell of `FLOW` reads `tagged`, so the child is held on `.prepare-release`.
  Verify: `git grep -c -F 'def test_prepare_over_http_is_refused_while_it_runs_and_stop_interrupts_it' tests/test_ui_jobs.py` prints `1`.
- [x] 3.5 In that test of `tests/test_ui_jobs.py` post `/api/jobs/prepare/stop`: status `200` and its `job` `kind` `prepare`; poll `_slot(app, client, "prepare")` until its `state` reads `stopped`, each poll under a deadline; assert the hub's cell of `FLOW` still reads `tagged`. The reader is held, so this proves the route and the interrupt; that no later stage starts is held by `test_stop_interrupts_the_stage_and_starts_no_later_one`.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_prepare_over_http_is_refused_while_it_runs_and_stop_interrupts_it` passes.
- [x] 3.6 In `tests/test_ui_jobs.py` add `test_stop_with_nothing_running_or_of_an_unknown_kind_is_refused`, carrying `ui:prepare:stop-interrupts-the-job`, over `_held_client`: `POST /api/jobs/prepare/stop` is `409` holding `no Prepare is running, so there is nothing to stop`, and `POST /api/jobs/nope/stop` is `409` holding `there is no nope job`.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_stop_with_nothing_running_or_of_an_unknown_kind_is_refused` passes.
- [x] 3.7 In `tests/test_ui_jobs.py` add `test_prepare_takes_the_cells_with_no_sheet_and_no_other`, carrying `ui:prepare:prepare-takes-the-cells-with-no-sheet`. `_collection(tmp_path, "assigned.jpg", "tagged.jpg", "sheeted.jpg", "damaged.jpg")`; `write_wd14` on the second run; `sheet(run, load_flow(FLOW).schema, vocabulary)` on the third and fourth; the fourth's newest file under `run.directory(FLOW, SHEETS)`, found by `latest_artifact` as `library.py` does, rewritten to `{}`. Assert `set(library.unprepared(library.hub(folder, OFFERED, FLOWS_DIR))[FLOW])` is the ids of the first and second runs.
  Verify: `uv run pytest tests/test_ui_jobs.py::test_prepare_takes_the_cells_with_no_sheet_and_no_other` passes.
- [x] 3.8 A new test that ran over five seconds in 3.4 carries `@pytest.mark.slow`; where none did, this task holds.
  Verify: `uv run pytest tests/test_ui_jobs.py` passes.

## 4 — The poll and the stream

- [ ] 4.1 In `tests/test_ui_billing.py` add `def _until(done: Callable[[], bool]) -> None`, which polls `done()` every `0.005` s for `20` s and then raises `AssertionError`, with `Callable` imported from `collections.abc` and `threading` and `time` from the standard library.
  Verify: `git grep -c -F 'def _until' tests/test_ui_billing.py` prints `1`.
- [ ] 4.2 In `tests/test_ui_billing.py` add `def test_gpunit_is_asked_on_start_and_while_a_session_runs_or_an_alert_is_open`, carrying `ui:billing:gpunit-is-asked-while-a-session-or-an-alert-is-open`. `running = {"on": False}` and `consulted: list[None]`, whose `session()` appends and returns `running["on"]`; `Billing(_volume(records, asked), tmp_path / "log", events.Broadcast(), session, now=lambda: NOW)`; `thread = billing.watch(interval=0.01)`. `_until` `len(asked) == 1`; then `_until` `len(consulted)` has grown by six and assert `len(asked) == 1`.
  Verify: `git grep -c -F 'def test_gpunit_is_asked_on_start' tests/test_ui_billing.py` prints `1`.
- [ ] 4.3 In that test set `running["on"] = True` and `_until` `len(asked)` passes its last value; set it `False`, `_until` `len(consulted)` has grown by six, take `settled = len(asked)`, then write `records / "pod"` and `_until` `len(asked) > settled`, so the alert alone asks. Delete the `pod` record, `_until` `not billing.alerting()`, `_until` `len(consulted)` has grown by six, take `settled = len(asked)`, `_until` it has grown by six again and assert `len(asked) == settled`. Then `billing.close()`, `thread.join(20)` and `assert not thread.is_alive()`.
  Verify: `uv run pytest tests/test_ui_billing.py::test_gpunit_is_asked_on_start_and_while_a_session_runs_or_an_alert_is_open` passes.
- [ ] 4.4 In `tests/test_ui_billing.py` add `test_an_alert_is_a_pod_or_a_volume_past_its_window`, carrying the key of 4.2: with a `Billing` as 4.2 builds it, `alerting()` is `False` with no record, `True` with a `pod` record, `False` with a window ending after `NOW` (`_window(records, "2026-10-21T13:00:00Z")`) and `True` with one ending before it (`"2026-10-21T11:00:00Z"`), each after the earlier record is removed.
  Verify: `uv run pytest tests/test_ui_billing.py::test_an_alert_is_a_pod_or_a_volume_past_its_window` passes.
- [ ] 4.5 In `tests/test_ui.py` add `test_a_stream_for_a_collection_sends_no_cell_of_another`, carrying `ui:events:a-stream-sends-only-its-collections-cells`. `events.stream(broadcast, lambda: {}, collection="a", heartbeat=WAIT)`; `next(stream)`; publish `("cell", {"collection": "b"})`, `("job", {"state": "x"})` and `("cell", {"collection": "a"})`. Assert the frames that follow equal `events.frame("job", {"state": "x"})` and `events.frame("cell", {"collection": "a"})`, then `broadcast.close()` and `next(stream, None) is None`.
  Verify: `uv run pytest tests/test_ui.py::test_a_stream_for_a_collection_sends_no_cell_of_another` passes.
- [ ] 4.6 In `tests/test_ui.py` add `test_a_quiet_stream_keeps_alive_and_ends_when_the_surface_stops`, carrying `ui:events:stopping-ends-open-streams-quietly`: `events.stream(broadcast, lambda: {}, heartbeat=0.01)`, its first frame starts `event: snapshot`, its next is `": keep-alive\n\n"`, and after `broadcast.close()` `next(stream, None) is None`.
  Verify: `uv run pytest tests/test_ui.py::test_a_quiet_stream_keeps_alive_and_ends_when_the_surface_stops` passes.
- [ ] 4.7 The phase's files agree with the keys.
  Verify: `uv run pytest tests/test_ui_billing.py tests/test_ui.py` passes.

## 5 — The page's bodies

- [ ] 5.1 **HALT CHECK** The server holds the key tuples [D6](design.md#d6) names, each on a line of its own; if it holds others or fewer, the plan is wrong.
  Verify: `git grep -c -E '^(OUTLINE|INK|STAGE1|PREVIEW|PROPOSE|BAKE)_KEYS = ' isekai/interface/ui/app.py` prints `6`.
- [ ] 5.2 Write `ui/src/test/wire.json` as [D6](design.md#d6) says: an object whose `bodies` holds an entry for each builder of its table, each with `builder`, `method`, `path`, `keys` and `server`, and `optional` where the table has one.
  Verify: `grep -c -F '"builder":' ui/src/test/wire.json` prints `6`.
- [ ] 5.3 In `ui/tsconfig.json` add `"resolveJsonModule": true` to `compilerOptions`, after its `"strict": true` line, so a test may import the fixture.
  Verify: `git grep -c -F '"resolveJsonModule": true' ui/tsconfig.json` prints `1`.
- [ ] 5.4 Write `ui/src/api.test.ts`: it imports `spec` from `./test/spec`, `vi` and `afterEach` from `vitest`, `import wire from './test/wire.json'` and the builders from `./api`. A helper `sent(call)` stubs `fetch` with `vi.stubGlobal`, answering `200` with `{}` and the headers `X-Ink-Box: 1,2,3,4`, `X-Preview-Box: 1,2,3,4` and `X-Ink-White: 128`, runs `call`, and returns the url, the method and `Object.keys(JSON.parse(body))`. A helper `answered(status, body, headers = {})` stubs `fetch` to answer `new Response(body, { status, headers })`. `afterEach` calls `vi.unstubAllGlobals()`.
  Verify: `grep -c -F "from './test/wire.json'" ui/src/api.test.ts` prints `1`.
- [ ] 5.5 In `ui/src/api.test.ts` add a `spec` for each builder of the fixture, naming each key literally on the call: `saveStageOne` `ui:pairs:the-pairs-stay-across-steps`, `saveOutline` `ui:outline-edit:a-click-adds-a-vertex-and-the-first-closes`, `inkView` `ui:outline-step:the-size-of-the-cuts-ink-is-the-outlines-box`, `placementPreview` `ui:preview:one-ask-follows-a-burst-of-changes`, `proposePairs` `ui:proposal:the-points-sent-are-the-tattoos-on-the-photograph` and `bakeTattoo` `ui:review:bake-waits-for-a-stage-and-then-queues`. Each calls its builder with arguments of the types of `ui/src/types.ts` and asserts the entry's `method`, a `path` matching its template with `{…}` as `[^/]+`, and the keys sent, sorted, equal to the entry's `keys`, sorted.
  Verify: `grep -c -E "^spec\('ui:(pairs:the-pairs|outline-edit:a-click|outline-step:the-size|preview:one-ask|proposal:the-points|review:bake)" ui/src/api.test.ts` prints `6`.
- [ ] 5.6 In `ui/src/api.test.ts` add three more `spec`s, one for each mutant of `VT-18`: `ui:picker:a-refusal-shows-its-fix` (through `answered`, `keepTattoo` answered `502` with an HTML body rejects `/api/tattoos answered 502`, and answered `409` with `{"refusal": "name taken"}` rejects `name taken`); `ui:draft-from:a-selection-drafts-into-the-flow-chosen` (`draft` answered `409` with `{"refusal": "x", "images": []}` resolves to that body); `ui:preview:a-refusal-clears-the-answer-and-shows-its-fix` (`inkView` answered `200` through `answered` with `X-Ink-White: 128` and no `X-Ink-Box` rejects `answered no ink box or white point`).
  Verify: `uv run python -m tools.test_ui` exits `0`.
- [ ] 5.7 In `tests/test_ui_wire.py` add `wire_faults(bodies, tuples, routes) -> list[str]`, returning a line for each entry whose `server` is no tuple, whose `keys` less `optional` is not its tuple, whose `optional` is not in its `keys`, whose method and path is no route, and for each tuple no entry names; and `test_the_page_bodies_agree_with_the_server_key_tuples`, marked `spec_exempt("structural: the page's request bodies and the server's key tuples agree")`, reading `ui/src/test/wire.json`, the tuples as every `*_KEYS` tuple of `isekai.interface.ui.app`, and the routes of `create_app(...)` built as `tests/test_ui_billing.py` builds its app, and asserting no fault.
  Verify: `uv run pytest tests/test_ui_wire.py::test_the_page_bodies_agree_with_the_server_key_tuples` passes.
- [ ] 5.8 In `tests/test_ui_wire.py` add `test_a_fixture_that_drifts_from_the_server_is_caught`, marked `spec_exempt("structural: twin of test_the_page_bodies_agree_with_the_server_key_tuples")`: `wire_faults` over a fixture that drops a key, names no tuple, names a route the server does not serve and leaves a tuple unnamed returns a line for each.
  Verify: `uv run pytest tests/test_ui_wire.py` passes.

## 6 — The mutants die

- [ ] 6.1 **HALT CHECK** `0135-the-paydown` is merged: the replay mode and the target exist; if they do not, this phase has nothing to run.
  Verify: `git grep -c -F 'tools.mutate --edits tests/mutants.json' Makefile` prints `1`.
- [ ] 6.2 **HALT CHECK** `0136-the-cli-and-the-session` is merged: `tests/mutants.json` holds its entry `PB-16`, so this change appends to the file after it.
  Verify: `grep -c -F 'PB-16' tests/mutants.json` prints `1`.
- [ ] 6.3 **HALT CHECK** Phases 1 to 5 edited no product file, so each line the mutants name stands: the refusal of 1.1 holds.
  Verify: `git grep -c -F 'if job is not None and self._slots[kind].running:' isekai/interface/ui/jobs.py` prints `1`.
- [ ] 6.4 Append each entry of [mutants.json](mutants.json) to `tests/mutants.json`, keys and order unchanged, indented as the file is; each opens with `"finding":`.
  Verify: `grep -c -F '"finding":' tests/mutants.json` prints `41`.
- [ ] 6.5 Run the replay. A line that names a survivor goes to 6.6.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
- [ ] 6.6 For each `survivor` line 6.5 printed, add in the file its entry names a test red with the mutant in place and green without it; only where no input tells the mutant from the line, give the entry `equivalent` with the reason, proven by reading the line. Never delete an entry. Where 6.5 printed none, this task holds.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
