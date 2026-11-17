# The review's actions — design

Review's actions move into one composable that reads the page through getters, with its test written before the view switches to it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`Review.vue` holds the actions an operator takes on a sheet in its `<script setup>`. Each reads the same things: the collection, the flow, the open sheet's digest, the sheet, the queue and the approval.

```
            props · current ──▶ reread ◀── approve ── sheet.flush ── approval.approve
 refused ◀──────────────────────  ▲  ▲                 (stops on a refused save)
 cancelling ◀── cancelApprove ────┘  └── discard ── sheet.flush ── discardDraft
 rereads' watchers ── live.jobs.render · sheet.loading ──▶ reread
 reread ──▶ focused · selectedChip     (the panes' and chips' state, which the view owns)
```

| measure | value | command |
|---|---|---|
| lines of the view before | 659 | `wc -l ui/src/views/Review.vue` |
| the ceiling and the listed row | 600 and 659 | `git grep -n -E "UI_FILE_LINES = |ui/src/views/Review.vue" -- tests/test_ratchets.py` |
| the view's `useKeys` calls | 1 | `git grep -c -h -F "useKeys(" -- ui/src/views/Review.vue` |

The moved code is far longer than the call that replaces it, and the view lands under the ceiling. The ratchet test measures it.

vitest cannot import a view's setup locals. A rule in a composable can be run in an effect scope with `fetch` stubbed, as `useSheet.test.ts` does. The unit scenarios that already name the actions' rules have no test of the actions themselves: `useSheet.test.ts` re-writes Review's `approve` in its own test, and `cancel.test.ts` holds the logic of `rereads` and none of its wiring.

## Goals / Non-Goals

**Goals**

- `Review.vue` falls under the page's ceiling and its ratchet row goes ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).
- The rules the actions hold run in a test on the unit layer, written before the view switches.
- Behaviour, DOM, keys and requests are as today.

**Non-Goals**

