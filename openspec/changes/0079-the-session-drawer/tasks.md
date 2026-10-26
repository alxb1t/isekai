# Tasks — 0079 the session drawer

The drawer beside the session pages, then the pages gone, per [design](design.md). Every new vitest test carries
`spec(…)`, every new pytest test `@pytest.mark.spec`, with the key its task names.

## Progress

- [x] 1 — The drawer
- [ ] 2 — The session pages removed

## 1 — The drawer

- [x] 1.1 **HALT CHECK** — no drawer exists, and a confirmed render routes to its session's page.
  Verify: `test -e ui/src/components/SessionDrawer.vue; echo $?` prints `1`, and `grep -c "name: 'session'" ui/src/components/RenderDialog.vue` prints `1`.
- [x] 1.2 Add `ui/src/stores/drawer.ts` per [D1](design.md#d1); in `ui/src/stores/drawer.test.ts` bind
  `ui:sessions:the-drawer-keeps-the-last-session`, and move `ui:sessions:the-selected-record-keeps-the-newest-response`
  there from `ui/src/stores/batch.test.ts`.
  Verify: `grep -c "spec('ui:sessions:" ui/src/stores/drawer.test.ts` prints `2`, and `grep -c 'the-selected-record-keeps-the-newest-response' ui/src/stores/batch.test.ts` prints `0`, and `uv run python -m tools.test_ui` exits 0.
- [x] 1.3 Add `ui/src/components/SessionDrawer.vue` per [D2](design.md#d2), drawn in `ui/src/App.vue`, its styles in
  `ui/src/app.css`; declare `⌃;`, and make `●` and the Render bar's link in `ui/src/components/RenderBar.vue` open it,
  per [D3](design.md#d3).
  Verify: `grep -c 'showModal' ui/src/components/SessionDrawer.vue` prints `1`, and `grep -c "code: 'Semicolon', ctrl: true" ui/src/App.vue` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.4 Open the drawer from `confirm` in `ui/src/components/RenderDialog.vue` per [D3](design.md#d3); in
  `test_confirming_the_dialog_opens_the_session` (`tests/e2e/test_render.py`) expect the drawer over the hub, the hub's
  URL kept.
  Verify: `grep -c "name: 'session'" ui/src/components/RenderDialog.vue` prints `0`, and `uv run pytest -q tests/e2e/test_render.py -k confirming` exits 0.
- [x] 1.5 Add a second renderable batch to `tests/e2e/conftest.py`, and `test_the_drawer_holds_the_render` to
  `tests/e2e/test_render.py`, bound to `ui:sessions:the-drawer-holds-the-render`.
  Verify: `grep -c 'the-drawer-holds-the-render' tests/e2e/test_render.py` prints `1`, and `uv run pytest -q tests/e2e/test_render.py` exits 0.

## 2 — The session pages removed

- [ ] 2.1 **HALT CHECK** — the session pages still answer.
  Verify: `grep -c "/b/:batch/sessions" ui/src/router.ts` prints `2`.
- [ ] 2.2 Delete the routes, `ui/src/views/SessionPage.vue`, `ui/src/views/Sessions.vue`, the Sessions tab, `⇧S` and
  `sessions()` in `ui/src/App.vue`, `sessions` in `ui/src/api.ts`, and the batch store's session state in
  `ui/src/stores/batch.ts`, per [D4](design.md#d4); delete `ui:sessions:an-observed-list-follows-its-render` in
  `ui/src/stores/batch.test.ts` and `test_the_list_shows_a_finished_session` in `tests/e2e/test_render.py`.
  Verify: `test -e ui/src/views/SessionPage.vue; echo $?` prints `1`, and `grep -c "shifted('KeyS')" ui/src/App.vue` prints `0`, and `grep -c 'an-observed-list-follows-its-render' ui/src/stores/batch.test.ts` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 2.3 Delete `/api/b/{batch}/sessions` in `isekai/interface/ui/app.py` and `library.sessions` in
  `isekai/interface/ui/library.py`, and make `library.session`'s refusal `{batch} holds no session {id!r}`, per
  [D4](design.md#d4); delete `test_a_batch_lists_its_sessions_running_first_then_newest` and check the refusal names
  the id in `test_a_session_is_served_from_its_record_and_an_unknown_id_refused` (`tests/test_ui_api.py`).
  Verify: `grep -c 'def sessions' isekai/interface/ui/library.py` prints `0`, and `grep -c 'its sessions are at' isekai/interface/ui/library.py tests/test_ui_api.py` prints `0` for each file, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [ ] 2.4 Edit `ui/design/spec.md` and `docs/data-flow.md` per [D5](design.md#d5).
  Verify: `grep -cE 'b/[^ ]*/sessions' ui/design/spec.md` prints `0`, and `grep -c '⌃; the render drawer' ui/design/spec.md` prints `1`, and `grep -c 'the render drawer' docs/data-flow.md` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
