---
bump: patch
version: 0.87.1
---

# The verbs move

`cli.py` hands its verbs to a package: each verb becomes one row its family's module holds, and the file keeps the parser's assembly and the dispatch. Behaviour is unchanged.

Reading map: [design](design.md) holds the package, the row and the proofs, [tasks](tasks.md) holds the phases.

## Why

`isekai/interface/cli.py` is the largest file of the interface and holds every verb's arguments in `build_parser` and every verb's run in a chain of branches in `dispatch`. A verb's name, arguments and run sit in separate places, and the file and `build_parser` are rows of the size ratchet.

A move, behind the record that pins every verb's arguments in order, makes the next versions small: the command builder, the stage registry and the seams each start from one row a verb.

## What Changes

- `isekai/interface/verbs/` is new: a front door, a shared module, and a module for each family of verbs.
- `build_parser` reads the rows in the verbs' order, and `dispatch` runs a row's run where it has one.
- `cli.py` keeps `VERBS`, `build_parser`, `dispatch`, `_per_item`, `_assign`, `_migrate`, `_dispatch_argv` and `main`, and shrinks to a front door.
- The ratchet rows of the file and of `build_parser` are removed, and a decision says a verb is declared once.
- The documents the move makes false are amended, and the moved mutants take their new path.
- Requirements: none touched. No spec delta.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `isekai/interface/cli.py` loses the verbs' arguments and runs.
- `isekai/interface/verbs/__init__.py`, `isekai/interface/verbs/common.py`, `isekai/interface/verbs/library.py`, `isekai/interface/verbs/drafts.py`, `isekai/interface/verbs/edits.py`, `isekai/interface/verbs/session.py`, `isekai/interface/verbs/prepare.py`, `isekai/interface/verbs/generate.py` and `isekai/interface/verbs/stages.py` are new.
- `tests/test_ratchets.py` loses the `cli.py` rows of the file and of `build_parser`, and `tests/mutants.json` takes new paths.
- `tests/record/verbs.json` pins every verb's arguments and stays byte-identical.
- `docs/decisions.md` gains a decision; `docs/principles.md`, `docs/modules.md`, `ARCHITECTURE.md`, `isekai/README.md` and `isekai/interface/README.md` are amended.
- The layer READMEs' derived tables follow the import graph: `isekai/foundation/README.md`, `isekai/shared/README.md`, `isekai/boundary/README.md` and `isekai/pipeline/README.md`.

## Not in this change

- `_per_item` and the second chain of the flow stages: its own version, not a move. Its ratchet rows stay.
- The command builder and a refusal's fix apart: a version before the isekai command.
- Help text, a new verb, a new flag and `prog`: no verb or flag changes.
- The image, the edit manifest's version and any re-pin: none is touched.
