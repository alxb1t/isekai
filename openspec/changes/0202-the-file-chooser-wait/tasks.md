# The file chooser wait — tasks

A person proves the cause on the Mac, the build writes the wait, and the person runs the browser tests ([D3](design.md#d3)).

## Progress

- [ ] 1 — The proof · **HUMAN**
- [ ] 2 — The wait · moderate
- [ ] 3 — The runs · **HUMAN**

## 1 — The proof

Run each command in a shell on the Mac, from the repository root: the run's sandbox cannot bind a loopback port.

- [ ] 1.1 Write `tests/e2e/test_probe.py` with the probe text of [D2](design.md#d2), verbatim.
  Verify: `grep -c -F "PROBE" tests/e2e/test_probe.py` prints `1`.
- [ ] 1.2 Run `uv run pytest tests/e2e/test_probe.py -q`. It writes `.data/probe-bare.txt` and `.data/probe-held.txt`, a line of each starting `PROBE`.
  Verify: `grep -c -F "PROBE" .data/probe-bare.txt .data/probe-held.txt` prints `200` for each file.
- [ ] 1.3 **HALT CHECK** The page keeps the key: no iteration ends `dropped`, in either variant. A `dropped` line halts the change ([D4](design.md#d4)).
  Verify: `grep -c -F " dropped " .data/probe-bare.txt .data/probe-held.txt` prints `0` for each file.
- [ ] 1.4 **HALT CHECK** The race shows: the `bare` variant ends `suppressed` at least once. None halts the change: the cause is not shown.
  Verify: `grep -c -F " suppressed " .data/probe-bare.txt` prints a count above `0`.
- [ ] 1.5 **HALT CHECK** The first dialog is the cause: the `held` variant ends `suppressed` at least once. None halts the change: the cause is the interception, not the dialog ([D4](design.md#d4)).
  Verify: `grep -c -F " suppressed " .data/probe-held.txt` prints a count above `0`.
- [ ] 1.6 In `design.md`, replace the line `Proof: not yet run.` with one paragraph that starts `Signal: `. It names one page event that comes before `keydown KeyA` on every `ok` line of `.data/probe-held.txt` and after it on every `suppressed` line, and copies one line of each that shows it. `change` and `input` do not qualify: Playwright's `set_files` fires them. No such event: stop, the wait has nothing to hang on.
  Verify: `grep -c -F "Signal: " openspec/changes/0202-the-file-chooser-wait/design.md` prints `1`.
- [ ] 1.7 Delete the probe and its output: `rm tests/e2e/test_probe.py .data/probe-bare.txt .data/probe-held.txt`.
  Verify: `ls tests/e2e/test_probe.py .data/probe-bare.txt .data/probe-held.txt` prints `No such file or directory` for each path.

## 2 — The wait

- [ ] 2.1 **HALT CHECK** The cause in `design.md` names the signal the wait hangs on.
  Verify: `grep -c -F "Signal: " openspec/changes/0202-the-file-chooser-wait/design.md` prints `1`.
- [ ] 2.2 In `tests/e2e/test_import.py`, add `def _closed(page: Page, answer: Callable[[], None]) -> None:`, with `Callable` imported from `collections.abc`. It arms a listener for the signal of `design.md`, calls `answer`, and returns when the signal has come. It passes no timeout.
  Verify: `git grep -c -F "def _closed(" -- tests/e2e/test_import.py` prints the path and `1`.
- [ ] 2.3 In `_choose`, replace `opened.value.set_files([])` with `_closed(page, lambda: opened.value.set_files([]))`, and end its docstring on `The first dialog is closed before ⇧A is pressed.`
  Verify: `git grep -c -F "_closed(page, lambda" -- tests/e2e/test_import.py` prints the path and `1`.

## 3 — The runs

Run each command in a shell on the Mac, from the repository root. A run that fails is not written down: report its output.

- [ ] 3.1 Run `repeat 10 { uv run pytest tests/e2e/test_import.py || break }` in zsh, a session each ([D5](design.md#d5)). When every session passes, replace the line `Ten runs: not yet run.` in `design.md` with `Ten runs: passed.`
  Verify: `grep -c -F "Ten runs: passed." openspec/changes/0202-the-file-chooser-wait/design.md` prints `1`.
- [ ] 3.2 Run `uv run pytest tests/e2e`. When it passes, replace the line `Browser directory: not yet run.` in `design.md` with `Browser directory: passed.`
  Verify: `grep -c -F "Browser directory: passed." openspec/changes/0202-the-file-chooser-wait/design.md` prints `1`.
