---
version: v0.32
---

# 0053 — the evaluation mechanism

A `summon` render is recognisably the person in the photograph, and a count says so. A cohort of synthetic people
on disk is the ground truth; every photograph is rendered once; an encoder the generator does not use picks, for
each render, the nearest photograph. Two counts over the cohort, the chance line beside them, every render a row.
Everything the old evaluator did beyond that is deleted, not repaired. **The feature is the count.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the cohort, the counts, the encoder, the record, the deletion |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `evaluation` |

## Why

**The evaluator is dead code.** Its one entry point reads a run shape nothing has written since the single render
path, and one refused render ends the run with nothing written. Its four axes were calibrated against forty blind
judgements and every one came back a coin flip.

**The published figures have no code.** The baseline's intervals, p-values, AUC and rank-1 were computed off-tree.

**The claim has no number.** The product's claim is identity preserved from the photograph; what the eye sees has
never been counted on a current flow.

## What Changes

- **The cohort is the ground truth:** one directory per person, their photographs inside; a run is matched to its
  photograph by the frame's digest ([D1](design.md#d1)).
- **Two counts over the cohort, never a score:** per render, the nearest photograph; a photograph-level hit and a
  person-level hit with the source excluded; the chance line beside each ([D2](design.md#d2)).
- **The encoder shares no pin with the generator:** YuNet finds and aligns the face, SFace embeds it, both from
  OpenCV's own Hugging Face repositories, on onnxruntime ([D3](design.md#d3)).
- **Every render is a row:** one record per batch, one table with a column per flow; a failure is a named row and
  never an exit ([D4](design.md#d4)).
- **The entry point reads a current run** ([D5](design.md#d5)).
- **No package is added; `[eval]` is deleted** ([D6](design.md#d6)).
- **The decision and the principles are written:** D37, the encoder shares no pin with the generator; `## Measurement`
  in the principles ([D7](design.md#d7)).
- **BREAKING: the old evaluator is deleted** — the canvas, the regions, the guard, the pose and colour axes, the
  labels, the baseline and their models — last, after the probe and the tests have proved the new method
  ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `evaluation`: ADDED *The cohort is the ground truth*.
- `evaluation`: ADDED *Two counts over the cohort, never a score*.
- `evaluation`: ADDED *The encoder shares no pin with the generator*.
- `evaluation`: ADDED *Every render is a row*.
- `evaluation`: in the deletion phase, per [D8](design.md#d8): *Every model the scorer loads is pinned and
  verified* is REMOVED and ADDED as *Every model the evaluator loads is pinned and verified*, without the sentence
  binding the recognizer to the generator's pin; REMOVED *The comparison canvas is
  the render's own*, *Regions are parsed from the photograph only*, *The face-location guard refuses rather than
  scores the wrong pixels*, *An absent face is its own outcome, never a low score*, *Every axis declares what it may
  claim*, *A cross-base comparison refuses only the axes it invalidates*, *The report is one record per render and
  one table per run*, *Human labels are collected blind and pairwise*.

## Impact

- **Files:** `evaluation/` rewritten — `__main__.py`, `cohort.py`, `face.py`, `eval_models.py`, `eval_models.json`,
  `README.md`; deleted — `evaluate.py`, `eval_backends.py`, `ciede2000.py`, `labels.py`, `baseline/`;
  `tools/derive_eval_manifest.py`; `pyproject.toml`, `uv.lock`; `docs/decisions.md`, `docs/principles.md`,
  `docs/modules.md`, `README.md`; the tests under *Tests* in [design](design.md#context).
- **Behaviour:** `python -m evaluation <runs> --cohort <dir>` scores a current batch; the old invocation is gone.
- **Formats:** no run file kind or manifest version moves. The batch's record is a new file outside every run.
- **Dependencies:** none added; `torch` and `transformers` leave the optional extra, which is deleted.
- **Spend:** none. The probe runs on renders already on disk.

## Not in this change

- **The control arm** — a variant flow with the face chain off, and its batch. Trigger: the first batch's counts exist.
- **Attribute recall** — hair and clothes read back from the render against the approved sheet.
- **A second seed, a second encoder, render↔render identification, a dose-response over `ip_weight`.**
- **A pose or colour measure.**
- **The batch and its committed record** — the operator renders the cohort once the evaluator ships, and the
  record it writes is committed, with the table beside it, by the change that publishes the figure. Trigger: the
  cohort is on disk.
- **Generating the cohort** — `synthetic_portraits`' work.
- **The root `README.md`'s showcase** — the portfolio's; this change touches only its lines naming `[eval]`.
- **Deleting the old models under `models/`** — the operator's.
