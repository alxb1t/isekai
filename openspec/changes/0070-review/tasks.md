# Tasks — 0070 review

The address, the rail and Approve, the layout, ④, then the dialogs, per [design](design.md). Every new pytest test
carries `@pytest.mark.spec`, and every new vitest test `spec("…")`, with the key its task names.

## Progress

- [ ] 1 — The address
- [ ] 2 — The rail and Approve
- [ ] 3 — The layout
- [ ] 4 — ④ as slots
- [ ] 5 — The dialogs

## 1 — The address

- [ ] 1.1 **HALT CHECK** — Review has no batch-level route, and the hub offers *Review next*.
  Verify: `grep -c "path: '/b/:batch/review'," ui/src/router.ts` prints `0`, and `grep -c 'Review next' ui/src/views/Hub.vue` prints `2`.
- [ ] 1.2 Add `short` to `Cell` in `isekai/interface/ui/library.py` per [D2](design.md#d2), and to `HubCell` in
  `ui/src/types.ts`; bind `ui:review:a-cell-counts-what-it-lacks` in `tests/test_ui_library.py`.
  Verify: `uv run pytest -q tests/test_ui_library.py` exits 0, and `grep -c 'ui:review:a-cell-counts-what-it-lacks' tests/test_ui_library.py` prints `1`.
- [ ] 1.3 Add `head` to `ui/src/composables/useQueue.ts`, bound to `ui:review:a-batch-opens-its-head` in
  `ui/src/composables/useQueue.test.ts`; add `ui/src/views/ReviewHead.vue` and its route per [D1](design.md#d1).
  Verify: `grep -c "name: 'review-head'" ui/src/router.ts` prints `1`, and `uv run python -m tools.test_ui` exits 0.
- [ ] 1.4 Point the Review tab and `⇧R` in `ui/src/App.vue` at `review-head`, the tab counting the unapproved; drop
  *Review next* and *nothing left to review* from `ui/src/views/Hub.vue`.
  Verify: `grep -c 'Review next\|nothing left to review' ui/src/views/Hub.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 1.5 Add `/b/<batch>/review` to `ui/design/spec.md` §4 and drop *Review next* from its J2 header; say Review
  opens the batch's head in `README.md` and in the flow diagram of `isekai/interface/ui/README.md`.
  Verify: `grep -c 'Review next' README.md isekai/interface/ui/README.md` prints `0` for each file.

## 2 — The rail and Approve

- [ ] 2.1 **HALT CHECK** — Approve moves on, and Revise rides a query.
  Verify: `grep -c 'after(\|nextRevised' ui/src/views/Review.vue` prints `4`.
- [ ] 2.2 Replace `useQueue`'s listing with `rail` in `ui/src/composables/useQueue.ts`, dropping `after`, `queued`
  and `reviewQueue`; rewrite `ui/src/composables/useQueue.test.ts`, binding `ui:review:the-rail-holds-every-unrendered-sheet`.
  Verify: `grep -c 'export function \(after\|queued\|reviewQueue\)' ui/src/composables/useQueue.ts` prints `0`, and `uv run python -m tools.test_ui` exits 0.
- [ ] 2.3 Keep Approve, Discard and Revise on their sheet in `ui/src/views/Review.vue` per [D4](design.md#d4); mark
  and head the rail in `ui/src/components/BatchRail.vue` per [D3](design.md#d3).
  Verify: `grep -c 'after(\|nextRevised\|queue:' ui/src/views/Review.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 2.4 Await the saves in flight in `flush` in `ui/src/composables/useSheet.ts`, and `flush` before Approve, per
  [D9](design.md#d9); bind `ui:save:an-approval-waits-for-a-save-in-flight` in `ui/src/composables/useSheet.test.ts`.
  Verify: `grep -c 'an-approval-waits-for-a-save-in-flight' ui/src/composables/useSheet.test.ts` prints `1`, and `uv run python -m tools.test_ui` exits 0.
- [ ] 2.5 Replace the queue tests in `tests/e2e/test_queue.py` per the design's [Tests](design.md#tests) table, and
  rebind the failure test to `ui:review:a-failure-after-approval-is-shown`; rebind `tests/test_ui_api.py`'s draft-on-open test.
  Verify: `grep -rc 'ui:queue:' tests` prints `0` for each file, and `uv run pytest -q tests/e2e/test_queue.py tests/test_ui_api.py` exits 0.
- [ ] 2.6 End `test_revise_opens_review_on_the_revision_and_approving_it_ends_at_the_hub` in `tests/e2e/test_render.py`
  on its approved sheet, renamed `test_revise_opens_review_on_the_revision`.
  Verify: `grep -c 'approving_it_ends_at_the_hub' tests/e2e/test_render.py` prints `0`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [ ] 2.7 Rewrite *The queue* bullet of `ui/design/spec.md` J3 per [D4](design.md#d4): Approve stays; the rail holds
  every sheet not yet rendered.
  Verify: `grep -c 'Approve moves to the next' ui/design/spec.md` prints `0`.

## 3 — The layout

- [ ] 3.1 **HALT CHECK** — the old header stands.
  Verify: `test -e ui/src/components/AppHeader.vue` exits 0.
- [ ] 3.2 Move the receipts into `ui/src/components/SheetHeader.vue`'s kicker and every refusal into
  `ui/src/components/ApproveBar.vue` per [D5](design.md#d5); drop SheetHeader's "schema order" line; delete `AppHeader.vue`.
  Verify: `test -e ui/src/components/AppHeader.vue` exits 1, `grep -c 'schema order' ui/src/components/SheetHeader.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.3 Draw the revision's header row and pair in `ui/src/components/SourcePanel.vue` per [D6](design.md#d6), and
  Discard in `ApproveBar.vue`.
  Verify: `grep -c 'fill window' ui/src/components/SourcePanel.vue` prints `0`, and `grep -c 'data-discard' ui/src/components/ApproveBar.vue` prints a number of at least `1`.
- [ ] 3.4 Move Discard's ask out of `test_revise_opens_review_on_the_revision` into a new
  `test_discard_asks_before_it_deletes` in `tests/e2e/test_render.py`, bound to `ui:revise:discard-asks-before-it-deletes`.
  Verify: `grep -c 'discard-asks-before-it-deletes' tests/e2e/test_render.py` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
- [ ] 3.5 Redraw J5·4 in `ui/design/spec.md` per [D6](design.md#d6), and say *Discard draft* asks, then deletes.
  Verify: `grep -c 'Discard revision' ui/design/spec.md` prints `0`.

## 4 — ④ as slots

- [ ] 4.1 **HALT CHECK** — a repeated seed passes `renders_of`.
  Verify: `grep -c 'twice' isekai/foundation/artifacts.py` prints `0`.
- [ ] 4.2 Refuse a seed listed twice in `renders_of` in `isekai/foundation/artifacts.py`; bind
  `review:renders:a-repeated-seed-is-refused` in `tests/test_review.py`.
  Verify: `uv run pytest -q tests/test_review.py` exits 0, and `grep -c 'a-repeated-seed-is-refused' tests/test_review.py` prints `1`.
- [ ] 4.3 Add `ui/src/slots.ts` per [D7](design.md#d7), bound to `ui:review:each-image-has-a-slot` in a new
  `ui/src/slots.test.ts`.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'each-image-has-a-slot' ui/src/slots.test.ts` prints `1`.
- [ ] 4.4 Draw ④ as slots right of the sheet rows in `ui/src/components/RendersBlock.vue`, `ui/src/views/Review.vue`
  and `ui/src/app.css`, with its keys, per [D7](design.md#d7).
  Verify: `grep -c 'add a seed' ui/src/components/RendersBlock.vue` prints `0`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.
- [ ] 4.5 Draw ④ to the right of the sheet in `ui/design/spec.md` J3 and J5·5, one slot per image.
  Verify: `grep -c 'one slot per image' ui/design/spec.md` prints a number of at least `1`.

## 5 — The dialogs

- [ ] 5.1 **HALT CHECK** — Review's photograph opens in its own lens.
  Verify: `test -e ui/src/components/PhotoOverlay.vue` exits 0.
- [ ] 5.2 Give `ui/src/components/ImageViewer.vue` its images and `←` / `→`; open the photograph and the revised
  render in it from `ui/src/views/Review.vue`; add *Side by side*; delete `PhotoOverlay.vue`, per [D8](design.md#d8).
  Verify: `test -e ui/src/components/PhotoOverlay.vue` exits 1, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 5.3 Add `test_the_photograph_opens_in_the_viewer` to `tests/e2e/test_review.py` and
  `test_side_by_side_shows_the_pair` to `tests/e2e/test_render.py`, each bound to its key.
  Verify: `cat tests/e2e/test_review.py tests/e2e/test_render.py | grep -c -E 'the-photograph-opens-in-the-viewer|side-by-side-shows-the-pair'` prints `2`, and `uv run pytest -q tests/e2e` exits 0.
- [ ] 5.4 Name the viewer and *Side by side* in `ui/design/spec.md` J3 and J5·4, and `⇧C` in §7's Review row.
  Verify: `grep -c 'Side by side' ui/design/spec.md` prints a number of at least `2`.
