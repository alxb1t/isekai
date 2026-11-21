# The file chooser wait — design

The import's browser test presses `⇧A` at once after it answers the sheet's first dialog, and a second dialog sometimes never comes; the helper waits for the first to close, on an event the page shows. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The sheet opens a file dialog as it mounts: `onMounted` calls `picker.value?.click()` (`ui/src/components/ImportSheet.vue:417-420`). `⇧A` runs the same `click()` (`ui/src/components/ImportSheet.vue:377-380`). The helper `_choose` answers the first dialog with no files, presses `⇧A` at once and waits out Playwright's default timeout for a second (`tests/e2e/test_import.py:34-45`). Its callers are `test_each_chosen_file_shows_its_upload_then_its_result` and `test_importing_a_new_collection_opens_its_hub_with_every_source_unassigned`.

The browser tests run in CI by `make e2e` and not in the gate (`Makefile:27-28`), because the sandbox of an unattended run cannot bind a loopback port: the `served` fixture does (`tests/e2e/conftest.py:179`). The cut hit the same limit, so the proof of the cause is not run here.

## Goals / Non-Goals

- **Goals:** the cause is named with its evidence; `_choose` no longer races the dialog it has just answered; the import's browser tests pass repeatedly.
- **Non-Goals:** a product change, a longer timeout, a retry, a changed assertion, a new test, a decision in force.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `_choose` waits for the first dialog to close, on an event the page shows, before it presses `⇧A` | Q324: the test is waiting for a dialog the browser has not yet allowed to open | a longer timeout; a retry of the test or of the key press, which hides the race |
| [D2](#d2) | A probe repeats the helper's open, answer and press, in a `bare` and a `held` variant, and reads the page's events; it is deleted once the cause is written | Q324, Q325: repeating the test cannot show a flake that fails seldom, and the named cause carries the fix | repeating the whole test alone |
| [D3](#d3) | The proof and the runs are `**HUMAN**` phases | the run's sandbox cannot bind a loopback port, so a machine phase could not run its checks | a machine phase whose `Verify:` can never run |
| [D4](#d4) | A page that drops the key halts the change | Q324: a product fix wants its own scenario, and a patch holds none | fixing `ui/src` in this change |
| [D5](#d5) | The import's browser tests run repeatedly as separate sessions | the `served` fixture is session-scoped and one test commits the fixed name `e2e-imported`, which the library refuses the second time (`isekai/pipeline/importing.py:577-578`) | one session that repeats the file with `--keep-duplicates`, which fails on the second commit whatever the wait |

### D1

The wait is a function `_closed(page, answer)` in `tests/e2e/test_import.py`. It arms a listener for the signal the proof names, calls `answer`, and returns when the signal has come. It passes no timeout. `_choose` calls it around its first `set_files([])`, so `⇧A` is pressed once the first dialog is closed.

### D2

Readings A and B fit one symptom:

- **Reading A**: `⇧A` clicks the picker while the first dialog is still open, and the browser opens no further one.
- **Reading B**: Playwright's interception of dialogs is off between the helper's `expect_file_chooser` blocks, so a dialog that does open is never reported.

The probe has the helper's shape in its `bare` variant, and keeps one `filechooser` listener on for the whole loop in its `held` variant. A `held` variant that fails too is Reading A.

The probe is a temporary `tests/e2e/test_probe.py`, never committed:

```python
"""A throwaway probe of the helper's race, deleted once the cause is written."""

from pathlib import Path

import pytest
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from tests.e2e.conftest import Served

LISTEN = """() => {
  window.__seen = []
  const picker = document.querySelector('.import__picker')
  for (const name of ['click', 'cancel', 'change', 'input', 'focus', 'blur'])
    picker.addEventListener(name, () => window.__seen.push(name))
  for (const name of ['focus', 'blur', 'visibilitychange'])
    addEventListener(name, () => window.__seen.push('window ' + name))
  addEventListener('keydown', (e) => window.__seen.push('keydown ' + e.code), true)
}"""


@pytest.mark.parametrize("variant", ["bare", "held"])
def test_probe(page: Page, served: Served, variant: str) -> None:
    lines: list[str] = []
    if variant == "held":
        page.on("filechooser", lambda chooser: None)
    for n in range(200):
        page.goto(served.url)
        with page.expect_file_chooser() as first:
            page.get_by_role("button", name="New collection").click()
        page.evaluate(LISTEN)
        first.value.set_files([])
        try:
            with page.expect_file_chooser(timeout=1000):
                page.keyboard.press("Shift+A")
            outcome = "ok"
        except PlaywrightTimeoutError:
            seen = page.evaluate("window.__seen")
            keyed = "click" in seen and "keydown KeyA" in seen
            outcome = "suppressed" if keyed else "dropped"
        lines.append(f"PROBE {variant} {outcome} {n} {page.evaluate('window.__seen')}")
    Path(".data").mkdir(exist_ok=True)
    Path(f".data/probe-{variant}.txt").write_text("\n".join(lines) + "\n")
```

An iteration ends in one of these words:

- `ok`: the dialog `⇧A` opens comes.
- `suppressed`: the page got the key and clicked the picker, and no dialog came.
- `dropped`: the page did not get both, which is a fault of the page ([D4](#d4)).

The `seen` list on each line is the order of the page's events, and the signal of [D1](#d1) is read from it.

### D3

A `**HUMAN**` phase is run on the Mac, outside the sandbox, with the commands of its tasks. Its `Verify:` is a fact written on disk, so a phase nobody ran does not close.

### D4

The build halts when an iteration ends `dropped`, or when the `held` variant never ends `suppressed`: the cause is not the one [D1](#d1) waits for.

- A page that drops the key is a product fault with its own scenario.
- An interception that is off between the blocks is a different test fix, which the person decides.
- A page that shows no event of the first dialog's closing leaves the wait nothing to hang on: task 1.6 stops, and a rescue rewrites the wait.

### D5

The command is `repeat 10 { uv run pytest tests/e2e/test_import.py || break }`, run in zsh, so a failed session stops the loop. Each session boots a fresh `served` library, so the commit of `e2e-imported` is the first in it. The refusal is in `isekai/pipeline/importing.py:577-578`, and the fixture is `tests/e2e/conftest.py:199`.

## The cause

**Read at the cut, not yet run.** The mount's `click()` opens the first dialog, and the helper answers it with `set_files([])`. `set_files` returns once Playwright has handed the browser its files, not once the page's picker has finished closing its dialog. `⇧A` then runs `click()` on a picker whose dialog may still be open, and the browser opens no second: the helper waits out its timeout. This is Reading A of [D2](#d2).

Evidence at the cut:

- CI was red on run `44917097991` (the merge of `0187`) and green on run `44920742303`, the merge after.
- The same test failed the same way on run `43605762087` (the merge of `0144`).
- `0187` touched no page or import code, so the page did not change between a red and a green run.
- The failing wait is the `expect_file_chooser` that follows the answered dialog, the only place the helper's dialogs meet.

### Proof

Proof: not yet run.

### The runs

Ten runs: not yet run.

Browser directory: not yet run.

## Tests

The change adds no test and removes none. The probe, `tests/e2e/test_probe.py`, is temporary and never committed. No end-to-end run is added.

| layer | tests before and after | command |
|---|---|---|
| end-to-end, `tests/e2e/test_import.py` | the same three | `git grep -c -F "def test_" -- tests/e2e/test_import.py` prints the path and `3` |

The callers of `_choose`, named in Context, run as before, with its wait between the dialogs ([D1](#d1)).

## Dependencies

None.

## Risks / Trade-offs

- **The probe shows no failure** → `suppressed` is absent and a **HALT CHECK** stops the build: the cause is not shown, and a rescue reads the output.
- **The page drops the key** → [D4](#d4): the build halts, and the product fix is another version's.
- **Repeated runs cannot prove a rare flake gone** → the named cause, with the probe's evidence, carries the fix (Q325).

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the proof, the wait and the runs.
