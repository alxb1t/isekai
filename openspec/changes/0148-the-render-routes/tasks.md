# The render routes — tasks

The phases: the render and jobs routes, the events stream, the documents. Each moves text and edits none; [design](design.md) says where each name goes.

## Progress

- [x] 1 — The render and jobs routes · moderate
- [x] 2 — The events stream · moderate
- [x] 3 — The documents · moderate

## 1 — The render and jobs routes

- [x] 1.1 **HALT CHECK** No test patches a name the moved code reads: the plan holds `Jobs` and `run` in `app.py` alone ([D5](design.md#d5)).
  Verify: `git grep -n -E 'setattr\((app_module|app), "(plan|keyed|KINDS|render|library|load_flow|tracked_flows|edit_at|approved_versions|edit_image_of|events|cell_event|_quote|_quoted_row|_taken_out|_hub|_cell_out|_strings|_whole)"' -- tests` prints nothing.
- [x] 1.2 Open with the pre-flight over the lines this phase moves, in `app.py`: the routes and closures from `post_prepare` to `post_check`, `cell_event`, `_whole`, `_quote` to `_taken_out`, `_hub`, `_cell_out` and `_strings` ([D7](design.md#d7)). A survivor is killed by a test or named in [Equivalent mutants](design.md#equivalent-mutants). The ranges are the lines of the cut's base, run once with `uv run python -m tools.mutate isekai/interface/ui/app.py:437-636 isekai/interface/ui/app.py:1158-1192 isekai/interface/ui/app.py:1335-1337 isekai/interface/ui/app.py:1340-1471 isekai/interface/ui/app.py:1496-1525 isekai/interface/ui/app.py:1609-1611 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_record.py` before the move; once the move has shifted `app.py` they hold other lines, and 1.10 runs the same mutants on their new homes.
  Verify: `grep -n -F '## Equivalent mutants' openspec/changes/0148-the-render-routes/design.md` prints a line.
- [x] 1.3 Move `_strings`, `_whole`, `_hub` and `_cell_out` from `app.py` into `routes/common.py`, text and docstrings unchanged, with the imports they need. `app.py` imports the four back from `isekai.interface.ui.routes.common` beside `_dimensions` ([D4](design.md#d4)).
  Verify: `git grep -n -E '^def (_strings|_whole|_hub|_cell_out)\(' -- isekai/interface/ui/routes/common.py` prints a line for each of the four names.
- [x] 1.4 Write `isekai/interface/ui/routes/rendering.py` with its docstring and `class RenderRoutes`: `__init__(surface)` and the handlers and helpers of [D1](design.md#d1), each moved from `create_app` with its docstring, its signature and its body unchanged but for [D3](design.md#d3)'s prefix, and the imports its bodies read.
  Verify: `grep -n -E '^    def (post_prepare|post_stop|quoted|_held|short_of|bakes_in|read_render_offer|post_quote|post_render|running_sessions|read_session|post_check)\(' isekai/interface/ui/routes/rendering.py` prints a line for each name of [D1](design.md#d1).
- [x] 1.5 Move `cell_event`, `_quote`, `_quoted_row` and `_taken_out` from `app.py` into `routes/rendering.py`, text and docstrings unchanged, and import into it from `routes/common.py` the helpers they read.
  Verify: `grep -n -E '^def (cell_event|_quote|_quoted_row|_taken_out)\(' isekai/interface/ui/routes/rendering.py` prints a line for each of the four names.
- [x] 1.6 End `routes/rendering.py` with `ROUTES`, a table of `Route` rows in the order [D1](design.md#d1) draws, and `mount(app, surface)`, as `routes/vocabulary.py` ends.
  Verify: `grep -n -E '^(ROUTES = |def mount\()' isekai/interface/ui/routes/rendering.py` prints a line for each of the two names.
- [x] 1.7 In `app.py` delete the moved routes, closures and module functions; bind `cell_event` and `mount as render_mount` from `routes.rendering`; call `render_mount(app, surface)` after `place_mount(app, surface)`, before `no_route`; drop each import the move leaves unused, as `ruff check` names them.
  Verify: `git grep -n -E '^    def (post_prepare|post_stop|quoted|_held|short_of|bakes_in|read_render_offer|post_quote|post_render|running_sessions|read_session|post_check)\(' -- isekai/interface/ui/app.py` prints nothing.
- [x] 1.8 Run the server's tests, the record, the ratchets and the layer guards: no assertion changes, and `Jobs(` still sits in `create_app`.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_pipeline_cli.py` passes.
- [x] 1.9 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [x] 1.10 Close with the same run on the new homes. `tools.mutate` copies tracked files only, so run `git add -N isekai/interface/ui/routes/rendering.py` first.
  The run is split by range, since one command over both modules outlasts the plan check's 600 seconds. `cell_event`'s two branch checks (`rendering.py` lines 250 and 253) time out before and after the move, each waiting out the 300-second default, so no range holds both: 211-249, 250-252 and 253-280 replace the one range 211-280. Each run leaves out `test_without_the_lock_an_update_writes_after_the_approval`, a race on `app.py`'s draft lock that fails the unmutated baseline when the plan check runs the nine side by side ([D7](design.md#d7)).
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:1-70 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:71-140 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:141-210 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:211-249 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:250-252 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:253-280 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:281-350 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`, `uv run python -m tools.mutate isekai/interface/ui/routes/rendering.py:351-421 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` and `uv run python -m tools.mutate isekai/interface/ui/routes/common.py:1-68 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_record.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` each exit 0, each survivor they print named in the design.

## 2 — The events stream

- [x] 2.1 Open with the tests' baseline: phase 1 has shifted `app.py`, so no range of it holds, and the closing run covers the same mutants ([D7](design.md#d7)).
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_record.py` passes.
- [x] 2.2 Write the new `isekai/interface/ui/routes/stream.py`: `class StreamRoutes` with `read_events`, moved from `create_app` with its docstring, comments and body unchanged but for [D3](design.md#d3)'s prefix, and the imports its body reads; a `ROUTES` table of its one `GET /events` row; `mount(app, surface)`.
  Verify: `grep -n -E '^(class StreamRoutes|ROUTES = |def mount\()|    def read_events\(' isekai/interface/ui/routes/stream.py` prints a line for each of the four names.
- [x] 2.3 In `app.py` delete `def read_events(` and its body; bind `mount as stream_mount` from `routes.stream`; call `stream_mount(app, surface)` after `render_mount(app, surface)`; drop each import the move leaves unused, as `ruff check` names them.
  Verify: `git grep -n -F 'def read_events(' -- isekai/interface/ui/app.py` prints nothing.
- [x] 2.4 Run the server's tests, the record, the ratchets and the layer guards.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_pipeline_cli.py` passes.
- [x] 2.5 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [x] 2.6 Close with `tools.mutate` on the new module, after `git add -N isekai/interface/ui/routes/stream.py`.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/stream.py:1-2000 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui_wire.py tests/test_ui_library.py tests/test_record.py` exits 0, each survivor it prints named in the design.

## 3 — The documents

- [x] 3.1 In `docs/decisions.md`, D59's *Accepts* line drops "the render, jobs and events routes and" and reads: "the routes that read a name a test patches stay closures of `create_app`, with `Jobs(` and `run` kept there, and so do the library, staging, review and images routes, until their versions. Reopen when the last of them moves." Its *Made by* line reads `0147`, `0148`.
  Verify: `git grep -n -F 'the render, jobs and events routes' -- docs/decisions.md` prints nothing.
- [x] 3.2 In the docstring of `isekai/interface/ui/app.py`, after the sentence saying the modules of `routes/` are reached through this module alone, add: "They hold the vocabulary, tattoo library and place routes, `RenderRoutes` and `StreamRoutes`; `create_app` declares the routes that read a name a test patches, and the rest."
  Verify: `git grep -n -F 'StreamRoutes' -- isekai/interface/ui/app.py` prints a line.
- [x] 3.3 In `isekai/interface/README.md`, the `ui/routes/` row reads "the vocabulary, tattoo library, place, render and jobs, and events routes" where it read "the vocabulary, tattoo library and place routes".
  Verify: `git grep -n -F 'render and jobs, and events routes' -- isekai/interface/README.md` prints a line.
- [x] 3.4 In `docs/modules.md`, the sentence ending "`interface/ui/events.py` streams what they report to the page as `/events`" ends instead "… as `/events`; `RenderRoutes` of `interface/ui/routes/rendering.py` starts the jobs and `StreamRoutes` of `interface/ui/routes/stream.py` serves the stream."
  Verify: `git grep -n -F 'StreamRoutes' -- docs/modules.md` prints a line.
- [x] 3.5 **HALT CHECK** UA-7's anchor stays in `app.py`: no phase edits the artifacts import block it names.
  Verify: `git grep -n -F '    renders_of,' -- isekai/interface/ui/app.py` prints a line.
- [x] 3.6 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`, then replay the recorded mutants.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
- [x] 3.7 Hold the series' conditions: nothing under `tests/record/`, no ratchet row and no entry of `tests/mutants.json` differs from the cut's base.
  Verify: `git diff --exit-code 7cf59b7d -- tests/record tests/test_ratchets.py tests/mutants.json` exits 0.
- [x] 3.8 Run the documents' and the guards' tests.
  Verify: `uv run pytest tests/test_docs.py tests/test_ratchets.py tests/test_layers.py tests/test_record.py` passes.
