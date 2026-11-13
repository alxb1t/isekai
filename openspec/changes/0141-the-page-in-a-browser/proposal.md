---
bump: patch
after: [0140-the-sheet-and-the-keys]
---

# The page in a browser

The browser tests pass whatever the page logs, and what only a browser shows is held by no test: the key list's focus, the keys typed into a field, and Approve pressed while a save is held. This change adds a guard that fails a browser test on a page error, a console error or a server error, and browser tests that hold those things.

Reading map: [design](design.md) holds the decisions, the guard's rules, the journeys and their cost, [tasks](tasks.md) its phases.

## Why

The audit read the browser suite and found what it cannot see. CI runs it after the merge, because a build cannot start Chromium (Q63), so each test below is written to fail loudly, never falsely green.

| finding | what it leaves unheld |
|---|---|
| `A7` | no hook fails a test on a page error, a console error or a 5xx: a page that throws still passes |
| `A3` with `VT-10` and `VT-26` | the key list's held focus is proven by a grep of its component, a command typed in a tag field is held by a unit test over a double, and the pane moves and `Esc` are never pressed in a browser |
| `A4` with `VT-1` | whether Approve waits for a save held at the network, and sends a lone refused save again, is unproven: the draft's save is sent with `keepalive`, and whether the browser tests' request routing sees it is unverified |

## What Changes

- `tests/e2e/guard.py` and the `context` fixture of `tests/e2e/conftest.py`: a browser test fails on a page error, a console error that is no failed load, a 5xx, and a 4xx it did not declare. `tests/e2e/test_queue.py` and `tests/e2e/test_routes.py` declare theirs.
- `tests/test_e2e_guard.py` holds the guard's rules without a browser.
- `tests/e2e/test_keys.py`: one journey of the key list, a field, `Esc` and the pane keys, on a collection of its own.
- `tests/e2e/test_queue.py`: Approve pressed while the draft's save is held at the network, and a lone refused save sent again, with `tests/e2e/held.py` for the held request.

Each requirement the delta touches:

- `ui` · *A dialog holds the focus from its first control while it is open*: gains a scenario for the key list holding the focus in a browser.
- `ui` · *Each command has one key, declared once, and none fires while typing*: gains a scenario for a letter typed in a tag field being text, and one for the pane keys moving the focus.
- `ui` · *The page's save state is true to the requests in flight, and a pending edit is sent on leaving*: gains a scenario for an approval waiting for a save held at the network, and one for a refused save sent again by the next approval.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: scenarios under existing requirements.

## Impact

- Tests: `tests/e2e/conftest.py`, `tests/e2e/test_queue.py`, `tests/e2e/test_routes.py`, `tests/e2e/test_import.py`, and new `tests/e2e/guard.py`, `tests/e2e/held.py`, `tests/e2e/test_keys.py`, `tests/test_e2e_guard.py`.
- Specs: the `ui` capability, by the delta of this change.
- Product: none. No format version moves, no verb or flag changes, and no requirement is added.
- Waits for `0140-the-sheet-and-the-keys`: its delta modifies the same requirements, so this one restates them as they will stand after it.
- Proven by CI after the merge ([D8](design.md#d8)): a build cannot start Chromium, so a red run is fixed by a patch at once.
- A patch by [CONTRIBUTING](../../../CONTRIBUTING.md): each scenario is added under a requirement that stands.

## Not in this change

- The tattoo screens' browser tests: *e2e tattoo*, once the place fixes are in.
- A MinionsFactory step that runs the browser tests before a merge: CI holds them.
- `VT-11`, `VT-13`, and the browser suite's splits, merges and shared state: the sweep after the refactor's last version.
- The sheet's undo, redo, remove and ④, and the `⌥` key: the spec audit takes them.
- A save that fails after the person switched sheet drops the edit: the refactor's page version fixes it.
- A key moving from a unit test to a browser test: it changes its `Layers` line, which modifies a requirement.
