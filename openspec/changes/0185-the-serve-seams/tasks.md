# The serve seams — tasks

Each phase gives one function a parameter, switches its test to pass a fake, and removes the module's row from the ratchet; the last amends the decision. Design: [design](design.md).

## Progress

- [x] 1 — The binary and the timeout, parameters of the bundle's build · moderate
- [x] 2 — The root, the build and the run, parameters of serve · moderate
- [x] 3 — D61 amended · moderate

## 1 — The binary and the timeout, parameters of the bundle's build

- [x] 1.1 **HALT CHECK** The base holds the evaluator's seams, so the ratchet's row ceiling is 21 before this phase.
  Verify: `git grep -n -e "^PATCHED_ROWS = 21" -- tests/test_ratchets.py` prints one line.
- [x] 1.2 In `isekai/interface/ui/bundle.py`, give `ensure_built` the keyword-only parameters `binary: str = BINARY` and `timeout: float = BUILD_TIMEOUT`, after `source: Path = SOURCE` ([D1](design.md#d1)).
  Verify: `git grep -n -F -e "binary: str = BINARY" -e "timeout: float = BUILD_TIMEOUT" -- isekai/interface/ui/bundle.py` prints the lines that hold its defaults.
- [x] 1.3 In `ensure_built` alone, change `which(BINARY)` to `which(binary)`, `[BINARY,` to `[binary,` and `timeout=BUILD_TIMEOUT` to `timeout=timeout`. In each refusal message, change `{BINARY!r}` to `{binary!r}`, `{BINARY}` to `{binary}` and `{BUILD_TIMEOUT}` to `{timeout}`. Leave `BINARY` and `BUILD_TIMEOUT` defined above it.
  Verify: `git grep -n -F -e "BINARY!r" -e "{BINARY}" -e "which(BINARY)" -e "[BINARY," -e "timeout=BUILD_TIMEOUT" -e "{BUILD_TIMEOUT}" -- isekai/interface/ui/bundle.py` prints nothing.
- [x] 1.4 In the docstring of `ensure_built`, add after its first paragraph: `` `binary` is the command and `timeout` the ceiling in seconds; each defaults to the constant above, and a test passes its own. ``
  Verify: `git grep -n -F "each defaults to the constant above" -- isekai/interface/ui/bundle.py` prints one line.
- [x] 1.5 In `test_a_build_that_does_not_finish_is_stopped_and_named` of `tests/test_ui.py`, delete the line `monkeypatch.setattr(bundle, "BINARY", str(npm))` and each `monkeypatch.setattr(bundle, "BUILD_TIMEOUT", …)` line. Pass `binary=str(npm), timeout=3` to the `bundle.ensure_built(source)` call under the first `pytest.raises(Refusal)`, and `binary=str(npm), timeout=60` to the one under `pytest.raises(KeyboardInterrupt)`. Keep the `monkeypatch` parameter: the test still uses `monkeypatch.context()`.
  Verify: `git grep -n -F -e '"BINARY"' -e '"BUILD_TIMEOUT"' -- tests/test_ui.py` prints nothing.
- [x] 1.6 In `tests/test_ratchets.py`, delete the row `"isekai.interface.ui.bundle": 3,` from `PATCHED_MODULES`.
  Verify: `git grep -n -F "isekai.interface.ui.bundle" -- tests/test_ratchets.py` prints nothing.
- [x] 1.7 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 20`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 20" -- tests/test_ratchets.py` prints one line.
- [x] 1.8 Run the bundle's tests and the ratchet with the row gone.
  Verify: `uv run pytest tests/test_ui.py tests/test_ratchets.py` exits 0.

## 2 — The root, the build and the run, parameters of serve

- [x] 2.1 In `isekai/interface/ui/__init__.py`, add the import `from collections.abc import Callable` above `from pathlib import Path`. Give `serve` the keyword-only parameters `root: Callable[[], Path] = library.root`, `ensure_built: Callable[[], Path] = ensure_built` and `run: Callable[..., None] | None = None`, after `port: int` ([D2](design.md#d2)).
  Verify: `git grep -n -F -e "root: Callable[[], Path] = library.root" -e "ensure_built: Callable[[], Path] = ensure_built" -e "run: Callable[..., None] | None = None" -- isekai/interface/ui/__init__.py` prints the lines that hold its defaults.
- [x] 2.2 In `serve`, replace its line `root = library.open_library(library.root())` with `opened = library.open_library(root())`, and read `opened` in its later reads of that local: `sweep(root)` and the first argument of `create_app`. `collection_runs` keeps its own `library.root()`.
  Verify: `git grep -n -F "library.root()" -- isekai/interface/ui/__init__.py` prints one line, in `collection_runs`.
- [x] 2.3 In `serve`, change the import line `from isekai.interface.ui.app import create_app, run` to the lines `from isekai.interface.ui.app import create_app` and `from isekai.interface.ui.app import run as run_app`, under the comment that stays. Change the line `run(app, host=HOST, port=port)` to `(run or run_app)(app, host=HOST, port=port)`.
  Verify: `git grep -n -F "(run or run_app)(app, host=HOST, port=port)" -- isekai/interface/ui/__init__.py` prints one line.
- [x] 2.4 In the docstring of `serve`, add after its first paragraph: `` `root`, `ensure_built` and `run` are what a test replaces; each defaults to what the product uses. ``
  Verify: `git grep -n -F "are what a test replaces; each defaults" -- isekai/interface/ui/__init__.py` prints one line.
- [x] 2.5 In `test_serve_returns_130_for_keyboard_interrupt` of `tests/test_ui.py`, delete the import `from isekai.interface.ui import app as app_module` and the lines `monkeypatch.setattr(ui.library, "root", library_root)`, `monkeypatch.setattr(ui, "ensure_built", ensure_built)` and `monkeypatch.setattr(app_module, "run", interrupted)`. Call `ui.serve(wired, port=7717, root=library_root, ensure_built=ensure_built, run=interrupted)`, wrapped as `ruff format` wraps it. Keep the patch of `Billing.watch` and every assertion.
  Verify: `git grep -n -F -e 'setattr(ui.library, "root"' -e 'setattr(ui, "ensure_built"' -e 'setattr(app_module, "run"' -- tests/test_ui.py` prints nothing.
- [x] 2.6 In `tests/test_ratchets.py`, delete the row `"isekai.interface.ui.app": 1,` from `PATCHED_MODULES`.
  Verify: `git grep -n -F "isekai.interface.ui.app" -- tests/test_ratchets.py` prints nothing.
- [x] 2.7 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 19`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 19" -- tests/test_ratchets.py` prints one line.
- [x] 2.8 Run the serve test, the server's tests, the `-S` guard and the ratchet with the row gone.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_ratchets.py` exits 0.

## 3 — D61 amended

- [x] 3.1 In `docs/decisions.md`, in the bold sentence of D61, add inside the bold, before its closing `**`, this sentence: `` `serve` takes the library's root, `ensure_built` and the server's `run` the same way, and `ensure_built` takes the binary and the timeout. `` ([D4](design.md#d4)).
  Verify: `git grep -n -F "the binary and the timeout" -- docs/decisions.md` prints one line.
- [x] 3.2 In `docs/decisions.md`, replace the *Accepts* bullet of D61, which ends with the sentence "Reopen when serve's collaborators are parameters.", with `- **Accepts:** nothing.`
  Verify: `git grep -n -F "collaborators are parameters" -- docs/decisions.md` prints nothing.
- [x] 3.3 In `docs/decisions.md`, add `0185` to the *Made by* bullet of D61, which then reads `` `0150`, `0185` ``.
  Verify: `git grep -n -e "Made by:.*0150.*0185" -- docs/decisions.md` prints one line.
- [x] 3.4 Run the tests the phases touched, with the layer, docs and spec guards.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_spec_bindings.py` exits 0.
- [x] 3.5 Run the standing mutants over the edits file.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
