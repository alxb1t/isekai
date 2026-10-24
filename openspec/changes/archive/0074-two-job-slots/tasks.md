# Tasks — 0074 two job slots

The job runner, the wire, the screens, then the docs, per [design](design.md). Every new pytest test carries
`@pytest.mark.spec`, and every new vitest test `spec("…")`, with the key its task names.

## Progress

- [x] 1 — The job runner
- [x] 2 — The wire
- [x] 3 — The screens
- [x] 4 — The docs

## 1 — The job runner

- [x] 1.1 **HALT CHECK** — `Jobs` holds one slot.
  Verify: `grep -c '_slots' isekai/interface/ui/jobs.py` prints `0`.
- [x] 1.2 Give `Jobs` a slot per kind, refusals, Stop and wait per kind, and a shutdown of both, in
  `isekai/interface/ui/jobs.py`, per [D1](design.md#d1) and [D2](design.md#d2); its callers in `isekai/interface/ui/app.py` name a kind.
  Verify: `grep -c '_slots' isekai/interface/ui/jobs.py` prints a number of at least `1`, and `uv run pytest -q tests/test_ui_jobs.py tests/test_ui.py` exits 0.
- [x] 1.3 Prefix each log line with its job per [D3](design.md#d3); bind `ui:prepare:a-render-runs-beside-a-prepare`,
  `ui:prepare:stopping-the-surface-interrupts-both` and `ui:prepare:the-log-names-each-job`, and recast `ui:prepare:one-job-at-a-time` to one kind, in `tests/test_ui_jobs.py`.
  Verify: `grep -c -E 'ui:prepare:(a-render-runs-beside|stopping-the-surface-interrupts-both|the-log-names-each-job)' tests/test_ui_jobs.py` prints `3`, and `uv run pytest -q tests/test_ui_jobs.py` exits 0.

## 2 — The wire

- [x] 2.1 **HALT CHECK** — Stop is one route.
  Verify: `grep -c '"/api/job/stop"' isekai/interface/ui/app.py` prints `1`.
- [x] 2.2 Carry `jobs` in the snapshot, `kind` on the `job` event, Render's hold per kind and `POST /api/jobs/{kind}/stop`
  in `isekai/interface/ui/app.py` per [D4](design.md#d4); the snapshot test of `ui:events:a-connection-starts-with-a-snapshot` reads both slots.
  Verify: `grep -c '"/api/job/stop"' isekai/interface/ui/app.py` prints `0`, and `uv run pytest -q tests/test_ui_jobs.py tests/test_ui_api.py` exits 0.

## 3 — The screens

- [x] 3.1 **HALT CHECK** — the hub holds Prepare back while a render runs.
  Verify: `grep -c 'A render is running' ui/src/views/Hub.vue` prints `1`.
- [x] 3.2 Hold `jobs.prepare` and `jobs.render` in `ui/src/stores/live.ts`, with `ui/src/api.ts` and `ui/src/types.ts`;
  bind `ui:events:a-job-event-fills-its-kinds-slot` in `ui/src/stores/live.test.ts`, per [D5](design.md#d5).
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'a-job-event-fills-its-kinds-slot' ui/src/stores/live.test.ts` prints `1`.
- [x] 3.3 Move `ui/src/App.vue`, `ui/src/stores/batch.ts`, `ui/src/views/Hub.vue`, `ui/src/views/SessionPage.vue`,
  `ui/src/views/Billing.vue`, `ui/src/components/RenderBar.vue` and `ui/src/components/RenderDialog.vue` to their own slots per [D5](design.md#d5).
  Verify: `grep -c 'A render is running\|blocked' ui/src/views/Hub.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 3.4 Add the step of the design's [Tests](design.md#tests) to `test_prepare_takes_the_assigned_cells_to_their_sheet_and_no_other`
  in `tests/e2e/test_prepare.py`.
  Verify: `grep -c 'data-render' tests/e2e/test_prepare.py` prints a number of at least `1`, and `uv run pytest -q tests/e2e` exits 0.

## 4 — The docs

- [x] 4.1 **HALT CHECK** — the design spec states one job slot.
  Verify: `grep -c 'One job slot' ui/design/spec.md` prints `1`.
- [x] 4.2 Rewrite rule 6 and §8 of `ui/design/spec.md`, the job runner's line in `isekai/interface/ui/README.md`, and
  `0073·R9`'s comments in `ui/src/sessions.ts` and its `render.py` row in `isekai/interface/README.md`, per [D6](design.md#d6).
  Verify: `grep -c 'One job slot' ui/design/spec.md` prints `0`, `grep 'render\.py. | .cli\.py' isekai/interface/README.md | grep -c 'ui/library.py'` prints `1`, and `uv run pytest -q tests/test_docs.py` exits 0.
