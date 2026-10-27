---
version: v0.57
---

# 0084 — flat summon

Summon's likeness in conjure's flat, lined anime look. Two candidate flows are prototyped against summon on the same
sheet and seed; the winner is kept as `summon-flat-anime-wai`, or nothing ships.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the candidates, the prototype, the pass rule, the winner |
| [tasks](tasks.md) | the phases, in build order — two of them the operator's, one metered |
| `specs/` | `image-generation` |

```
1 candidates  summon-flat-a, summon-flat-b ─▶ 2 the operator's photographs ─▶ 3 sheets (summon's, copied)
   ─▶ 4 ⚠️ GPU one session on summon's seeds, then the count ─▶ 5 the operator's verdict ─▶ 6 the winner, or no merge
```

## Why

**A summon render reads as semi-realistic anime beside conjure's cel look.** InstantID runs to the last step and
into the hires pass, and its adapter, trained on photographs, pulls the whole image toward 2.5D shading.

## What Changes

- **Two candidate flows** — A ends InstantID early with a flat prompt; B adds a hires pass on the plain checkpoint
  ([D1](design.md#d1), [D2](design.md#d2)).
- **A prototype** — the operator's photographs in `.data/flat-summon-prototype/`, summon's sheets corrected by the agent and copied to both, one session on summon's seeds
  ([D3](design.md#d3), [D4](design.md#d4)).
- **The verdict** — by eye and by the cohort count, against summon on the same photographs ([D5](design.md#d5)).
- **The winner kept** as `summon-flat-anime-wai`, offered in the app; the loser deleted ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation`:
  - ADDED *A flat flow is its subject with the face chain ending early and a flat style* — the files, the graph and
    the manifest a flat flow may change, and no other.

## Impact

- **Code:** `flows/summon-flat-a-anime-wai/` and `flows/summon-flat-b-anime-wai/` (then `flows/summon-flat-anime-wai/`).
- **Tests:** `tests/test_flow.py`.
- **Docs:** `docs/decisions.md` (a new decision), `AGENTS.md`, `README.md`.

## Not in this change

- **Summon, conjure and control** — pinned as they are.
- **A new model** — the lineart re-render and an instruction edit wait for their own version.
- **A manifest dial for `end_at`** — set in the flat flow's own graph.
- **A failed prototype's merge** — if neither candidate passes, the branch is destroyed and nothing ships.
