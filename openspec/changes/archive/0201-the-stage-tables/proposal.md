---
bump: patch
version: 0.88.11
after: [0200-the-upload-session]
---

# The stage tables

The tables above the foundation are held to the stage record, and Prepare's order and its tag rule are written once, beside the record.

Reading map: [design](design.md) holds the decisions, the code and the guard, [tasks](tasks.md) its phases: the guard, the kinds, Prepare, then the documents.

## Why

[D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy) declares each stage once and leaves the tables above the foundation as they are, to reopen when they are read from the record. Little of them derives from it byte for byte, and no test holds any of them to it: a new stage edits each table by memory.

Prepare's rule, that a photograph is tagged when any flow it is prepared for has a tagger, is written twice, by the app's plan and by the verb. This version derives what derives, holds the rest to the record by one test, and writes the rule once. It changes no behaviour.

## What Changes

- `tests/test_run_directory.py` gains one guard, `test_each_stage_tables_keys_are_the_records`, and its twin. The guard holds the keys of `_KINDS`, `STAGES`, `_WRITES`, `PREPARE`, `REACHED` and the runner's `_BUILDERS` to the record; the twin shows it names a table with a key the record lacks and each table a new stage leaves out. It is written first and passes before a line moves.
- `_KINDS` of `isekai/interface/ui/library.py` reads its keys from the record, its words stay written, and a case holds each stage folder's word for Home's row.
- `isekai/foundation/producers.py` holds `PREPARE`, Prepare's order by verb, and `tagged_runs`, its tag rule, and `isekai/foundation/run.py` re-exports both. `plan` of `isekai/interface/ui/jobs.py` and `run_prepare` of `isekai/interface/verbs/prepare.py` walk `PREPARE` and read `tagged_runs`. `jobs.PREPARE` is bound back from the foundation, and `isekai/interface/progress.py` no longer declares it.
- Cases for the rule and the order of Prepare's plan and of the verb are written before the move, and `tools.mutate` runs over the lines of `plan` and of the verb's steps before and after.
- `docs/decisions.md` amends D73's sentence, *Accepts* and *Made by*, and the foundation README's `producers.py` row names the new names.

No requirement is touched. Every line a verb prints, every wire byte and every file a run writes stay, and `ui/src/wire.ts` does not change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

`isekai/foundation/producers.py` and `isekai/foundation/run.py` gain `PREPARE` and `tagged_runs`. `isekai/interface/ui/library.py`, `isekai/interface/ui/jobs.py`, `isekai/interface/verbs/prepare.py` and `isekai/interface/progress.py` change the lines named above. `tests/test_run_directory.py`, `tests/test_ui_library.py`, `tests/test_ui_jobs.py` and `tests/test_pipeline_cli.py` gain cases, and `tests/test_progress.py` changes an import line. `docs/decisions.md` and `isekai/foundation/README.md` change. No decision is added.

## Not in this change

- A field on `Producer`: `_KINDS` has one reader, which does not earn one.
- `STAGES`, `_WRITES`, `REACHED` and the runner's builders derived from the record: they stay written, held to it by the guard.
- The words of `_KINDS`, which stay written, and the stage names of a child's line, which `isekai/interface/progress.py` keeps.
- The sequence inside a stage, the pipeline's own `STAGE` constants, the hub cell's `Stage`, and the paid stages' own sequences.
- A scenario or a spec delta, any file under the top-level `ui/`, `tools/` or `evaluation/`, and `ui/src/wire.ts`.
