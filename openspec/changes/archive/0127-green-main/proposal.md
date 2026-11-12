---
bump: patch
version: 0.86.1
after: [0126-cuts-per-photograph]
---

# Green main

`main` goes green again, on any machine and at any load: the failing checks are fixed in tests and the workflow alone.

Reading map: [design](design.md) holds the decisions and the cost of the tests, [tasks](tasks.md) the reds, then the load-bound tests.

## Why

The last runs of CI on `main` failed at *Gate*, and its *Browser tests* step was skipped behind the red. Below that, tests that pass alone fail under load, so a green run proves little about the code the refactor leans on.

```
CI today                      CI after

Gate (red)                    Gate (red or green)
  |                             |
  x  Browser tests skipped      +-- Browser tests run (if: always())
```

## What Changes

Edits to tests and `.github/workflows/ci.yml` alone. No product file moves.

- The file chooser's handler in `tests/e2e/test_import.py` is a lambda, as Playwright's `page.on` needs.
- The chunked spline in `tests/test_chain.py` is compared with the whole one within `atol=1e-9` pixels, not bit for bit.
- The *Browser tests* step of `.github/workflows/ci.yml` runs whatever the gate says.
- The lock pair in `tests/test_ui_api.py` is ordered so the unlocked twin always commits both updates, and the locked test fails with the lock removed.
- The lock's refusal is asserted by its sentence, not its status alone.
- The imports-stream test reads each import's events off one feed in one loop, and closes the stream only once the stream has framed the `converted` event it asserts.
- Each child that runs until interrupted, in `tests/test_ui_jobs.py` and `tests/test_ui.py`, waits on short sleeps.
- The shutdown test in `tests/test_ui_jobs.py` settles in ten seconds.

No requirement is touched, so the delta is empty and `.openspec.yaml` carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Files: `.github/workflows/ci.yml`, `tests/e2e/test_import.py`, `tests/test_chain.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui.py`, and `tests/test_infra.py`, read and not edited.
- No format version moves, no verb or flag is deprecated, and the product is the same for the same inputs, so the change meets each condition of a patch in [CONTRIBUTING.md](../../../CONTRIBUTING.md).
- No dependency is added.

## Not in this change

- The tattoo screens' browser tests — *e2e tattoo*, once the place fixes are in.
- A MinionsFactory step that runs the browser tests before a merge — out of scope for now; CI holds them.
- The mis-bound scenarios — the *spec audit*.
- The slow build-timeout test, and the tests CI skips: they go with the speed work and the guards.
