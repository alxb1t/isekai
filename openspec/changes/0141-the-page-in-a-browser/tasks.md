# The page in a browser — tasks

Phases that guard the browser tests against a page that logs an error, press the key list, a field and the pane keys in a browser, and hold Approve over a held save. A build cannot run Chromium, so each phase is checked by collection and the gate; CI runs the browser tests after the merge ([D8](design.md#d8)).

## Progress

- [ ] 1 — The guard · moderate
- [ ] 2 — The keys in a browser · moderate
- [ ] 3 — Save and approve · moderate

## 1 — The guard

- [ ] 1.1 **HALT CHECK** A refusal is answered with `REFUSED = 409`, as [D3](design.md#d3) reads it for the declarations; if the line reads otherwise, the plan is wrong.
  Verify: `git grep -c -h -F 'REFUSED = 409' isekai/interface/ui/app.py` prints `1`.
- [ ] 1.2 Write `tests/e2e/guard.py` as [D2](design.md#d2) gives it, with a one-line module docstring above and the imports `Sequence` from `collections.abc` and `dataclass` and `field` from `dataclasses`.
  Verify: `grep -c -F 'def faults(' tests/e2e/guard.py` prints `1`.
- [ ] 1.3 In `tests/e2e/conftest.py` import `BrowserContext` from `playwright.sync_api`, `urlsplit` from `urllib.parse`, and `Refused`, `Seen` and `faults` from `tests.e2e.guard`; after `served` add the fixtures `refusals` and `context` exactly as [D1](design.md#d1) gives them.
  Verify: `git grep -c -h -F 'def context(' tests/e2e/conftest.py` prints `1`.
- [ ] 1.4 In `tests/e2e/test_queue.py` import `Refused` from `tests.e2e.guard`, give `test_a_failure_reading_the_next_state_shows_in_the_approve_bar` the parameter `refusals: list[Refused]`, and before its `page.route(` call append `Refused(409, "/api/c/queue-fails/hub")` to it.
  Verify: `git grep -c -h -F 'Refused(409, "/api/c/queue-fails/hub")' tests/e2e/test_queue.py` prints `1`.
- [ ] 1.5 In `tests/e2e/test_routes.py` import `Refused` from `tests.e2e.guard`, give `test_a_reload_lands_on_the_same_hub_and_the_same_review` the parameter `refusals: list[Refused]`, and before the `page.goto` of `no-such-collection` append `Refused(409, "/api/c/no-such-collection/")` to it.
  Verify: `git grep -c -h -F 'Refused(409, "/api/c/no-such-collection/")' tests/e2e/test_routes.py` prints `1`.
- [ ] 1.6 Write `tests/test_e2e_guard.py` with a one-line docstring and `test_the_guard_names_each_fault`, marked `spec_exempt("structural: the browser tests' guard names a page error, a console error, a server error and an undeclared refusal")`. `faults` of `Seen(errors=["boom"], consoles=[("error", "TypeError: x is not a function")], responses=[(500, "/api/library"), (404, "/api/gone")])` and no declaration is `["page error: boom", "console error: TypeError: x is not a function", "server error: 500 /api/library", "undeclared refusal: 404 /api/gone"]`.
  Verify: `uv run pytest tests/test_e2e_guard.py::test_the_guard_names_each_fault` passes.
- [ ] 1.7 In `tests/test_e2e_guard.py` add `test_the_guard_lets_a_failed_load_a_warning_and_a_declared_refusal_by`, marked `spec_exempt("structural: the browser tests' guard lets by what a page may log")`. `faults` of `Seen` with consoles `("error", "Failed to load resource: the server responded with a status of 409 (Conflict)")`, `("warning", "deprecated")` and `("log", "hello")`, responses `(200, "/api/library")` and `(409, "/api/c/queue-fails/hub")`, and `[Refused(409, "/api/c/queue-fails")]` is `[]`.
  Verify: `uv run pytest tests/test_e2e_guard.py::test_the_guard_lets_a_failed_load_a_warning_and_a_declared_refusal_by` passes.
- [ ] 1.8 In `tests/test_e2e_guard.py` add `test_a_declaration_nothing_answers_is_a_fault`, marked `spec_exempt("structural: the browser tests' guard refuses a declared refusal that no response met")`. `faults` of `Seen(responses=[(200, "/api/library")])` and `[Refused(409, "/api/c/x/")]` is `["declared refusal never answered: 409 /api/c/x/"]`; of `Seen(responses=[(404, "/api/c/x/hub")])` and the same declaration, `["undeclared refusal: 404 /api/c/x/hub", "declared refusal never answered: 409 /api/c/x/"]`.
  Verify: `uv run pytest tests/test_e2e_guard.py::test_a_declaration_nothing_answers_is_a_fault` passes.
- [ ] 1.9 The browser tests still collect, with the guard in their fixtures.
  Verify: `uv run pytest tests/e2e --collect-only -q` exits `0`.
- [ ] 1.10 Every test carries its key or its exemption.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_e2e_guard.py` passes.

## 2 — The keys in a browser

- [ ] 2.1 **HALT CHECK** The key list holds no control `Tab` reaches, so [D6](design.md#d6) holds its focus by the page behind it and not by a wrap; if a control is there, the plan is wrong.
  Verify: `git grep -c -E '<(button|input|select|textarea|a)[ >]' -- ui/src/components/KeyList.vue` exits `1`.
- [ ] 2.2 **HALT CHECK** The key list is the dialog the journey finds by `data-key-list`.
  Verify: `git grep -c -h -F 'data-key-list' ui/src/components/KeyList.vue` prints `1`.
- [ ] 2.3 **HALT CHECK** The app bar's button carries the title `the key list` the journey finds it by.
  Verify: `git grep -c -h -F 'the key list ' ui/src/App.vue` prints `1`.
- [ ] 2.4 In `QUEUES` of `tests/e2e/conftest.py`, after its `queue-fails` entry, add `"keys-hold": (("kay", (720, 1000)),),`.
  Verify: `git grep -c -h -F '"keys-hold"' tests/e2e/conftest.py` prints `1`.
- [ ] 2.5 Write `tests/e2e/test_keys.py` exactly as [D4](design.md#d4) gives it. Its commit body says why no existing test fits: `test_the_photograph_opens_in_the_viewer` ends on a changed viewport, an open list and a saved edit, and no other test reaches an editable Review with nothing open.
  Verify: `grep -c -F 'def test_the_keys_hold_in_a_browser' tests/e2e/test_keys.py` prints `1`.
- [ ] 2.6 The journey collects.
  Verify: `uv run pytest tests/e2e/test_keys.py --collect-only -q` exits `0`.
- [ ] 2.7 Each key the journey names is one this change's delta holds, on the layer it binds.
  Verify: `uv run pytest tests/test_spec_bindings.py` passes.

## 3 — Save and approve

- [ ] 3.1 **HALT CHECK** The draft's save is sent with `keepalive` by `saveDraft`, as [D7](design.md#d7) reads it; if it is not, the held PUT is no question of the route and the plan is wrong.
  Verify: `git grep -c -h -F "{ keepalive: true }" ui/src/api.ts` prints `1`.
- [ ] 3.2 Write `tests/e2e/held.py` as [D7](design.md#d7) gives it, with a one-line docstring above and the imports `Page` and `Route` from `playwright.sync_api`.
  Verify: `grep -c -F 'def sent(' tests/e2e/held.py` prints `1`.
- [ ] 3.3 In `tests/e2e/test_import.py` import `sent` from `tests.e2e.held`, delete `_sent`, and call `sent(` where `_sent(` was called, in `_release` and in the tests that hold a stream, a removal and a commit.
  Verify: `git grep -c -F '_sent(' -- tests/e2e/test_import.py` exits `1`.
- [ ] 3.4 In `QUEUES` of `tests/e2e/conftest.py`, after the `keys-hold` entry, add `"save-holds": (("lou", (725, 1000)), ("max", (735, 1000))),`.
  Verify: `git grep -c -h -F '"save-holds"' tests/e2e/conftest.py` prints `1`.
- [ ] 3.5 In `tests/e2e/test_queue.py` add the imports [D7](design.md#d7) lists, but `Refused`, which 1.4 imported, and `FLOW`, which joins the existing `from tests.e2e.conftest import` line; after its last test add the constants, `_edit`, `_holds_the_edit` and `test_approve_waits_for_a_save_held_at_the_network` exactly as it gives them.
  Verify: `git grep -c -h -F 'def test_approve_waits_for_a_save_held_at_the_network' tests/e2e/test_queue.py` prints `1`.
- [ ] 3.6 In `tests/e2e/test_queue.py` add `test_a_refused_save_is_sent_again_by_the_next_approval` exactly as [D7](design.md#d7) gives it. The commit body of both tests says why none fits: no test holds a request on Review, and a held save needs an editable sheet no earlier test has approved.
  Verify: `git grep -c -h -F 'def test_a_refused_save_is_sent_again_by_the_next_approval' tests/e2e/test_queue.py` prints `1`.
- [ ] 3.7 The browser tests collect.
  Verify: `uv run pytest tests/e2e --collect-only -q` exits `0`.
- [ ] 3.8 Each key the tests name is one this change's delta holds, on the layer it binds.
  Verify: `uv run pytest tests/test_spec_bindings.py` passes.
