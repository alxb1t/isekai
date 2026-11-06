---
bump: patch
debt: [0095·R4, 0095·R5, 0095·R6, 0095·R7, 0095·R9, 0095·R11, 0095·R12, 0095·R18, 0095·R20, 0095·R21, 0095·S6, 0096·R8, 0096·R9, 0101·R4, 0103·R7, 0097·R1, 0101·R1, 0099·R1, 0099·R2, 0101·R5, 0106·R8]
---

# 0109 — the paydown

The backlog brought back under its watch. The void, done and record cards are closed, and the small, safe ones paid.
`--color-accent`, used as text, meets AA in every Catppuccin theme. No format, verb or product moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, the cards closed, and the test cost |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | none: `skip_specs`, per [D5](design.md#d5) |

```
1 the tests    ⇧A held while Import commits · Home's edge row through Home      (e2e steps)
2 the remedy   the copy's schema remedy names --new-version
3 the accent   Latte's and Frappé's --color-accent take their ink · Latte's link rule gone · the PAIRS row
4 the record   the deleted-render row in ui/design/spec.md · D48's lead
```

## Why

**Converge reads the debt, and a finding that repeats a card counts one level worse.** Void cards inflate the
`open-backlog-cards` measure past its watch, and stale ones would turn old nits into blocking findings. The cards paid
here are each a line or a test step. The accent fails AA as text on Latte's and Frappé's surface today.

## What Changes

- **The commit-in-flight test** presses `⇧A` while the commit is held and sees no file dialog ([D1](design.md#d1)).
- **Home's edge row** is held through Home in a browser, not only through `useEdges` ([D1](design.md#d1)).
- **The copy's schema refusal** offers `review --new-version`, which writes a draft when the target already holds an
  approval ([D2](design.md#d2)).
- **Latte's and Frappé's `--color-accent`** take their `--accent-ink` value. Latte's link rule goes. `themes.test.ts`'s
  `PAIRS` checks the accent as text ([D3](design.md#d3)).
- **The UI design spec's state table** gains the deleted-render row. **D48's lead** drops Latte's link exception
  ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Each fix is required by a requirement as it stands, per [D5](design.md#d5):

- `ui` — *The app offers five themes, and the choice is kept*: "the sheet's text 4.5:1" already covers the accent as
  text; the code now meets it.
- `ui` — *Sources are chosen in the file dialog, and each shows its own upload*: "except while Import commits" gains
  a test step, not new words.
- `ui` — *A folder in the library is a collection when it holds `sources/`*: `ui:batch-folder:an-edge-row-shows-the-head`
  gains a browser step, not new words.
- `review` — *An approval is copied from another flow's approval, recording where it came from*: the refusal still
  names the field; only its remedy's command changes.

## Impact

- `isekai/pipeline/review.py`.
- `ui/src/themes.css`, `ui/src/themes.test.ts`.
- Tests: `tests/test_review.py`, `tests/e2e/test_import.py`, `tests/e2e/test_routes.py`.
- Docs: `ui/design/spec.md`, `docs/decisions.md`.
- The debt: the cards under `debt:` above, deleted by the release. The chained-source card is written at the cut.

## Not in this change

- `0070·R20`, `useSheet`'s save coalescing: waits on the next change to `useSheet`.
- `0072·R5`: needs Review on the live store.
- `0106·R1`, a delete that drops another collection's thumbnail: a design change.
- `0060·R5`, `0060·R6`, `op·pod-start-comment`: an edit to `pod_start.py` needs an image rebuild, the split image's.
- The chained-source route, `op·chained-source`: a design change, waiting on its trigger.
- `CHANGELOG.md`'s released `0.67.0` bullet (`0101·R1`): a release record, not edited.
- `.appbar__count`'s `var(--accent)` (`ui/src/app.css:2370`), under 4.5:1 on Latte's `--ground-deep`: `--accent` is
  not `--color-accent`, and the settled fix is the latter's.
