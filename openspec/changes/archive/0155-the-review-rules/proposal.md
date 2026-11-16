---
bump: patch
version: 0.87.11
after: [0154-the-review-routes]
---

# The review rules

Review's pure rules leave `ui/src/views/Review.vue` for `ui/src/lens.ts` and `ui/src/kicker.ts`, each with its test first where a scenario covers it, and the view switches to them.

Reading map: [design](design.md) holds the modules, the bindings and the rules that move untested, [tasks](tasks.md) holds the phases `lens` and `kicker`.

## Why

`Review.vue` is a large view with its rules inside its `<script setup>`, where vitest cannot import them. The series splits it so the view falls under the page's ceiling ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)); this version takes the rules a view needs no browser to hold, and the next takes its actions. Behaviour does not change: every class, `data-*` hook and key stays as it is.

## What Changes

- `ui/src/lens.ts` is new: the `Lens` type, `viewedOf` (what the viewer shows for a lens) and `photographStep` (what `⌃P` does from a lens).
- `ui/src/lens.test.ts` is new, written before the view switches, each case bound to the scenario whose text covers it.
- `ui/src/kicker.ts` is new: `kickerOf` (the sheet's status line), `clock` and `minute` (the times it shows).
- `ui/src/kicker.test.ts` is new, written before the view switches, bound the same way.
- `ui/src/views/Review.vue` imports them and loses its `Lens` type, its `viewed`, `clock`, `minute` and `kicker` bodies and the branches of `photograph`; it keeps its one `useKeys` call, its commands in today's order, and every `ref` and `computed` that feeds them.
- `tests/test_ratchets.py` lowers the `Review.vue` row to the view's new length. The row stays: the view is still over its ceiling.

## Capabilities

### New Capabilities

None. The change adds no requirement, so it carries `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- Code: `ui/src/views/Review.vue`, `ui/src/lens.ts`, `ui/src/kicker.ts`.
- Tests: `ui/src/lens.test.ts`, `ui/src/kicker.test.ts`, the `Review.vue` row of `tests/test_ratchets.py`.
- No server, spec, flow, format version or decision moves. No dependency is added.

## Not in this change

- Review's actions: reread, discard, approve, cancel and the refusal. The next version of the series takes them, and removes the view's ratchet row.
- The sheet's history (`useSheet.ts`), the panes, the lens' DOM code (`openLens`, `closeLens`, `toggleLens`) and the chips.
- A child component, a key's declaration, any class or `data-*` hook, and the CSS.
- A scenario or a requirement: a patch adds none.
