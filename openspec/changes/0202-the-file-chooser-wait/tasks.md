# The file chooser wait — tasks

One build phase: the helper presses `⇧A` again when no dialog opens. No phase is a person's, and nothing here is run in a browser: CI's browser step proves the change after its merge ([D2](design.md#d2), [D3](design.md#d3)).

## Progress

- [x] 1 — The press · moderate

## 1 — The press

- [x] 1.1 In `tests/e2e/test_import.py`, import Playwright's timeout beside the names the file takes from `playwright.sync_api`: `TimeoutError as PlaywrightTimeout`.
  Verify: `git grep -c -F "TimeoutError as PlaywrightTimeout" -- tests/e2e/test_import.py` prints the path and `1`.
- [x] 1.2 Above `_choose`, add the constants `PRESSES = 4` and `SHORT_MS = 2_000`, each with a one-line comment that says what it counts ([D1](design.md#d1)).
  Verify: `git grep -c -e "^PRESSES = 4" -e "^SHORT_MS = 2_000" -- tests/e2e/test_import.py` prints the path and `2`.
- [x] 1.3 Add `def _pressed(page: Page) -> FileChooser:` above `_choose`, as [D1](design.md#d1) gives it: `PRESSES` presses of `Shift+A`, each inside `page.expect_file_chooser(timeout=SHORT_MS)`, a `PlaywrightTimeout` going on to the next; then one press inside `page.expect_file_chooser()` with no timeout given. It returns the dialog of the press that opened one. Its docstring says a press the browser answers with no dialog is pressed again, and that the last wait is the default one.
  Verify: `git grep -c -F "def _pressed(page: Page) -> FileChooser:" -- tests/e2e/test_import.py` prints the path and `1`.
- [x] 1.4 In `_choose`, replace the second `with page.expect_file_chooser() as chooser:` block and the `chooser.value.set_files(...)` line after it with `_pressed(page).set_files([str(path) for path in files])`, and end its docstring with the sentence `⇧A is pressed again when no dialog opens.` Its first block, the dialog the mount opens, stays as it is.
  Verify: `git grep -c -F "_pressed(page).set_files([str(path) for path in files])" -- tests/e2e/test_import.py` prints the path and `1`.
- [x] 1.5 The file still collects, with the three tests it held and no other.
  Verify: `uv run pytest tests/e2e/test_import.py --collect-only -q` exits 0.
- [x] 1.6 No file but `tests/e2e/test_import.py`, `CHANGELOG.md` and this change's directory changes.
  Verify: `git status --short -- isekai ui tools evaluation docs` prints nothing.
