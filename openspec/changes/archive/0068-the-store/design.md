# Design — 0068 the store

How the page holds one stream and one copy of its batch, and how each upload keeps its own state.
**Verdict: feasible** — the server already serves a batch and an import on one stream; the page stops opening three.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `7c1eba3` (`v0.41.0`):

- **The streams:** `useLive` opens `/events` (`ui/src/composables/useLive.ts:20`); `Hub.vue` opens `?batch=`
  (`ui/src/views/Hub.vue:358`); `ImportSheet.vue` opens `?staging=` (`ui/src/components/ImportSheet.vue:136`). The
  route takes both parameters and snapshots both (`isekai/interface/ui/app.py:523-545`); `events.stream` filters
  `cell` by batch and `file` by staging (`isekai/interface/ui/events.py`). `ui/design/spec.md:419` says one stream.
- **The batch, three times:** `Hub.vue` holds `info` (`:53`, `:396`) and the running and refused cells (`:45-47`);
  `useQueue.load` fetches `hub()` for Review (`ui/src/composables/useQueue.ts:83-90`); `Renders.vue` fetches
  `renders()` (`:198`, `:205`). `useRenderOffer` serves the hub and Renders (`ui/src/composables/useRenderOffer.ts:12`).
- **`useLive()` callers:** `App.vue`, `useRenderOffer.ts`, `RenderBar.vue`, `RenderDialog.vue`, `Session.vue`,
  `Hub.vue`, `Renders.vue`. `stopJob()` is called at `Hub.vue:258` and `Session.vue:57`; `checkBilling()` at
  `Session.vue:65`. `main.ts` installs only the router.
- **The import:** `Reader._files` is keyed by upload name (`isekai/pipeline/importing.py:246`); the sheet gives an
  event to the first unread tile of that name (`ImportSheet.vue:148-166`). `Imports.commit` checks `refuse_unread`
  and commits while the reader runs (`importing.py:297-304`); its class docstring says the reader stops first
  (`:263-268`). The PUT answers `{"file", **state}` (`app.py:355-367`).
- **The 0067 cards:** `ui/src/bars.ts:18`; `useRenderOffer.ts:18-24`, `:36-38`; `ui/src/views/Renders.vue:16-17`;
  `isekai/shared/image.py:611`, `:624`; `tests/test_ui_library.py:398`.
- **Vitest** runs in node, each test stubbing what it reaches (`ui/vitest.config.ts`); `spec("…")` binds
  (`ui/src/test/spec.ts`).

| measured at the cut | value | command |
|---|---|---|
| vitest tests | 8 | `cat ui/src/*.test.ts ui/src/composables/*.test.ts \| grep -c "^spec("` |
| e2e tests | 21 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| tests in `tests/test_importing.py` | 22 | `grep -c "def test_" tests/test_importing.py` |
| tests in `tests/test_ui_api.py` | 63 | `grep -c "def test_" tests/test_ui_api.py` |

## Goals / Non-Goals

