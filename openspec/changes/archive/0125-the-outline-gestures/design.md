# The outline gestures — design

The page learns a press rule, a rule for placing a point, a redo and the keys for undo, redo and close, and loses its hint lines. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

- The panel (`ui/src/components/ImagePanel.vue`) turns a press into a click when it moves at most `SLOP` (4 px), into a drag of the vertex `grab` names, or into a pan.
- The outline (`OutlineStep.vue`), the render step's sketch and the pairs (`StageRender.vue`, `StagePhoto.vue`) each read the click their own way.
- `closes` needs the floor of points and a click within `RADIUS` (10 screen px) of point 0, so a near miss fell through to `added` and stacked a point under point 1.
- Undo is `Draft.past` and `Pairs.past`; nothing redoes.
- The placement screen declares no key, and `nokeys.test.ts` reads its components' source to keep it so.

```
press ─▶ ImagePanel ── gestureOf(shift, grabbed) ──▶ place │ move │ pan
                              │ place: click (shift)         │ move: drag(index)   │ pan: the view
                              ▼
        OutlineStep / StageRender sketch ─▶ placed(draft, at, scale, rules)   (polygon.ts)
        StagePhoto / StageRender pairs   ─▶ clicked │ touched                 (pairs.ts)
keydown ─▶ key store ─▶ placeCommands: undo · redo · close                    (placeKeys.ts)
```

## Goals / Non-Goals

