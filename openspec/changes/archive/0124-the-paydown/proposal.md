---
bump: patch
version: v0.78.1
beside: [0119-the-tattoo-edit, 0120-the-bakes-in-the-app]
debt: [0111·R1, 0111·R2, op·chained-source, 0072·R5, 0070·R20, 0118·S1]
---

# The paydown

The debt cards no open version claims are paid, each under a requirement already in force, so `.minions/debt.md` holds no card once `0119` and `0120` release.

Reading map: [design](design.md) holds the decisions, the tests and the risks, [tasks](tasks.md) holds a phase per card.

## Why

`open-backlog-cards` passed its `watch` at `0118`. `0119` and `0120` pay their cards; these are the cards left, each a small fix or a line of prose.

## What Changes

One line per requirement the [delta](specs/) touches. A patch adds a scenario or rewords a sentence under a requirement, never a requirement.

- **review · An approval is copied once from another flow's approval, its seeds with it** — a copy is in step when the target holds the same seeds, listed or rendered, so a second `approve --from` after both rendered writes nothing (0111·R1). Its rationale says a `T=S` render reads the source's seeds when it runs (0111·R2).
- **cli · A render session's limit is estimated from its work, at most the configured ceiling** — a line whose source request names another source request's flow is refused before the pod, naming the request that renders the same seeds (op·chained-source).
- **ui · Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet** — Review reads an approved sheet again when a render for its collection starts or ends, so *Cancel approve* follows the render (0072·R5).
- **ui · The page's save state is true to the requests in flight, and a pending edit is sent on leaving** — a save waiting behind another takes later edits instead of queueing a second request, and a failed save leaves the draft pending only when no save waits (0070·R20).
- **ui · The hub shows each source's stage in each offered flow, and a tick assigns it** — the cell modal's rows keep their height and the grid scrolls to a fourth row (0118·S1).
- **Prose, no requirement** — D49's *Why*, D38's note and the README say what a `T=S` render takes (0111·R2).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review` — the copy's in-step rule and its rationale.
- `cli` — the render session's source order.
- `ui` — Review's cancel, the save queue and the cell modal's rows.

## Impact

- Code: `isekai/pipeline/review.py`, `isekai/interface/render.py`, `ui/src/views/Review.vue`, a new `ui/src/cancel.ts`, `ui/src/composables/useSheet.ts`, `ui/src/app.css`; `ui/src/App.vue` is read, not edited.
- Tests: `tests/test_review.py`, `tests/test_render.py`, a new `ui/src/cancel.test.ts`, `ui/src/composables/useSheet.test.ts`, `tests/e2e/test_render.py`, `tests/e2e/conftest.py`.
- Docs: `docs/decisions.md`, `README.md`, `ui/design/spec.md`, and the living specs through the delta.
- Shared with `0119`: `render.py`, `docs/decisions.md`. Shared with `0120`: `ui/design/spec.md`, `ui/src/app.css`, the `ui` spec. The lines differ; the version that releases second takes a catch-up merge.

## Not in this change

- The cards `0119` pays and the cards `0120` pays.
- `DraftDialog`'s several-image path (`0118`'s non-goal).
- A check of a copy's fields against its source's latest approval: `0111` removed it on purpose.
- A new decision: D49 and D38 are amended in place, and no id is taken.
- `make setup` without Chromium.
