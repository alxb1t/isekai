# Tasks — 0099 the eighth walkthrough

The cards, then `⇧A`, then the edges, per [design](design.md). Each new test or step carries the `spec` key its task
names.

## Progress

- [x] 1 — The cards
- [x] 2 — ⇧A
- [x] 3 — The edges

## 1 — The cards

- [x] 1.1 In `ui/src/staging.ts`, take `Phase` and `Tile` over from `ui/src/components/ImportSheet.vue`, give `removal`
  its `leaving` parameter, its `phase` still a `string`, and add `handOff` and `requeue`, per [D1](design.md#d1),
  [D2](design.md#d2), [D3](design.md#d3).
  Verify: `grep -n -e '^export type Phase' -e '^export interface Tile' -e '^export function handOff' -e '^export function requeue' -e 'leaving = false' ui/src/staging.ts` prints a line for each.
- [x] 1.2 In `ImportSheet.vue`, delete its own `Phase` and `Tile`, import `Tile` from `../staging`, guard `remove()` by
  `leaving`, call `handOff` in `remove()` and `requeue` in `settle()`, and drop `heir`, `orphans` and `StagedFile` from its imports,
  per [D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3).
  Verify: `grep -n -e 'leaving.has(one.key)' -e 'handOff(tiles.value, one)' -e 'requeue(tiles.value)' ui/src/components/ImportSheet.vue` prints a line for each.
- [x] 1.3 In `ui/src/staging.test.ts`: under `ui:sheet:a-chosen-file-is-removed-alone`, `removal(…, true)` is `null`;
  under `ui:sheet:a-removed-files-copy-keeps-it`, `handOff` gives a copy the upload, result and `asIs` and returns
  `null`, else `'b.jpg'`, and `requeue` clears and queues a lone copy, leaving a held one as it was.
  Verify: `npm --prefix ui run test -- src/staging.test.ts` exits 0.

## 2 — ⇧A

- [x] 2.1 In `ImportSheet.vue`, add the `add-files` command and the hint on *Add files…*, per [D4](design.md#d4),
  importing `shifted` from `../stores/keys`.
  Verify: `grep -n -e "id: 'add-files'" -e 'KeyHint command="add-files"' ui/src/components/ImportSheet.vue` prints a line for each.
- [x] 2.2 In `tests/e2e/test_import.py`, `_choose` answers the mount's chooser with `set_files([])`, then takes the chooser
  from `page.keyboard.press("Shift+A")`; `test_each_chosen_file_shows_its_upload_then_its_result` gains the key
  `ui:sheet:shift-a-opens-the-file-dialog` and `expect(…"Add files…")).to_contain_text("⇧A")`.
  Verify: `grep -n -e 'press("Shift+A")' -e 'ui:sheet:shift-a-opens-the-file-dialog' tests/e2e/test_import.py` prints a line for each.
- [x] 2.3 In `ui/design/spec.md`, J1·4's `            [ Add files… ] ┐` → `         [ Add files… ⇧A ] ┐`, and §7's
  `| dialogs |` row's `esc cancel, held while an import commits` → `esc cancel, held while an import commits · ⇧A Add
  files…, in the import sheet`.
  Verify: `grep -n -F -e '[ Add files… ⇧A ] ┐' -e 'commits · ⇧A Add files…, in the import sheet' ui/design/spec.md` prints a line for each.

## 3 — The edges

- [x] 3.1 Add `ui/src/composables/useEdges.ts` per [D5](design.md#d5), and `useEdges.test.ts` beside it under
  `ui:batch-folder:an-edge-row-shows-the-head`: over stubs, row 0 of 3 scrolls the page to its top, row 2 to its
  `scrollHeight`, row 1 neither, and each then scrolls its cell `nearest` (`invocationCallOrder`).
  Verify: `npm --prefix ui run test -- src/composables/useEdges.test.ts` exits 0.
- [x] 3.2 Reveal a key's move by `useEdges` in `ui/src/views/Hub.vue` and `ui/src/views/Home.vue`, per
  [D6](design.md#d6).
  Verify: `grep -c 'useEdges(() => page.value)' ui/src/views/Hub.vue ui/src/views/Home.vue` prints `ui/src/views/Hub.vue:1` and `ui/src/views/Home.vue:1`.
- [x] 3.3 In `tests/e2e/test_prepare.py`'s `test_a_tick_assigns_the_flow_and_survives_a_reload`, add
  `@pytest.mark.spec("ui:hub:an-edge-row-shows-the-head")` and a last step: `page.set_viewport_size({"width": 1280,
  "height": 300})`, `j` pressed twice, *Add sources…* `not_to_be_in_viewport()`, `k` pressed twice, `to_be_in_viewport()`.
  Verify: `grep -n -e 'ui:hub:an-edge-row-shows-the-head' -e 'set_viewport_size' tests/e2e/test_prepare.py` prints a line for each.
