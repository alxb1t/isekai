# The review's panes — design

Where `paneOf` and the panes' selectors live, and how the view reads them from there. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`Review.vue` writes the panes' selectors twice: `paneOf` asks `closest` for `.rail`, `.source`, `.renders-block` and `.form`, and `entry` queries `.rail__card--current`, `.source`, `.renders-block` and `input.fragment`. Both read the document, so vitest, which runs in node with no DOM, holds neither.

`paneOf` itself is pure over one fact: whether an element answers `closest` for a selector. `ui/src/cells.ts` already types such a target as `{ closest(selector: string): unknown } | null`. A stub that answers `closest` therefore proves `paneOf`, and `panes.ts` already holds the panes' type, their order and their keys.

## Goals / Non-Goals

- Goal: `paneOf` and the selectors of each pane live in `panes.ts`, held by a test written before the view switches.
- Goal: `Review.vue` reads both from `panes.ts`, and every class, `data-*` hook and key stays as it is.
- Non-goal: `enter`, `remember`, `paneNow` and `entry`'s reading of the last field. They read the document and the view's refs, which no test in node reaches.
- Non-goal: a requirement, a scenario, a decision, or a change to the view's one `useKeys` call.
- `CONTRIBUTING.md`'s mutation pre-flight names `isekai/` and `evaluation/`. `ui/src` is not among them, so no mutation run is a phase here.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `SELECTORS` is one table of `holds`, `entry` and an optional `within` per pane | `paneOf` and `entry` then read one spelling of each selector | two tables; keeping the literals in the view |
| [D2](#d2) | `paneOf` takes anything that answers `closest` and asks the panes ④ before the sheet | a stub proves it in node, and ④ sits inside the sheet's form | taking an `Element`; asking in `PANES` order |
| [D3](#d3) | `entry` stays in the view and reads the table | it reads the document and `lastField`, which the view owns | moving `entry` into `panes.ts` |
| [D4](#d4) | `paneOf`'s proof is steps in the existing test, bound to the scenario it already carries | an added step needs no key of its own and reaches no state of its own | a second test with the same key; a new scenario |

### D1

```ts
/** Where a pane is: `holds` is what an element inside it answers `closest` for, `entry` what
    the focus enters, and `within`, when set, what inside `entry` takes it. */
export interface PaneSelectors {
  holds: string
  entry: string
  within?: string
}

export const SELECTORS: Record<Pane, PaneSelectors> = {
  rail: { holds: '.rail', entry: '.rail__card--current' },
  source: { holds: '.source', entry: '.source' },
  sheet: { holds: '.form', entry: 'input.fragment' },
  renders: {
    holds: '.renders-block',
    entry: '.renders-block',
    within: 'button:not(:disabled), input',
  },
}
```

The sheet's `entry` is a prefix: the view adds `[data-field="<field>"]` to it, because the field is the view's.

### D2

```ts
/** The panes in the order `paneOf` asks: ④ before the sheet, whose form holds it. */
const NESTED: Pane[] = ['rail', 'source', 'renders', 'sheet']

/** Return the pane an element sits in, or null. e.g. an element inside ④ -> 'renders' */
export function paneOf(element: { closest(selector: string): unknown } | null): Pane | null {
  if (!element) return null
  for (const pane of NESTED) if (element.closest(SELECTORS[pane].holds)) return pane
  return null
}
```

The order is today's: an element inside ④ answers `closest` for `.renders-block` and for `.form`, and `renders` must win. A `document.activeElement` is an `Element`, which answers `closest`, so the view's calls need no cast beyond the one `remember` has.

### D3

`entry` keeps its name, its place and its return type, and reads the table:

```ts
function entry(next: Pane): HTMLElement | null {
  const { entry: selector, within } = SELECTORS[next]
  if (next === 'sheet') {
    const field = lastField.value ?? schema.value[0]
    return field
      ? document.querySelector<HTMLInputElement>(`${selector}[data-field="${field}"]`)
      : null
  }
  const found = document.querySelector<HTMLElement>(selector)
  if (!within) return found
  return found?.querySelector<HTMLElement>(within) ?? found
}
```

Each branch answers what today's does: the rail and the source the one element, ④ its first enabled button or input else the block, and the sheet the input of the last field, else the schema's first, else null.

### D4

The steps are `paneOf` over a stub, `inside(...held)`, that answers `closest` truthy for the selectors it is given and null for the rest. Each `holds` selector is spelled as a literal in the stub's arguments, and one last step compares `SELECTORS` whole to the literal table of [D1](#d1), so every `entry` and `within` is pinned too:

```ts
/* An element that sits inside each selector in `held`, as `closest` answers for it. */
function inside(...held: string[]) {
  return { closest: (selector: string) => (held.includes(selector) ? {} : null) }
}
```

| step | stub is inside | `paneOf` answers |
|---|---|---|
| the rail | `.rail` | `rail` |
| the source | `.source` | `source` |
| the sheet | `.form` | `sheet` |
| ④, which sits in the sheet's form | `.renders-block` and `.form` | `renders` |
| a pane's own form | `.form` | `sheet` |
| no pane | none | null |
| no element | `null` is passed | null |

One more step takes no stub: `expect(SELECTORS).toEqual(…)` against the literal table of D1, with `within` on the `renders` row alone.

## Tests

The change adds steps to a test and no test. The key `ui:keys:review-moves-between-its-panes` carries them, so `tests/test_spec_bindings.py` needs no new binding, and `tests/test_ratchets.py` is run for the view's size, its table empty.

| layer | added | removed | the command that counts |
|---|---|---|---|
| unit, vitest | steps in the one test of `ui/src/panes.test.ts` | none | `git grep -c -E "^spec\(" -- ui/src/panes.test.ts` prints `ui/src/panes.test.ts:1` before and after |
| end-to-end | none | none | `git grep -c -F "panes" -- tests/e2e` prints nothing; the browser tests are `make e2e`, and CI runs them |

`T2`: the steps join the one test in `panes.test.ts` because a pane's pure rules are proved there, and none of them reaches the key store the test sets up. `T3`: each step builds its own stub and asserts nothing an earlier step set up. `T5`: no test is deleted or merged, so the `I16` table is empty.

## Dependencies

None.

## Risks / Trade-offs

- The table's text is now a second place a class name appears, besides the templates and `css/`. A renamed class turns the stub's literals red in vitest, which the gate runs, but a template's class is not read by the test.
- `moveRow` keeps its own `input.fragment[data-field=…]` literal, and `fourStops` its own `.renders-block`. They are not a pane's entry, and the view's other readers are out of this change.
- No test in node reaches `entry`, so the browser tests, which CI runs, hold the focus the table gives.

## Verdict

Feasible: `paneOf` and the table are pure, `cells.ts` types the same stub, and the view's other code is untouched.
