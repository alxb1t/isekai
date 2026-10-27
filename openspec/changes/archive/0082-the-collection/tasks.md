# Tasks — 0082 the collection

The CLI and the stages, the app, then the docs, per [design](design.md). No test is added; every test that names a
folder-sense batch is renamed with the code it tests.

## Progress

- [x] 1 — The CLI and the stages
- [x] 2 — The app
- [x] 3 — The docs

## 1 — The CLI and the stages

- [x] 1.1 **HALT CHECK** — `import` takes `--batch`.
  Verify: `grep -c '"--batch"' isekai/interface/cli.py` prints `1`.
- [x] 1.2 Rename the folder sense per [D2](design.md#d2) in `isekai/interface/cli.py`, `isekai/interface/render.py`,
  `isekai/interface/compare_view.py`, `isekai/pipeline/importing.py`, `isekai/foundation/artifacts.py`, `evaluation/`
  and `tools/derive_field_map.py`, and in `tests/test_importing.py`, `tests/test_pipeline_cli.py`, `tests/test_compare.py`
  and `tests/test_render.py`; follow a renamed name into its callers under `isekai/interface/ui/`; keep D1's senses,
  and say *invocation* for the field map's and the tagger's inputs in `cli.py`.
  Verify: `grep -rniwE --include='*.py' 'batch|batches' isekai/interface/cli.py isekai/interface/render.py isekai/interface/compare_view.py isekai/pipeline/importing.py isekai/foundation/artifacts.py evaluation tools/derive_field_map.py | grep -v 'A batch ends in a question\|Batch is the general\|whole batch\|prompt in the batch\|the batch first' | wc -l` prints `0`, and `grep -c '"--collection"' isekai/interface/cli.py` prints `1`, and `uv run pytest -q --ignore=tests/e2e` exits 0.

## 2 — The app

- [x] 2.1 **HALT CHECK** — the app's addresses name a batch.
  Verify: `grep -c "path: '/b/:batch" ui/src/router.ts` prints `6`.
- [x] 2.2 Rename the routes, the API, the payload keys, the identifiers and the words per [D3](design.md#d3) in
  `isekai/interface/ui/` and `ui/src/`, moving `ui/src/stores/batch.ts` to `ui/src/stores/collection.ts` and
  `ui/src/stores/batch.test.ts` to `ui/src/stores/collection.test.ts`; rename them in `tests/test_ui_api.py`,
  `tests/test_ui_library.py`, `tests/test_ui_jobs.py` and `tests/e2e/`.
  Verify: `grep -rniwE 'batch|batches' isekai/interface/ui ui/src | grep -v 'Key\|spec(' | wc -l` prints `0`, and `grep -rn "/api/b/\|'/b/:" isekai ui/src tests | wc -l` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0, and `uv run pytest -q` exits 0.

## 3 — The docs

- [x] 3.1 **HALT CHECK** — D40 calls the folder a batch.
  Verify: `grep -c '### D40 · A batch is a library folder' docs/decisions.md` prints `1`.
- [x] 3.2 Rename the folder sense per [D4](design.md#d4) in `docs/decisions.md`, `docs/data-flow.md`,
  `docs/modules.md`, `README.md`, `AGENTS.md`, `ui/design/spec.md`, `evaluation/README.md` and each `README.md` under
  `isekai/`; keep D1's senses.
  Verify: `grep -c '### D40 · A collection is a library folder' docs/decisions.md` prints `1`, and `grep -rn 'd40--a-batch' docs README.md | wc -l` prints `0`, and `grep -c -- '--collection COLLECTION' README.md` prints `1`, and `uv run pytest -q tests/test_docs.py` exits 0.
