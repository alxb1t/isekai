---
bump: patch
---

# 0114 — the delete's leftovers

Deleting a flow's last render empties its folder in the two cases `0112` missed: a render group holding failure records,
and a flow holding its own copies of the photograph's tags and caption from before the shared ones.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `image-generation` |

```
1 the failure records   a group holding failure records alone counts as no render; they go with it
2 the own description   a flow with no approval left loses its wd14/, tags/, captions/ where photo/ holds that kind
3 the record            docs D4, D50; principles, data-flow, threat model, migrate's and app's docstrings
```

## Why

**`0112`'s aim, "delete the last render → Hub and Review show nothing", still fails twice.** A render that failed once
leaves its failure records in the render group, so the group never empties and the approval stays. A flow tagged before
the shared tags (D17) keeps its own `wd14/`, `tags/` and `captions/`, so its folder never empties and `0113`'s untick
of an empty folder cannot clear the cell.

## What Changes

- **The failure records**: discarding a group's last render deletes the group's failure records with it, and an older
  approval whose group holds failure records alone counts as an approval with no render
  ([D1](design.md#d1)).
- **The own description**: a flow left with no approval loses its own `wd14/`, `tags/` and `captions/`, each where
  `photo/` holds that kind; the photograph's own stay ([D2](design.md#d2)).
- **The record**: docs D4 and D50, `docs/principles.md`, `docs/data-flow.md`, `THREAT_MODEL.md`, and the docstrings
  of `isekai/foundation/migrate.py` and `isekai/interface/ui/app.py` follow ([D3](design.md#d3)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation` — *A render is discarded whole, and its approval goes with its last render*: a group holding
  failure records alone is no render, and goes with its records; a flow with no approval left loses its own copies of
  the photograph's description where `photo/` holds that kind. New scenarios under it.

## Impact

- Code: `isekai/foundation/run.py`, `isekai/pipeline/generate.py`, `isekai/pipeline/review.py`,
  `isekai/foundation/migrate.py`, `isekai/interface/ui/app.py`.
- Tests: `tests/test_generate.py`, `tests/test_review.py`.
- Docs: `docs/decisions.md`, `docs/principles.md`, `docs/data-flow.md`, `THREAT_MODEL.md`.
- No format version, verb, flag or product moves: a patch. `flows/`, `config/`, `gpunit.toml` and `ui/` are
  untouched.

## Not in this change

- Clearing the per-flow duplicates already in the library (brief Q1): a one-off after release, its dry run first, for
  the operator's word. Where a photograph has no shared copy, it moves the flow's copy there first.
- A flow's own description where `photo/` lacks that kind: it stays, and the run stays refused until migrated.
- A failure record beside a render that stays: the group keeps it.
- Unticking a *tagged* cell: `0113`.
