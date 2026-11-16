# The billing watch — tasks

One phase: the test that holds the raising path, then the guard that makes it green.

## Progress

- [x] 1 — The guarded ask · moderate

## 1 — The guarded ask

- [x] 1.1 In `tests/test_ui_billing.py`, add `test_an_ask_that_raises_does_not_stop_the_watch`, built as
  [D4](design.md#d4) says and bound to `ui:billing:an-ask-that-raises-does-not-stop-the-asking`.
  Verify: `uv run pytest tests/test_ui_billing.py -k an_ask_that_raises` exits 1 with `the condition never held`.

- [x] 1.2 In `isekai/interface/ui/billing.py`, add `Billing._ask` after `check` as [D1](design.md#d1) and [D2](design.md#d2)
  say, and make `watch`'s `loop` call it in place of both `self.check()` calls; `check` and `watch`'s signature stay.
  Verify: `uv run pytest tests/test_ui_billing.py` exits 0.
