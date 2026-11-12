# The paydown — tasks

A phase per debt card, in the order of [design](design.md)'s decisions.

## Progress

- [x] 1 — The copy in step · moderate
- [ ] 2 — The copy's prose · moderate
- [ ] 3 — The chained source · moderate
- [ ] 4 — The cancel follows the render · moderate
- [ ] 5 — The save queue · hard
- [ ] 6 — The modal's rows · moderate

## 1 — The copy in step

Closes 0111·R1: a second `approve --from` after both flows rendered writes nothing ([D1](design.md#d1)).

- [x] 1.1 Add `test_a_copy_in_step_after_both_rendered_writes_nothing` to `tests/test_review.py`, after `test_an_approved_target_is_not_copied_over`, bound to `review:copy-from:a-copy-is-in-step-once-both-have-rendered`.
  It copies, writes `<seed>.png` files into the source's `001` group and, in one case, the target's, then copies again: no new approval where the target rendered, and `002` listing the seeds where it did not.
  Verify: `git grep -n "a-copy-is-in-step-once-both-have-rendered" -- tests/test_review.py` prints a line.
- [x] 1.2 In `_copy_approval` in `isekai/pipeline/review.py`, replace the `renders_of(mine, newest, afresh) == renders` clause with the `copied_renders` comparison of [D1](design.md#d1), and reword the docstring to "listed or rendered". The test of 1.1 is red until this task is done.
  Verify: `uv run pytest tests/test_review.py -k in_step` exits 0.

## 2 — The copy's prose

Closes 0111·R2: the prose says what a `T=S` render takes, and no check is added ([D2](design.md#d2)). The review spec's rationale is in the delta and folds at release.

- [ ] 2.1 In `docs/decisions.md`, D49's *Why*, across its line wrap: before ``off, and the seeds travel with the copy, so that holds with no later check; a copy naming its source kept``, after ``off. The copy lists the source's seeds; a `T=S` render reads the source's latest seeds when it runs, and the copy's fields follow the source's only when `approve --from` is run again. A copy naming its source kept``.
  Verify: `git grep -n "holds with no later check" -- docs/decisions.md` prints nothing.
- [ ] 2.2 In `docs/decisions.md`, D38's note: before ``and its seeds are copied rather than checked.``, after ``and no check holds it to its source: a `T=S` render reads the source's seeds when it runs.``
  Verify: `git grep -n "copied rather than checked" -- docs/decisions.md` prints nothing.
- [ ] 2.3 In `README.md`, the `--seeds-from` line: before `render each run on the seeds of that flow's latest render;`, after `render each run on the seeds of that flow's latest render, read when the render runs;`.
  Verify: `git grep -n "read when the render runs" -- README.md` prints a line.

## 3 — The chained source

Closes op·chained-source: a chained source is refused before the pod ([D3](design.md#d3)).

- [ ] 3.1 Add `test_a_chained_source_is_refused_before_the_pod` to `tests/test_render.py` after the dependent-before-source test, bound to `cli:render-limit:a-chained-source-is-refused-before-the-pod`.
  It runs `session(runs, "control-anime-wai=summon-anime-wai", "summon-flat-anime-wai=control-anime-wai", opener=opener)` and expects status 1, no session opened, and the concrete message of [D3](design.md#d3) in `log(runs)`.
  Verify: `git grep -n "a-chained-source-is-refused-before-the-pod" -- tests/test_render.py` prints a line.
- [ ] 3.2 In `in_session_sources` in `isekai/interface/render.py`, refuse a source request whose source is another source request's flow, with the message of [D3](design.md#d3), and add the rule to its docstring. The test of 3.1 is red until this task is done.
  Verify: `uv run pytest tests/test_render.py -k chained` exits 0.
- [ ] 3.3 Rewrite the docstring of `_requested` in `isekai/interface/render.py` to say what it plans, as [D3](design.md#d3) states it: before ``with the most images it renders across `ids`.``, after the plan of each request kind.
  Verify: `git grep -n "with the most images it renders" -- isekai/interface/render.py` prints nothing.

## 4 — The cancel follows the render

Closes 0072·R5: Review reads an approved sheet again when a render for its collection starts or ends ([D4](design.md#d4)).

- [ ] 4.1 **HALT CHECK** The stream is open on Review: `ui/src/App.vue` follows each route's collection, so `jobs.render` moves there ([D4](design.md#d4)).
  Verify: `git grep -n "live.follow" -- ui/src/App.vue` prints a line.
- [ ] 4.2 Create `ui/src/cancel.ts` with `export function holdsCancel` and `export function readsAgain` as [D4](design.md#d4) defines them, importing `collectionsOf` from `./stores/live`.
  Verify: `git grep -n "export function readsAgain" -- ui/src` prints a line.
- [ ] 4.3 Create `ui/src/cancel.test.ts` with `spec('ui:review:the-cancel-follows-the-render', …)`: a render starting and ending for the collection reads again; one for another collection, and any move on a sheet that is not approved, does not.
  Verify: `npm run test --prefix ui -- cancel` exits 0.
- [ ] 4.4 In `ui/src/views/Review.vue`, import `useLiveStore` and `readsAgain`, and add a `watch` on `live.jobs.render` that calls `reread(current.value)` when `readsAgain` answers true, as [D4](design.md#d4) states.
  Verify: `git grep -n "readsAgain" -- ui/src/views/Review.vue` prints a line.
- [ ] 4.5 In `ui/design/spec.md`, the Cancel approve bullet: before `while a render session runs for the collection, the reason says so.`, after `while a render session runs for the collection, the reason says so, and it follows the render as it starts and ends.`
  Verify: `git grep -n "follows the render as it starts and ends" -- ui/design/spec.md` prints a line.

## 5 — The save queue

Closes 0070·R20: a queued, unsent save takes the newest payload, and a failed save restores `dirty` only when none waits ([D5](design.md#d5)).

- [ ] 5.1 In `ui/src/composables/useSheet.test.ts`, give each `Call` a `refuse(message)` that answers `{ ok: false, status: 409, json: async () => ({ refusal: message }) }`.
  Add `spec('ui:save:edits-inside-a-slow-save-are-sent-as-one-request', …)`: the first save unanswered, edits each past the debounce, then the first save answers; a further request states its receipt and holds every edit, and none follows its answer.
  Verify: `git grep -n "edits-inside-a-slow-save-are-sent-as-one-request" -- ui/src/composables/useSheet.test.ts` prints a line.
- [ ] 5.2 Add `spec('ui:save:a-failed-save-leaves-nothing-to-send-again', …)` to the same file: the first save is refused while a second waits, the second holds every edit, and after it answers a `flush()` sends nothing.
  Verify: `git grep -n "a-failed-save-leaves-nothing-to-send-again" -- ui/src/composables/useSheet.test.ts` prints a line.
- [ ] 5.3 In `ui/src/composables/useSheet.ts`, add `queued` to each `inFlight` entry, replace a queued save's draft in `send()`, read the draft in `write()` after its wait, and gate `dirty = true` in its catch, as [D5](design.md#d5) sketches.
  Verify: `npm run test --prefix ui -- useSheet` exits 0.

## 6 — The modal's rows

Closes 0118·S1: a cell modal's rows keep their height and the grid scrolls ([D6](design.md#d6)).

- [ ] 6.1 In `ui/src/app.css`, add `.pick--cell .pick__tiles { flex-shrink: 0; }` after the `.pick--cell figcaption` rule, with a one-line comment saying the column scrolls, not each row.
  Verify: `git grep -n "flex-shrink: 0" -- ui/src/app.css` prints a line.
- [ ] 6.2 In `tests/e2e/conftest.py`, add the constant `TENFOLD = "tenfold"` with a comment, and in `served` make its collection: one source approved with `_approved`, rendered at every seed from 1 to 10 with `_render_at`.
  Verify: `git grep -n "TENFOLD" -- tests/e2e/conftest.py` prints a line.
- [ ] 6.3 In `tests/e2e/test_render.py`, add `test_a_cell_of_ten_renders_keeps_its_rows_whole`, bound to `ui:hub:a-cell-of-ten-renders-scrolls-its-grid`, after the steps [D6](design.md#d6) lists; the commit body says why no existing test fits.
  Where Chromium starts, `uv run pytest tests/e2e/test_render.py -k rows` runs it, and CI holds it.
  Verify: `git grep -n "a-cell-of-ten-renders-scrolls-its-grid" -- tests/e2e/test_render.py` prints a line.
