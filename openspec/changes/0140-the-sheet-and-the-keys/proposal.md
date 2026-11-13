---
bump: patch
after: [0139-the-boundary]
debt: [0124·S2]
---

# The sheet and the keys

The sheet's saves, the key dispatch and the chooser's decision are held by tests that never reach their lines, and Cancel approve can stay stale after a render ends during the first read. This change teaches the mutation replay to run vitest, holds each of those lines, fixes the stale cancel, and pins it all with mutants.

Reading map: [design](design.md) holds the decisions, the exact code of the fix and the tests, [tasks](tasks.md) its phases, [mutants](mutants.json) the entries phase 5 replays.

## Why

The audit ran each test against mutants of the page's source. The findings below survived: the vitest suite stays green with the line gone, and the replay that proves it runs pytest alone.

| finding | what it leaves unheld |
|---|---|
| `VT-14` | a lone failed save is never sent again, so an approval after it states the draft without the last edit |
| `VT-15` | a refused save and a failed read show nothing |
| `VT-16` | the debounce is held from above alone, so a burst of typing could be one write per key |
| `VT-17` | a screen's command could lose a shared key to the keys offered everywhere, and a textarea or an editable element is no text field |
| `VT-19` | whether Review opens the chooser is decided by a function no test calls |
| `VT-8` and card `0124·S2` | a render that moves while the sheet is being read is dropped, so *Cancel approve* is offered stale against its requirement |
| `VT-18` | `api.ts`'s refusal, per-image draft refusal and box header are held by no test; `0137-the-server` writes the tests and leaves the mutants to the replay |

## What Changes

- `tools/mutate.py` runs an entry under vitest when it names `"runner": "vitest"`, and links `ui/node_modules` into the copy for those entries alone.
- Tests resend a lone failed save, show a refusal and a failed read, hold the debounce from below, run the screen before everywhere, take a textarea and an editable element as text fields, and call `chooses`.
- `ui/src/cancel.ts` and `ui/src/views/Review.vue`: a render that moves during a read is remembered and the sheet read again once the read lands, an approved one alone.
- `tests/mutants.json` gains this change's mutants and `0137-the-server`'s in `ui/src/api.ts`, replayed by `make mutants`.

Each requirement the delta touches:

- `ui` · *The page's save state is true to the requests in flight, and a pending edit is sent on leaving*: gains a scenario for a lone failed save sent again and one for a burst of edits as one save.
- `ui` · *Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet*: gains a scenario for a refused save shown, one for a sheet that cannot be read, and one for a render that moves during the read.
- `ui` · *Each command has one key, declared once, and none fires while typing*: gains a scenario for a screen taking the keys before everywhere.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: scenarios under existing requirements.

## Impact

- Product: `ui/src/cancel.ts`, `ui/src/views/Review.vue`.
- Tools: `tools/mutate.py`.
- Tests: `tests/test_mutate.py`, `ui/src/composables/useSheet.test.ts`, `ui/src/stores/keys.test.ts`, `ui/src/composables/useQueue.test.ts`, `ui/src/cancel.test.ts`; `tests/test_ratchets.py` is run, not edited, as `ui/src/views/Review.vue` sits at its ceiling.
- Docs: `CONTRIBUTING.md` says how a vitest mutant is named.
- Specs: the `ui` capability, by the delta of this change.
- Waits for `0139-the-boundary`, and through it `0137-the-server`: they append to `tests/mutants.json`, and phase 5 holds `0137-the-server`'s mutants of `ui/src/api.ts` by the vitest it writes.
- A patch by [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves, no verb or flag changes, each fix is required by a requirement that stands, and a sheet's fields, the prompt and the image are the same for the same inputs. The fix changes when the page reads an approved sheet again: once more after a render moved during its read.

## Not in this change

- The browser's own tests: the guard on page errors, the key list's held focus, a command typed in a tag field, pane moves, and *Approve* pressed while a save is held. They wait for the version that holds the page in a browser, which CI proves after the merge (Q63).
- The sheet's undo, redo, remove and ④, and the `⌥` key: no requirement names them, so the spec audit takes them.
- A save that fails after the person switched sheet drops the edit and shows nothing: the refactor's page version fixes it, as no requirement demands the switch's case.
- `VT-11`, `VT-13`, and the browser suite's splits, merges and shared state: the sweep after the refactor's last version.
- `VT-12`, the tattoo screens' keys: *e2e tattoo*.
- Any package: vitest and the runtime are locked already.
