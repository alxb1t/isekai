---
bump: patch
version: 0.86.5
after: [0130-the-record]
---

# The net's holes

No patch in the suite passes blind, and a pre-flight can measure a move: the silent patches are made loud, a guard holds every patch to a name its module reads, and a mutation runner of the standard library says which mutants a set of tests kills.

Reading map: [design](design.md) holds the decisions, each silent patch with its remedy and the runner's rules, [tasks](tasks.md) the silent patches and the guard, then the runner.

## Why

A patch in a test is a promise that the product reaches the patched name. Several promises are never checked: a tripwire that raises on a path the test never takes, a stand-in for a host that no assertion shows was called, and a patch that stays when the code that read it moves. The refactor that follows moves code between modules, so a patch left pointing at a name nothing reads goes on passing.

The refactor also needs to know whether a test notices a line it moves. The audit measured that with scripts that need a coverage database kept outside the repository; a program in `tools/`, of the standard library alone, measures it from a clean checkout.

```
today                                       after

a tripwire no test shows can fire           each tripwire has a twin that fires it
a stand-in no assertion shows was asked     the stand-in records its calls, and a test reads them
a patch of a name nothing reads: unseen     a guard names it
which mutants a test kills: an audit's      uv run python -m tools.mutate <path:lines> --tests <files>
  scripts, off the repository
```

## What Changes

Edits to tests, a tool and one document. No `.py` under `isekai/` or `evaluation/` moves.

- Each silent patch is made loud: the sentinel of the suite's model records, the tripwires on the model record, on the wiring's reader, on the tagger's provisioning and on the photograph's file, and the stand-ins for the Ollama host, the library's root, the bundle's build, the chunked spline's kernel and the importer's clean and write.
- `tests/test_ratchets.py` gains a guard that every patch of a module of `isekai`, `evaluation` or `tools` names a name that module reads, with its twin.
- `tools/mutate.py` runs the named tests unmutated in a copy of the tracked files, then each mutant of the chosen lines one at a time, and prints each verdict with its operator; `tests/test_mutate.py` holds it.
- `CONTRIBUTING.md` says when to run it.

No requirement is touched, so the delta is empty and `.openspec.yaml` carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Tests edited: `tests/test_caption.py`, `tests/test_pipeline_cli.py`, `tests/test_wd14.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui.py`, `tests/test_chain.py` and `tests/test_importing.py`, each by the silent patches it holds, and `tests/test_ratchets.py` by the guard and the walk it shares with the patch ratchet.
- Added: `tools/mutate.py` and `tests/test_mutate.py`.
- Document edited: `CONTRIBUTING.md`.
- Read and not edited: the autouse fixture of `tests/conftest.py`, which the sentinel proves, `isekai/shared/chain.py`, which the runner's first real run mutates in a copy, and every other product file a patch names.
- No format version moves, no verb or flag is deprecated, and the product is the same for the same inputs, so the change meets each condition of a patch in [CONTRIBUTING.md](../../../CONTRIBUTING.md).
- No dependency is added: the runner imports the standard library alone and runs `pytest`, which the project already has.

## Not in this change

- A patch removed or a test deleted: each silent patch stays and gains what proves it is reached.
- A product file edited to give a patch a seam.
- A mutation run over the product, and a mutant killed: the runner reports survivors, and the refactor versions that move code run it.
- A coverage database, a mutation package, or a plugin of pytest.
- The mis-bound scenarios — the *spec audit* — and the tattoo screens' browser tests — *e2e tattoo*.
