# The hub's rules — design

Where each of `Hub.vue`'s pure rules lands, and which test holds it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`ui/src/views/Hub.vue` declares its rules in its plain script block and its setup block. The plain block holds `toPrepare` and `prepareButton`, which the test this change deletes, `ui/src/views/Hub.test.ts`, imports from the view.

The setup block holds the stage track's tables `SEGMENTS`, `DONE` and `RUNNING`, the cell's `word`, `segment` and `hint`, `reviewable`, `stem`, `cell` and the `changes` rule. Each reads a cell, a source or the store's running map, and no more.

`ui/src/bars.ts` already holds the Prepare bar's rules (`bar`, `prepared`, `held`) and `ui/src/cells.ts` the cell's (`action`, `pending`, `locked`, `ready`). Both are plain modules a vitest file imports. A vitest test binds a scenario through `spec` and has no exempt form (`tests/test_spec_bindings.py`), so a test of a moved rule names the scenario whose text covers it.

```
Hub.vue (plain block)    toPrepare, prepareButton        ──▶ bars.ts
Hub.vue (setup block)    cell, changes, reviewable, hint ──▶ cells.ts   a scenario covers them: test first
                         SEGMENTS, DONE, RUNNING, word,
                         segment, stem                   ──▶ cells.ts   no scenario covers them: untested
```

## Goals / Non-Goals

