---
version: v0.34
backlog: [0053·R15, 0053·R16, 0053·R17, 0053·R18, 0054·R4, 0054·R8, 0054·R9]
---

# 0055 — attribute recall

Did the hair, the eyes and the clothes the operator approved survive into the picture. A command of its own,
`python -m evaluation.recall <runs> [<run>…]`, reads each render with the tagger that fills the sheet and counts,
per scored field, the approved sheet's tags it reads back, naming every one it misses. It needs no cohort and no
face model. The change also empties the backlog. **The feature is the recall command.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the count, the reader, the command, the records, the cards |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `evaluation`, `image-generation` |

## Why

**Half the claim has no number.** Identity is face, hair, clothes and pose. The cohort count covers the face.
Hair and clothes reach a render as the approved sheet's tags, and nothing checks that a tag asked for was drawn.

**The schema already says which fields.** Each flow's schema marks its scored fields, and no code reads the mark.

**The cohort evaluator ranks the oldest render.** After a second approval and render it scores the first group,
while the control pairs on the latest.

**The backlog holds seven small cards**, most on files this change edits.

## What Changes

- **The count:** per scored field, the approved sheet's tags the tagger reads back from the render over the tags
  asked; each missed tag named ([D1](design.md#d1)).
- **The reader:** the pipeline's own tagger, at its own floor, verified by its own manifest; D39 says so and why
  ([D2](design.md#d2)).
- **The command:** `python -m evaluation.recall <runs> [<run>…]` reads every render alone against the approval
  its group came from, prints a row per render and a total per flow, and writes `<batch>/recall.json`
  ([D3](design.md#d3)).
- **The cohort evaluator scores the latest render group** ([D4](design.md#d4)).
- **The cards:** a refusal that ends in a fix, a test's name, a spec's why, an importer line, a count in the
  README, a SHALL sentence; one card retired ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `evaluation`: ADDED *Attribute recall counts the approved sheet's scored tags read back from each render*.
- `evaluation`: MODIFIED *Every render is a row* — the row ranks the first seed of the flow's latest render group;
  its why names the record as the file a batch publishes.
- `image-generation`: MODIFIED *A flow renders on another flow's seeds when the operator names it* — gains the
  sentence its damaged-record scenario proves.

## Impact

- **Files:** `evaluation/recall.py`, `evaluation/record.py` (new); `evaluation/__main__.py`,
  `evaluation/README.md`; `tests/test_recall.py`, `tests/test_recall_cli.py`, `tests/recall/` (new);
  `tests/test_cohort.py`, `tests/test_evaluation_cli.py`; `docs/decisions.md`, `isekai/boundary/README.md`,
  `README.md`; `openspec/specs/evaluation/spec.md`'s header lines.
- **Behaviour:** a new command; the cohort command ranks the latest group's first seed; one refusal's wording.
- **Formats:** no run file kind or manifest version moves. `recall.json` is a new file outside every run.
- **Dependencies:** none. No model is added: the tagger is the pipeline's.
- **Spend:** none.

## Not in this change

- **A base line** — how often another person's render shows the same tag. Trigger: a cohort batch has recall
  counts worth comparing.
- **A split by `edited`** — the reviewed route against the unreviewed one.
- **Whether the sheet matches the photograph** — the review's.
- **Pose geometry** — `pose` here is pose tags read back.
- **Editing the control arm's archived design** — 0054·R8 is retired, not fixed.
