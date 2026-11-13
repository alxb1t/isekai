# The prototype's ink — tasks

The extractor reads the white point as the prototype does, then the outline step names the floor; each phase ends green, per [design](design.md).

## Progress

- [x] 1 — The prototype's ink · moderate
- [ ] 2 — The floor · moderate

## 1 — The prototype's ink

- [x] 1.1 In `isekai/shared/ink.py` delete `_MIN_SKIN`, `_SKIN_GAP` and `_skin_beside`, and the comments above them ([D1](design.md#d1)). In `_automatic_point` delete the `beside` read and the refusal after the percentile, keep the empty refusal, and return after the percentile. Change the docstring's clause "a point that reads ink, not skin, is refused" to "an outline with no lit pixel is refused".
  Verify: `git grep -n -e _SKIN_GAP -e _MIN_SKIN -e _skin_beside -- isekai` prints nothing and exits 1.
- [x] 1.2 In `tests/test_ink.py` replace the tests that match `no bare skin inside the outline` with `test_ink_extract_a_tight_outline_over_a_solid_fill_is_cut_by_the_percentile`, bound by `@pytest.mark.spec("edit:ink:a-tight-outline-over-a-solid-fill-is-cut-by-the-percentile")`. Parametrize it over the fills `BLACK_INK`, `(160, 120, 96)` and `(172, 150, 120)`, and assert `_at(extract_ink(_arm(fill), _tight(), None, None), 80, 80)[:3] == (255, 255, 255)`.
  Verify: `uv run pytest tests/test_ink.py -k tight_outline_over_a_solid_fill` passes.
- [x] 1.3 In `tests/test_ink.py` move the marker of `test_ink_extract_a_one_channel_fill_keeps_its_ink_under_a_wider_outline` to the new key. In `test_ink_extract_refuses_an_image_with_no_skin` pass `Image.new("L", (64, 64), 255)` as the outline and replace its `spec_exempt` with `@pytest.mark.spec("edit:ink:an-outline-with-no-bare-skin-is-refused")`. In `test_ink_grey_an_outline_with_no_bare_skin_is_refused` call `white_grey(Image.new("RGB", (160, 160), (5, 5, 5)), _tight())`.
  Verify: `uv run pytest tests/test_ink.py tests/test_spec_bindings.py` passes.
- [x] 1.4 In `docs/decisions.md` add `### D57 · The white point is the prototype's percentile` after D54, in the form of its neighbours: the bold decision, a Why bullet, and a Made-by bullet naming `0132`. The decision reads: the automatic white point is the `white` percentile, per channel, of the lit pixels inside the outline, compared with nothing; an outline with no lit pixel is refused, naming the fix. The Why says the prototype proved it on a blackwork sleeve, and that a fill read as its own white point shows in the ink view ([D5](design.md#d5)).
  Verify: `git grep -c "### D57" -- docs/decisions.md` prints `docs/decisions.md:1`.

## 2 — The floor

- [ ] 2.1 In `config/tattoo.json` change `"outline_min": 20` to `"outline_min": 3` ([D3](design.md#d3)). In `tests/test_tattoo_library.py` change the pin `(4096, 20, 120)` to `(4096, 3, 120)`. In `tests/test_ui_tattoo.py` change `"outline_min": 20` to `"outline_min": 3`.
  Verify: `uv run pytest tests/test_tattoo_library.py tests/test_ui_tattoo.py` passes.
- [ ] 2.2 In `ui/src/stages.ts` give `forwardOf` a third argument, `floor: number`. Below it the wait reads `outline open · ${points} of ${floor} points`; from it on, as now ([D4](design.md#d4)).
  Verify: `git grep -n -F "floor} points" -- ui/src/stages.ts` prints the wait's line.
- [ ] 2.3 In `ui/src/stages.test.ts` pass `3` in each `forwardOf` call and keep the 27-point case. Move the below-floor assertions of `ui:stages:forward-waits-for-a-closed-outline` into `spec('ui:stages:forward-names-the-floor-while-the-outline-is-short', …)`, asserting `outline open · 1 of 3 points` and `outline open · 0 of 3 points`.
  Verify: `uv run python -m tools.test_ui` exits 0.
- [ ] 2.4 In `ui/src/tattoos.ts` give `closeLine` a second argument, `floor: number`. Below it the line reads `add ${more} more ${more === 1 ? 'point' : 'points'} to close · ${count} of ${floor}`, `more` being `floor - count`; from it on, as now ([D4](design.md#d4)).
  Verify: `git grep -n -F "to close · " -- ui/src/tattoos.ts` prints the line's source.
- [ ] 2.5 In `ui/src/tattoos.test.ts` rewrite `ui:outline-step:one-line-says-how-to-close` at a floor of 3, for open outlines of 3 and 5 points and a closed one. Add `spec('ui:outline-step:the-line-names-the-floor-while-the-outline-is-short', …)` for open outlines of 0, 1 and 2 points, reading the lines of [D4](design.md#d4).
  Verify: `uv run python -m tools.test_ui` exits 0.
- [ ] 2.6 In `ui/src/components/OutlineStep.vue` pass `props.limits.outline_min` as the floor in the `closeLine` call and the `forwardOf` call ([D7](design.md#d7)).
  Verify: `git grep -c "outline_min" -- ui/src/components/OutlineStep.vue` prints `ui/src/components/OutlineStep.vue:3`, the rules' read and the two calls.
- [ ] 2.7 In `ui/design/spec.md` change the J9·3 row's line from `close the outline on its first point · 0 points` to `add 3 more points to close · 0 of 3`.
  Verify: `git grep -n "close the outline on its first point" -- ui/design/spec.md` prints nothing and exits 1.
