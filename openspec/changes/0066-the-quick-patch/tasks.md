# The quick patch — tasks

Build the [design](design.md) against the [UI delta](specs/ui/spec.md); keep the backlog and frozen archives unchanged.
Each phase is independently buildable. The tests and their retained assertions are named in [Tests](design.md#tests).

## Progress

- [ ] 1 — Prose
- [ ] 2 — Layout
- [ ] 3 — Progress
- [ ] 4 — Shutdown

## 1 — Prose

- [ ] 1.1 **HALT CHECK** Confirm the installed server seam required by [D4](design.md#d4).
  Verify: `uv run python -c 'import uvicorn; assert callable(uvicorn.Server.handle_exit); assert callable(uvicorn.Server.run)'` exits 0.
- [ ] 1.2 Correct the child-process descriptions in `isekai/interface/ui/__init__.py` and the Known breaks in `docs/principles.md`, per [D6](design.md#d6).
  Verify: the docstring names Prepare and Render; the Known breaks name `short`, `quote`, `run_ids` and reserve the rendered-seed reason for `paired` and `_revision`.
- [ ] 1.3 Clarify [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) in `docs/decisions.md` with [D2](design.md#d2)'s confirmation boundary.
  Verify: `rg -n -F 'The quote compares image total and limit, not source or approval identity.' docs/decisions.md` finds that sentence in D4.

## 2 — Layout

- [ ] 2.1 Add `ui/src/words.ts` and `ui/src/words.test.ts` for [D7](design.md#d7)'s `noun` helper, including the explicit `batches` plural.
  Verify: `npm --prefix ui test -- src/words.test.ts` passes the count-label scenario for zero, one and plural counts.
- [ ] 2.2 Use `noun` in `ui/src/views/Home.vue`, `Hub.vue` and `ui/src/components/AppHeader.vue`, `ImportSheet.vue`, `RenderDialog.vue`, `SheetHeader.vue`.
  Verify: their count expressions use `noun` for batch, source, flow, input, file, image and field labels; `batch` supplies `batches` explicitly.
- [ ] 2.3 Set the header gap and remove the redundant Add sources margin in `ui/src/app.css`; extend the tick/reload test in `tests/e2e/test_prepare.py`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/e2e/test_prepare.py::test_a_tick_assigns_the_flow_and_survives_a_reload` passes its added computed-gap assertion and retained assertions.
- [ ] 2.4 State the singular-count rule and the hub header's 12 px gap in `ui/design/spec.md`.
  Verify: the design names both rules while its disabled-reason rule and navigation remain unchanged.

## 3 — Progress

- [ ] 3.1 Add [D3](design.md#d3)'s accepted-cell progress to `isekai/interface/ui/jobs.py`; add `test_prepare_totals_count_cells_once` and extend the stopped-slot equality in `tests/test_ui_jobs.py`.
  Verify: `uv run pytest -q tests/test_ui_jobs.py::test_prepare_totals_count_cells_once tests/test_ui_jobs.py::test_stop_interrupts_the_stage_and_starts_no_later_one` passes.
- [ ] 3.2 Preserve progress in the snapshot assembled by `isekai/interface/ui/app.py`; add `test_reconnect_keeps_prepare_progress` in `tests/test_ui_jobs.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_ui_jobs.py::test_reconnect_keeps_prepare_progress` proves the original start time and fixed total survive reconnect after completion advances.
- [ ] 3.3 Extend `ui/src/types.ts` and `ui/src/composables/useLive.ts`; draw the shared Prepare formatter in `ui/src/App.vue` and `ui/src/views/Hub.vue`, per [D3](design.md#d3).
  Verify: both views read the shared formatter and clock; neither uses nullable stage/flow fields as Prepare totals.
- [ ] 3.4 Add the bounded reader/release-file fixture to `tests/e2e/wiring.py` and `tests/e2e/conftest.py`; extend the running Prepare test in `tests/e2e/test_prepare.py`, per [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/e2e/test_prepare.py::test_prepare_takes_the_assigned_cells_to_their_sheet_and_no_other` passes totals, ticking-time, reload and retained cell assertions.
- [ ] 3.5 Make `ui/design/spec.md`'s JobStrip and running PrepareBar use [D3](design.md#d3)'s cell totals and elapsed time consistently.
  Verify: both descriptions state the fixed accepted-cell total and sheet-completed count; the additional motion remains undeclared by this patch.

## 4 — Shutdown

- [ ] 4.1 Add [D4](design.md#d4)'s stop state and signal hook in `isekai/interface/ui/events.py` and `app.py`; add `test_closed_broadcast_ends_existing_and_late_streams` in `tests/test_ui.py`.
  Verify: `uv run pytest -q tests/test_ui.py::test_closed_broadcast_ends_existing_and_late_streams` proves prompt wake-up and late-subscription termination; the signal hook delegates to uvicorn.
- [ ] 4.2 Handle the surviving interrupt in `isekai/interface/ui/__init__.py`; add `test_sigint_ends_streams_without_cancellation_output` and `test_serve_returns_130_for_keyboard_interrupt` to `tests/test_ui.py`, per [D4](design.md#d4) and [Tests](design.md#tests).
  Verify: `uv run pytest -q tests/test_ui.py::test_sigint_ends_streams_without_cancellation_output tests/test_ui.py::test_serve_returns_130_for_keyboard_interrupt` passes with quiet status 130.
- [ ] 4.3 Base terminal recovery on close state in `isekai/interface/ui/jobs.py`; add failed-close/kept-window tests and extend successful-stop/timeout assertions in `tests/test_ui_jobs.py`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_ui_jobs.py::test_failed_close_at_stop_names_the_fix tests/test_ui_jobs.py::test_kept_window_at_stop_needs_no_remedy tests/test_ui_jobs.py::test_a_surface_stopped_mid_render_closes_the_window_after_the_teardown tests/test_ui_jobs.py::test_a_stop_whose_wait_runs_out_names_the_command_that_closes_the_window` passes.
