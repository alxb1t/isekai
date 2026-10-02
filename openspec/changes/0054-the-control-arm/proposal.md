---
version: v0.33
---

# 0054 — the control arm

The floor under the count: `summon` with the face chain at zero, on the same sheet and the same noise. A flow
`control-anime-wai` is `summon-anime-wai`'s directory with its two face dials at 0 and nothing else changed, held
equal by a test; its approval is copied from `summon`'s with the origin recorded; its renders reuse `summon`'s
seeds. The evaluator then prints both rows, and the difference is the face mechanism's share. **The feature is
the control flow and what feeds it.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the flow, the copy, the seeds, the records |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `image-generation`, `review`, `run-directory` |

## Why

**The count has no floor.** The evaluator reports how often a `summon` render is nearest its own person, beside
chance. Six people who differ in age, gender and hair can be told apart by hair and skin alone, and the sheet
carries those into every render. Nothing says how many hits the sheet buys with no face mechanism at all.

**`conjure` is not that floor.** Its schema carries face fields `summon`'s lacks, so its render is the tags
trying to draw the face, not `summon` minus the photograph.

**The dials cannot be moved from the command line**, so the floor is a flow.

## What Changes

- **A control flow:** `flows/control-anime-wai/`, `summon`'s files byte for byte but `flow.json`'s identifier
  and its face dials at 0; a test holds the equality ([D1](design.md#d1)).
- **An approval copied across flows:** `approve --from <flow>` writes an approval under the target flow from the
  source flow's latest approval, validated against the target's schema, recording the source flow and version
  ([D2](design.md#d2)).
- **Seeds taken from another flow:** `generate --seeds-from <flow>` renders one image per seed of the source
  flow's latest render group, read from filenames; `render.sh` takes `control-anime-wai=summon-anime-wai`; the
  render's record names the source ([D3](design.md#d3)).
- **The one crossing is named:** a stage reads another flow's artifacts only when the operator names that flow
  as a source, and what it writes records it; D38 says so ([D4](design.md#d4)).
- **The recipe:** `evaluation/README.md` says how the control batch is rendered and read ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation`: ADDED *A control flow equals its subject flow but for the dials it zeroes*.
- `image-generation`: ADDED *A flow renders on another flow's seeds when the operator names it*.
- `review`: ADDED *An approval is copied from another flow's approval, recording where it came from*.
- `run-directory`: MODIFIED *The run directory is input above, flow below, and every artifact is a flow's own* —
  gains the one crossing: a source flow the operator names, recorded by what is written.

## Impact

- **Files:** `flows/control-anime-wai/` (new); `isekai/pipeline/review.py`, `isekai/pipeline/generate.py`,
  `isekai/foundation/artifacts.py`, `isekai/interface/cli.py`, `infra/render.sh`; `tests/test_flow.py`,
  `tests/test_review.py`, `tests/test_generate.py`, `tests/test_pipeline_cli.py`; `docs/decisions.md`,
  `evaluation/README.md`, `README.md`, `CLAUDE.md`.
- **Behaviour:** a third tracked flow; two new flags, each refusing what it cannot do by name; `render.sh`
  accepts a flow name where a count stood. Nothing changes for `summon` or `conjure`.
- **Formats:** no run file kind or manifest version moves. The approved record and the render record each gain
  one optional key, naming a source.
- **Dependencies:** none.
- **Spend:** none. The control batch is the operator's, after release.

## Not in this change

- **The control batch and its figure** — the operator's, over the first `summon` batch's runs. Trigger: that
  batch exists.
- **The evaluator** — it already prints a row per flow.
- **Removing InstantID from the graph** — the dials at zero are the control; the graph stays byte-identical.
- **Pairing by anything but the seed; a per-pair delta; a significance test.**
- **`run-flows`** — the skill stays on `summon` and `conjure`.
- **Attribute recall, the dose-response, a hard-negative cohort** — the techniques after this one.
