---
bump: patch
after: [0184-the-evaluator-seams]
---

# The serve seams

`serve` and the bundle's build take what a test replaces as arguments, so the server's entry and its bundle leave the patched-modules table of the ratchet.

Reading map: [design](design.md) holds the signatures and the test cost, [tasks](tasks.md) holds a phase for each seam and one for the decision.

## Why

`tests/test_ratchets.py` lists each module whose own names a test patches, and [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) says a row goes with its offender. The rows of `isekai.interface.ui.app` and `isekai.interface.ui.bundle` stand over the patch of `run`, which only `serve` reads, and the patch of the build's binary and timeout. [D61](../../../docs/decisions.md#d61--what-a-test-replaces-in-the-server-is-a-parameter-of-create_app) accepts the patch of `run` and names `serve`'s collaborators as parameters for its reopening. A collaborator passed as an argument needs no patch, so each row is paid by a default parameter and a test that passes its fake.

## What Changes

- `ensure_built(source, *, binary=, timeout=)` in `isekai/interface/ui/bundle.py`, defaulting to `BINARY` and `BUILD_TIMEOUT`. The test that patched them passes the stand-in `npm` and the ceiling.
- `serve(wired, *, port, root=, ensure_built=, run=)` in `isekai/interface/ui/__init__.py`, each defaulting to what the product uses, the server's `run` still imported inside `serve`. The test that patched the library's root, `ensure_built` and `run` passes its three stand-ins.
- The rows of `isekai.interface.ui.app` and `isekai.interface.ui.bundle` leave `PATCHED_MODULES`, and `PATCHED_ROWS` is set to 19.
- D61 in `docs/decisions.md` says `serve` and the bundle's build take theirs as parameters, and its *Accepts* is closed.

Every printed line, refusal and exit code is unchanged, and no test's assertion changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes, so the change carries `skip_specs: true`.

## Impact

- `isekai/interface/ui/bundle.py` and `isekai/interface/ui/__init__.py`: a parameter or three, and the lines of each body that read them.
- `tests/test_ui.py`: stand-ins passed where the bundle's test and the serve test patched.
- `tests/test_ratchets.py`: the rows of `isekai.interface.ui.app` and `isekai.interface.ui.bundle`, and the row ceiling.
- `docs/decisions.md`: D61.

## Not in this change

- `Wiring` grouped, and the proposer on the server's own object.
- The rows that stay: `isekai.interface.ui` for the patch of `serve` in `tests/test_pipeline_cli.py`, `isekai.interface.ui.library` for the patches of `_shrunk` and `_upright`, and `isekai.interface.ui.events`.
- The ratchet's sight and its stale counts.
- Any patch that injects a failure or a race.
- `provision.py`, which is frozen into the pod image.
- Any change to `create_app`, `app.py` or a route, and any file under `ui/`, `tools/` or `evaluation/`.
