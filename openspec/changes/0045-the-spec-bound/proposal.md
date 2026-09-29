---
version: v0.30.2
backlog: [0041·R9, 0043·R6]
---

# 0045 — the spec bound

The gate checks that every scenario has a test and every test a scenario. A new test reads the specs, the active
changes' deltas and the tests' markers; the one unbound key is bound; the no-scan refusal gets its own scenario; the
hold's test checks the stop.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the checker, the key set, and each rebinding |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` |

## Why

**The bindings are kept by hand.** `CLAUDE.md` says there is no spec↔test binding checker, and one scenario,
`run-directory:identity:a-prefix-collision-refuses`, has no test naming it. Nothing would catch a second.

**Bindings point at the wrong thing.** The refusal of a scan no one answers is bound to the mismatch scenario,
and the test of "the hold is bounded and marked" does not check that the hold ends in the stop.

## What Changes

- **`tests/test_spec_bindings.py` in the gate:** a key no test names, a marker naming no key, and a test with no marker
  or more than one each fail ([D1](design.md#d1), [D2](design.md#d2)).
- **The unbound key is bound** to the test that exercises it ([D3](design.md#d3)).
- **A scan no one answers gets its own scenario**, and its tests bind to it ([D4](design.md#d4)).
- **The hold's test checks the stop** ([D5](design.md#d5)).
- **`CLAUDE.md` names the checker** ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - MODIFIED *A pod's host key is checked before anything is sent* — gains a scan no one answers, refused.

## Impact

- **Files:** `tests/test_spec_bindings.py` (new), `tests/test_run_directory.py`, `tests/test_infra.py`, `CLAUDE.md`.
- **Behaviour:** none; the gate refuses a binding it did not check before.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **Reading every scenario against the code** — after the portfolio.
- **Rewriting a spec** — *terse specs*.
