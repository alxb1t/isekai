---
bump: patch
after: [0131-the-nets-holes]
debt: [0119·R5]
---

# The prototype's ink

The ink is cut as the prototype cut it, and the outline step says how many points a close needs.

Reading map: [design](design.md) holds the decisions, the test cost and the bound accepted, [tasks](tasks.md) holds its phases: the extractor, then the floor.

## Why

The person's second session on *Place a tattoo* at `v0.86.0` (wish list W1 and W2) met W2 first. The right arm's blackwork sleeve, which the prototype's extractor cut, is refused by the shipped one: both its outlines read a white point at a mean of 0.646 of the skin, under the `_MIN_SKIN` 0.7 that a check added by `0119` holds.

With that check off, `extract_ink` and the prototype give the same layer to the byte on the sleeve's photograph and mask. W2 blocks every screen after the outline.

An outline also closes only from 20 points, a floor `0121` set with no recorded reason, and the close line names the count and never the floor. The person cannot see what is left before a close works.

## What Changes

- `isekai/shared/ink.py` reads the white point as the prototype does: the `white` percentile, per channel, of the lit pixels inside the outline, compared with nothing. `_MIN_SKIN`, `_SKIN_GAP` and `_skin_beside` go; the refusal of an outline with no lit pixel inside it stays.
- The refusal's tests are retired and a test holds that a tight outline over a solid fill is cut, not refused. The decision is added to `docs/decisions.md` as D57, and the debt card `0119·R5` is paid by it.
- `outline_min` in `config/tattoo.json` goes from 20 to 3. The server's checks and the page's rules read it as they do now.
- Below the floor the close line reads *add N more points to close · K of F* and the forward line *outline open · K of F points*. At or past it they read as they do now.

Requirements touched, one line each:

- `edit`: *The ink is cut by `isekai ink`* loses its refusal of an outline whose inside reads darker than the skin beside it. Its scenario *an outline with no bare skin inside it is refused* is narrowed to an image with no lit pixel inside the outline, and the scenario *a tight outline over a solid fill is cut by the percentile* is added.
- `ui`: *The outline step shows the ink and keeps its white point and tone* says its close line names the floor while the outline is short of it, with a scenario for it.
- `ui`: *The outline step goes forward to the stage its tattoo takes* says its wait names the floor while the outline is short of it, with a scenario for it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edit`: the ink's white point is compared with nothing.
- `ui`: the close line and the forward wait name the floor.

## Impact

- Code: `isekai/shared/ink.py`, `config/tattoo.json`, `ui/src/tattoos.ts`, `ui/src/stages.ts`, `ui/src/components/OutlineStep.vue`.
- Tests: `tests/test_ink.py`, `tests/test_tattoo_library.py`, `tests/test_ui_tattoo.py`, `ui/src/tattoos.test.ts`, `ui/src/stages.test.ts`.
- Docs: `docs/decisions.md`, `ui/design/spec.md`.
- No format version moves, no verb or flag is deprecated, and every input the shipped extractor accepted gives the same layer to the byte.
- The live line `0127`–`0131` is the test-audit series. This patch opens none of its files but the spec bindings.

## Not in this change

- A white point picked by a click on bare skin, and the field editable after a refusal: when the ink step is next reworked.
- A reach for broad fills: when a photograph's fill is wider than `reach` and the operator reports it.
