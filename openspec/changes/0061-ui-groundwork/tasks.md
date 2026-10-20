# Tasks — 0061 ui groundwork

The harness, the defects, the library, the shell, the hub, the queue, then the docs and the deletions, per
[design](design.md). Every new pytest test carries `@pytest.mark.spec` and every vitest test `spec("<key>", …)`, with
the key its task names.

## Progress

- [x] 1 — The harness
- [x] 2 — The defects
- [ ] 3 — The library
- [ ] 4 — The shell
- [ ] 5 — The hub
- [ ] 6 — The queue
- [ ] 7 — The docs and the deletions

## 1 — The harness

- [x] 1.1 **HALT CHECK** — `ui` still takes `--flow` exactly once, and no JS test runner is declared.
  Verify: `grep -c 'action=_OneFlow' isekai/interface/cli.py` prints `1`, and `grep -c -E 'vitest|playwright' ui/package.json` prints `0`.
- [x] 1.2 Add the dev dependencies of [Dependencies](design.md#dependencies): `uv add --dev pytest-playwright==0.10.0`, then in `ui/` `npm install --save-exact --save-dev vitest@5.0.5`.
  Verify: `grep -c 'pytest-playwright==0.10.0' pyproject.toml` prints `1`, and `grep -c '"vitest": "5.0.5"' ui/package.json` prints `1`.
- [x] 1.3 Add a `browsers` target to `Makefile` running `uv run playwright install chromium`, and a CI step running `make browsers` before `Gate` in `.github/workflows/ci.yml`, per [D7](design.md#d7).
  Verify: `make -n browsers` prints `uv run playwright install chromium`, and `grep -c 'make browsers' .github/workflows/ci.yml` prints `1`.
- [x] 1.4 **HALT CHECK** — Chromium launches headless here, after `make browsers`.
  Verify: `uv run python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print(b.version); b.close(); p.stop()"` prints a version.
- [x] 1.5 Add `ui/vitest.config.ts`, the `test` script in `ui/package.json`, `ui/src/test/spec.ts` and `tools/test_ui.py`, which runs `npm run test` and refuses by name without `ui/node_modules/`; add `uv run python -m tools.test_ui` to `gate` after `tools.typecheck_ui`, per [D7](design.md#d7).
  Verify: `make -n gate` prints `uv run python -m tools.test_ui`, and `uv run python -m tools.test_ui` exits 0.
- [x] 1.6 Teach `tests/test_spec_bindings.py` to read `spec("…")` from `ui/src/**/*.test.ts`, with a test that a vitest key with no living key is caught, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_spec_bindings.py` exits 0, and `grep -c 'test.ts' tests/test_spec_bindings.py` prints a number of at least `1`.
- [x] 1.7 In `isekai/interface/wiring.py`, make `wiring_from` import and call the factory `ISEKAI_WIRING` names when it is set, after `_check_run_root`; add `tests/e2e/wiring.py` with `fake`, per [D6](design.md#d6).
  Verify: `grep -c 'ISEKAI_WIRING' isekai/interface/wiring.py` prints a number of at least `1`, `grep -rn 'from tests\|import tests' isekai` prints nothing, and `uv run pytest -q tests/test_pipeline_cli.py` exits 0.
- [x] 1.8 Add `tests/e2e/conftest.py`: a session fixture that writes fixture runs under `tmp_path` and starts today's `isekai ui --flow summon-anime-wai` on a free port with `ISEKAI_WIRING=tests.e2e.wiring:fake`, per [D7](design.md#d7).
  Verify: `grep -c 'ISEKAI_WIRING' tests/e2e/conftest.py` prints a number of at least `1`.
- [x] 1.9 Add `tests/e2e/test_review.py` characterising today's page: a tag committed from the autocomplete (`ui:vocabulary:matches-are-ranked-by-post-count`), an approved input read-only (`ui:approval:approved-input-opens-read-only`), ⌥Space opening the cheatsheet (`ui:cheatsheet:every-declared-criterion-is-answered`).
  Verify: `uv run pytest -q tests/e2e` exits 0, and `grep -c 'pytest.mark.spec' tests/e2e/test_review.py` prints a number of at least `3`.

## 2 — The defects

- [x] 2.1 **HALT CHECK** — the defects still hold: the counter zeroed in `open()`, no `keepalive`, no process group, `Origin` checked only when sent, `caption_command` without `--runs`.
  Verify: `grep -c 'inFlight = 0' ui/src/composables/useSheet.ts` prints `1`, `grep -c 'keepalive' ui/src/api.ts` prints `0`, `grep -c 'start_new_session' isekai/interface/ui/bundle.py` prints `0`, `grep -c 'if origin is not None and origin not in origins' isekai/interface/ui/app.py` prints `1`, and `grep -c 'python -m isekai caption --flow {batch.flow.id} {held.run.id}' isekai/interface/ui/app.py` prints `1`.
- [x] 2.2 Fix 0018·R5 in `ui/src/composables/useSheet.ts` with a token per save, and add `ui/src/composables/useSheet.test.ts` binding `ui:save:a-stale-save-cannot-clear-saving`, per [D8](design.md#d8).
  Verify: `grep -c 'inFlight = 0' ui/src/composables/useSheet.ts` prints `0`, and `uv run python -m tools.test_ui` exits 0.
- [x] 2.3 Fix 0018·R12: `keepalive: true` on the draft `PUT` in `ui/src/api.ts`, with a test in `ui/src/composables/useSheet.test.ts` binding `ui:save:a-pending-edit-is-sent-on-leaving`, per [D8](design.md#d8).
  Verify: `grep -c 'keepalive: true' ui/src/api.ts` prints `1`, and `grep -c 'ui:save:a-pending-edit-is-sent-on-leaving' ui/src/composables/useSheet.test.ts` prints `1`.
- [x] 2.4 Fix 0023·R5 in `isekai/interface/ui/bundle.py` — `Popen` with `start_new_session=True`, `os.killpg` on timeout — and make the test bound to `ui:bundle:an-unfinished-build-is-stopped-and-named` in `tests/test_ui.py` see the group stopped, per [D8](design.md#d8).
  Verify: `grep -c 'start_new_session=True' isekai/interface/ui/bundle.py` prints `1`, and `uv run pytest -q tests/test_ui.py` exits 0.
- [x] 2.5 Fix 0023·S1 in `_addressed_here` (`isekai/interface/ui/app.py`) and add a test in `tests/test_ui_api.py` binding `ui:address:a-cross-site-request-without-origin-is-refused`, per [D8](design.md#d8).
  Verify: `grep -c 'Sec-Fetch-Site' isekai/interface/ui/app.py` prints a number of at least `1`, and `grep -c 'a-cross-site-request-without-origin-is-refused' tests/test_ui_api.py` prints `1`.
- [x] 2.6 Fix 0032·R1: build `caption_command` through `_remedy` in `isekai/interface/ui/app.py`, and extend the test bound to `ui:source:a-missing-caption-names-its-command` in `tests/test_ui_api.py` to a non-default runs root, per [D8](design.md#d8).
  Verify: `grep -c 'python -m isekai caption --flow {batch.flow.id} {held.run.id}' isekai/interface/ui/app.py` prints `0`, and `uv run pytest -q tests/test_ui_api.py` exits 0.

## 3 — The library

- [ ] 3.1 Add `isekai/interface/ui/library.py` — the library from `ISEKAI_LIBRARY`, created when absent, refused through `trackable` inside the tree; batches by `sources/`; each row's figures; each cell's stage — per [D1](design.md#d1), [D2](design.md#d2) and [D4](design.md#d4). It imports no web framework.
  Verify: `grep -c -E 'fastapi|starlette' isekai/interface/ui/library.py` prints `0`, and `uv run python -c "import isekai.interface.ui.library"` exits 0.
- [ ] 3.2 Add `tests/test_ui_library.py` binding `ui:library:an-absent-library-is-created`, `ui:library:a-library-git-can-reach-is-refused`, every `ui:batch-folder:*` key and every `ui:hub:*` key of [the ui delta](specs/ui/spec.md).
  Verify: `uv run pytest -q tests/test_ui_library.py` exits 0, and `grep -c 'ui:hub:the-hub-writes-nothing' tests/test_ui_library.py` prints `1`.

## 4 — The shell

- [ ] 4.1 Add `vue-router` per [Dependencies](design.md#dependencies): in `ui/`, `npm install --save-exact vue-router@5.4.0`.
  Verify: `grep -c '"vue-router": "5.4.0"' ui/package.json` prints `1`.
- [ ] 4.2 Switch the verb per [D1](design.md#d1): in `isekai/interface/cli.py` drop `photos`, `--runs`, `--flow` and `_OneFlow` from `ui`; `serve` in `isekai/interface/ui/__init__.py` serves the library; delete `isekai/interface/ui/batch.py`.
  Verify: `grep -c '_OneFlow' isekai/interface/cli.py` prints `0`, `test -e isekai/interface/ui/batch.py` exits 1, and `uv run python -m isekai ui --flow summon-anime-wai` exits 2.
- [ ] 4.3 Rewrite `isekai/interface/ui/app.py` onto the API of [D3](design.md#d3) — every review route under `/api/b/{batch}/review/{digest}/{flow}`, `index.html` for any other `GET` — keeping its guard and `_remedy`.
  Verify: `grep -c '/api/b/{batch}' isekai/interface/ui/app.py` prints a number of at least `5`, and `grep -c '"/api/batch"' isekai/interface/ui/app.py` prints `0`.
- [ ] 4.4 Move `tests/test_ui_api.py` onto the new paths, and per the table in [Tests](design.md#tests) delete the `ui:startup:*` and `ui:batch:*` tests in `tests/test_ui.py` and the `cli:flow-selection:a-serving-verb-takes-one-flow` tests in `tests/test_pipeline_cli.py`; add a test there binding `ui:library:the-verb-takes-no-arguments`.
  Verify: `grep -c -E 'ui:startup|ui:batch:|a-serving-verb-takes-one-flow' tests/test_ui.py tests/test_pipeline_cli.py` prints `0` for each file, and `uv run pytest -q tests/test_ui.py tests/test_ui_api.py tests/test_pipeline_cli.py` exits 0.
- [ ] 4.5 Add `ui/src/router.ts` (`/`, `/b/:batch/hub`, `/b/:batch/review/:digest/:flow`), `ui/src/App.vue` with the shell — AppBar, JobStrip idle, the BillingBanner slot — the tokens of [design spec §2](design-spec.md#2--tokens) in `ui/src/styles.css`, `ui/src/views/Home.vue` per §5's J7·1, and the review surface as `ui/src/views/Review.vue`; delete `ui/src/ReviewApp.vue`.
  Verify: `test -e ui/src/ReviewApp.vue` exits 1, `grep -c "'/b/:batch/review/:digest/:flow'" ui/src/router.ts` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 4.6 Move `tests/e2e/conftest.py` to `isekai ui` over a fixture library with `ISEKAI_LIBRARY` set, point `tests/e2e/test_review.py` at the review URL, and add `tests/e2e/test_routes.py` binding `ui:routes:a-reload-lands-on-the-same-screen` and `ui:routes:an-unknown-batch-is-refused`; bind `ui:routes:a-run-is-named-by-its-digest` in `tests/test_ui_api.py`.
  Verify: `uv run pytest -q tests/e2e` exits 0, and `grep -c 'ui:routes:' tests/e2e/test_routes.py` prints `2`.

## 5 — The hub

- [ ] 5.1 Add `ui/src/views/Hub.vue` per [design spec §5](design-spec.md#5--the-journeys)'s J2 grid, read-only: stage tracks and words from `/api/b/{batch}/hub`, a disabled checkbox for no flow with its reason, `unreadable` cells, focus, ↵ to the cell's Review, ⌥0–⌥3 per §7.
  Verify: `grep -c "'/b/:batch/hub'" ui/src/router.ts` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 5.2 Extend `tests/e2e/test_routes.py`'s reload test with a step from Home to a batch's hub, then ↵ on a sheet cell to its Review.
  Verify: `uv run pytest -q tests/e2e/test_routes.py` exits 0.

## 6 — The queue

- [ ] 6.1 Implement the queue per [D5](design.md#d5) in `ui/src/composables/useQueue.ts`, `ui/src/views/Hub.vue` and `ui/src/views/Review.vue`: *Review next*, the rail as the queue, Approve to the next sheet or the hub, the post-approve failure in the approve bar (0018·R8); in `isekai/interface/ui/app.py`, a draft through `review` on opening.
  Verify: `test -e ui/src/composables/useQueue.ts` exits 0, `grep -c 'Review next' ui/src/views/Hub.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 6.2 Add `tests/e2e/test_queue.py` binding `ui:queue:approve-moves-to-the-next-sheet`, `ui:queue:after-the-last-sheet-the-hub-opens` and `ui:queue:a-failure-after-approval-is-shown`; bind `ui:queue:opening-a-sheet-writes-its-draft` in `tests/test_ui_api.py`.
  Verify: `uv run pytest -q tests/e2e/test_queue.py tests/test_ui_api.py` exits 0, and `grep -c 'ui:queue:' tests/e2e/test_queue.py` prints `3`.

## 7 — The docs and the deletions

- [ ] 7.1 Copy `openspec/changes/0061-ui-groundwork/design-spec.md` to `ui/design/spec.md`, and delete every other file under `ui/design/`, per [D10](design.md#d10).
  Verify: `ls ui/design` prints `spec.md` alone.
- [ ] 7.2 Rewrite in `docs/decisions.md` D4, D18, D19 and D24, and add D40 and D41, per [D10](design.md#d10).
  Verify: `grep -c -E '^### D40 · A batch is a library folder holding|^### D41 · The test seam is a factory named in the environment' docs/decisions.md` prints `2`, and `grep -c 'Sec-Fetch-Site' docs/decisions.md` prints a number of at least `1`.
- [ ] 7.3 Move `README.md`, `docs/data-flow.md`, `docs/modules.md`, `isekai/interface/ui/README.md`, `CLAUDE.md` and `.env.example` onto `isekai ui` and the library, per [D10](design.md#d10).
  Verify: `grep -c -E 'ui --flow|ui <run-id>' README.md docs/data-flow.md` prints `0` for each file, `grep -c 'ISEKAI_LIBRARY' .env.example` prints `1`, and `uv run pytest -q tests/test_docs.py tests/test_spec_prose.py` exits 0.
- [ ] 7.4 Delete `.claude/skills/run-flows/`, `.claude/skills/compare-renders/` and `tests/test_agent_skills.py`; reword the comments at `isekai/interface/compare_view.py:38` and `tests/test_render.py:570`; remove the skills from `README.md`, per [D9](design.md#d9).
  Verify: `test -e .claude/skills/run-flows` exits 1, `test -e .claude/skills/compare-renders` exits 1, `test -e tests/test_agent_skills.py` exits 1, and `grep -rn 'run-flows\|compare-renders' README.md isekai tests` prints nothing.
