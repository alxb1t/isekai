---
bump: patch
---

# The billing watch

A gpunit ask that raises no longer ends the billing watch's thread: the watch asks again at the next interval.

Reading map: [design](design.md) holds the guard's place, its breadth and the test's plan, [tasks](tasks.md) holds the one phase.

## Why

`Billing.watch`'s loop calls `check()` with no guard, and a check can raise `OSError`: it opens the log and runs gpunit
as a child process. One raise ends the thread, and gpunit is never asked again. The requirement says it is asked every
half minute while a session runs or an alert is open; this change makes the loop keep that.

## What Changes

- `Billing.watch`'s loop asks through one guarded method: a check that raises costs that ask alone, and the loop waits
  for the next interval and asks again.
- The start ask and each interval's ask are guarded alike.
- Check again, the route's ask, is not guarded: it raises to its caller as it does today.
- A scenario under *Billing state is read from gpunit's own records*, and a test bound to it, red with the guard
  removed.

Requirements touched:

- MODIFIED `Billing state is read from gpunit's own records` — gains the scenario *an ask that raises does not stop the
  asking*; its text and its other scenarios are as they were.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — one scenario under the billing requirement.

## Impact

- `isekai/interface/ui/billing.py` — `Billing._ask` and the calls of `watch`'s loop.
- `tests/test_ui_billing.py` — a test added; no assertion of an existing test changes.
- The living `ui` spec gains the scenario when the release folds the delta.
- No format version, flag, verb or image-frozen file moves.

## Not in this change

- What a check that raises shows on the page: the band, a message, a log line. A card, if the person wants it.
- Check again's own failure: the route raises as today.
- Any move of `app.py`: that is `the-surface`, after this version.
- A new decision: the guard sets no rule.
