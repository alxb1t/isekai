---
bump: patch
after: [0136-the-cli-and-the-session]
---

# The server

The front ends' second half hardened: the jobs' slots, the guard that answers before a handler, Prepare and Stop over HTTP, the billing poll and the event stream, and the page's request bodies — tests, and the mutants that hold them. No product file changes.

Reading map: [design](design.md) holds the decisions, the test cost and the evidence; [tasks](tasks.md) holds its phases; [mutants](mutants.json) holds the entries phase 6 replays.

## Why

The audit of the suite found the server held by tests that pass on the wrong evidence. The alert a failed window close must raise, a second job after one ended and the render slot's steps are held by no test; the address guard is never shown to refuse before its handler, so a write that lands and is then answered 403 stays green.

The billing poll runs in no test, and the one test near it patches the poll away. Prepare and Stop are posted by no pytest, and nothing compares the bodies `ui/src/api.ts` builds with the keys the server reads. The refactor of the server leans on these tests, so they harden first.

## What Changes

- The jobs' tests: the alert on a failed close, a second job after one ended, and the render slot's steps and images read from the child's lines.
- The guard's tests: a foreign `Host` and a foreign `Origin` on a write change nothing on disk; every loopback spelling is sent through the middleware; each refusal of a malformed body is driven by a request; an upload past its declared length is refused before its body is read.
- Prepare and Stop over HTTP, with a real child held on a file: Prepare refused while it runs, Stop interrupting it, Stop idle and of an unknown kind refused, and the cells Prepare takes decided by `unprepared`.
- The billing poll over its double, and the event stream's collection filter and heartbeat.
- One fixture, `ui/src/test/wire.json`, of each request the page builds for the Place and tattoo routes: a vitest holds `api.ts` to it, a pytest holds the server's key tuples to it. A vitest holds `api.ts`'s unwrapping of a refusal.
- The change's mutants are added to `tests/mutants.json`, and each dies.

Requirements the delta touches, one line each:

- `ui` · *A damaged run file or a malformed draft update is refused, never failed*: gains a scenario for a body of the wrong shape.
- `ui` · *Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer*: gains scenarios for a job after an ended one and for the cells Prepare takes.
- `ui` · *The page is told of a job as it runs*: gains a scenario for a stream's collection filter.
- `ui` · *The render job opens the volume, renders, and closes the volume unless kept*: gains scenarios for the alert on a failed close and for the verb's lines.
- `ui` · *Billing state is read from gpunit's own records*: gains a scenario for the poll.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: the requirements listed above gain scenarios; no requirement's text moves.

## Impact

- Product: none.
- Tests: `tests/test_ui_jobs.py`, `tests/test_ui_api.py`, `tests/test_ui.py`, `tests/test_ui_billing.py`, the new `tests/test_ui_wire.py` and the new `ui/src/api.test.ts`.
- Fixture: the new `ui/src/test/wire.json`, read by both suites.
- Config: `ui/tsconfig.json` gains `resolveJsonModule`, so a vitest may import the fixture; `ui/src/types.ts` is read, not edited.
- Data: `tests/mutants.json` gains the change's entries, which `make mutants` replays outside the gate.
- Builds after `0136-the-cli-and-the-session`, which builds after `0135-the-paydown` and brings the replay mode and the file.

## Not in this change

- The billing poll that dies silently when a check raises. It needs a product change; the refactor's *the server* makes it.
- The render route over HTTP with a running child: its steps are held at the job, in phase 1.
- The tattoo screens' browser tests: *e2e tattoo*, once the place fixes are in.
- A step that runs the browser tests before a merge: CI holds them.
- The mis-bound scenarios: the *spec audit*.
