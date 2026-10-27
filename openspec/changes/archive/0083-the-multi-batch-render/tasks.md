# Tasks — 0083 the multi-batch render

The session, the app, then the drawer, per [design](design.md). Every new test carries its spec key.

## Progress

- [x] 1 — One session over many collections
- [x] 2 — The quote and the dialog
- [x] 3 — The drawer

## 1 — One session over many collections

- [x] 1.1 **HALT CHECK** — the verb renders one runs root.
  Verify: `grep -c 'runs = Path(args.runs)' isekai/interface/render.py` prints `1`.
- [x] 1.2 Take many runs roots in `render` (`isekai/interface/cli.py`, `isekai/interface/render.py`) per
  [D1](design.md#d1) and [D2](design.md#d2); open a record per collection and tee the log to each per
  [D3](design.md#d3), with `collections` in `SessionRecord` (`isekai/foundation/artifacts.py`); in
  `tests/test_render.py` bind `cli:render-short:many-collections-render-in-one-session`,
  `cli:render-limit:one-boot-for-many-collections` and `cli:render-session:each-collection-holds-its-record`.
  Verify: `grep -c 'many-collections-render-in-one-session\|one-boot-for-many-collections\|each-collection-holds-its-record' tests/test_render.py` prints `3`, and `uv run pytest -q tests/test_render.py` exits 0, and `uv run ty check` exits 0.
- [x] 1.3 Rewrite D36's *Accepts* line in `docs/decisions.md` per [D7](design.md#d7); in `README.md`, name
  `render <runs>…` beside the single-collection usage.
  Verify: `grep -c 'from every collection, until the teardown' docs/decisions.md` prints `1`, and `grep -c 'Reopen when a pod serves more than one batch' docs/decisions.md` prints `0`, and `grep -c 'render <runs>…' README.md` prints a number of at least `1`.

## 2 — The quote and the dialog

- [x] 2.1 **HALT CHECK** — the app quotes one collection.
  Verify: `grep -c 'def quoted(collection: str)' isekai/interface/ui/app.py` prints `1`.
- [x] 2.2 Quote and start across collections in `isekai/interface/render.py`, `isekai/interface/ui/app.py` and
  `isekai/interface/ui/jobs.py` per [D4](design.md#d4); in `tests/test_ui_api.py` bind
  `ui:render:the-dialog-quotes-every-collection` and `ui:render:past-the-ceiling-disables-render` and move the quote and
  start tests to the new routes; in `tests/test_ui_jobs.py` start renders with collections.
  Verify: `grep -c '"/api/render/quote"' isekai/interface/ui/app.py` prints `1`, and `grep -c 'the-dialog-quotes-every-collection\|past-the-ceiling-disables-render' tests/test_ui_api.py` prints `2`, and `uv run pytest -q tests/test_ui_api.py tests/test_ui_jobs.py` exits 0.
- [x] 2.3 Draw the rows, ticks and ceiling in `ui/src/components/RenderDialog.vue` and `+n in other collections` in
  `ui/src/components/RenderBar.vue` per [D5](design.md#d5), with `ui/src/api.ts` and `ui/src/types.ts`; in
  `tests/e2e/test_render.py` find the collection's row in the dialog.
  Verify: `grep -c 'in other collections' ui/src/components/RenderBar.vue` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0, and `uv run pytest -q tests/e2e/test_render.py` exits 0.

## 3 — The drawer

- [x] 3.1 **HALT CHECK** — the drawer shows one record.
  Verify: `grep -c 'export function stacked' ui/src/sessions.ts` prints `0`.
- [x] 3.2 Add `stacked` and its move to `ui/src/sessions.ts`, group records by id in `ui/src/stores/live.ts` and
  `ui/src/stores/drawer.ts`, and stack the grids in `ui/src/components/SessionDrawer.vue`, per [D6](design.md#d6); bind
  `ui:sessions:the-grids-stack-by-collection` in `ui/src/sessions.test.ts`, and move the drawer's and the live store's
  tests to `shown`'s collections.
  Verify: `grep -c 'the-grids-stack-by-collection' ui/src/sessions.test.ts` prints `1`, and `uv run python -m tools.test_ui` exits 0, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 3.3 In `ui/design/spec.md`, J4's dialog and drawer say a row per collection, the ticks, the ceiling, a grid per
  collection; in `docs/data-flow.md`, the render line names many collections in one session.
  Verify: `grep -c 'a row per collection' ui/design/spec.md` prints a number of at least `1`, and `grep -c 'many collections' docs/data-flow.md` prints a number of at least `1`, and `uv run pytest -q tests/e2e` exits 0.
