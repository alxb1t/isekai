# Tasks — 0086 compare any image

The server, then the page, per [design](design.md). Every new test carries its spec key.

## Progress

- [ ] 1 — The source's images and the route
- [ ] 2 — The pick and the view

## 1 — The source's images and the route

- [ ] 1.1 **HALT CHECK** — Compare reaches one flow.
  Verify: `grep -c '/compare/{other}/{other_seed}' isekai/interface/ui/app.py` prints `1`.
- [ ] 1.2 Serve `source` from `read_render` and compare across flows and with the photograph in `read_compare`
  (`isekai/interface/ui/app.py`) per [D1](design.md#d1), [D3](design.md#d3) and [D4](design.md#d4); in
  `tests/test_ui_api.py` move `ui:compare:any-two-images-of-a-cell` to summon against flat summon and
  `ui:compare:a-seed-pairs-with-its-newest-older-version` to the pick's start.
  Verify: `grep -c '/compare/{other_flow}/{other_version}/{other_seed}' isekai/interface/ui/app.py` prints `1`, and `grep -c '/compare/photo' isekai/interface/ui/app.py` prints a number of at least `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.

## 2 — The pick and the view

- [ ] 2.1 **HALT CHECK** — the large view still offers *Side by side*.
  Verify: `grep -c 'data-side-by-side' ui/src/views/RenderLarge.vue` prints `1`.
- [ ] 2.2 Add `sourceGrid` and `movePick` to `ui/src/cells.ts` and delete `pick`; bind
  `ui:compare:the-pick-moves-by-row-and-column` and delete `ui:compare:one-other-image-is-compared-at-once` in
  `ui/src/cells.test.ts`, per [D2](design.md#d2).
  Verify: `grep -c 'the-pick-moves-by-row-and-column' ui/src/cells.test.ts` prints `1`, and `grep -c 'one-other-image-is-compared-at-once' ui/src/cells.test.ts` prints `0`, and `uv run python -m tools.test_ui` exits 0.
- [ ] 2.3 Draw the grid in `ui/src/components/ComparePick.vue`, the route in `ui/src/router.ts`, the pair in
  `ui/src/views/Compare.vue`, and delete `⇧C` and *Side by side* in `ui/src/views/RenderLarge.vue`, with `ui/src/api.ts`
  and `ui/src/types.ts`, per [D2](design.md#d2)–[D5](design.md#d5); in `tests/e2e/test_render.py` pick in the grid and
  the photograph's row.
  Verify: `grep -c 'data-side-by-side' ui/src/views/RenderLarge.vue` prints `0`, and `grep -c "compare/photo" ui/src/router.ts` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [ ] 2.4 Edit `ui/design/spec.md` per [D6](design.md#d6).
  Verify: `grep -c '⇧C \*Side by side\*' ui/design/spec.md` prints `0`, and `grep -c 'the image compare started from' ui/design/spec.md` prints a number of at least `1`, and `uv run pytest -q tests/e2e` exits 0.
