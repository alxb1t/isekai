---
bump: patch
version: 0.86.10
after: [0135-the-paydown]
---

# The CLI and the session

The front ends' first half hardened: the verbs' refusals, the remedies they print, the free checks before a pod is rented, and the batch that survives its refusals — tests, the product fixes they found and the mutants that hold them.

Reading map: [design](design.md) holds the decisions, the test cost and the table of what is deleted; [tasks](tasks.md) holds its phases; [mutants](mutants.json) holds the entries phase 5 replays.

## Why

The audit of the suite found the CLI and the render session held by tests that pass on the wrong evidence: *no verb is refused* reads an exit code, so a traceback passes; no test reaches the range checks of `--count`, `--limit` or `--seed`; the free check that must stop a session before it rents runs on the request path alone; the busy-port probe runs in no test. Some findings are product defects: a stage verb with no flow is refused by argparse without listing the tracked flows, which its requirement demands, and the empty runs root's remedy prints `tag --flow`, which the build refuses. The refactor of the verbs and the session leans on these tests, so they harden first.

## What Changes

- A stage verb with no `--flow` is refused with the tracked flows listed, exit 2 as now. A product edit in `isekai/interface/cli.py`.
- The empty runs root's remedy names `assign --flow` in place of `tag --flow`. A product edit in `isekai/interface/render.py`.
- The CLI's own tests: no verb, a count, a seed and a limit out of range, each read in process by its message.
- The remedy sweep drops its bare verbs, reaches a refusal of the session and of `dispatch`, and refuses a printed photograph verb that names a flow.
- The session's tests: a failing free check with no request, the limit's floor and a given limit, a lone source request, an empty runs root, `render` through the parser, the busy-port probe on a real socket, the window of recorded edit durations.
- One CLI batch test in place of the three that rebuild the batch by hand; a failing sampling beside a good one; a chain of pending edits; the replaced draft's content read.
- The change's mutants are added to `tests/mutants.json`, and each dies.

Requirements the delta touches, one line each:

- `cli` · *The rendering verb takes many photographs and either a count or explicit seeds*: gains a scenario for a count or a seed out of range.
- `cli` · *A render session's limit is estimated from its work, at most the configured ceiling*: gains scenarios for a limit below the floor, a limit below one second, and a given limit.
- `edit` · *A render session runs every pending edit*: gains scenarios for a failed sampling beside a good one and for a chain of pending edits.
- `pod-image` · *A render session reaches its tunnel without a proxy*: gains a scenario for a busy port.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: the rendering verb's requirement and the session limit's gain scenarios.
- `edit`: the pending-edit session's requirement gains scenarios.
- `pod-image`: the tunnel's requirement gains a scenario.

## Impact

- Product: `isekai/interface/cli.py` (the parser's refusal of a missing `--flow`) and `isekai/interface/render.py` (one remedy's words). No format version, flag, verb or output moves.
- Tests: `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_render.py`, `tests/test_gpu.py`, `tests/test_generate.py`, `tests/test_edit.py`, `tests/test_review.py`, `tests/test_spec_bindings.py`.
- Docs: `docs/principles.md` names the batch test in place of one it replaces.
- Data: `tests/mutants.json` gains the change's entries, which `make mutants` replays outside the gate.
- Builds after `0135-the-paydown`, which brings the replay mode and the file.

## Not in this change

- The server's half of the front ends: the jobs, the routes, the wire. They are the next version, `the-server`.
- The differences between the front ends — the app's guard and a terminal render, `discard`'s edit thumbnails, `approve --cancel` unguarded. The refactor's *acts* fixes them with their tests.
- The tattoo screens' browser tests: *e2e tattoo*, once the place fixes are in.
- A step that runs the browser tests before a merge: CI holds them.
- The mis-bound scenarios: the *spec audit*.
