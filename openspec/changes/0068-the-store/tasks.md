# Tasks — 0068 the store

The live store, the stream it follows, the batch store, then the import and the cards, per [design](design.md).
Every new pytest test carries `@pytest.mark.spec`, and every new vitest test `spec("…")`, with the key its task names.

## Progress

- [x] 1 — The live store
- [x] 2 — One stream
- [x] 3 — The batch store
- [ ] 4 — The upload id and the cards

## 1 — The live store

- [x] 1.1 **HALT CHECK** — no store library is installed.
  Verify: `grep -c 'pinia' ui/package.json` prints `0`.
- [x] 1.2 Run `npm install --save-exact pinia@4.1.0 @vue/devtools-api@8.2.1` in `ui/`, and install `createPinia()` in
  `ui/src/main.ts`, per [D1](design.md#d1).
  Verify: `grep -c -E '"(pinia": "4\.1\.0|@vue/devtools-api": "8\.2\.1)"' ui/package.json` prints `2`, and `grep -c 'createPinia' ui/src/main.ts` prints `1`.
- [x] 1.3 Add `ui/src/stores/live.ts` per [D2](design.md#d2), still opening a bare `/events`; move `App.vue`,
  `Session.vue`, `RenderBar.vue`, `RenderDialog.vue`, `Hub.vue`, `Renders.vue` and `useRenderOffer.ts` onto it; delete
  `ui/src/composables/useLive.ts`.
  Verify: `test -e ui/src/composables/useLive.ts` exits 1, `grep -rc 'stopJob()' ui/src/views` prints `0` for each file, and `uv run python -m tools.typecheck_ui` exits 0.

## 2 — One stream

- [x] 2.1 **HALT CHECK** — the hub and the import sheet open streams of their own.
  Verify: `grep -c 'new EventSource' ui/src/views/Hub.vue ui/src/components/ImportSheet.vue` prints `1` for each file.
- [x] 2.2 Add `follow` and `listen` to `ui/src/stores/live.ts` per [D3](design.md#d3); follow the route's batch in
  `ui/src/App.vue`; take the hub's snapshot and `cell` events through `listen` in `ui/src/views/Hub.vue`.
  Verify: `grep -c 'new EventSource' ui/src/views/Hub.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.3 Follow the import's staging id in `ui/src/components/ImportSheet.vue`, its tiles read from the live store's
  `files`, per [D3](design.md#d3).
  Verify: `grep -c 'new EventSource' ui/src/components/ImportSheet.vue` prints `0`, and `uv run pytest -q tests/e2e/test_import.py` exits 0.
- [x] 2.4 Bind `ui:events:one-stream-follows-the-batch-and-the-import` in a new `ui/src/stores/live.test.ts`, with
  `EventSource` stubbed.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'one-stream-follows-the-batch-and-the-import' ui/src/stores/live.test.ts` prints `1`.
- [x] 2.5 Say the page's one stream names its batch and its open import, and opens again when either changes, in
  `ui/design/spec.md` §8 and the `/events` bullet of `isekai/interface/ui/README.md`.
  Verify: `grep -c 'opens again' ui/design/spec.md isekai/interface/ui/README.md` prints `1` for each file.

## 3 — The batch store

- [x] 3.1 **HALT CHECK** — the Render offer is a composable.
  Verify: `test -e ui/src/composables/useRenderOffer.ts` exits 0.
- [x] 3.2 Add `ui/src/stores/batch.ts` per [D4](design.md#d4), its offer requests numbered; open it on the route's
  batch in `ui/src/App.vue`; delete `ui/src/composables/useRenderOffer.ts`.
  Verify: `test -e ui/src/composables/useRenderOffer.ts` exits 1, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 3.3 Move `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue` and `useQueue` in `ui/src/composables/useQueue.ts`
  onto the batch store per [D5](design.md#d5).
  Verify: `grep -c 'await hub(' ui/src/views/Hub.vue ui/src/composables/useQueue.ts` prints `0` for each file, and `uv run pytest -q tests/e2e` exits 0.
- [x] 3.4 Rewrite `ui/src/composables/useQueue.test.ts` against the batch store; bind `ui:render:a-stale-offer-is-dropped`
  in a new `ui/src/stores/batch.test.ts`.
  Verify: `uv run python -m tools.test_ui` exits 0, and `grep -c 'a-stale-offer-is-dropped' ui/src/stores/batch.test.ts` prints `1`.
- [x] 3.5 Say `BarState.rendering` is this batch's session in `ui/src/bars.ts`, and that a row's versions run oldest
  to newest in the header comment of `ui/src/views/Renders.vue`, per [D7](design.md#d7).
  Verify: `grep -c 'A render session running\. \*/' ui/src/bars.ts` prints `0`, and `grep -c 'its images from' ui/src/views/Renders.vue` prints `0`.

## 4 — The upload id and the cards

- [ ] 4.1 **HALT CHECK** — the reader keys its files by upload name.
  Verify: `grep -c 'self._files\[name\] = state' isekai/pipeline/importing.py` prints `1`.
- [ ] 4.2 Add the upload id, `Reader.seal` and the commit's seal to `isekai/pipeline/importing.py`, and the PUT's
  `upload` to `isekai/interface/ui/app.py`, per [D6](design.md#d6); read `files` by `upload` in the staging tests of
  `tests/test_ui_api.py` and in `tests/test_importing.py`.
  Verify: `grep -c 'def seal' isekai/pipeline/importing.py` prints `1`, and `uv run pytest -q tests/test_importing.py tests/test_ui_api.py` exits 0.
- [ ] 4.3 In `tests/test_importing.py`, bind `ui:sheet:two-uploads-of-one-name-keep-their-own-states` and
  `ui:sheet:an-upload-after-import-is-refused`, and rebind `test_a_read_that_raises_refuses_its_file_and_the_next_is_read`
  to `ui:sheet:a-failed-read-refuses-its-file-alone`.
  Verify: `grep -c -E 'ui:sheet:(two-uploads-of-one-name|an-upload-after-import|a-failed-read-refuses)' tests/test_importing.py` prints `3`, and `uv run pytest -q tests/test_importing.py` exits 0.
- [ ] 4.4 Key the live store's `files` by `upload` in `ui/src/stores/live.ts`, and each tile by its `upload` in
  `ui/src/components/ImportSheet.vue`, per [D6](design.md#d6).
  Verify: `grep -c 'tile.file.name === event.file' ui/src/components/ImportSheet.vue` prints `0`, and `uv run pytest -q tests/e2e/test_import.py` exits 0.
- [ ] 4.5 Name `DecompressionBombError` beside `OSError` in the `upright_thumbnail` and `upright_jpeg` docstrings in
  `isekai/shared/image.py`; bind the bomb test in `tests/test_ui_library.py` to `ui:renders:an-unreadable-image-is-refused`.
  Verify: `grep -c 'DecompressionBombError' isekai/shared/image.py` prints a number of at least `2`, and `grep -c 'spec_exempt("twin: a file past' tests/test_ui_library.py` prints `0`.
- [ ] 4.6 Say each upload keeps its own state, and none lands once Import commits, in the import bullet of
  `isekai/interface/ui/README.md`.
  Verify: `grep -c 'upload id' isekai/interface/ui/README.md` prints a number of at least `1`, and `uv run pytest -q tests/test_docs.py` exits 0.
