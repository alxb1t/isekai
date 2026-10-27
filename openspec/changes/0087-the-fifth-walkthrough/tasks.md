# Tasks — 0087 the fifth walkthrough

The bar and the scroll, the keys and the pick, Compare, then the large view's steps, per [design](design.md). Every
new vitest test carries `spec(…)` with the key its task names.

## Progress

- [x] 1 — The bar and the scroll
- [ ] 2 — The keys and the pick
- [ ] 3 — Compare
- [ ] 4 — The large view's steps

## 1 — The bar and the scroll

- [x] 1.1 **HALT CHECK** — the bar's running branch shows only when nothing is short.
  Verify: `grep -c 'v-if="images + others > 0' ui/src/components/RenderBar.vue` prints `1`.
- [x] 1.2 Show the running session's totals and the images waiting for the next session in `ui/src/bars.ts` and
  `ui/src/components/RenderBar.vue` per [D1](design.md#d1); bind `ui:render:a-running-session-shows-its-totals` in
  `ui/src/bars.test.ts`.
  Verify: `grep -c 'wait for the next session' ui/src/bars.ts` prints a number of at least `1`, and `grep -c 'a-running-session-shows-its-totals' ui/src/bars.test.ts` prints `1`, and `uv run python -m tools.test_ui` exits 0.
- [x] 1.3 Scroll a restored focus to the centre in `ui/src/views/Renders.vue` and `ui/src/views/Hub.vue` per
  [D2](design.md#d2); in `tests/e2e/test_render.py` check the image in view after `Esc` in
  `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` and `test_a_rendered_cell_opens_its_newest_image`.
  Verify: `grep -l "block: 'center'" ui/src/views/Renders.vue ui/src/views/Hub.vue | wc -l` prints `2`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.

## 2 — The keys and the pick

- [ ] 2.1 **HALT CHECK** — Compare is a plain `c`.
  Verify: `grep -c "keys: plain('KeyC')" ui/src/views/RenderLarge.vue` prints `1`.
- [ ] 2.2 Take `shifted('KeyC')` for `compare` in `ui/src/views/RenderLarge.vue` per [D3](design.md#d3); caption each
  tile `v<N>` and name the focused tile in the head in `ui/src/components/ComparePick.vue` per [D4](design.md#d4); bind
  `ui:compare:the-pick-names-the-focused-tile` in `ui/src/cells.test.ts`; press `Shift+C` in the compare tests of
  `tests/e2e/test_render.py`.
  Verify: `grep -c "keys: plain('KeyC')" ui/src/views/RenderLarge.vue` prints `0`, and `grep -c 'the-pick-names-the-focused-tile' ui/src/cells.test.ts` prints `1`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [ ] 2.3 In `docs/decisions.md` D25, `` `⇧`+letter for a command, always for one that writes, a plain letter only where
  nothing is typed`` → ``a plain letter moves, a command is `⇧` + a letter, a plain letter only where nothing is
  typed``.
  Verify: `grep -c 'a plain letter moves, a command is' docs/decisions.md` prints `1`, and `grep -c 'always for one that writes' docs/decisions.md` prints `0`.

## 3 — Compare

- [ ] 3.1 **HALT CHECK** — Compare lists the changed fields.
  Verify: `grep -c 'data-changed' ui/src/views/Compare.vue` prints a number of at least `1`.
- [ ] 3.2 Drop `changed`, `different_seeds` and `same_sheet` from `read_compare` (`isekai/interface/ui/app.py`), and
  draw the pair and its heads alone, centred and as tall as the window, in `ui/src/views/Compare.vue` and
  `ui/src/app.css`, with `ui/src/types.ts`, per [D5](design.md#d5); edit `ui:compare:any-two-images-of-a-cell` in
  `tests/test_ui_api.py` and the compare tests in `tests/e2e/test_render.py`.
  Verify: `grep -c 'data-changed\|compare__line' ui/src/views/Compare.vue` prints `0`, and `grep -c '"same_sheet"' isekai/interface/ui/app.py` prints `0`, and `uv run pytest -q tests/test_ui_api.py tests/e2e/test_render.py` exits 0.

## 4 — The large view's steps

- [ ] 4.1 **HALT CHECK** — the large view takes no `h` `l`.
  Verify: `grep -c "plain('KeyH'" ui/src/views/RenderLarge.vue` prints `0`.
- [ ] 4.2 Add `screenOrder` to `ui/src/cells.ts` and step the large view with `h` `l` and the arrows in
  `ui/src/views/RenderLarge.vue` per [D6](design.md#d6); bind `ui:renders:the-large-view-steps-its-screens-order` in
  `ui/src/cells.test.ts`.
  Verify: `grep -c 'the-large-view-steps-its-screens-order' ui/src/cells.test.ts` prints `1`, and `grep -c "plain('KeyH'" ui/src/views/RenderLarge.vue` prints `1`, and `uv run python -m tools.test_ui` exits 0, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 4.3 Edit `ui/design/spec.md` per [D7](design.md#d7).
  Verify: `grep -c 'Compare with…  ⇧C' ui/design/spec.md` prints a number of at least `1`, and `grep -c 'wait for the next session' ui/design/spec.md` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
