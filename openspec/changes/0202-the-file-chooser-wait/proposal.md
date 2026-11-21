---
bump: patch
after: [0201-the-stage-tables]
---

# The file chooser wait

The import's browser test waits for the dialog it has just answered to close before it presses `⇧A`. A test fix: no product line changes.

Reading map: [design](design.md) holds the cause of the flake, the probe that shows it and the wait, [tasks](tasks.md) holds the proof, the wait and the runs.

## Why

The import's browser test failed in CI on the merge of `0187` (run `44917097991`) and on the merge of `0144` (run `43605762087`), and passed on the merge after each. Both times `_choose` timed out on its second dialog. `0187` touched no page or import code, so the race is the test's own.

## What Changes

- `tests/e2e/test_import.py`: `_choose` waits for the first dialog to close before it presses `⇧A`.
- `design.md`: the cause of the timeout and the evidence for it, written once a probe has shown it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change touches no requirement, so it carries `skip_specs`.

## Impact

One test file, `tests/e2e/test_import.py`. No product file changes, no format version moves, and no assertion changes.

## Not in this change

- Any file under `ui/src` or `isekai/`. A page that drops the key is a product fault: it wants its own scenario, when the probe of [design](design.md#d2) shows it.
- A longer timeout.
- A retry of the whole test, or of the key press.
- A decision in force: `docs/decisions.md` is untouched.
