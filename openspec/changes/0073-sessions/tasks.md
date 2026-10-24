# Tasks — 0073 sessions

The record, the routes, the screens, the viewer, then the overdue prose, per [design](design.md). Every new pytest
test carries `@pytest.mark.spec` with the key its task names.

## Progress

- [ ] 1 — The record
- [ ] 2 — The routes
- [ ] 3 — The screens
- [ ] 4 — The viewer
- [ ] 5 — The prose

## 1 — The record

- [ ] 1.1 **HALT CHECK** — no session file kind exists.
  Verify: `grep -c 'Artifact("session"' isekai/foundation/artifacts.py` prints `0`.
- [ ] 1.2 Add `SESSION_FILE`, `SessionRecord` and `replace` to `isekai/foundation/artifacts.py` per [D1](design.md#d1);
  write the record from `_session` in `isekai/interface/render.py` and take `--session` in `isekai/interface/cli.py`, per [D2](design.md#d2).
  Verify: `grep -c 'Artifact("session", 1)' isekai/foundation/artifacts.py` prints `1`, and `uv run python -m isekai render --help` exits 0.
- [ ] 1.3 Bind every `cli:render-session:` key of the [cli](specs/cli/spec.md) delta in `tests/test_render.py`.
  Verify: `uv run pytest -q tests/test_render.py` exits 0, and `grep -c 'cli:render-session:' tests/test_render.py` prints `4`.
- [ ] 1.4 Name `--session` and the record beside the log in `README.md`'s `render` flags.
  Verify: `grep -c 'sessions/' README.md` prints a number of at least `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 2 — The routes

- [ ] 2.1 **HALT CHECK** — the app serves no session.
  Verify: `grep -c '/api/b/{batch}/sessions' isekai/interface/ui/app.py` prints `0`.
- [ ] 2.2 Add `sessions` to `isekai/interface/ui/library.py` and the session routes to `isekai/interface/ui/app.py` per
  [D3](design.md#d3); bind both `ui:sessions:` unit keys in `tests/test_ui_api.py`.
  Verify: `uv run pytest -q tests/test_ui_api.py` exits 0, and `grep -c -E 'ui:sessions:(a-batch-lists|a-session-reads)' tests/test_ui_api.py` prints `2`.
- [ ] 2.3 Pass `--session` from `render_command`, keep the id in the slot, and fail a raising `volume up`'s step, in
  `isekai/interface/ui/jobs.py`, per [D3](design.md#d3) and [D7](design.md#d7); bind `ui:render-job:an-opening-that-raises-fails-its-step` in `tests/test_ui_jobs.py`.
  Verify: `uv run pytest -q tests/test_ui_jobs.py` exits 0, and `grep -c 'an-opening-that-raises-fails-its-step' tests/test_ui_jobs.py` prints `1`.
- [ ] 2.4 Add the render step of [D7](design.md#d7) to `test_an_approved_sheet_carries_why_it_cannot_be_cancelled` in
  `tests/test_ui_api.py`.
  Verify: `grep -rc 'render session is running' tests/test_ui_api.py` prints a number of at least `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.

## 3 — The screens

- [ ] 3.1 **HALT CHECK** — `/session` is the session's screen.
  Verify: `grep -c "path: '/session'" ui/src/router.ts` prints `1`.
- [ ] 3.2 Add `ui/src/views/Sessions.vue`, `ui/src/views/SessionPage.vue` and `ui/src/views/Billing.vue` with their
  routes, the Sessions tab, the indicator and `⇧S` in `ui/src/App.vue`, per [D4](design.md#d4) and [D5](design.md#d5); delete `Session.vue`.
  Verify: `test -e ui/src/views/Session.vue` exits 1, `grep -c "path: '/session'" ui/src/router.ts` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.3 Land `test_confirming_the_dialog_opens_the_session` in `tests/e2e/test_render.py` on the session's page;
  write a finished record in `tests/e2e/conftest.py`; add `test_the_list_shows_a_finished_session`, bound to its key.
  Verify: `grep -c 'the-list-shows-a-finished-session' tests/e2e/test_render.py` prints `1`, and `uv run pytest -q tests/e2e` exits 0.
- [ ] 3.4 Replace `/session` with the sessions' addresses and `/billing` in `ui/design/spec.md` §4, J4 and J8, and in
  `isekai/interface/ui/README.md`.
  Verify: `grep -c '/session\b' ui/design/spec.md` prints `0`, and `grep -c 'sessions/' isekai/interface/ui/README.md` prints a number of at least `1`.

## 4 — The viewer

- [ ] 4.1 **HALT CHECK** — session tiles are their own size.
  Verify: `grep -c 'width: 60px' ui/src/app.css` prints a number of at least `1`.
- [ ] 4.2 Open a session's images and the batch's sources in `ui/src/components/ImageViewer.vue` from `SessionPage.vue`,
  tiles at the Renders size in `ui/src/app.css`; read `last` on each step, per [D6](design.md#d6).
  Verify: `grep -c 'const last = props.images.length - 1' ui/src/components/ImageViewer.vue` prints `0`, and `uv run python -m tools.typecheck_ui` exits 0.

## 5 — The prose

- [ ] 5.1 **HALT CHECK** — the cancel's docstring says it returns the draft.
  Verify: `grep -c 'and return the draft' isekai/pipeline/review.py` prints `1`.
- [ ] 5.2 Apply [D7](design.md#d7)'s wording to `README.md`, `isekai/interface/README.md`, `ui/design/spec.md` J3,
  `ui/src/views/Review.vue`'s cancel comment and `cancel`'s docstring in `isekai/pipeline/review.py`.
  Verify: `grep -c 'and return the draft' isekai/pipeline/review.py` prints `0`, `grep -c '…/cancel' isekai/interface/README.md` prints `1`, and `grep -c 'Once something was\|writes it again' README.md` prints `0`.
