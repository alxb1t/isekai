---
bump: patch
version: 0.87.15
debt: [0135·S1, 0137·R1, 0137·S1, 0143·R1, 0144·R1, 0148·R2, 0149·S1, 0154·R1, 0156·R1, 0158·R1]
---

# The paydown tests

The cards of `debt:` close with tests, a record of red runs and one scenario split; no line of the product changes.

Reading map: [design](design.md) holds the decisions, the mutants and the test cost, [tasks](tasks.md) holds the phases.

## Why

`.minions/debt.md` is over its paydown line. The cards of `debt:` ask for a test, a red run kept nowhere or a closing note, and none asks for a product edit. This version pays them; the cards in `ui/src` are the paydown's second version.

```
 the cards                 what closes them                 where
 0137·R1  0137·S1          a stronger test                  tests/test_ui_api.py
 0149·S1                   a guard that drops comments      tests/test_css_files.py
 0137·R1  0137·S1          a red run kept as a mutant       tests/mutants.json
 0148·R2  0154·R1
 0158·R1
 0154's third AND          a scenario of its own            the ui spec delta
 0135·S1                   the scanner's own line, checked  tests/test_ratchets.py
 0143·R1  0144·R1  0156·R1 no edit: the archive is frozen   openspec/changes/archive/
```

## What Changes

- **Phase 1** — the foreign-Host test reads as well as writes, the upload test makes the request's body raise, and the CSS guard drops comments before it counts ([D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3)).
- **Phase 2** — the refused third format leaves the three-AND scenario for a scenario of its own, and its test gains the key ([D4](design.md#d4)).
- **Phase 3** — edits in `tests/mutants.json` keep the red runs the cards ask for, and `make mutants` kills each ([D5](design.md#d5)).
- **Phase 4** — `0135·S1` closes on a check of the scanner's own line, and `0143·R1`, `0144·R1` and `0156·R1` close with no edit ([D6](design.md#d6)).
- **MODIFIED** `An image's large view shows its sheet and walks the photograph's row, and its thumbnail is made once` — the third-format refusal becomes the scenario `a photograph in a third format is refused`.

No format version moves and no behaviour changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — one scenario added under an existing requirement, one AND moved out of another scenario.

## Impact

- Tests: `tests/test_ui_api.py`, `tests/test_css_files.py` and `tests/mutants.json` are edited; `tests/test_ratchets.py` is read.
- Specs: the delta `specs/ui/spec.md`.
- Debt: the cards of `debt:` close at release.

## Not in this change

- Any file under `isekai/`, `ui/src/` or `openspec/changes/archive/`.
- `0143·S1`, `0142·S1` and `0142·S2`, the page cards in `ui/src`, and the deletion's lost completion: the paydown's second version.
- A case for a shared name in the scanner's twin: it would change an existing test's expected value ([D6](design.md#d6)).
- An edit to an archived change: an archived design is frozen.
- A card raised after `4eaa00dd`.
- A change to [D61](../../../docs/decisions.md#d61--what-a-test-replaces-in-the-server-is-a-parameter-of-create_app): the upload test patches a name of Starlette, not of the server.
