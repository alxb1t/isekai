# Tasks — 0093 the tests revisited

The rule, the flakes, then the browser tests, per [design](design.md).

## Progress

- [x] 1 — The rule
- [ ] 2 — The flakes
- [ ] 3 — The browser

## 1 — The rule

- [x] 1.1 `unmarked` and its test in `tests/test_spec_bindings.py` follow [D1](design.md#d1); its twin passes a test with
  two `spec` markers and fails `spec` beside `spec_exempt`.
  Verify: `grep -c 'def test_every_test_carries_one_marker' tests/test_spec_bindings.py` prints `0`, and `uv run pytest tests/test_spec_bindings.py` exits 0.
- [x] 1.2 `spec()` in `ui/src/test/spec.ts` takes a key or an array of keys, and `_VITEST_SPEC` reads both, per
  [D1](design.md#d1); the binding twin reads a fixture `spec(['a', 'b'], …)` as both keys.
  Verify: `uv run python -m tools.test_ui` exits 0, and `uv run pytest tests/test_spec_bindings.py -k vitest` exits 0.
- [x] 1.3 `CONTRIBUTING.md` and `CODING_STANDARDS.md` say each behaviour a test holds carries its key and pytest warns on
  an unregistered marker; `CODING_STANDARDS.md`'s *Project rules* gain *Extend before adding*, per [D2](design.md#d2).
  Verify: `grep -c 'Extend before adding' CODING_STANDARDS.md` prints `1`, and `grep -c 'silently ignores' CODING_STANDARDS.md` prints `0`.

## 2 — The flakes

- [ ] 2.1 Rewrite `test_the_report_reaches_the_loopback_with_a_proxy_exported` in `tests/test_render.py` socketless, per
  [D3](design.md#d3).
  Verify: `grep -c 'ThreadingHTTPServer' tests/test_render.py` prints `0`, and `uv run pytest tests/test_render.py -k proxy_exported` exits 0.
- [ ] 2.2 Rewrite `test_sigint_ends_streams_without_cancellation_output` in `tests/test_ui.py` in-process, lifting the
  `Server` subclass in `isekai/interface/ui/app.py` to module scope, per [D3](design.md#d3). Remove `LOOPBACK` from the
  `Makefile` and its mention in `.github/workflows/ci.yml` and `CONTRIBUTING.md`.
  Verify: `grep -c 'LOOPBACK' Makefile` prints `0`, and `uv run pytest tests/test_ui.py -k sigint` exits 0.
  The `gate` recipe and `Makefile` change by exactly these lines, the dry run too:
  ```diff
  - # The tests outside `tests/e2e/` that serve on 127.0.0.1.
  - LOOPBACK = tests/test_ui.py::test_sigint_ends_streams_without_cancellation_output tests/test_render.py::test_the_report_reaches_the_loopback_with_a_proxy_exported
  - # tests, but those an unattended run's sandbox cannot run -- the browser's, as
  - # Chromium never starts there, and the few that serve on 127.0.0.1 -- which
  - # `make e2e` runs apart, and CI runs both
  - uv run pytest --ignore=tests/e2e $(addprefix --deselect ,$(LOOPBACK))
  - uv run pytest --ignore=tests/e2e --deselect tests/test_ui.py::test_sigint_ends_streams_without_cancellation_output --deselect tests/test_render.py::test_the_report_reaches_the_loopback_with_a_proxy_exported
  + # tests, but the browser's, as Chromium never starts in an unattended run's
  + # sandbox -- which `make e2e` runs apart, and CI runs both
  + uv run pytest --ignore=tests/e2e
  - # The browser tests in `tests/e2e/`, on Chromium, and the tests that serve on
  - # loopback. Out of the gate while the sandbox cannot run them; CI runs it after
  - # the gate.
  + # The browser tests in `tests/e2e/`, on Chromium. Out of the gate while the
  + # sandbox cannot run them; CI runs it after the gate.
  - uv run pytest tests/e2e $(LOOPBACK)
  + uv run pytest tests/e2e
  ```
- [ ] 2.3 The watchdog tests in `tests/test_render.py`, the bundle-timeout test in `tests/test_ui.py` and `_overlap` in
  `tests/test_ui_api.py` follow [D4](design.md#d4).
  Verify: `grep -c 'fired.wait(0.15)' tests/test_render.py` prints `0`, `grep -c '"ps"' tests/test_ui.py` prints `0`, and `for i in $(seq 20); do uv run pytest -q tests/test_render.py -k watchdog || exit 1; done` exits 0.

## 3 — The browser

- [ ] 3.1 Merge the browser tests per [Tests](design.md#tests), each merged test carrying both keys.
  Verify: `cat tests/e2e/test_*.py | grep -c '^def test_'` prints `19`, and `uv run pytest --collect-only -q tests/e2e` exits 0.
- [ ] 3.2 Add the drawer's viewport step and the pick's width step under their restored keys, and `0091·R4`'s and
  `0091·R9`'s steps in the merged import test, per [D5](design.md#d5).
  Verify: `grep -c 'the-drawer-fits-its-widest-grid\|the-pick-holds-its-width' tests/e2e/test_render.py` prints `2`, and `uv run pytest tests/test_spec_bindings.py` exits 0.
- [ ] 3.3 Name the order couplings in `tests/e2e/conftest.py`, per [D5](design.md#d5).
  Verify: `grep -c 'test_prepare.py' tests/e2e/conftest.py` prints a count above 0.