- Goal: every pure rule of the hub's cells and bar lives in `bars.ts` or `cells.ts`, and `Hub.vue` calls it.
- Goal: each rule a scenario covers has its test written before the view switches to it.
- Non-goal: any change of what the page shows. Each class, `data-*` hook, label and key is as it is, and no existing test's assertion changes.
- Non-goal: the hub's focus and selection, the ratchet row of `Hub.vue`, and any other view.
- Non-goal: a `tools.mutate` pre-flight. No line of `isekai/` or `evaluation/` moves, and `git grep -c -E '"path": "ui/src/(cells|bars|views/Hub)' -- tests/mutants.json` prints nothing, so no mutant names these files.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `toPrepare` and `prepareButton` move to `bars.ts`; the case of `Hub.test.ts` moves to `bars.test.ts` unchanged and the file is deleted | Q136: the functions sit beside the bar's other rules, and a test sits beside its module | keeping the plain script block for a test |
| [D2](#d2) | The cell's rules go to `cells.ts` as pure functions of a source and a cell, and the tables beside them | Q132: `cells.ts` holds `action`, `pending` and `ready` already, and a new module would split the cell's rules | a new `track.ts` for the stage track |
| [D3](#d3) | A rule a scenario covers has its test first, bound to that scenario; a rule none covers moves untested | Q134: vitest cannot bind a test to a scenario whose text does not cover it, and a patch adds no requirement (Q5) | a test bound to a scenario that does not cover the rule; a new scenario |
| [D4](#d4) | The view keeps `word`, `segment` and `hint` as one-line wrappers that read the store's running map | Q132 and Q135: the template, its hooks and its keys stay as they are, and the store's map stays the view's | passing the map into every template call |
| [D5](#d5) | `Hub.vue` stays past its ceiling, so its row stands, and the row's number is lowered to the file's lines | [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets): a row goes with its offender, and the focus's move removes the file's last excess | removing the row here |

### D1

`bars.ts` imports `noun` from `./words` and declares `toPrepare(sources, collection)` and `prepareButton(changes)` with the bodies and comments `Hub.vue` holds now. `Hub.vue` imports them from `../bars` and imports `noun` for its template, which the plain block imported. The case of `Hub.test.ts`, a file this change deletes, becomes a `spec('ui:prepare:the-bar-names-its-photographs', …)` of `bars.test.ts`, its assertions as they are.

### D2

These land in `cells.ts`, beside `action`, `pending` and `ready`.

| name | does | replaces in `Hub.vue` |
|---|---|---|
| `cellOf(source, flow)` | the source's cell for a flow, `EMPTY_CELL` when it has none | `cell` |
| `changesOf(sources, flows)` | each pending cell as `{ source, flow }`, source by source, flow by flow | the body of `changes` |
| `reviewable(source, cell)` | whether the source has a run (a digest) and the cell a status | `reviewable` |
| `hintOf(source, cell)` | the focused cell's hint: `action`'s, held to `reviewable` for a review or a sheet, else null | the body of `hint` |
| `wordOf(cell, running)` | the word a cell shows: the running stage's word, `rendered ×n`, or the stage | the body of `word` |
| `segmentClass(cell, running, index)` | `hub__segment--running`, `hub__segment--done` or the empty string for one segment | the body of `segment` |
| `stem(name)` | a file's name without its extension | `stem` |

`SEGMENTS`, `DONE` and `RUNNING` are exported with the values `Hub.vue` holds now. `running` is the stage running in the cell, from the store's map, or `undefined`.

### D3

| rule | scenario that covers it | test |
|---|---|---|
| `toPrepare`, `prepareButton` | `ui:prepare:the-bar-names-its-photographs` | the moved case, in `bars.test.ts` |
| `changesOf`, `cellOf` | `ui:prepare:prepare-takes-the-cells-with-no-sheet`: Prepare names the assigned and the tagged cells and no sheeted or unreadable one | a new `spec` in `cells.test.ts`, written first |
| `hintOf`, `reviewable` | `ui:hub:a-click-follows-the-cells-stage`: a click opens Review on a sheet or a draft | steps added to the test of that key in `cells.test.ts`, written first |

The stage track's tables, `wordOf`, `segmentClass` and `stem` have no scenario: the hub requirement names the stage a cell carries and the name a source shows, and no scenario says the segments, the running words or the extension's removal. They move untested and are named here. The browser tests under `tests/e2e/` reach the track and the names through the page, and CI runs them after the merge.

The brief's acceptance reads "each moved rule with a test written before the view switched to it". Read with Q134, it holds for each rule a scenario covers.

### D4

```
word(source, flow)    ──▶ wordOf(cellOf(source, flow), running.value[key(source, flow)])
segment(source, flow, index) ──▶ segmentClass(cellOf(source, flow), running.value[key(source, flow)], index)
hint(source, flow)    ──▶ hintOf(source, cellOf(source, flow))
```

The view imports `cellOf` as `cell`, so each call site reads as it did. A wrapper stays a `function` with its own return line, as the closures are, so the view's length is the one the evidence table of `## Tests` expects. The template, each class, each `data-*` hook, the one `useKeys` call and the order of its commands are not touched.

### D5

The ratchet checks a row by its name and the table's count, not by the number beside it. The number is lowered to the file's lines after the move, so the table still names today's size.

A premise holds the plan: the view lands above its ceiling, so the row stands. If it lands at the ceiling or under, [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) removes the row in this change, and the build halts at the `HALT CHECK` of phase 3.

## Tests

The change adds a vitest test for `changesOf`, moves the one case of `Hub.test.ts`, and adds steps to one existing test. It adds no pytest test and no end-to-end run. Counts are before → after.

| what | before → after | command |
|---|---|---|
| `spec` tests in `ui/src/cells.test.ts` | 10 → 11 | `git grep -c "^spec(" -- ui/src/cells.test.ts` |
| `spec` tests in `ui/src/bars.test.ts` | 7 → 8 | `git grep -c "^spec(" -- ui/src/bars.test.ts` |
| `spec` tests in `ui/src/views/Hub.test.ts` | 1 → file deleted | `git grep -c "^spec(" -- ui/src/views/Hub.test.ts` |
| end-to-end runs added | 0 | tests × engines: none added |
| lines of `ui/src/views/Hub.vue` | 671 → about 620, past the ceiling of 600 | `git grep -c "" -- ui/src/views/Hub.vue` |

`tests/test_ratchets.py` changes in its data alone, the number of the `Hub.vue` row; no assertion changes.

- **T1:** each test is a unit test of a plain function, the lowest layer there is.
- **T2:** the `hintOf` steps extend the test of `ui:hub:a-click-follows-the-cells-stage`. `changesOf` gets a new `spec` because no vitest test binds `ui:prepare:prepare-takes-the-cells-with-no-sheet`, which a pytest test binds for the server's plan.
- **T5:** the one test the change removes is mapped below.

| removed test | carried by |
|---|---|
| `ui/src/views/Hub.test.ts`: `ui:prepare:the-bar-names-its-photographs` | `ui/src/bars.test.ts`: the same key, the same assertions |

## Dependencies

None.

## Risks / Trade-offs

- **The view lands at its ceiling or under.** Then its row is stale and `tests/test_ratchets.py` is red. The `HALT CHECK` of phase 3 stops the build; the fix is a plan amend that removes the row and lowers the table's count, per [D5](#d5).
- **The stage track's rules move untested.** A slip in `wordOf`, `segmentClass` or the tables shows only in the browser tests CI runs after the merge. Each body is moved as it stands, and `tools.typecheck_ui` holds the names and the types.
- **A moved function reads one more argument than the closure did.** `wordOf` and `segmentClass` take the running stage the closure read from the store; the wrappers pass `running.value[key(source, flow)]`, the same read.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the Prepare bar's words, the cell rules a scenario covers, and the rules none covers.
