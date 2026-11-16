# The billing watch — design

The watch's loop asks gpunit through one guarded method, so a raise costs one ask. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`Billing.watch` in `isekai/interface/ui/billing.py` starts a daemon thread. Its loop calls `self.check()` on start, then
at each interval while a session runs or an alert is open. `check()` opens the log and runs gpunit through
`Volume.status`, so it can raise `OSError`, and nothing catches it: the first raise ends the thread.

The `ui` requirement *Billing state is read from gpunit's own records* already says gpunit is asked while a session
runs or an alert is open. The defect is against that requirement, so the fix adds a scenario and no requirement.

```
loop ──▶ _ask ──▶ check ──▶ gpunit
          │  raise
          └──────▶ swallowed ──▶ wait one interval ──▶ loop
Check again ──▶ check ──▶ raise reaches the route, as today
```

## Goals / Non-Goals

- Goal: a raise from an ask, on start or at an interval, does not end the watch.
- Goal: a test bound to the new scenario that goes red when the guard is removed.
- Non-goal: showing the failure anywhere. The page, the band and the log stay as they are.
- Non-goal: guarding Check again, `POST /api/billing/check`, which raises to its caller as today.
- Non-goal: any other edit of `billing.py` or a move of `app.py`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the loop asks through a new method `Billing._ask`, which calls `check()` and returns nothing | one guard serves the start ask and the interval ask, and `check()` stays unguarded for Check again | a `try` inside `check()` — Check again would stop raising; a `try` around the whole loop — the first raise would still end it |
| [D2](#d2) | `_ask` catches `Exception` | an ask runs a file open and a child process, and any raise ends the thread; the watch's one job is to keep asking | `OSError` alone — a `ValueError` from the environment's read would still end the thread |
| [D3](#d3) | a swallowed raise records nothing | what a failed check shows on the page is a decision of its own, and no requirement asks for it | a log line or a published state — it adds behaviour a patch may not |
| [D4](#d4) | the test is one in `tests/test_ui_billing.py`, on a gpunit double whose ask raises on its first and third ask | the first covers the start ask, the third an interval's ask, both through the one method | one raise only — it leaves a guard on one call site passing |

### D1

`watch` keeps its signature and its thread. Its loop becomes:

```python
def loop() -> None:
    self._ask()
    while not self._stop.wait(interval):
        if self._running() or self.alerting():
            self._ask()
```

`_ask` is a method beside `check`, with a docstring saying a raise costs this ask alone.

### D2

`except Exception` is the one breadth that keeps the thread alive for every ask. It never catches `BaseException`, so a
`KeyboardInterrupt` or `SystemExit` still ends the thread.

### D3

The next ask is at the next interval, and only while a session runs or an alert is open, as the requirement says.
Nothing is asked when neither holds, even after a raised start ask.

### D4

- The double is `Volume(run=…, records=…)` with a `run` that records each ask, then raises `OSError` on the asks
  whose number is in a set holding the first and the third.
- The session is `lambda: True`, so every interval asks.
- The test waits with `_until` for the fifth ask and asserts `thread.is_alive()`.
- After `close()` and the join, it adds the next ask's number to the set and calls `billing.check()`, which raises
  `OSError`: Check again is as today.

## Tests

One unit test is added, in the existing file. No test is deleted, merged or edited, so there is no `I16` table.

| layer | before | after | command |
|---|---|---|---|
| unit, `tests/test_ui_billing.py` | 5 | 6 | `grep -c '^def test_' tests/test_ui_billing.py` |
| end-to-end | 0 added | 0 added | no browser test: the watch is a thread, and no screen changes |

The new test is red with the guard removed: the unguarded loop ends at its first ask, so the ask count never reaches
the test's target and `_until` raises. It runs at the existing test's interval, `0.01` s, so it needs no `slow` marker
when green. The existing watch test holds the quiet path, the new one the raising path; a new end-to-end test fits
neither, and none is added.

## Dependencies

None.

## Risks / Trade-offs

- A check that always raises is asked again every interval, silently. The page shows no sign of it. That is today's
  behaviour for the first raise, widened to every one; the page's view of it is a card if wanted, not this patch.
- `except Exception` hides a bug in `check()` from the thread. The route's Check again still raises it to the person.

## Verdict

Ready to build: `_ask` and the loop's calls, the test, and the scenario in the delta.
