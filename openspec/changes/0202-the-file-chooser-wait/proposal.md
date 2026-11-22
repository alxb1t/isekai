---
bump: patch
after: [0201-the-stage-tables]
---

# The file chooser wait

The import's browser test presses `⇧A` again when the dialog it waits for does not open. A test fix: no product line changes, and no phase is a person's.

Reading map: [design](design.md) holds what is known of the flake and the press, [tasks](tasks.md) holds the one build phase.

## Why

The import's browser test failed in CI on the merges of `0144` (run `43605762087`), `0187` (run `44917097991`) and `0198` (run `44947985280`), and passed on the merge after each. Each time `_choose` timed out on its second dialog. None of the three touched page or import code, so the page did not change between a red and a green run.

## What Changes

- `tests/e2e/test_import.py`: after it answers the sheet's first dialog, `_choose` presses `⇧A` and waits a short time for the dialog; when none opens it presses again, a bounded number of times, and its last wait is today's.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change touches no requirement, so it carries `skip_specs`.

## Impact

One test file, `tests/e2e/test_import.py`. No product file changes, no format version moves, and no assertion changes.

## Not in this change

- Any file under `ui/src` or `isekai/`.
- A longer timeout, or a retry of the whole test.
- A proof of the cause: the run cannot open a browser, and CI's browser step proves the change after its merge.
- Any phase a person runs.
- A decision in force: `docs/decisions.md` is untouched.
