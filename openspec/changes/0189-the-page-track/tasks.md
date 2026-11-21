# The page track — tasks

Hold the hub cell's track by vitest cases on the code as it stands, then key `RUNNING` by the union of the verbs Prepare runs and narrow `wordOf` and `segmentClass` by one guard.

## Progress

- [x] 1 — Hold the track by cases, passing before a line moves · moderate
- [ ] 2 — Type the track by the union of Prepare's verbs · moderate

## 1 — Hold the track by cases, passing before a line moves

- [x] 1.1 **HALT CHECK** The premise of [D3](design.md#d3) stands: no case of `ui/src/cells.test.ts` reads the track's names.
  Verify: `git grep -n -e "wordOf" -e "segmentClass" -e "SEGMENTS" -e "RUNNING" -e "DONE" -- ui/src/cells.test.ts` prints nothing.

- [x] 1.2 In `ui/src/cells.test.ts` import `DONE`, `SEGMENTS`, `segmentClass` and `wordOf` from `./cells`, and add `spec('ui:hub:a-cells-stage-comes-from-its-run', …)` per [D3](design.md#d3), after the case bound to `ui:hub:a-click-follows-the-cells-stage`. It asserts `SEGMENTS` and `DONE` against their literal values, and, for `null` and each stage of `DONE`, that the six `segmentClass(cell(stage), undefined, i)` read `hub__segment--done` below the stage's count and `''` from it on, the counts written as literals.
  Verify: `git grep -n -F "ui:hub:a-cells-stage-comes-from-its-run" -- ui/src/cells.test.ts` prints one line.

- [x] 1.3 In the same case assert `wordOf(cell(stage), undefined)` is the stage for each stage of `DONE` but `rendered`, `''` for `cell(null)`, `rendered ×0` for `cell('rendered')`, and `rendered ×2` for `{ ...cell('rendered'), renders: 2 }`.
  Verify: `git grep -n -F "rendered ×2" -- ui/src/cells.test.ts` prints one line.

- [x] 1.4 In the same file import `RUNNING` and add `spec('ui:events:a-stages-report-reaches-the-stream', …)` per [D3](design.md#d3) and [D1](design.md#d1): `RUNNING` equals `tag` at segment 1 with `tagging…`, `caption` at 2 with `captioning…` and `sheet` at 3 with `filling the sheet…`, and each verb's segment indexes that verb in `SEGMENTS`, looped over the literal `['tag', 'caption', 'sheet'] as const`, which types both before the union and after it.
  Verify: `git grep -n -F "ui:events:a-stages-report-reaches-the-stream" -- ui/src/cells.test.ts` prints one line.

- [x] 1.5 In the same case assert, per [D2](design.md#d2): `wordOf(cell('tagged'), 'caption')` is `captioning…`; `segmentClass(cell('tagged'), 'caption', i)` over every index of `SEGMENTS` reads `hub__segment--done`, `hub__segment--done`, `hub__segment--running`, then `''` for each index after; a `sheet` cell running `sheet` has its segment 3 running, not done; a `null` cell running `tag` has only segment 1 running.
  Verify: `git grep -n -F "'caption')" -- ui/src/cells.test.ts` prints one line.

- [x] 1.6 In the same case assert a stage the table lacks, per [D2](design.md#d2): `wordOf(cell('tagged'), 'review')` is `review…` and `wordOf(cell('tagged'), 'toString')` is `toString…`; `segmentClass(cell('tagged'), 'toString', i)` marks no segment running and the segments `tagged` has done done; an empty `running` reads as none, `wordOf(cell('tagged'), '')` being `tagged`.
  Verify: `git grep -n -F "toString…" -- ui/src/cells.test.ts` prints one line.

## 2 — Type the track by the union of Prepare's verbs

- [ ] 2.1 **HALT CHECK** The premise of [D2](design.md#d2) stands: the store holds the running stage as a `string`, which `Hub.vue` passes to both functions.
  Verify: `git grep -n -F "const running = ref<Record<string, string>>({})" -- ui/src/stores/collection.ts` prints one line.

- [ ] 2.2 In `ui/src/cells.ts` add `export type PrepareVerb = 'tag' | 'caption' | 'sheet'` above `RUNNING`, with a one-line comment, and type `RUNNING`, now `Record<string, { segment: number; word: string }>`, as `Record<PrepareVerb, { segment: number; word: string }>`, per [D1](design.md#d1); its rows are not edited.
  Verify: `git grep -n -F "Record<string, { segment" -- ui/src/cells.ts` prints nothing.

- [ ] 2.3 In the same file add, after `RUNNING`, `const isPrepareVerb = (name: string): name is PrepareVerb => Object.hasOwn(RUNNING, name)` with a one-line comment, per [D2](design.md#d2). In `wordOf` read `RUNNING[running].word` when `isPrepareVerb(running)` and `` `${running}…` `` when not; in `segmentClass` test `isPrepareVerb(running)` before `RUNNING[running].segment === index`. Both keep their `string | undefined` parameter, their docstring and their example, so `Hub.vue` compiles against them unchanged.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
