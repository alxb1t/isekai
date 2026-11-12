# The record — tasks

Tests alone: the graphs, the run, the verbs, the routes, then the wire. Decisions are in [design](design.md).

## Progress

- [ ] 1 — The graphs · moderate
- [ ] 2 — The run · moderate
- [ ] 3 — The verbs · moderate
- [ ] 4 — The routes · moderate
- [ ] 5 — The wire · moderate

## 1 — The graphs

- [ ] 1.1 Create `tests/record.py` per [D1](design.md#d1): a module docstring saying what the record is and that `uv run python -m tests.record` writes it, then `REPO_ROOT`, `RECORD`, `FLOWS` (the flow ids under `flows/`, `summon-anime-wai` first), `dump(value)`, `recorded(name)`, an empty `FILES`, `derive(done)`, `write(directory)` and `main()`.
  Verify: `uv run python -c "import tests.record"` exits 0.

- [ ] 1.2 In `tests/record.py`, add `def wiring(*, runs)` and `def using(client)` per [D2](design.md#d2) and [D3](design.md#d3): `wiring` returns `dataclasses.replace(fake(runs=runs), client=<the module variable>, out=<a new StringIO, kept in OUTS>, err=<a new StringIO>)`, `fake` from `tests/e2e/wiring.py`; `using` sets `ISEKAI_WIRING` through `os.environ` and the module variable, and restores both.
  Verify: `grep -n -F "def using(" tests/record.py` prints the definition.

- [ ] 1.3 In `tests/record.py`, add `Done` (the fields `root`, `library`, `collection`, `runs`, `run`, `renders`, `edits` and `said`: the pass's directory, library, collection, runs root and run, the render client, the edit client and the stdout of each verb) and `def drive(done)` per [D2](design.md#d2): `caption` and `tag` over the photograph with no `--flow`, then `assign`, `sheet`, `review`, `approve` and `generate --seed 42` over every flow of `FLOWS` with `--flow` repeated, each through `main` with `--runs` the collection's runs root. `sheet` and `generate` take `--progress json`. Each call asserts exit status 0, naming the wiring's `err` text.
  Verify: `grep -n -F "def drive(" tests/record.py` prints the definition.

- [ ] 1.4 In `tests/record.py`, add `offline(root)`: write `jpeg_bytes(1200, 900)` as `ada.jpg` in the collection's `sources/`, open its run, restate `_png(pixels)`, `SIDE` and `SKIN` from `tests/test_edit_session.py`, set the render client to a `FakeComfyClient` answering a PNG of `np.full((SIDE, SIDE, 3), SKIN, dtype=np.uint8)`, and `drive` it. **HALT CHECK** Run it: a flow that refuses a verb — a sheet its field map cannot fill, an approval that wants a hand edit — means the plan is wrong. Edit nothing else and stop.
  Verify: `uv run python -c "import pathlib, tempfile; from tests.record import offline; offline(pathlib.Path(tempfile.mkdtemp()))"` exits 0.

- [ ] 1.5 In `tests/record.py`, add the edit to `offline` per [D2](design.md#d2): request an edit of the first flow's render `outputs/001/42.png`, whose composite equals the render but for the tattoo's square multiplied in, written under the pass's directory; set the edit client to a `RecordingComfyClient` answering a flat crop; run `edit --pending <run id>/<flow>`; and assert the edit client's last submission holds the node class `SetUnionControlNetType`. **HALT CHECK** A refused request or sampling means the plan is wrong: edit nothing else and stop.
  Verify: `uv run python -c "import pathlib, tempfile; from tests.record import offline; print(any(offline(pathlib.Path(tempfile.mkdtemp())).runs.rglob('42.edit-1.png')))"` prints `True`.

- [ ] 1.6 In `tests/record.py`, add `graphs(done)`, returning `{"flows": {<flow id>: <graph>}, "edit": <graph>}` from the render client's submissions in the order of `FLOWS` and the edit client's last, asserting the submissions cover every flow, and register it as `FILES["graphs"]`.
  Verify: `uv run python -c "import tests.record as r; print(sorted(r.FILES))"` prints `['graphs']`.

- [ ] 1.7 Create `tests/test_record.py` per [D9](design.md#d9): a module-scoped fixture running `offline` under `tmp_path_factory` and `derive`; `test_the_pass_renders_every_flow_and_the_edit` (each flow's `outputs/001/42.png` and the edit's `42.edit-1.png` exist); `test_each_record_file_is_what_the_writer_derives`, parametrized over `sorted(FILES)`; `test_the_record_directory_holds_the_files_the_writer_names`; and its twin `test_a_stale_record_file_is_caught` over `differing(directory, derived)`, added to `tests/record.py`. Each carries `spec_exempt("structural: …")`, the twin `structural: twin of test_the_record_directory_holds_the_files_the_writer_names`.
  Verify: `uv run pytest tests/test_record.py -k "renders_every_flow or stale_record_file" -q` exits 0.

- [ ] 1.8 Run `uv run python -m tests.record`, which writes `tests/record/graphs.json`, and read it: each graph under `"flows"` holds its flow's nodes, and the `"edit"` graph holds the union ControlNet node.
  Verify: `uv run pytest tests/test_record.py -q` exits 0.

## 2 — The run

- [ ] 2.1 In `tests/record.py`, add `def normalised(value, root)` and `def entry(path, root)` per [D4](design.md#d4): a `duration` is asserted a number and set to `0.0`, a string holding `root.resolve()` is rewritten with `<root>`, then one holding `root`; a `.json` file is `{"json": …}`, a `.png` is `{"pixels": <sha256 of the mode, the size and the decoded bytes>}`, any other file `{"bytes": <sha256>}`.
  Verify: `grep -n -F "def entry(" tests/record.py` prints the definition.

- [ ] 2.2 In `tests/record.py`, add `paths(done)`, mapping each file under the runs root, relative and sorted, to its `entry`, and register it as `FILES["run"]`.
  Verify: `uv run python -c "import tests.record as r; print(sorted(r.FILES))"` prints `['graphs', 'run']`.

- [ ] 2.3 In `tests/test_record.py`, add `test_a_duration_and_the_root_are_normalised`, `test_a_png_is_recorded_by_its_pixels_and_any_other_file_by_its_bytes` (encodings of the same pixels give the same entry, a changed pixel another) and `test_each_recorded_graph_is_the_one_its_render_record_digests`, comparing `graph_digest` of each flow's graph with `graph_sha256` of its `42.render.json`, and the edit's with its record's.
  Verify: `uv run pytest tests/test_record.py -k "normalised or recorded_by or digests" -q` exits 0.

- [ ] 2.4 In `test_each_record_file_is_what_the_writer_derives`, assert before the comparison that the derived text names neither the pass's directory, as given or resolved, nor `Path.home()`.
  Verify: `grep -n -F "Path.home()" tests/test_record.py` prints the assertion.

- [ ] 2.5 In `tests/test_resume.py`, add `test_a_second_pass_over_the_same_runs_moves_nothing`, bound to `cli:resume:second-pass-is-inert`: `offline(tmp_path)`, then `drive` again over the same `Done`, and the render client's submissions and `paths(done)` are as they were.
  Verify: `uv run pytest tests/test_resume.py -k second_pass_over_the_same_runs -q` exits 0.

- [ ] 2.6 Run `uv run python -m tests.record`, which writes `tests/record/run.json`, and read it: every path is relative, every duration is `0.0`, no file names this machine.
  Verify: `uv run pytest tests/test_record.py tests/test_resume.py -q` exits 0.

## 3 — The verbs

- [ ] 3.1 In `tests/record.py`, add `def relative(default)` and `def walk(parser)` per [D5](design.md#d5): `walk` reads `parser._actions`, each subparser's arguments and its mutually exclusive groups into `{dest, flags, nargs, required, default, choices, type, metavar, action}`, no help text; a `Path` default under `REPO_ROOT` is written relative, one outside raises.
  Verify: `grep -n -F "def walk(" tests/record.py` prints the definition.

- [ ] 3.2 In `tests/record.py`, add `flags(done)`, returning `walk(build_parser())` from `isekai/interface/cli.py`, and register it as `FILES["verbs"]`.
  Verify: `uv run python -c "import tests.record as r; print(sorted(r.FILES))"` prints `['graphs', 'run', 'verbs']`.

- [ ] 3.3 In `tests/test_record.py`, add `test_the_walk_reads_each_flag_of_a_parser`, over a parser the test builds, holding a flag, a positional, a choice, a repeatable flag and an exclusive group, and `test_a_default_inside_the_repository_is_recorded_relative_and_one_outside_is_refused`.
  Verify: `uv run pytest tests/test_record.py -k "walk_reads or default_inside" -q` exits 0.

- [ ] 3.4 Run `uv run python -m tests.record`, which writes `tests/record/verbs.json`, and read it: the `--runs` default is `".data/runs"`, and every verb of `VERBS` in `isekai/interface/cli.py` is there.
  Verify: `uv run pytest tests/test_record.py tests/test_pipeline_cli.py -q` exits 0.

## 4 — The routes

- [ ] 4.1 In `tests/record.py`, add `shape(value)` per [D6](design.md#d6), and in `tests/test_record.py` `test_a_shape_names_keys_and_types_and_no_value`, over a mapping, an empty list, a list of mappings and each scalar.
  Verify: `uv run pytest tests/test_record.py -k a_shape_names -q` exits 0.

- [ ] 4.2 In `tests/record.py`, add `Call(method, template, fill, body)`, whose `fill` and `body` take `done` and `seen` per [D7](design.md#d7), `CHILD_ROUTES` as the table there, `served(done)` copying the pass's library under its directory and building `create_app` of `isekai/interface/ui/app.py` over the copy as `_client` of `tests/test_ui_api.py` does, on the wiring of `tests/e2e/wiring.py` and a bundle stand-in, and `answer(client, call)`, returning the status and the `shape` of a JSON answer or the `media_type` of another.
  Verify: `grep -n -F "CHILD_ROUTES" tests/record.py` prints the table.

- [ ] 4.3 In `tests/record.py`, add `CALLS` and a call for every GET route of `create_app` that is not in `CHILD_ROUTES` and not a tattoo's, `Call("GET", "/api/library")` first: the hub, the tags and the fields, the review with its photograph and its source, a render with its image, its thumbnail, its comparisons and its edits, a source with its thumbnail, a collection's render dialog, an unknown `/api/` path and the page.
  Verify: `grep -n -F 'Call("GET", "/api/library"' tests/record.py` prints the call.

- [ ] 4.4 In `CALLS`, add a call for every POST and PUT route of the library's runs not in `CHILD_ROUTES`, each in the state the calls above left: assign, draft, a draft's update, approval, cancel and discard; the placement's proposal; the render's quote; the billing check, `Call("POST", "/api/billing/check")`; and Stop, which refuses with nothing running.
  Verify: `grep -n -F 'Call("POST", "/api/billing/check"' tests/record.py` prints the call.

- [ ] 4.5 In `CALLS`, add the calls that use a staging, `Call("POST", "/api/staging")` first, each consuming a staging of its own: an upload polled until its `GET` answers 200 and its commit; a tattoo's creation, then the tattoo's GET routes, its outline, stage-1 pairs, ink, preview and bake.
  Verify: `grep -n -F 'Call("POST", "/api/staging"' tests/record.py` prints the call.

- [ ] 4.6 In `CALLS`, add a call for every DELETE route last: a render, a tattoo (`Call("DELETE", "/api/tattoos/…")`), and, from a staging of their own and a poll of the file's `GET`, a staged file and the staging.
  Verify: `grep -n -F 'Call("DELETE", "/api/tattoos/' tests/record.py` prints the call.

- [ ] 4.7 In `tests/record.py`, add `answers(done)`, running `CALLS` in order and returning each `"<METHOD> <template>"` with its answer, and register it as `FILES["routes"]`. In `tests/test_record.py`, add `test_every_route_of_the_app_is_recorded_or_left_to_a_child`, over the routes of `app.routes` that answer a method, its twin `test_the_route_check_catches_a_route_no_call_covers` over a small app, and `test_no_route_answers_a_valid_call_with_a_server_error`. **HALT CHECK** A recorded status of 500 or more is a product defect a patch may not fix: edit nothing else and stop.
  Verify: `uv run pytest tests/test_record.py -k "every_route or route_check or server_error" -q` exits 0.

- [ ] 4.8 Run `uv run python -m tests.record`, which writes `tests/record/routes.json`, and read each shape: a key that varies from run to run is a halt, never a normalisation of the product. The file holds `"GET /api/library"`.
  Verify: `uv run pytest tests/test_record.py tests/test_ui_api.py -q` exits 0.

## 5 — The wire

- [ ] 5.1 In `tests/record.py`, add `lines(done)`, returning `{"sheet": <the sheet's done line of the first flow>, "render": <its render's done line>}` read from the stdout `drive` kept, each parsed from its JSON line, and register it as `FILES["wire"]`.
  Verify: `uv run python -c "import tests.record as r; print(sorted(r.FILES))"` prints `['graphs', 'routes', 'run', 'verbs', 'wire']`.

- [ ] 5.2 Run `uv run python -m tests.record`, which writes `tests/record/wire.json`, and read it: the sheet's line names a run, a flow, `"stage": "sheet"` and the state `done`.
  Verify: `grep -n -F '"stage": "sheet"' tests/record/wire.json` prints the line.

- [ ] 5.3 In `tests/test_progress.py`, add `test_the_session_reads_the_lines_the_cli_prints`: `progress_line` of `isekai/interface/render.py` returns each recorded line as the mapping, and `_Images`, over a stand-in for its steps, takes one image from the render's line and none from the sheet's. It carries `spec_exempt("structural: the session reads the lines the CLI prints")`.
  Verify: `uv run pytest tests/test_progress.py -k session_reads -q` exits 0.

- [ ] 5.4 In `tests/test_ui_jobs.py`, add `test_the_cell_and_the_job_read_the_sheet_line_the_cli_prints`: a child prints the recorded sheet line with `run` set to the test's run, over a collection whose run holds a sheet; `cell_event` publishes a `cell` event for `FLOW` in the state `done`, and `complete` of `isekai/interface/ui/jobs.py` counts the `sheet` stage done once. It carries `spec_exempt("structural: the cell and the job read the line the CLI prints")`.
  Verify: `uv run pytest tests/test_ui_jobs.py -k sheet_line_the_cli_prints -q` exits 0.
