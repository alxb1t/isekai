# The hub's rules — tasks

The phases move `Hub.vue`'s pure rules into `bars.ts` and `cells.ts`, a test first where a scenario covers the rule, then the view switches.

## Progress

- [x] 1 — The Prepare bar's words · moderate
- [ ] 2 — The cell rules a scenario covers · moderate
- [ ] 3 — The rules no scenario covers · moderate

## 1 — The Prepare bar's words

`toPrepare` and `prepareButton` go to `bars.ts` with the case that tests them, per [D1](design.md#d1).

- [x] 1.1 In `ui/src/bars.test.ts` import `prepareButton` and `toPrepare` from `./bars` and add the case of `ui/src/views/Hub.test.ts` as `spec('ui:prepare:the-bar-names-its-photographs', …)`, after the last test, its assertions unchanged.
  Verify: `git grep -n -F "the-bar-names-its-photographs" -- ui/src/bars.test.ts` prints a line.
- [x] 1.2 In `ui/src/bars.ts` import `noun` from `./words` and add `toPrepare` and `prepareButton`, their bodies and comments as `ui/src/views/Hub.vue` holds them.
  Verify: `uv run python -m tools.test_ui ui/src/bars.test.ts` exits 0.
- [x] 1.3 Delete `ui/src/views/Hub.test.ts`, the test that imports from `./Hub.vue`, its case carried by 1.1 as the `## Tests` table of [the design](design.md#tests) maps it.
  Verify: `git grep -n -F "./Hub.vue" -- ui/src` prints nothing.
- [x] 1.4 In `ui/src/views/Hub.vue` delete the plain `<script lang="ts">` block, and in `<script setup>` import `noun` from `../words` and `prepareButton` and `toPrepare` from `../bars`.
  Verify: `git grep -n -F "<script lang=" -- ui/src/views/Hub.vue` prints nothing.

## 2 — The cell rules a scenario covers

`cellOf`, `changesOf`, `reviewable` and `hintOf` go to `cells.ts`, each test first, bound as [D3](design.md#d3) says.

- [ ] 2.1 In `ui/src/cells.test.ts` add `spec('ui:prepare:prepare-takes-the-cells-with-no-sheet', …)` over `changesOf(sources, flows)`: sources `ada.jpg` and `bea.jpg`, flows `a`, `b` and `c`, cells assigned, tagged, sheet and unreadable, one flow absent from a source's `cells`. It expects `{ source, flow }` for the assigned and the tagged cells alone, source by source, flow by flow.
  Verify: `git grep -n -F "prepare-takes-the-cells-with-no-sheet" -- ui/src/cells.test.ts` prints a line.
- [ ] 2.2 In `ui/src/cells.ts` import `HubSource` and add `cellOf(source, flow)` and `changesOf(sources, flows)` as [D2](design.md#d2) lists them, `changesOf` reading `pending` of `cellOf`.
  Verify: `uv run python -m tools.test_ui ui/src/cells.test.ts` exits 0.
- [ ] 2.3 In the test of `ui:hub:a-click-follows-the-cells-stage` in `ui/src/cells.test.ts` add steps for `hintOf(source, cell)`: a sheet cell on a source with a digest and a cell with a status gives `'↵ review'`; the same cell on a source with no digest gives `null`, and so does a sheet cell with no status; an approved cell with a newest image gives `'↵ view'`; a tagged cell gives `null`. The existing steps stay as they are.
  Verify: `git grep -n -F "hintOf(" -- ui/src/cells.test.ts` prints a line.
- [ ] 2.4 In `ui/src/cells.ts` add `reviewable(source, cell)` and `hintOf(source, cell)` as [D2](design.md#d2) lists them, `hintOf` held to `reviewable` for the review and sheet actions, as `hint` in `ui/src/views/Hub.vue` is now.
  Verify: `uv run python -m tools.test_ui ui/src/cells.test.ts` exits 0.
- [ ] 2.5 In `ui/src/views/Hub.vue` import `cellOf as cell`, `changesOf`, `hintOf` and `reviewable` from `../cells`; delete the local `cell` and `reviewable`; make `changes` a `computed` over `changesOf`, `hint` a wrapper over `hintOf`, and call `reviewable(source, cell(source, flow))` in `review`, as [D4](design.md#d4) draws it.
  Verify: `git grep -n -E "function (cell|reviewable)\(" -- ui/src/views/Hub.vue` prints nothing.

## 3 — The rules no scenario covers

The stage track and the source's name go to `cells.ts` with no test, [D3](design.md#d3) naming them.

- [ ] 3.1 In `ui/src/cells.ts` import `Stage` and add the exports `SEGMENTS`, `DONE`, `RUNNING`, `wordOf(cell, running)`, `segmentClass(cell, running, index)` and `stem(name)`, each body as `ui/src/views/Hub.vue` holds it, `running` the stage name the cell runs, `undefined` when none runs.
  Verify: `git grep -c -E "^export (const (SEGMENTS|DONE|RUNNING)|function (wordOf|segmentClass|stem))" -- ui/src/cells.ts` prints `ui/src/cells.ts:6`.
- [ ] 3.2 In `ui/src/views/Hub.vue` delete `SEGMENTS`, `DONE`, `RUNNING` and `stem`, make `word` and `segment` wrappers over `wordOf` and `segmentClass` reading `running.value[key(source, flow)]`, import the new names, and drop the imports now unused (`EMPTY_CELL`, `HubCell`, `Stage`).
  Verify: `git grep -n -E "(const|function) (SEGMENTS|DONE|RUNNING|stem)" -- ui/src/views/Hub.vue` prints nothing.
- [ ] 3.3 In `BIG_UI_FILES` of `tests/test_ratchets.py` change the row `"ui/src/views/Hub.vue": 671` to the lines `git grep -c "" -- ui/src/views/Hub.vue` prints, as [D5](design.md#d5) says.
  Verify: `git grep -n -F '"ui/src/views/Hub.vue": 671' -- tests/test_ratchets.py` prints nothing.
- [ ] 3.4 **HALT CHECK** `ui/src/views/Hub.vue` is still past its ceiling, so its row stands: a file that falls to its ceiling makes its row stale and this red.
  Verify: `uv run pytest tests/test_ratchets.py` exits 0.
