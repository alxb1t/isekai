# Tasks — 0071 the review patch

The prose, then the route test, per [design](design.md). The spec cards are paid by the delta itself.

## Progress

- [ ] 1 — The prose
- [ ] 2 — The route test

## 1 — The prose

- [ ] 1.1 **HALT CHECK** — the README still describes the queue.
  Verify: `grep -c 'Approve moves to the\|on each draft' README.md` prints `2`.
- [ ] 1.2 Rewrite `README.md:259` and `:264` per [D2](design.md#d2).
  Verify: `grep -c 'Approve moves to the\|on each draft' README.md` prints `0`, and `uv run pytest -q tests/test_docs.py` exits 0.
- [ ] 1.3 Rewrite the comments in `ui/src/composables/useSheet.ts`, `ui/src/views/Review.vue` and
  `ui/src/components/TagInput.vue` per [D2](design.md#d2).
  Verify: `grep -c 'header line\|lens moves the batch\|Two saves can be in' ui/src/composables/useSheet.ts ui/src/views/Review.vue ui/src/components/TagInput.vue` prints `0` for each file.

## 2 — The route test

- [ ] 2.1 **HALT CHECK** — no test opens a batch's Review address.
  Verify: `grep -c '/review"' tests/e2e/test_routes.py` prints `0`.
- [ ] 2.2 Add the head and empty-page steps of [D3](design.md#d3) to
  `test_a_reload_lands_on_the_same_hub_and_the_same_review` in `tests/e2e/test_routes.py`.
  Verify: `grep -c '/review"' tests/e2e/test_routes.py` prints `2`, and `uv run pytest -q tests/e2e/test_routes.py` exits 0.
