---
version: v0.34.1
backlog: [0055·R5, 0055·R11, 0055·R12]
---

# 0056 — the evaluation paydown

The backlog the evaluation versions left, closed. Both evaluation records name a run by its digest prefix and
nothing more; the empty latest group gets a scenario of its own; one card about an archived file is retired.
**A patch: it delivers no feature.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the prefix, the scenario, the retired card |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `evaluation` |

## Why

**A record holds more than its table shows.** A run's id is a digest prefix and a slug of the photograph's
filename. Recall writes the whole id into `recall.json` and prints the prefix; the cohort evaluator writes and
prints the whole id. A filename can be a person's name, and a record is the file a batch publishes.

**A behaviour has no scenario.** A latest render group that holds no render is reported as not rendered, and
the test proving it is bound to a scenario about renders under two approvals.

**One card names a frozen file.** The archived `tasks.md` of the recall change carries `Verify:` counts later
commits moved.

## What Changes

- **Both records name a run by its digest prefix**, and each table prints the same; the command line and the
  error stream keep the full id ([D1](design.md#d1)).
- **The empty latest group has its own scenario**, and its test is bound to it ([D2](design.md#d2)).
- **0055·R12 is retired**, not fixed ([D3](design.md#d3)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `evaluation`: MODIFIED *Every render is a row* — a scored run is named by its digest prefix; an empty latest
  group is not rendered, and no earlier group is ranked in its place.
- `evaluation`: MODIFIED *Attribute recall counts the approved sheet's scored tags read back from each render* —
  a row names its run by its digest prefix.

## Impact

- **Files:** `evaluation/record.py`, `evaluation/__main__.py`, `evaluation/recall.py`;
  `tests/test_evaluation_cli.py`, `tests/test_recall_cli.py`; the fixture pairs `tests/cohort/evaluation.json`,
  `evaluation.txt` and `tests/recall/recall.json`, `recall.txt`.
- **Behaviour:** `evaluation.json` and `recall.json` carry a 12-character run prefix where they carried the
  full id; the cohort table's non-hit lines print the prefix.
- **Formats:** no run file kind or manifest version moves. Neither record declares a version.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **A run's directory name, the command line's run ids, the error stream's lines** — each keeps the full id.
- **A manifest key saying a flow is a control** — `compare`'s "no runs" refusal still names every tracked flow.
  Trigger: a second control flow, or a change that moves the manifest version.
- **Editing an archived change.**
