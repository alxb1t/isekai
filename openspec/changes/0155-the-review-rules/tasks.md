# The review rules — tasks

The phases `lens` and `kicker`, each a module with its test written first and the view switched to it, per [design](design.md).

## Progress

- [x] 1 — The viewer's rules in `lens.ts` · moderate
- [x] 2 — The status line's rules in `kicker.ts` · moderate

## 1 — The viewer's rules in `lens.ts`

- [x] 1.1 Write `ui/src/lens.test.ts` first: one `spec(` per row of [D3](design.md#d3)'s `lens.ts` table, its key a string literal, its assertions the text of that scenario's WHEN and THEN, over `viewedOf` and `photographStep` from `./lens`. Then add `ui/src/lens.ts` per [D1](design.md#d1), with the body of `viewed` and the branch order of `photograph` from `ui/src/views/Review.vue`, comments moved with the code.
  Verify: `uv run python -m tools.test_ui ui/src/lens.test.ts` exits 0.
- [x] 1.2 In `ui/src/views/Review.vue` import `Lens`, `viewedOf` and `photographStep` from `../lens`, delete the local `type Lens`, make `viewed` one `computed` calling `viewedOf`, and write `photograph()` as [D1](design.md#d1) shows. Leave `openLens`, `closeLens`, `photographKey` and the one `useKeys` call as they are ([D5](design.md#d5)).
  Verify: `git grep -n "^type Lens" -- ui/src/views/Review.vue` prints nothing.

## 2 — The status line's rules in `kicker.ts`

- [x] 2.1 Write `ui/src/kicker.test.ts` first: one `spec(` for the row of [D3](design.md#d3)'s `kicker.ts` table, its key a string literal, its assertions that a draft from another flow's approval reads `draft` and names no approval, over `kickerOf` from `./kicker`. Then add `ui/src/kicker.ts` per [D2](design.md#d2): `clock` and `minute` as they are in `ui/src/views/Review.vue`, and `kickerOf` with the branch order of `kicker`, comments moved with the code.
  Verify: `uv run python -m tools.test_ui ui/src/kicker.test.ts` exits 0.
- [x] 2.2 In `ui/src/views/Review.vue` import `clock`, `kickerOf` and `minute` from `../kicker`, delete the local `clock` and `minute`, and make `kicker` one `computed` calling `kickerOf` with the fields of [D2](design.md#d2). Keep `approvedAt` a `computed` over `clock`.
  Verify: `git grep -n -E "^const (clock|minute) =" -- ui/src/views/Review.vue` prints nothing.
- [x] 2.3 Print the view's length with `wc -l ui/src/views/Review.vue`, then replace `"ui/src/views/Review.vue": 696` in `BIG_UI_FILES` of `tests/test_ratchets.py` with the path and that number ([D6](design.md#d6)). The row stays.
  Verify: `git grep -n -F '"ui/src/views/Review.vue": 696' -- tests/test_ratchets.py` prints nothing.
