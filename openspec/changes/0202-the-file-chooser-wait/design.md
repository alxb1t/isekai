# The file chooser wait — design

The import's browser test presses `⇧A` once after it answers the sheet's first dialog, and a second dialog sometimes never comes; the helper presses again when none opens. Verdict: ready to build, in the one phase of [tasks](tasks.md).

## Context

The sheet opens a file dialog as it mounts: `onMounted` calls `picker.value?.click()` (`ui/src/components/ImportSheet.vue:417-420`). `⇧A` runs the same `click()` (`ui/src/components/ImportSheet.vue:377-380`). The helper `_choose` answers the first dialog with no files, presses `⇧A` at once and waits out Playwright's default timeout for a second (`tests/e2e/test_import.py:34-45`). Its callers are `test_each_chosen_file_shows_its_upload_then_its_result` and `test_importing_a_new_collection_opens_its_hub_with_every_source_unassigned`.

The browser tests run in CI by `make e2e` and not in the gate (`Makefile:27-28`), because the sandbox of an unattended run cannot bind a loopback port: the `served` fixture does (`tests/e2e/conftest.py:179`). So nothing in this change is run in a browser by the build.

## Goals / Non-Goals

- **Goals:** a press of `⇧A` that the browser answers with no dialog is pressed again; the helper never waits less than it does today; no phase is a person's.
- **Non-Goals:** a product change, a longer timeout, a retry of the whole test, a changed assertion, a new test, a proof of the cause, a decision in force.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `_choose` presses `⇧A` through `_pressed`, which presses again when no dialog opens, a bounded number of times, its last wait today's | Q335, Q336: the fix must be safe without knowing the cause, and the worst case of a bounded press is today's test | a wait on a page event nobody has shown; a longer timeout; a retry of the whole test |
| [D2](#d2) | The cause is not proved here, and CI's browser step is the proof | Q337: the run cannot open a browser, and every browser test of this repository was proven by CI after its merge | a probe run by a person |
| [D3](#d3) | No phase is a person's | Q338: a version that changes a browser test carries no phase that a person runs | the proof and the runs as a person's phases |

### D1

`tests/e2e/test_import.py` gains two constants above `_choose`: `PRESSES = 4`, the presses that wait a short time, and `SHORT_MS = 2_000`, that time in milliseconds.

It gains `_pressed(page: Page) -> FileChooser`. For each of `PRESSES` it opens `page.expect_file_chooser(timeout=SHORT_MS)`, presses `Shift+A` inside it, and returns the dialog; a Playwright timeout goes on to the next press. After them it opens `page.expect_file_chooser()` with no timeout given, presses `Shift+A` once more and returns that dialog, so the last wait is the default one the helper has today. The timeout it catches is `TimeoutError` of `playwright.sync_api`, imported under the name `PlaywrightTimeout` beside the names the file already imports from there.

`_choose` calls `_pressed(page).set_files(...)` with the list it passes today, in place of its second `expect_file_chooser` block. Its first block, the dialog the mount opens, is untouched.

### D2

What is known of the cause is in [The cause](#the-cause). A red run of this test after this change is a product question, and it gets an investigation of its own.

### D3

The build writes the helper and the gate holds what a gate can: the file still collects, and no other line of it changes. CI runs `make e2e` on the merge.

## The cause

**Not proved.** The reading at the cut was a race: `set_files` returns once Playwright has handed the browser its files, not once the page's picker has closed its dialog, and a `click()` on a picker whose dialog is still closing opens no second dialog. A probe of that reading, run on the Mac on 2026-11-22, did not reproduce it: no iteration of its bare variant was suppressed. So the cause may be the race at CI's speed, or something this change does not name.

What is certain:

- CI was red on runs `43605762087`, `44917097991` and `44947985280`, and green on the merge after each.
- Each time the failing wait was the `expect_file_chooser` that follows the answered dialog.
- None of the three merges touched page or import code.

A second press answers the race reading, and costs nothing under any other: when every short wait times out, the helper ends on the wait it has today.

## Tests

The change adds no test and removes none.

| layer | tests before and after | command |
|---|---|---|
| end-to-end, `tests/e2e/test_import.py` | the same three | `git grep -c -e "^def test_" -- tests/e2e/test_import.py` prints the path and `3` |

The callers of `_choose`, named in Context, run as before, with the press of [D1](#d1) between the dialogs.

## Dependencies

None.

## Risks / Trade-offs

- **The cause is another** → the helper behaves as today and the test stays flaky; CI shows it, and [D2](#d2) says what follows.
- **A page that drops one key press passes on the next** → accepted (Q336): a person presses a key twice, and it is not worth a red run.
- **A dialog that opens after a short wait has ended** → the next press finds a picker whose dialog is open and opens none; the last wait then times out as today's test does. Never worse than today.

## Verdict

Ready to build, in the one phase of [tasks](tasks.md): the press.