- Goal: Shift places, the plain mouse pans, ⌘Z undoes, ⇧⌘Z redoes, `↵` and a near miss close, and the outline step says its one thing once.
- Goal: pay down [0123·S4](#d9), which sits on the step the person reaches next.
- Non-Goal: any server, run-file or library change; the hint text for the picker and the library are the next version's.
- Non-Goal: a decision in force changes. This change adds or overturns none, so `docs/decisions.md` is not edited.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The press is place, move or pan, read by `gestureOf` in `press.ts` | one rule for every panel that takes points (Q6) | a rule per component |
| [D2](#d2) | The cursor is a crosshair under Shift, the hand, the grabbing hand while a pan or move is under way | the person must see what a press will do (W8, Q8) | one cursor for all |
| [D3](#d3) | `placed` in `polygon.ts` is the Shift rule for the outline and the render sketch | the near miss stacked a hidden 16th point (W12, Q7) | patching `closes` alone |
| [D4](#d4) | The pair step: shift-click is `clicked`, a plain click is `touched` (select only) | "the pair step the same" (W8, Q6); a click on a point still selects, so *Delete* has a target | dropping selection by click |
| [D5](#d5) | `future` beside `past` in `Draft` and `Pairs`; a change clears it | redo is ⇧⌘Z (W9) | a redo stack outside the states |
| [D6](#d6) | `placeCommands` in `placeKeys.ts`: `undo`, `redo`, `close`, declared on the screen scope by the outline step and the stages that hold pairs | the keys stay declared in one place (Q8) | a listener in each component |
| [D7](#d7) | One line above the controls; the per-control *outline open* and the hint lines go | said once, as the act (W10, W11, Q9) | keeping both |
| [D8](#d8) | The first point grows and reads *close* under the pointer once the outline can close; the panel emits `hover` | W12, Q7 | marking it whenever it can close |
| [D9](#d9) | `usePlacing.load` forgets every ask when it holds another tattoo | returning to a tattoo clears its pairs, so its ask must go (Q11, 0123·S4) | keeping the pairs with the ask |

### D1

`press.ts` holds `gestureOf(shift, grabbed)`: Shift held → `place`; else a `grabbed` index → `move`; else `pan`.

- `ImagePanel` calls `grab` only when Shift is up. A `place` press that travels past `SLOP` is dropped, neither a placement nor a pan.
- A press within `SLOP` still emits `click`, and its `Press.shift` is the Shift held at the press.
- The plain click reaches the pair editor, which selects with it; the outline ignores it. A double click acts only with Shift up.

### D2

`press.ts` also holds `cursorOf(shift, active)`, `active` true while a pan or a move is under way: `crosshair` under Shift unless active, `grabbing` when active, else `grab`. `ImagePanel` keeps `shifting` from `keydown` and `keyup` of Shift on `window`, from `shiftKey` on every pointer move, and clears it on window `blur`. It sets a class on `.panel__viewport` that `app.css` maps to the cursor. The panel is the only listener; [D6](#d6) names the others.

### D3

`placed(draft, at, scale, rules)` returns the draft after a shift-click, in this order:

| the click | an open outline | a closed outline |
|---|---|---|
| within `RADIUS` of the first vertex, and `canClose` | closed | nothing |
| within `RADIUS` of any other vertex, or of the first below the floor | nothing | nothing |
| within `RADIUS` of an edge | `inserted` there | `inserted` there |
| anywhere else | `added` | nothing |

`canClose(draft, rules)` is open and at the floor. `closes` stays, and `vertexAt` and `inserted` keep their behaviour. `OutlineStep.vue` and `StageRender.vue`'s sketch call `placed` and keep no copy of the rule, so the near miss is gone in both. A plain double click on a vertex still calls `removed`.

### D4

`touched(state, side, at, scale, radius)` in `pairs.ts` selects the pair of the point within reach, else returns the state.

- A shift-click calls `clicked`, whose rule is unchanged: within reach it selects and never adds, else it completes the lone pair, moves the lone point, or adds.
- "The pair step the same" reads so: Shift places, a plain press selects, pans or moves.
- The pair step has no double-click removal, as before; *Delete* removes the selected pair.

### D5

`Draft` and `Pairs` gain `future`. `changed` clears it. `undone` pushes the state it leaves onto it, `redone` pops it back, and a drag's later moves (`fresh` false) keep it. `arrived` in `pairs.ts` joins the arrival to every snapshot of `future` as it does of `past`, so neither undo nor redo drops it. `blank`, `drafted`, `none` and `held` start with `future` empty.

### D6

`placeCommands({ undo, redo, close })` in `placeKeys.ts` returns the commands `undo` on `Mod+Z`, `redo` on `⇧Mod+Z` and `close` on `Enter`. None is `inField`, so a text field keeps its own; `close` also waits while a control has focus (`isControl`), so a button keeps `↵`.

- `OutlineStep.vue`, `StagePhoto.vue` and `StageRender.vue` each call `useKeys('screen', placeCommands(…))`.
- The outline step acts on its draft. `StagePhoto` acts on `first`, with no `close`. `StageRender` acts on the sketch while one is drawn and on `second` otherwise, and `close` closes the sketch.
- The key list shows them from the declarations.
- `nokeys.test.ts` allows `useKeys` only in those files and only the ids `undo`, `redo` and `close`, allows `keydown` and `keyup` only in `ImagePanel.vue`, and still bars `useKeyStore` and `.declare(` everywhere.

### D7

`tattoos.ts` gains `closeLine(outline)`, `close the outline on its first point · N points` while the outline is open and none once closed, `1 point` for one. `OutlineStep.vue` draws it above the ink view's heading. `controlsWait` stays as the predicate that disables the controls; its text is drawn nowhere. The forward button's own reason (`outline open · N points` in `stages.ts`) stays: it says why *Next* waits, not how to close. The hint lines in `OutlineStep.vue`, `StageRender.vue` (`data-outline-hint`) and `PairList.vue` go; the crop line under the ink view keeps its class.

### D8

`ImagePanel` emits `hover` with the image point under an idle pointer, or `null` when it leaves. `OutlineStep.vue` holds it and draws the first vertex larger, with the text *close*, while `closes` holds for it at the view's scale. It shows under the pointer whether Shift is held or not.

### D9

`usePlacing.load` sets `proposalAsked` to `noAsks` in the branch that replaces the held tattoo, beside `second.value = none`.

- An answer still on its way then fails `stands`, so it is not applied.
- Returning to the tattoo finds no ask and its pairs cleared, so `due` is true.
- A step change that holds the same tattoo returns before that branch and keeps its ask.
- `ui:proposal:a-stage-with-no-pairs-asks-once` keeps its key. Its test's assertions about an ask kept across another tattoo reverse, because that kept ask is the card's fault.

## Tests

Every test is a vitest unit test in node, the lowest layer that can fail for these rules; the change adds no end-to-end test, so it adds no end-to-end run on any engine. No test runs over 5 s.

| test file | tests added or changed | scenario keys |
|---|---|---|
| `ui/src/press.test.ts` | added: place, move and pan; the crosshair, the hand and the grabbing hand | `ui:panel:shift-places-and-a-plain-press-pans`, `ui:panel:the-cursor-follows-shift-and-the-pan` |
| `ui/src/polygon.test.ts` | added: `placed` by where it lands; the near miss; redo; `canClose`; existing click tests read as shift-clicks | `ui:outline-edit:a-shift-click-places-by-where-it-lands`, `ui:outline-edit:a-near-miss-never-adds-a-vertex`, `ui:outline-edit:redo-restores-what-undo-took`, `ui:outline-edit:closing-needs-the-floor` |
| `ui/src/pairs.test.ts` | added: `touched`; redo with the arrival | `ui:pairs:a-plain-click-selects-and-places-nothing`, `ui:pairs:redo-restores-what-undo-took` |
| `ui/src/placeKeys.test.ts` | added: the keys run, the field and the button keep theirs, the key list shows them | `ui:place-keys:undo-redo-and-close-run-from-the-keys`, `ui:place-keys:the-keys-are-listed-with-the-apps` |
| `ui/src/tattoos.test.ts` | added: `closeLine` | `ui:outline-step:one-line-says-how-to-close` |
| `ui/src/composables/usePlacing.test.ts` | changed: the ask kept across another tattoo reverses | `ui:proposal:returning-to-a-tattoo-asks-again`, `ui:proposal:a-stage-with-no-pairs-asks-once` |
| `ui/src/nokeys.test.ts` | rewritten, see below | `ui:place-keys:the-screen-declares-only-undo-redo-and-close` |

The **I16** table. No test is deleted or merged. One test is rewritten, and its scenario is removed by the delta:

| test | now | carried by |
|---|---|---|
| `ui:place-keys:the-screen-declares-no-command` in `ui/src/nokeys.test.ts` | the same test, narrowed to allow the outline step and the pair stages, the ids `undo`, `redo` and `close`, and the panel's `keydown` | `ui:place-keys:the-screen-declares-only-undo-redo-and-close`, which keeps its bars on `useKeyStore`, `.declare(` and every other file's `useKeys` and `keydown` |

## Dependencies

None.

## Risks / Trade-offs

- A press under Shift that travels is dropped, so a slip of Shift's timing places nothing: the cost of a crosshair that never pans.
- The Shift cursor trusts `keydown`, `keyup`, `shiftKey` on pointer moves and `blur`; a Shift released outside the window waits for the next pointer move.
- The pair step's plain click selects, which Q6 does not say; it keeps *Delete* reachable from the image. Reversible: `touched` alone changes.
- `Enter` closing needs `isControl` to read `document`; `placeCommands` reads it through `globalThis` so a node test passes.

## Verdict

Ready to build: the gestures first, then the keys and words, each phase on a green `make check`, the last on a green gate.
