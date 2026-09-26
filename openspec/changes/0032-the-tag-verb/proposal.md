---
version: v0.23
---

# 0032 — the tag verb

`caption` writes the prose only; a new `tag` verb writes both tag lists, each isolated from the other's
failure; a flow's manifest declares whether it needs the tagger, and a flow that declares none gets an
empty sheet to fill by hand.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | every choice that settles how, and the rows carried with it |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | the `tag` verb, the tagger declaration, the empty sheet, the missing caption |

## Why

**Flows that need no tagger are coming, and today every flow is tagged.** `caption` runs the prose, WD14
and the JoyCaption tags as one verb, and no manifest key says whether a flow needs tags
(`docs/decisions.md` D1).

**The sheet's input waits on Ollama.** The prose runs first, and a prose refusal abandons the photograph's
WD14 list, which is the sheet's only input. D1 records this as a known consequence.

**`--new-version` has no single meaning.** On `caption` it re-reads the prose and re-runs both taggers, so
the fix for a damaged WD14 list re-reads a photograph it does not need.

## What Changes

- **BREAKING — `caption` writes the prose only.** A run tagged by the old `caption` keeps its lists; a new
  run needs `tag` before `sheet`, and `sheet` refuses naming `tag` ([D2](design.md#d2)).
- **A new verb, `tag`**: WD14, then the JoyCaption tags, into the existing `wd14/` and `tags/`. A failure
  in either tagger leaves the other's list written ([D2](design.md#d2)).
- **`--new-version` re-produces every artifact its own verb writes, and nothing else** ([D2](design.md#d2)).
- **BREAKING — the manifest declares `"tagger": true | false`**, a required boolean, and `MANIFEST_VERSION`
  moves 3 → 4. Both tracked flows declare `true` and are re-pinned in place ([D1](design.md#d1)).
- **`tag` refuses a flow that declares no tagger**, before any work ([D2](design.md#d2)).
- **A flow that declares no tagger gets a sheet with every field empty**; a flow that declares one still
  refuses when its list is absent ([D3](design.md#d3)).
- **The review surface shows a missing caption with the command that writes it** ([D4](design.md#d4)).
- **The record**: D1 rewritten, D31 added, the verbs drawn as two independent verbs at ①
  ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli` · *A new artifact version is requested explicitly* — the flag re-produces what its own verb writes.
- `cli` · *Every stage verb requires the flows it acts on, and takes more than one* — `tag` joins the list;
  *"sorting"* goes.
- `cli` · *Every per-flow seam is resolved per flow, on the model that flow names* — removed; replaced by
  *… for a flow that declares its stage*: the pinned seam resolves for every flow that declares the tagger.
- `tagging` · *A failing tagger leaves every artifact produced before it complete* — removed; replaced by
  *Each tagger's failure is its own, and the local tagger runs first*: isolated both ways under `tag`, and
  `caption` writes no tag list.
- `tagging` · *The local tagger runs for every flow, and the hosted one runs on the model the flow names*
  — removed; replaced by *Both taggers run for a flow that declares the tagger, and the hosted one runs on
  the model the flow names*.
- `sheet` · *The stage takes a tag list, a schema, a vocabulary and a field map, and returns fields* —
  removed; replaced by *The stage fills fields from the tag list of a flow that declares the tagger, and
  leaves them empty for a flow that declares none*.
- `image-generation` · *A flow is a flat directory of named files whose manifest declares and never
  computes* — the manifest also declares whether it needs the tagger; a divergence, not every change, is a
  new flow.
- `image-generation` · *Every flow declares whether it needs the tagger* — added.
- `ui` · *A missing caption is shown with the command that writes it* — added.

## Impact

- **Files:** `isekai/interface/cli.py`, `isekai/interface/wiring.py`, `isekai/interface/ui/`
  (`app.py`, `batch.py`), `isekai/pipeline/` (`tagging.py`, `sheet.py`, `caption.py`),
  `isekai/foundation/` (`flow.py`, `artifacts.py`), `isekai/boundary/ollama.py`, both flows' `flow.json`
  and `graph.json`, `ui/src/`, `tests/`, `docs/`, the READMEs, `CLAUDE.md`, `CHANGELOG.md`.
- **Behaviour:** a new verb; `caption` writes less; the manifest format moves; an empty sheet for a
  tagger-free flow; a line in the review surface. The render and its prompt are unchanged for both tracked
  flows.
- **Dependencies:** none.

## Not in this change

- **Retiring the JoyCaption tagger** — no stage reads its list; whether the review aid helps is a
  measurement.
- **Declaring anything about the sheet, review or prose in the manifest** — the key declares the tagger
  alone.
- **A tagger-free flow's sheet from any source but empty fields**, and **a tracked flow that declares
  `false`** — a test fixture proves that path.
- **The review surface's unchecked reads of `fields`, `tags` and `tag`** — a behaviour fix, not part of
  this feature.
- **Re-identifying either flow.**
