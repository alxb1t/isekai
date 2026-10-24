# Tasks — 0072 cancel approve

The review stage, the verb, then the surface, per [design](design.md). Every new pytest test carries
`@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — The review stage
- [x] 2 — The verb
- [x] 3 — The surface

## 1 — The review stage

- [x] 1.1 **HALT CHECK** — the review stage has no cancel.
  Verify: `grep -c 'def cancel' isekai/pipeline/review.py` prints `0`.
- [x] 1.2 Add `cancellable` and `cancel` to `isekai/pipeline/review.py` per [D1](design.md#d1), [D2](design.md#d2)
  and [D3](design.md#d3); bind every `review:cancel:` key of the [review](specs/review/spec.md) delta in `tests/test_review.py`.
  Verify: `uv run pytest -q tests/test_review.py` exits 0, and `grep -c 'review:cancel:' tests/test_review.py` prints `6`.

## 2 — The verb

- [x] 2.1 **HALT CHECK** — `approve` takes no `--cancel`.
  Verify: `grep -c '"--cancel"' isekai/interface/cli.py` prints `0`.
- [x] 2.2 Add `--cancel` to `approve` in `isekai/interface/cli.py` per [D4](design.md#d4); bind both
  `cli:approve-cancel:` keys in `tests/test_pipeline_cli.py`.
  Verify: `uv run python -m isekai approve --help` exits 0, and `grep -c 'cli:approve-cancel:' tests/test_pipeline_cli.py` prints `2`.
- [x] 2.3 Name `approve --cancel` in the verbs list of `README.md`.
  Verify: `grep -c 'approve --cancel' README.md` prints a number of at least `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 3 — The surface

- [x] 3.1 **HALT CHECK** — Review's payload says nothing of cancelling.
  Verify: `grep -c '"cancel"' isekai/interface/ui/app.py` prints `0`.
- [x] 3.2 Add `cancel` to `read_input` in `isekai/interface/ui/app.py` and a cancel route beside the approve route,
  per [D5](design.md#d5); bind `ui:review:the-sheet-says-why-it-cannot-be-cancelled` in `tests/test_ui_api.py`.
  Verify: `uv run pytest -q tests/test_ui_api.py` exits 0, and `grep -c 'the-sheet-says-why-it-cannot-be-cancelled' tests/test_ui_api.py` prints `1`.
- [x] 3.3 Show *Cancel approve* in `ui/src/components/ApproveBar.vue` and run it from `ui/src/views/Review.vue` per
  [D5](design.md#d5), with `ui/src/api.ts` and `ui/src/types.ts`; reset `refused` per [D6](design.md#d6).
  Verify: `grep -c 'Cancel approve' ui/src/components/ApproveBar.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 3.4 Add a batch to `QUEUES` in `tests/e2e/conftest.py` and `test_cancel_approve_opens_the_sheet_again` to
  `tests/e2e/test_queue.py`, bound to `ui:review:cancel-approve-opens-the-sheet-again`.
  Verify: `grep -c 'cancel-approve-opens-the-sheet-again' tests/e2e/test_queue.py` prints `1`, and `uv run pytest -q tests/e2e/test_queue.py` exits 0.
- [x] 3.5 Say in `ui/design/spec.md` J3 that an approved sheet offers *Cancel approve* while nothing derives from it.
  Verify: `grep -c 'Cancel approve' ui/design/spec.md` prints a number of at least `1`.
