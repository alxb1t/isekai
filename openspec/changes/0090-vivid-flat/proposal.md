---
bump: minor
---

# 0090 — vivid flat

Flat summon's likeness in brighter colour, as three looks chosen by eye: `summon-semireal-anime-wai` and
`summon-vivid-anime-wai` new, `summon-flat-anime-wai` re-pinned in place, and the app offering five flows.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `image-generation`, `ui` |

```
1 the flows    semireal and vivid copied from the prototype, renamed; flat's trailer re-pinned; one style table
2 the record   D44 amended, D46 new; README, AGENTS.md; the app's five flows
```

## Why

**Flat summon kept the person but lost colour.** It renders with less chroma than summon. A prototype tried four
prompt and dial changes on the operator's photographs, and the operator chose three looks by eye. `lineart` in flat's
trailer was not the cause of the lost colour, and the face chain's early end was not either: the prompt was.

## What Changes

- **`summon-semireal-anime-wai`**, new: flat's face chain with summon's whole prompt ([D1](design.md#d1)).
- **`summon-vivid-anime-wai`**, new: flat's face chain, summon's trailer, and a negative that refuses muted colour
  ([D1](design.md#d1)).
- **`summon-flat-anime-wai`**, re-pinned: `lineart` becomes `anime coloring, colorful` ([D1](design.md#d1)).
- **One style table** holds each styled flow to summon ([D2](design.md#d2)).
- **The app offers** summon, semireal, flat, vivid and conjure ([D3](design.md#d3)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation` — *A flat flow is its subject with the face chain ending early and a flat style*: its trailer's
  terms.
- `image-generation` — *A semireal and a vivid flow are their subject's face chain ending early, in a style of their
  own*: added.
- `ui` — *Draft from this starts from an image, for any flow the app offers, and opens Review on the draft*: its
  diagram lists the five flows.

## Impact

- `flows/summon-semireal-anime-wai/`, `flows/summon-vivid-anime-wai/` new; `flows/summon-flat-anime-wai/flow.json`.
- `tests/test_flow.py`, `config/ui.json`, `docs/decisions.md`, `README.md`, `AGENTS.md`.
- No pod, no image rebuild, no model: the image copies no flow, and the three declare flat's models.

## Not in this change

- A render of the new flows under their final names: the prototype's renders are the evidence, the bytes differing
  only in each manifest's `flow`.
- `summon-anime-wai`, `control-anime-wai`, `conjure-anime-wai`: unchanged.
- The prototype's offline tools: `lift.py`, `table.py`, `candidates.py`.
- A list of retired flows: the app offers what `config/ui.json` names.
