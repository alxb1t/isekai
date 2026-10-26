# Design — 0079 the session drawer

How the running render moves from a batch's page into a drawer every screen opens, and what goes with the page.
**Verdict: feasible** — the drawer is the session page's content in the modal dialog the app already draws, read
from a store that follows the running render the live store already knows.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `63d656d` (`v0.51.0`):

- **The shell:** `⇧S` opens *the running session, else the open batch's sessions* (`sessions()`,
  `ui/src/App.vue:76–81`, declared `:95`); the Sessions tab (`:131–137`); the running render's link `● render 06:41`
  (`:140–146`). The hub's and Renders' Render bar links the session as `Session ⇧S`
  (`ui/src/components/RenderBar.vue:56–57`).
- **The routes:** `/b/:batch/sessions` (`Sessions.vue`) and `/b/:batch/sessions/:id` (`SessionPage.vue`)
  (`ui/src/router.ts:10–11`, `:36–37`); confirming a render pushes the session's route
  (`ui/src/components/RenderDialog.vue:50–54`).
- **The session page** draws a record and the render slot: the steps, Stop, the outcome, the grid
  (`ui/src/views/SessionPage.vue`); its keys at `screen` scope (`:153–164`); it reads the record through the batch
  store (`:185–195`).
- **The batch store** holds `sessions` and the shown `session` (`ui/src/stores/batch.ts:42–44`), reads them
  (`reloadSessions` `:99–118`, `showSession` `:128–131`), and re-reads them as the render moves (`:202–218`). The live
  store holds `activeSessions` and `activeRender`, the running render across batches (`ui/src/stores/live.ts:52–67`).
- **The API:** `/api/sessions/running` (`isekai/interface/ui/app.py:545`), `/api/b/{batch}/sessions` (`:556`),
  `/api/b/{batch}/sessions/{name}` (`:561`); `library.sessions` (`isekai/interface/ui/library.py:293`) and
  `library.session`, whose refusal names `/b/<batch>/sessions` (`:321–329`).
- **The keys:** the top overlay masks every layer below it (`reached`, `ui/src/stores/keys.ts:158–168`); the viewer is
  a modal `<dialog>` (`showModal`, `ui/src/components/ImageViewer.vue:111`). `Billing.vue` shares the `.session` class
  (`ui/src/views/Billing.vue:27`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_api.py` | 73 | `grep -c "def test_" tests/test_ui_api.py` |
| vitest tests | 42 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -cE "^(spec\|test\|it)\("` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** the running render one key away on every screen; nothing left of the session pages. **Non-Goals:** a
change to the render job, its records or the CLI; a finished session found again.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **the drawer's store** `ui/src/stores/drawer.ts`: `open`, `shown: {batch, id} \| null`, `record`, `photographs`; `shown` follows the live store's `activeRender` — a new render replaces it, an ended one stays until the app reloads; `record` is read by `/api/b/{batch}/sessions/{id}` on each render-slot change and each `activeSessions` change, an older answer never replacing a newer; `photographs` names each column's source from that batch's hub, read once, else the run's own photograph | the running render is the app's, not the open batch's | the batch store, keyed by the open batch |
| [D2](#d2) | **the drawer** `ui/src/components/SessionDrawer.vue`, drawn once by `App.vue`: a `<dialog>` opened by `showModal`, `width: max(50vw, 480px)` at the right, its `::backdrop` dark; a click on the backdrop closes it; its content is the session page's — the steps, Stop, the outcome, `Nothing is billing.`, the grid — moved from `SessionPage.vue`; with nothing shown, `No render running.`; its keys at `overlay` scope: `h j k l` arrows, `↵` the viewer over the focused row, `⇧I` that batch's Renders and close, `⌃;` and `Esc` close; the viewer is the `ImageViewer` modal, above it | the 0078 dialogs are modal; the top layer stacks | a plain `div` under an open viewer |
| [D3](#d3) | **the ways in:** `⌃;` — `{ code: 'Semicolon', ctrl: true }`, `inField`, `everywhere`, real `Ctrl` — toggles the drawer, masked while another dialog is open; the app bar's `●` and the Render bar's link become buttons that open it, the bar's hint `⌃;`; `RenderDialog` confirms, holds the slot, closes, and opens the drawer on the session instead of routing | one way in, from anywhere | `⇧S` |
| [D4](#d4) | **removed:** the `sessions` and `session` routes, `SessionPage.vue`, `Sessions.vue`, the Sessions tab, `⇧S` and `sessions()` in `App.vue`; `/api/b/{batch}/sessions`, `library.sessions`, `sessions` in `ui/src/api.ts`; the batch store's `sessions`, `session`, `reloadSessions`, `showSession`, `observed` and their watchers; `library.session`'s refusal `{batch} holds no session {id!r}`; the `.session` rules `Billing.vue` uses stay | nothing links to them | a redirect |
| [D5](#d5) | **the docs:** `ui/design/spec.md` — §4's session rows deleted; J2's `Session ⇧S` → `Session ⌃;`; J4's addresses `…/sessions/<id>` → `the drawer over the hub`; §7's *everywhere* `⇧S the running session, else the batch's sessions` → `⌃; the render drawer, from a field too`, its *Session* row named *Drawer*; `docs/data-flow.md`'s render line `/b/<batch>/sessions/<id>` → `the render drawer` and `the app's sessions are read from it` → `the app's drawer reads it` | the docs name what is there | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · vitest | `ui:sessions:the-drawer-keeps-the-last-session` | `ui:sessions:the-selected-record-keeps-the-newest-response` moves from `ui/src/stores/batch.test.ts` to `ui/src/stores/drawer.test.ts` | `ui/src/stores/drawer.test.ts` |
| unit · pytest | none | `test_a_session_is_served_from_its_record_and_an_unknown_id_refused` — the refusal names the id | `tests/test_ui_api.py` |
| e2e | `ui:sessions:the-drawer-holds-the-render` | `test_confirming_the_dialog_opens_the_session` — the drawer over the hub, the hub's URL kept | `tests/e2e/conftest.py` gains a second renderable batch; `tests/e2e/test_render.py` |

**End-to-end runs added:** one, on Chromium only (T4) — a drawer's keys, its backdrop and the viewer above it are a
browser's (T1). A render spends its batch's shortfall, so the drawer takes a batch of its own rather than following
the confirmation test (T2, T3); its steps are one flow, the drawer opened, closed and opened again.

**Removed or merged:**

| test | where | goes to |
|---|---|---|
| `test_the_list_shows_a_finished_session` | `tests/e2e/test_render.py` | retired by [D4](#d4) |
| `test_a_batch_lists_its_sessions_running_first_then_newest` | `tests/test_ui_api.py` | retired by [D4](#d4) |
| `ui:sessions:an-observed-list-follows-its-render` | `ui/src/stores/batch.test.ts` | retired by [D4](#d4) |
| `ui:sessions:the-selected-record-keeps-the-newest-response` | `ui/src/stores/batch.test.ts` | `ui/src/stores/drawer.test.ts`, the same key |

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** `⌃;` is typed as `;` in a field on some layouts → it matches `event.code`, the physical key (D25), and
  the page takes it by `preventDefault`.
- **[Trade-off]** a reload forgets the last session's outcome → its images are on Renders, and its record on disk.

## Migration Plan

The drawer lands beside the session pages (phase 1); the pages, routes and list go once the drawer's test is green
(phase 2), per A4.

## Verdict

**Feasible.** The content moves; the store follows state the live store already holds.
