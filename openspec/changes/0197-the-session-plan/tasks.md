# The session plan — tasks

Move the plan of a render session from `isekai/interface/render.py` to `isekai/interface/plan.py`, bind each name back, and leave `quote` and `Record` where they are. No moved line changes.

## Progress

- [x] 1 — The estimate and the edit queue · moderate
- [x] 2 — The plan and the quote's parts · moderate
- [x] 3 — The documents · moderate

## 1 — The estimate and the edit queue

- [x] 1.1 Create `isekai/interface/plan.py`: a docstring saying it holds the plan of a render session and never imports `render.py`; the imports of [D1](design.md#d1) that phase 1's code reads, which are `dataclasses`, `json`, `math`, `statistics`, `Collection`, `Mapping`, `Sequence`, `dataclass`, `Path`, `HOLD_SECONDS`, `Refusal`, `REPOSITORY`, `Run`, `render_groups`, `sidecars`, `duration_of`, `pending`, `records` and `duration`; then `RENDER_CONFIG`, `RECENT` and `FLOOR_S` with their comments, copied from `isekai/interface/render.py`.
  Verify: `uv run python -c "from isekai.interface.plan import RENDER_CONFIG, RECENT, FLOOR_S"` exits 0.
- [x] 1.2 Copy these from `isekai/interface/render.py` into `plan.py`, after the constants, in this order and unchanged with their docstrings: `Timing`, `load_timing`, `Estimate`, `recent`, `recent_edits`, `estimate`, `Work` with its comment, `estimated`, `Edits`, `edits_of`, `edit_records`, `pending_edits`.
  Verify: `uv run python -c "from isekai.interface.plan import Timing, Estimate, Edits, Work, load_timing, recent, recent_edits, estimate, estimated, edits_of, edit_records, pending_edits"` exits 0.
- [x] 1.3 In `isekai/interface/render.py` delete the constants and the definitions of 1.1 and 1.2, with `Work`'s comment and the constants' comments, and import them from `isekai.interface.plan` as [D2](design.md#d2) says. Plainly: `FLOOR_S`, `Edits`, `edits_of`, `estimated`, `load_timing`. As `X as X`, one statement each, as `record_running` is, under a comment that they moved to `plan.py` and stay importable here: `RECENT`, `RENDER_CONFIG`, `Timing`, `Estimate`, `recent`, `recent_edits`, `estimate`, `Work`, `edit_records`, `pending_edits`. Write the `HOLD_SECONDS` import as `HOLD_SECONDS as HOLD_SECONDS` ([D4](design.md#d4)).
  Verify: `uv run python -c "from isekai.interface.render import FLOOR_S, RECENT, RENDER_CONFIG, HOLD_SECONDS, Timing, Estimate, Edits, Work, load_timing, recent, recent_edits, estimate, estimated, edits_of, edit_records, pending_edits; assert Timing.__module__ == edits_of.__module__ == 'isekai.interface.plan'"` exits 0.
- [x] 1.4 Run `uv run ruff check --fix isekai/interface/render.py isekai/interface/plan.py` and `uv run ruff format isekai/interface/render.py isekai/interface/plan.py`: they drop each import `render.py` no longer reads and sort both files' imports. `plan.py` imports nothing of `render.py`.
  Verify: `uv run ruff check isekai/interface/render.py isekai/interface/plan.py` exits 0.
- [x] 1.5 In `tests/mutants.json` set `RE-1`'s `path` to `isekai/interface/plan.py`. Its `find` is unchanged and occurs once there.
  Verify: `git grep -n -F "isekai/interface/plan.py" -- tests/mutants.json` prints one line.
- [x] 1.6 Run `uv run python -m tools.derive_imported_by`: `plan.py` now imports the pod start, the edit and the generate stage, so the layer READMEs' derived tables change, and `tests/test_docs.py` holds each to the import graph.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 1.7 Confirm the suite still reads each moved name through `render`.
  Verify: `uv run pytest tests/test_render.py tests/test_edit_session.py tests/test_ui_api.py tests/test_ratchets.py` exits 0.

## 2 — The plan and the quote's parts

- [x] 2.1 Append to `plan.py`, in this order and unchanged with their docstrings and comments: `Line`, `NOTHING_SHORT` with its comment, `Short`, `_plan`, `_images`, `short`, `_unready`, `Quote`. Add the imports they read: `SessionPlan` from `isekai.foundation.artifacts`; `Flow`, `load_flow` and `tracked_flows` from `isekai.foundation.flow`; `REVIEW`, `SHEETS`, `approved_versions`, `current_draft` and `latest_artifact` to the `isekai.foundation.run` import; `Wiring` from `isekai.interface.wiring`; `shortfall` to the `isekai.pipeline.generate` import.
  Verify: `uv run python -c "from isekai.interface.plan import Line, NOTHING_SHORT, Short, _plan, _images, short, _unready, Quote"` exits 0.
- [x] 2.2 In `isekai/interface/render.py` delete those definitions and their comments. `quote` stays, between where `Quote` and `edit_records` were.
  Verify: `git grep -n -e "^class Line" -e "^NOTHING_SHORT" -e "^class Short" -e "^def _plan(" -e "^def _images(" -e "^def short(" -e "^def _unready(" -e "^class Quote" -- isekai/interface/render.py` prints nothing.
- [x] 2.3 Add them to the import from `isekai.interface.plan` in `isekai/interface/render.py`. Plainly: `Line`, `Quote`, `_images`, `_plan`, `short`. As `X as X`, one statement each, under the same comment: `NOTHING_SHORT`, `Short`, `_unready`.
  Verify: `uv run python -c "from isekai.interface.render import Line, Quote, Short, NOTHING_SHORT, short, _plan, _images, _unready; assert Quote.__module__ == short.__module__ == 'isekai.interface.plan'"` exits 0.
- [x] 2.4 Run `uv run ruff check --fix isekai/interface/render.py isekai/interface/plan.py` and `uv run ruff format isekai/interface/render.py isekai/interface/plan.py`, then `uv run python -m tools.derive_imported_by`, which writes the derived tables again: `render.py` no longer imports the edit and generate stages.
  Verify: `uv run ruff check isekai/interface/render.py isekai/interface/plan.py` exits 0.
- [x] 2.5 `quote` and `Record` stay in `render.py` and take no new parameter, so a patch of `load_timing` or `session_id` on `render` still reaches them ([D3](design.md#d3)).
  Verify: `git grep -n -e "^def quote(" -e "^class Record:" -- isekai/interface/render.py` prints two lines.
- [x] 2.6 `quote` and `_session` call `load_timing()` as a name of `render.py`.
  Verify: `git grep -c -F "load_timing()" -- isekai/interface/render.py` prints `isekai/interface/render.py:2`.
- [x] 2.7 `isekai/interface/plan.py` names nothing of `isekai.interface.render`, which would close a cycle.
  Verify: `git grep -n -F "isekai.interface.render" -- isekai/interface/plan.py` prints nothing.
- [x] 2.8 **HALT CHECK** `render.py` is still over the long-file ceiling, so its row of `tests/test_ratchets.py` stands. A failure means the move took more than the plan names.
  Verify: `uv run pytest tests/test_ratchets.py tests/test_layers.py tests/test_docs.py` exits 0.
- [x] 2.9 Confirm the suite still reads each moved name through `render`.
  Verify: `uv run pytest tests/test_render.py tests/test_edit_session.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_pipeline_cli.py` exits 0.

## 3 — The documents

- [x] 3.1 In `isekai/interface/README.md` add a `plan.py` row directly after `render.py`, before any `progress.py` row, in `## Files`: the plan of a render session — its timing, its estimate, what each approval lacks, the edit queue's reading and the quote's data — read by `render.py`, and importing nothing of it. In the `render.py` row change "finds what each approval lacks, less each `--without`, or takes the requests, assembles every prompt, estimates the session's limit and its quote," to "takes the requests or what `plan.py` finds each approval lacks, less each `--without`, assembles every prompt, quotes the session and sets its limit,".
  Verify: `git grep -c -e "^| .plan.py. |" -- isekai/interface/README.md` prints `isekai/interface/README.md:1`.
- [x] 3.2 In the same README add a `plan.py` row directly after `render.py`, before any `progress.py` row, in `## Imported by`, `—` in its other cells, then run `uv run python -m tools.derive_imported_by`, which fills it.
  Verify: `git grep -c -e "^| .plan.py. |" -- isekai/interface/README.md` prints `isekai/interface/README.md:2`.
- [x] 3.3 In `isekai/README.md` add `plan.py` directly after `render.py`, before any `progress.py`, in the `interface/` row.
  Verify: `git grep -c -F "plan.py" -- isekai/README.md` prints `isekai/README.md:1`.
- [x] 3.4 In `docs/principles.md` change "`interface/render.py`'s `short` decides what each approval lacks of its count, and its `quote` reaches `estimate` to price the session;" to "`interface/plan.py`'s `short` decides what each approval lacks of its count and its `estimate` prices a session, which `interface/render.py`'s `quote` reaches;", keeping the file's wrap.
  Verify: `git grep -c -F "interface/plan.py" -- docs/principles.md` prints `docs/principles.md:1`.
- [x] 3.5 In `isekai/boundary/README.md` change the note's "`interface/render.py` imports `pod_start.py` for the hold its limit's floor is above;" to "`interface/plan.py` imports `pod_start.py` for the hold its limit's floor is above, and `interface/render.py` binds it again;", keeping the wrap.
  Verify: `git grep -c -e "^> .interface/plan.py. imports" -- isekai/boundary/README.md` prints `isekai/boundary/README.md:1`.
- [x] 3.6 Run the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
