# Tasks — 0063 render

The count and seeds, what is short, the limit, progress, the job and billing, the UI, the Renders view, the docs,
then one metered proof, per [design](design.md). Every new pytest test carries `@pytest.mark.spec` with the key its
task names.

## Progress

- [x] 1 — The count and seeds
- [x] 2 — What is short
- [x] 3 — The limit
- [x] 4 — Progress
- [x] 5 — The job and billing
- [ ] 6 — The render UI
- [ ] 7 — The Renders view
- [ ] 8 — The docs
- [ ] 9 — ⚠️ **HUMAN · METERED** — two images rendered from the UI

## 1 — The count and seeds

- [x] 1.1 **HALT CHECK** — the draft has no `renders` field, and `gpunit.toml`'s ceiling is `45m`.
  Verify: `grep -c 'renders' isekai/foundation/artifacts.py` prints `0`, and `grep -c '^ceiling = "45m"' gpunit.toml` prints `1`.
- [x] 1.2 Add `renders` to `ReviewDraft` and `ReviewApproved` in `isekai/foundation/artifacts.py`, carry it through `isekai/pipeline/review.py`, and refuse approval as [D1](design.md#d1) says; bind every `review:renders:*` key in `tests/test_review.py`.
  Verify: `uv run pytest -q tests/test_review.py` exits 0, and `grep -c 'review:renders:' tests/test_review.py` prints `3`.
- [x] 1.3 Make `render` in `isekai/pipeline/generate.py` take the approval's seeds first and draw the rest of its count, per [D1](design.md#d1); bind every `image-generation:approved-count:*` key in `tests/test_generate.py`.
  Verify: `uv run pytest -q tests/test_generate.py` exits 0, and `grep -c 'image-generation:approved-count:' tests/test_generate.py` prints `3`.
- [x] 1.4 Add the ④ Renders block — the count stepper and the seeds list — to `ui/src/views/Review.vue`, writing through the draft `PUT`, per the design spec's J3·2.
  Verify: `grep -c 'renders' ui/src/views/Review.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.

## 2 — What is short

- [x] 2.1 Make `render <runs>` with no request render what is short, skip a run without the flow, and leave out an unapproved flow, in `isekai/interface/render.py` and `isekai/interface/cli.py`, per [D2](design.md#d2); bind every `cli:render-short:*` key in `tests/test_render.py`.
  Verify: `uv run pytest -q tests/test_render.py` exits 0, and `grep -c 'cli:render-short:' tests/test_render.py` prints `3`.

## 3 — The limit

- [x] 3.1 Add `config/render.json` per [D3](design.md#d3), and `duration` to the render record in `isekai/foundation/artifacts.py` and `isekai/pipeline/generate.py`; bind `image-generation:duration:a-render-carries-its-duration` in `tests/test_generate.py`.
  Verify: `grep -c '"limit_factor": 1.5' config/render.json` prints `1`, and `grep -c 'image-generation:duration:' tests/test_generate.py` prints `1`.
- [x] 3.2 Add `--limit` and the estimate to `isekai/interface/render.py`, remove `CEILING_S`, and pass the limit to `gpu.open_session` as the `Spec`'s `ceiling_s` in `isekai/boundary/gpu.py`, and print `session limit <seconds>s` on stderr as it opens, per [D3](design.md#d3); rewrite `tests/test_render.py:604`'s assertion to the limit; bind every `cli:render-limit:*` key in `tests/test_render.py`.
  Verify: `grep -c 'CEILING_S' isekai/interface/render.py` prints `0`, `grep -c 'cli:render-limit:' tests/test_render.py` prints `4`, and `uv run pytest -q tests/test_render.py` exits 0.
- [x] 3.3 Set `ceiling = "3h"` and `max_hourly = 0.90` in `gpunit.toml`, `SESSION_CEILING_SECONDS = 3 * 60 * 60` in `tests/conftest.py`, and bind `pod-image:stop:a-sessions-ceiling-is-its-limit` and `pod-image:stop:the-window-outlasts-the-longest-session` in `tests/test_infra.py`, per [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `grep -c -E '^ceiling = "3h"$|^max_hourly = 0.90$' gpunit.toml` prints `2`, and `uv run pytest -q tests/test_infra.py tests/test_pod_start.py` exits 0.

## 4 — Progress

- [x] 4.1 Add `--progress json` to `render` per [D5](design.md#d5), and bind `cli:render-progress:each-image-of-the-total` in `tests/test_render.py`.
  Verify: `uv run python -m isekai render --help` prints `--progress`, and `grep -c 'cli:render-progress:' tests/test_render.py` prints `1`.

## 5 — The job and billing

- [x] 5.1 Add `session` and `volume` to `Wiring` in `isekai/interface/wiring.py` with real defaults, and doubles in `tests/e2e/wiring.py`, per [D6](design.md#d6).
  Verify: `grep -c 'volume=' tests/e2e/wiring.py` prints a number of at least `1`, and `uv run pytest -q tests/test_pipeline_cli.py` exits 0.
- [x] 5.2 Add `isekai/interface/ui/billing.py` per [D7](design.md#d7), and `Jobs.render` in `isekai/interface/ui/jobs.py` with the quote, render and check routes in `isekai/interface/ui/app.py`, per [D8](design.md#d8).
  Verify: `uv run python -c "import isekai.interface.ui.billing"` exits 0, and `grep -c '/render/quote' isekai/interface/ui/app.py` prints `1`.
- [x] 5.3 Add `tests/test_ui_billing.py` binding every `ui:billing:*` key, and in `tests/test_ui_jobs.py` bind every `ui:render-job:*` key, `ui:render:the-dialog-lists-what-renders` and `ui:render:without-a-key-render-is-disabled`.
  Verify: `uv run pytest -q tests/test_ui_billing.py tests/test_ui_jobs.py` exits 0, and `grep -c 'ui:billing:' tests/test_ui_billing.py` prints `3`.

## 6 — The render UI

- [ ] 6.1 Add the Render dialog to `ui/src/views/Hub.vue`, `ui/src/views/Session.vue` at `/session`, and the alert band and quiet volume item to `ui/src/App.vue`, per the design spec's J4, J8b and J8c.
  Verify: `grep -c "'/session'" ui/src/router.ts` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 6.2 Add `tests/e2e/test_render.py` binding `ui:render:the-confirmation-starts-the-render`.
  Verify: `uv run pytest -q tests/e2e/test_render.py` exits 0.

## 7 — The Renders view

- [ ] 7.1 Add the renders and thumbnail routes to `isekai/interface/ui/app.py`, the cache under `.cache/` in `isekai/interface/ui/library.py`, and `ui/src/views/Renders.vue` with `ui/src/views/RenderLarge.vue`, per [D9](design.md#d9).
  Verify: `grep -c '/renders' isekai/interface/ui/app.py` prints a number of at least `2`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 7.2 Bind `ui:renders:versions-newest-first` and `ui:renders:a-thumbnail-is-made-once` in `tests/test_ui_api.py`, and extend `tests/e2e/test_render.py` with a step binding `ui:renders:the-large-view-shows-its-sheet`.
  Verify: `uv run pytest -q tests/test_ui_api.py tests/e2e/test_render.py` exits 0, and `grep -c 'ui:renders:' tests/test_ui_api.py` prints `2`.

## 8 — The docs

- [ ] 8.1 Rewrite the cost rule in `CLAUDE.md` and D26 and D36 in `docs/decisions.md`, per [D10](design.md#d10); describe the render from the UI in `README.md` and `docs/data-flow.md`.
  Verify: `grep -c '45 minutes and ~\$0.30' CLAUDE.md` prints `0`, `grep -c 'max_hourly' CLAUDE.md docs/decisions.md` prints a number of at least `1` for each file, and `uv run pytest -q tests/test_docs.py tests/test_spec_prose.py` exits 0.

## 9 — ⚠️ HUMAN · METERED — two images rendered from the UI

- [ ] 9.1 Start the surface: `uv run --env-file .env python -m isekai ui`, open `http://127.0.0.1:8517/`, and in a batch from `ls ~/isekai` approve two sheets with count 1.
  Verify: `ls ~/isekai/<the batch>/runs/*/*/review/*.approved.json` lists at least two files.
- [ ] 9.2 Press Render on that batch's hub; read the quote; confirm only on the operator's go.
  Verify: `grep -c 'session limit' ~/isekai/<the batch>/log.txt` prints a number of at least `1`, and the session view ends on *Nothing is billing.*
- [ ] 9.3 Confirm both images and their durations on disk, and that nothing is left on RunPod.
  Verify: `grep -l '"duration"' ~/isekai/<the batch>/runs/*/*/outputs/*/*.render.json` lists two files, and the RunPod MCP's `list-pods` and `list-network-volumes` show no `gpunit-isekai` pod and no `gpunit-isekai` volume.
