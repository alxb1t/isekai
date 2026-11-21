---
bump: patch
version: 0.87.44
after: [0187-the-runner-move]
---

# The stage attempt

The shared sequence of the unpaid stages becomes one function, `attempt` in `isekai/foundation/run.py`; every refusal stays byte-equal.

Reading map: [design](design.md) holds the function, its lookup and the proof of equality, [tasks](tasks.md) its phases: cases first, the function, the sites, the ratchet, the documents.

## Why

`caption`, `wd14`, `tags` and `sheet` end in the same sequence: check the budget, do the work in a `try`, record the failure, raise the refusal. Each site spells it again, and `refusal_for` takes more positional parameters than the ceiling allows to serve them, a listed row of the wide-function ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

No test holds a stage's refusal whole, only fragments of it, and [D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy) leaves the sequence inside a stage as it is. A shared function is safe only once a case holds each refusal's bytes.

## What Changes

- Cases hold each stage's refusal whole, and a mutation run pins each stage's sequence and `refusal_for`, before a line moves.
- `isekai/foundation/run.py` gains `attempt`: the budget's check, an optional open step, the work, the failure's record, the refusal.
- `isekai/foundation/producers.py` gains `producer_for`, a lookup of a stage's row by its key.
- `caption`, `wd14`, `tags` and `sheet` call `attempt`; each keeps its guard and its numbering, and `caption`'s briefing and `wd14`'s tagger are the open step.
- `refusal_for` takes the stage's key, reads its folder, verb and budget from the row, and its row leaves the wide-function ratchet.
- [D73](../../../docs/decisions.md#d73--a-stage-is-declared-once-in-isekaifoundationproducerspy)'s *Accepts* is amended. No decision is added.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Behaviour is unchanged, and the change carries `skip_specs`.

## Impact

- `isekai/foundation/run.py`, `isekai/foundation/producers.py`, `isekai/pipeline/caption.py`, `isekai/pipeline/tagging.py`, `isekai/pipeline/sheet.py`.
- `tests/test_run_directory.py`, `tests/test_caption.py`, `tests/test_tagging.py`, `tests/test_sheet_stage.py` and `tests/test_ratchets.py`; no assertion of an existing test changes.
- `docs/decisions.md`, `isekai/foundation/README.md`.
- The import graph `python -m isekai` loads is unchanged.

## Not in this change

- `assemble` and `render` in `isekai/pipeline/generate.py`: the paid stage's per-seed check decides spending, its refusals have their own templates, and its failure's kind is a boundary class the foundation cannot import.
- A stage's guard and its numbering: each site keeps its own.
- The refusal's noun as a field of the stage's row: one function reads it, so a field is not earned.
- Any refusal's text, the pipeline's own `STAGE` constants and the hub cell's `Stage`.
- The interface's tables, until they are read from the record.
- Any file under `ui/`, `tools/` or `evaluation/`.