- A change to `useSheet`, `useApproval`, `useQueue` or `cancel.ts`.
- A key: the composable declares none.
- A test of Cancel approve's and Discard's own bodies on the unit layer ([D6](#d6)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `useReviewActions(page)` takes getters for the collection, the flow and the open digest, the sheet, a queue that can `load`, the approval and a `settled` callback; it returns `refusal`, `cancelling`, `approve`, `cancelApprove`, `discard` and `forget` | an action reads the page and changes nothing the view owns but through `settled` | passing `props` whole; returning `reread` |
| [D2](#d2) | The view calls it where its `rereads` line stands, and destructures what it returns | the rereads' watchers are created before `watch(current)`, as today, so their order against it does not move | calling it at the top of the setup |
| [D3](#d3) | `settled` clears `focused` and `selectedChip`; the composable never sees them | the panes and the chips own them | moving the refs into the composable |
| [D4](#d4) | The view still creates `useApproval()` and passes it in; `forget` clears the approval and then the refusal, the order `watch(current)` has today | the view reads `approval.at` and `approval.working` itself | creating the approval inside the composable |
| [D5](#d5) | The composable declares no key; the view keeps its `useKeys` call, its commands in today's order | a second call is a newer layer that answers a key first | a `useKeys` call in the composable |
| [D6](#d6) | The test binds the unit scenarios that already cover a rule of the actions; Cancel approve's and Discard's own bodies move with no vitest test | an `e2e` key cannot be bound from vitest, and a patch adds no requirement | a new scenario; a `spec_exempt` form, which vitest does not have |
| [D7](#d7) | No decision is added to `docs/decisions.md` | the series' rules live in its brief and [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) already says a row goes with its offender | a decision on composables |

### D1

The composable is `ui/src/composables/useReviewActions.ts`:

```ts
import { computed, ref, watch } from 'vue'
import { cancelApproval, discardDraft } from '../api'
import { rereads } from '../cancel'
import { useLiveStore } from '../stores/live'
import type { useApproval } from './useApproval'
import type { useSheet } from './useSheet'

/** What the actions read of the page, and the callback they hand back to it. */
export interface ReviewActionsPage {
  collection: () => string
  flow: () => string
  digest: () => string
  sheet: ReturnType<typeof useSheet>
  queue: { load: () => Promise<unknown> }
  approval: ReturnType<typeof useApproval>
  settled: () => void
}

export function useReviewActions(page: ReviewActionsPage) {
  /* refused, cancelling, refusal, reread, discard, approve, cancelApprove, forget, the watchers */
  return { refusal, cancelling, approve, cancelApprove, discard, forget }
}
```

Each body is today's, word for word, with `props.collection` read as `page.collection()`, `props.flow` as `page.flow()`, `current.value` as `page.digest()`, `sheet` as `page.sheet` and the ref writes in `reread` as `page.settled()`. The comments move with their code.

| name | today | in the composable |
|---|---|---|
| `refused`, `cancelling` | refs of the view | refs of the composable; `cancelling` is returned |
| `refusal` | `approval.refusal.value ?? sheet.refusal.value ?? refused.value`, a computed | the same computed, returned |
| `reread(id)` | sets `refused` to `null`, reads the queue and the sheet, clears the panes' state, sets `refused` on a rejected queue read | the same, with `page.settled()` for the clearing; not returned |
| `discard`, `approve`, `cancelApprove` | as the view has them | as they are; `cancelApprove` calls `approval.forget()` and then `reread` |
| `forget` | `approval.forget()` then `refused.value = null`, lines of `watch(current)` | one function, the same lines in the same order |
| the watchers | `rereads(...)` and the `watch` calls on `live.jobs.render` and `sheet.loading` | the same statements, `live` from `useLiveStore()` inside the composable |

### D2

The view's call stands where `const follow = rereads(...)` stands, between the `onUnmounted` line and `watch(current, ...)`:

```ts
const { approve, cancelApprove, cancelling, discard, forget, refusal } = useReviewActions({
  collection: () => props.collection,
  flow: () => props.flow,
  digest: () => current.value,
  sheet,
  queue,
  approval,
  settled: () => {
    focused.value = null
    selectedChip.value = null
  },
})
```

The commands in `useKeys` and the template read `approve`, `cancelApprove`, `discard`, `cancelling` and `refusal` from a `const` declared below them. Each read is inside a closure or the template, which run after the setup, so no read meets the `const` before it holds a value.

### D3

`reread` ends a read by clearing the pane's focus and the chip selection. The view passes that as `settled`; the composable calls it in the place today's writes stand, after the queue and the sheet have answered and before the rejected read is shown.

### D4

`approval` stays a value of the view: `approvedAt` reads `approval.at`, and the approve bar reads `approval.working`. `watch(current)` calls `forget()` where it calls `approval.forget()` and sets `refused` to `null` now; those lines are adjacent today, so the order holds.

### D5

`git grep -n -F "useKeys" -- ui/src/composables/useReviewActions.ts` prints nothing. `Review.vue`'s `useKeys('screen', [...])` call is not edited, its commands stay in today's order, and the key store's newest layer answers first as it does now.

### D6

A vitest test binds a scenario through `spec`, with no exempt form, and an `e2e` key needs a binder under `tests/e2e/`. The unit scenarios below cover a rule the composable holds; the test binds each, and several tests may carry one key.

| key | what the composable's test shows |
|---|---|
| `ui:save:an-approval-waits-for-a-save-in-flight` | `approve()` sends the approval once the save in flight answers, stating the draft it wrote, then reads the sheet again |
| `ui:review:a-refused-save-is-shown` | on a refused save `approve()` and `discard()` send nothing and `refusal` holds the sheet's message |
| `ui:review:the-cancel-follows-the-render` | an approved open sheet is read again when `live.jobs.render` starts or ends for its collection, and an editable one is not |
| `ui:review:a-render-that-moves-during-the-read-is-read-again` | a render that moves while the sheet loads is read again once it lands approved, and not once it lands editable |

These scenarios of the `ui` spec stay with the browser, because they are `e2e`: *Approve stays on the sheet*, *a failure after approval is shown*, *Cancel approve opens the sheet again* and *Discard asks before it deletes*. The bodies of `cancelApprove` and `discard`, the `cancelling` flag and the rejected-read branch of `reread` move with no vitest test of their own; CI runs the browser tests after each merge.

### D7

`docs/decisions.md` holds no rule this version sets: the series' rules are in its brief, a composable is no decision, and [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) already removes a row with its offender. No document names `Review.vue`'s actions, `useSheet` or `useApproval`, so none is made false.

## Tests

The change adds a vitest file and no other test; it deletes and merges none. Each bound scenario is a unit scenario of the `ui` spec, so no end-to-end run is added.

| layer | added | removed | command |
|---|---|---|---|
| vitest, unit | the tests of `ui/src/composables/useReviewActions.test.ts` | none | `git grep -c -h -E "^spec\(" -- ui/src/composables/useReviewActions.test.ts` |
| pytest | none; `tests/test_ratchets.py` loses a row and a count | none | `git grep -n -F "BIG_UI_FILES" -- tests/test_ratchets.py` |
| end-to-end | none | none | `git grep -c -h -F "useReviewActions" -- tests/e2e` |

The harness is the hand-released `fetch` of `ui/src/composables/useSheet.test.ts`, written again in the new file. Sharing it would edit an existing test file; a later version may lift it. Every wait is `vi.advanceTimersByTimeAsync(0)`, because `useLiveStore` starts intervals that a run of all timers never ends.

| test | key | the steps it takes |
|---|---|---|
| waits | `ui:save:an-approval-waits-for-a-save-in-flight` | commit twice inside one save, `approve()`, answer each request in turn |
| refused | `ui:review:a-refused-save-is-shown` | refuse the only save, then `approve()` and `discard()` |
| follows | `ui:review:the-cancel-follows-the-render` | move the render slot with an approved sheet open, then an editable one |
| lands | `ui:review:a-render-that-moves-during-the-read-is-read-again` | move the slot while the sheet loads, land it approved, then editable |

The tests are run before the view switches: the composable stands beside the view, unused, and the suite is green.

## Dependencies

None.

## Risks / Trade-offs

- **The watchers' order.** A watcher created earlier runs earlier in a flush. D2 keeps the statements where they stand, so `watch(current)` still follows them.
- **A `const` read below its use.** Each earlier read is a closure or the template. `uv run python -m tools.typecheck_ui` refuses a read that runs at once.
- **The moved bodies are not edited.** A change of a word is a behaviour change; the diff of each moved function reads as the same text with its reads renamed.
- **A mutant of the moved code.** No entry of `tests/mutants.json` names `Review.vue`; the pre-flight of `CONTRIBUTING.md` covers `isekai/` and `evaluation/`, and this version moves nothing of them.

## Verdict

Feasible. The actions read what the page already holds, the only state of the view they change is reached through a callback, and the test of each rule that has a unit scenario is written before the view switches.