**Goals:** one stream per page; one copy of the open batch; every batch screen live; each upload its own state.
**Non-Goals:** a server stream API; per-batch store instances; moving per-screen state into stores.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `npm install --save-exact pinia@4.1.0 @vue/devtools-api@8.2.1` in `ui/`; `main.ts` installs `createPinia()` | Pinia approved; its required peer named, not implied | `^` ranges |
| [D2](#d2) | `ui/src/stores/live.ts`, `useLiveStore`, a setup store: `job`, `billing`, `loaded`, `now`, `files`; `renderRunning`; `stop()`, `checkBilling()`; `prepareTotals`, `renderTotals`; the only `EventSource`; `listen(kind, handler)` for another store's events. `useLive.ts` is deleted | one owner of the stream and the slot | a store per event kind |
| [D3](#d3) | `follow({ batch, staging })` opens the stream again naming both, only when either changes; `App.vue` follows the route's batch; `ImportSheet.vue` follows its staging id while open, then `null` | each connect snapshots, so nothing is lost; no server change | a server-side subscribe call |
| [D4](#d4) | `ui/src/stores/batch.ts`, `useBatchStore`, a setup store for the open batch: `name`, `hub`, `running`, `refusals`, `renders`, `offer`, `dialog`, `rendering`; `open(batch)` resets on another batch; it takes the snapshot's hub and `cell` events through `listen`; a job's end reads the hub, the renders if loaded, and the offer again; each offer request is numbered and an older answer dropped. `useRenderOffer.ts` is deleted | one copy; `0067·R12` | instances per batch id |
| [D5](#d5) | per screen: the hub's focus, selection, viewer and sheets; Review's `useSheet`, `useApproval`, `useVocabulary`; `useQueue` reads `useBatchStore().hub`, its `load` calling `reloadHub`; `queue`, `firstFlow`, `after` stay functions | no other screen shares them | a store per composable |
| [D6](#d6) | `Reader.put` names each upload `u1`, `u2`, … and returns `{upload, file, state}`; `files()` and each event are keyed by `upload`; `Reader.seal()` refuses while a file is unread, else refuses every later `put`; `Imports.commit` seals, commits, and unseals on a refusal; the sheet keeps each tile's `upload` and reads its state from `files` | `0064·R3`, `0064·R2` | a client-made id |
| [D7](#d7) | `0064·R10`: the read-failure test bound to `ui:sheet:a-failed-read-refuses-its-file-alone`; `0067·R10`: `BarState.rendering` says this batch's session; `0067·R11`: `Renders.vue` says its versions run oldest to newest; `0067·R13`: both docstrings name `DecompressionBombError`; `0067·R14`: the bomb test bound to `ui:renders:an-unreadable-image-is-refused` | the cards' fixes | |

### D3

```
/                 follow({batch: null,  staging: null})  ─▶ /events
/b/a/hub          follow({batch: 'a',   staging: null})  ─▶ /events?batch=a
  Add sources…    follow({batch: 'a',   staging: 's1'})  ─▶ /events?batch=a&staging=s1
  sheet closed    follow({batch: 'a',   staging: null})  ─▶ /events?batch=a
/b/a/renders      unchanged                               ─▶ no reconnect
```

### D6

```
PUT …/files/IMG_1.jpg ─▶ {upload: "u1", file: "IMG_1.jpg", state: "waiting"}
PUT …/files/IMG_1.jpg ─▶ {upload: "u2", file: "IMG_1.jpg", state: "waiting"}
event file {upload: "u2", state: "refused", …}   ─▶ the tile holding u2
commit ─▶ seal (refused while unread) ─▶ commit ─▶ close;   a put after seal is refused
```

**Erratum, archived 0067:** `openspec/changes/archive/0067-hub-and-renders/proposal.md:9` and `:51` say a Renders row
runs its *images* oldest to newest; its *versions* do, each version's seeds in seed order. The archive is frozen; this
note is the correction.

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · vitest | `ui:events:one-stream-follows-the-batch-and-the-import`, `ui:render:a-stale-offer-is-dropped` | `ui:approval:a-re-opened-input-is-not-counted-approved`, against the batch store | `ui/src/stores/live.test.ts`, `ui/src/stores/batch.test.ts`, `ui/src/composables/useQueue.test.ts` |
| unit · pytest | `ui:sheet:two-uploads-of-one-name-keep-their-own-states`, `ui:sheet:an-upload-after-import-is-refused` | `test_a_read_that_raises_refuses_its_file_and_the_next_is_read`, rebound to `ui:sheet:a-failed-read-refuses-its-file-alone`; the bomb test, bound to `ui:renders:an-unreadable-image-is-refused`; the staging tests, read by `upload` | `tests/test_importing.py`, `tests/test_ui_library.py`, `tests/test_ui_api.py` |
| e2e | none | none | the suite stays the regression net |

**End-to-end runs added:** none. One stream and the stale offer are store logic, held at the vitest layer (T1); the
upload id and the seal are the reader's, held at pytest's.

**Removed or merged:** none.

## Dependencies

- `pinia` `4.1.0`, exact — the stores.
- `@vue/devtools-api` `8.2.1`, exact — Pinia's required peer.

Both go in `ui/package.json`'s `dependencies`; `ui/package-lock.json` pins what they bring: `nostics`,
`@vue/devtools-kit`, `@vue/devtools-shared`, `birpc`, `hookable`, `perfect-debounce`.

## Risks / Trade-offs

- **[Risk]** a reconnect drops an event between the old stream and the new → the new one's snapshot carries the job
  slot, the hub and the files whole.
- **[Risk]** a store read outside a component's setup finds no active Pinia → `main.ts` installs it before mount; each
  store test calls `setActivePinia(createPinia())`.
- **[Trade-off]** the stream reconnects when an import opens and closes → one short reconnect, against two streams
  held for the sheet's life.

## Verdict

**Feasible.** The server is unchanged except the reader's upload id and seal; the page moves its state into two
stores and opens one stream.
