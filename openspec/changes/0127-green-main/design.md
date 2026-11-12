# Green main — design

Fixes in tests and the workflow alone that turn `main` green on any machine and at any load. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

CI on `main` fails at *Gate* on `tests/test_chain.py`, and its *Browser tests* step has no `if:`, so the red gate skips it. That step fails in turn on every run: `tests/e2e/test_import.py` hands Playwright a built-in method as the file chooser's handler.

Tests in `tests/test_ui_api.py`, `tests/test_ui_jobs.py` and `tests/test_ui.py` pass alone and fail under load. Each leaves an outcome to thread scheduling, a dropped event or a thirty-second child.

```
phase 1  the reds       chooser · spline · CI's browser step
phase 2  under load     lock pair · refusal sentence · imports stream · idle children · settle
```

The change is built after `0126-cuts-per-photograph` releases, for the machine's load. The two share no file known at the cut.

## Goals / Non-Goals

Goals:

- `make gate` is green wherever it runs, and `make e2e` runs after a red gate.
- Each load-bound test holds what it claims whatever the scheduler does.

Non-Goals:

- No product file moves. The slow build-timeout test, the tests CI skips and the duplicates stay as they are.
- No test is added, deleted or merged.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The change holds the failing checks of `main` and the load-bound tests, nothing else: the slow build-timeout test goes with the speed work, the tests CI skips with the guards, the duplicates after | one invariant: `main` green, on any machine and any load | the build-timeout test, the skipped tests and the duplicates, here |
| [D2](#d2) | The chunked spline is compared within `atol=1e-9` pixels; no product change | the product is float64, and nothing promises equal bits | a product change to make the chunks bit-equal |
| [D3](#d3) | The chooser's fix and the spline's are proven by CI on the merge's push, read by the plan; a red run is fixed by a patch at once | the sandbox has no browser and no Linux; the chooser's fix ran here before | a local proof of either |
| [D4](#d4) | The change is cut now, after `0126-cuts-per-photograph`: its build waits until that version releases | the machine's load; `0125-the-outline-gestures` released as v0.85.0 before the cut, so it is not named | a cut that builds beside the other version |
| [D5](#d5) | The change is `0127-green-main`, a patch, built on Sonnet 5.5 high and converged on Codex checkers as the last versions of this repository | small tests to place; the house's converge | — |

### D1

The edits, by file:

| file | edit |
|---|---|
| `tests/e2e/test_import.py` | the chooser's handler is a lambda |
| `tests/test_chain.py` | the spline's chunks are compared within a tolerance |
| `.github/workflows/ci.yml` | the *Browser tests* step carries `if: always()` |
| `tests/test_ui_api.py` | the lock pair is ordered; the refusal is asserted by its sentence; the stream test reads one feed in one loop |
| `tests/test_ui_jobs.py` | each child that runs until interrupted waits on short sleeps; the shutdown test settles in ten seconds |
| `tests/test_ui.py` | the stream test's idle child waits on short sleeps |

`tests/test_infra.py` is read and not edited. Its checks of the workflow hold with `if: always()` in the step: both `run:` lines exist, each step carries `ISEKAI_PLACEMENT: absent`, and no one-line `run:` holds `": "`.

### D2

`np.array_equal(spline(grid), whole)` becomes `np.testing.assert_allclose(spline(grid), whole, rtol=0, atol=1e-9)`. The arrays are float64 pixel coordinates in about `-10..60`, so `1e-9` is far under any pixel. `tests/test_chain.py`'s test keeps its name and its `spec_exempt` mark.

### D3

Phase 1 cannot be proven here: `make gate` leaves `tests/e2e` out, and Chromium does not start in an unattended run. Its checks are the gate's type check of the lambda and the workflow's text. The proof is CI's run on the push that merges the change.

### D4

`after:` names `0126-cuts-per-photograph` alone. Its archive folder is in `HEAD` before this change builds.

### D5

The phases rate `moderate`: small tests to place, and a lock test ordered by an event. The build runs on Sonnet 5.5 high whole.

## Load-bound tests

How each of phase 2's tests stops depending on the scheduler.

**The lock pair.** `_overlap` in `tests/test_ui_api.py` sets `reached` inside `check` before the second update's precondition runs. Without the lock, the first update may write before that precondition, so the outcome is thread scheduling, and the locked test can pass with the lock removed from the product.

```
before   second: check -> reached.set() -> precondition        first writes when reached is set
after    second: check -> precondition -> reached.set()        first writes once the second has passed
```

With the lock, the second waits at `Waited`, which sets `reached`, so the first writes and the second's precondition then refuses. Without it, the second passes its precondition before the first writes, so both commit and the locked test fails.

**The refusal's sentence.** `_overlap` returns each update's status and body. The locked test asserts the second's `refusal` holds `changed since this page last read it`, the sentence of `_precondition` in `isekai/interface/ui/app.py`, as the other tests of that refusal in `tests/test_ui_api.py` do.

**The imports stream.** The test reads each import off one feed in turn, and the first read drops the other import's events. `_until_each_read` takes each import with its uploads, reads the feed once and keeps each import's `file` events apart. `_until_read` stays as the one-import call over it, so its other callers do not change.

**The idle children.** A child that sleeps thirty seconds loses an interrupt that lands before its sleep starts, for the whole sleep. Each child becomes `while True: time.sleep(0.05)`, so a lost interrupt costs the next turn of the loop. The children are `SLEEP` and the scripts around it in `tests/test_ui_jobs.py`, and the stream test's child in `tests/test_ui.py`.

**The shutdown test.** `_stop_with_window` in `tests/test_ui_jobs.py` settles in two seconds, which a loaded machine outlasts. It settles in ten, the `WAIT` of `tests/test_ui_api.py`'s reads.

## Tests

The change adds and removes no test and adds no end-to-end run. Counts are those of `uv run pytest --collect-only -qq --ignore=tests/e2e tests/test_chain.py tests/test_infra.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui.py` at the base, and the same command holds them after.

| file | tests before | tests after |
|---|---|---|
| `tests/test_chain.py` | 24 | 24 |
| `tests/test_infra.py` | 77 | 77 |
| `tests/test_ui_api.py` | 114 | 114 |
| `tests/test_ui_jobs.py` | 33 | 33 |
| `tests/test_ui.py` | 20 | 20 |
| `tests/e2e/test_import.py` | 3 | 3 |

| layer | added | removed | command |
|---|---|---|---|
| unit and integration | 0 | 0 | the command above |
| end-to-end | 0 | 0 | `uv run pytest --collect-only -qq tests/e2e/test_import.py`, whose count is in the table above |

No test is deleted or merged, so there is no table of what carries each one's assertions (`T5`). Each edited test keeps its `spec` or `spec_exempt` mark, so the spec-bindings test is unchanged.

## Dependencies

None.

## Risks / Trade-offs

- Phase 1's chooser and spline fixes are proven only by CI on the merge's push ([D3](#d3)). A red run is fixed by a patch at once.
- A load-bound test proves its order by reading, not by a red run: the scheduler cannot be made to fail it on demand. The reviewer reads the locked test against the product's lock.
- `if: always()` runs the browser tests after a cancelled gate too. That costs minutes of CI and hides nothing.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). No decision of `docs/decisions.md` is added or amended, and no requirement is touched.
