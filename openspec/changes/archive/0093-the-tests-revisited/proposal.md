---
bump: patch
version: v0.62.2
backlog: [0091·R4, 0091·R9]
---

# 0093 — the tests revisited

The suite read whole: a test may carry a key per behaviour it holds, a new case goes into an existing test first, the
browser tests that share a page become one, and the loopback and flaky tests run without a socket or a clock. No
behaviour moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the merges |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
1 the rule      a test carries one key per behaviour · vitest's spec() takes several · extend before adding
2 the flakes    the proxy and the shutdown tests socketless, back in the gate · the timers and ps made deterministic
3 the browser   the tests sharing a page merged · the two dropped scenarios back · 0091·R4, R9
```

## Why

**Each browser test pays a context and a page boot, and versions kept adding tests rather than steps.** A step that
adds a behaviour could not carry its key, since a test held one marker, so `0091` dropped two scenarios. Four tests left
the gate because they served on loopback, and three more flaked under the sandbox or a loaded runner.

## What Changes

- **A test carries one or more `spec` keys**, or one `spec_exempt`; vitest's `spec()` likewise ([D1](design.md#d1)).
- **Extend before adding** is a project rule ([D2](design.md#d2)).
- **The proxy and the shutdown tests** run in-process and return to the gate; `LOOPBACK` goes ([D3](design.md#d3)).
- **The watchdog, bundle-timeout and overlap tests** wait on events, not the clock ([D4](design.md#d4)).
- **The browser tests sharing a page** merge, the dropped scenarios return as second keys ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The running render opens in a drawer every screen offers*: the scenario *the drawer fits its widest grid*.
- `ui` — *A version says what it was, and Compare sets an image beside…*: the scenario *the pick holds its width*.

## Impact

- `tests/test_spec_bindings.py`, `ui/src/test/spec.ts`, `tests/test_render.py`, `tests/test_ui.py`,
  `tests/test_ui_api.py`, `tests/e2e/`; `Makefile`, `.github/workflows/ci.yml`; `CONTRIBUTING.md`, `CODING_STANDARDS.md`.

## Not in this change

- The browser tests back in the gate: Chromium never starts inside the sandbox, which is MinionsFactory's to fix.
- `0091·R7`, `0091·R8`: their trigger is the next change to `ImportSheet.vue`.
- Deleting unit tests: the keys with many tests are refusal and provisioning families, not duplicates.
