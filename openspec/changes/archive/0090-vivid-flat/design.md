# Design — 0090 vivid flat

Two flows copied in under their final names, one re-pinned, held to summon by one table, and offered in the app.
**Verdict: feasible.**

## Context

`prototype/vivid` holds the candidates as `flows/summon-vivid-{b,f,g}-anime-wai/`. Each equals
`flows/summon-flat-anime-wai/` but for `flow.json`'s `flow`, and its prompt's `trailer` and `negative`. The operator
chose G, F and B by eye on the prototype's renders.

## Goals / Non-Goals

**Goals:** the three looks in `main` under their final names; each held equal to summon but for its style; every
digest pinned and recorded; the app offering five flows.

**Non-Goals:** a new render, a graph change, a model, any change to summon, control or conjure.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `flows/summon-vivid-g-anime-wai/` becomes `flows/summon-semireal-anime-wai/` and `flows/summon-vivid-f-anime-wai/` becomes `flows/summon-vivid-anime-wai/`, each copied byte for byte from `prototype/vivid` with `flow.json`'s `flow` set to its directory. `flows/summon-flat-anime-wai/flow.json` takes B's trailer. `graph.json`'s `filename_prefix` stays `summon-anime-wai` | `load_flow` refuses a name that is not its directory; summon, control and flat share the prefix | a `-v2` flat: the old configuration is abandoned, its renders keep their recorded digest |
| <a id="d2"></a>**D2** | `tests/test_flow.py`'s `FLATS`, `FLAT_TRAILER` and `FLAT_NEGATIVE` become one table, `STYLED`, mapping each styled flow to its subject, its trailer's added terms and its negative's. The flat tests read flat's row; three new tests, one per scenario, read the semireal and vivid rows. An empty term adds nothing | a new look costs one row | a constant per flow |
| <a id="d3"></a>**D3** | `config/ui.json`'s `flows`: `summon-anime-wai`, `summon-semireal-anime-wai`, `summon-flat-anime-wai`, `summon-vivid-anime-wai`, `conjure-anime-wai` | the operator's order; nothing vanishes from the app | |
| <a id="d4"></a>**D4** | D44 names flat's new trailer and gains this change; D46 records semireal and vivid; README's flow line drops "immutable"; `AGENTS.md`'s flow list names both and calls flat's look flat. `tests/test_flow.py`'s failure message stays | the message's own comment forbids an "unless" clause, and a re-pin is this change's deliberate act | rewording the message |

**The style table**, as `tests/test_flow.py` holds it after phase 1:

| flow | subject | trailer gains | negative gains |
|---|---|---|---|
| `summon-flat-anime-wai` | `summon-anime-wai` | `flat color, cel shading, anime coloring, colorful` | `realistic, photorealistic, 3d, semi-realistic` |
| `summon-semireal-anime-wai` | `summon-anime-wai` | nothing | nothing |
| `summon-vivid-anime-wai` | `summon-anime-wai` | nothing | `realistic, photorealistic, 3d, semi-realistic, monochrome, greyscale, muted color` |

## Tests

| layer | adds | removes |
|---|---|---|
| unit | the semireal and vivid rows of the tracked-flow tests, which pick up a new directory by themselves; three tests bound to `image-generation:styled:*` | none |
| end-to-end | none | none |

`tests/test_flow.py` is parametrised over `tracked_flows()`, so each new directory adds its rows there; `uv run pytest
tests/test_flow.py --collect-only -q | tail -1` counts them before and after. This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **A digest no CHANGELOG bullet carries fails `test_a_re_pin_leaves_a_record_a_later_reader_can_find`** → phase 1's
  entry names each new digest.
- **The browser tests read the real `config/ui.json`** → `tests/e2e/test_import.py` counts the offered flows live; they
  run in CI, out of the gate.

## Verdict

**feasible.** Every file named exists at `ab956e1` or on `prototype/vivid`, and no model, image or graph moves.
