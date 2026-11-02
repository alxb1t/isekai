# Tasks — 0090 vivid flat

The flows, then the record, per [design](design.md).

## Progress

- [x] 1 — The flows
- [x] 2 — The record

## 1 — The flows

- [x] 1.1 Copy `flows/summon-vivid-g-anime-wai/` from `prototype/vivid` to `flows/summon-semireal-anime-wai/` and
  `flows/summon-vivid-f-anime-wai/` to `flows/summon-vivid-anime-wai/` with `git show`, then set each `flow.json`'s
  `flow` to its directory, per [D1](design.md#d1).
  Verify: `diff <(git show prototype/vivid:flows/summon-vivid-g-anime-wai/graph.json) flows/summon-semireal-anime-wai/graph.json` and the same for F's prints nothing, and `grep -c '"flow": "summon-vivid-anime-wai"' flows/summon-vivid-anime-wai/flow.json` prints `1`.
- [x] 1.2 In `flows/summon-flat-anime-wai/flow.json`, the trailer, before → after: `flat color, cel shading, lineart` →
  `flat color, cel shading, anime coloring, colorful`.
  Verify: `grep -c 'anime coloring, colorful' flows/summon-flat-anime-wai/flow.json` prints `1`.
- [x] 1.3 In `tests/test_flow.py`, replace `FLATS`, `FLAT_TRAILER` and `FLAT_NEGATIVE` with `STYLED`, per the
  [style table](design.md#d2); the flat tests read flat's row, and add one test per `image-generation:styled:*` scenario
  of [the delta](specs/image-generation/spec.md), parametrised over the semireal and vivid rows.
  Verify: `grep -c 'FLAT_TRAILER' tests/test_flow.py` prints `0`, and `grep -c 'image-generation:styled:' tests/test_flow.py` prints `3`.
- [x] 1.4 Add `summon-semireal-anime-wai` and `summon-vivid-anime-wai` to `PINNED`, and re-pin `summon-flat-anime-wai`,
  each from `uv run python -c 'from isekai.foundation.flow import manifest_digest as d; print(d("<flow>"))'`.
  Verify: `uv run pytest tests/test_flow.py -k 'not a_re_pin_leaves_a_record'` exits 0; the record test passes once
  the phase's CHANGELOG entry names the three digests.

## 2 — The record

- [x] 2.1 `config/ui.json`'s `flows`, per [D3](design.md#d3).
  Verify: `uv run python -c 'import json; print(json.load(open("config/ui.json"))["flows"])'` prints `['summon-anime-wai', 'summon-semireal-anime-wai', 'summon-flat-anime-wai', 'summon-vivid-anime-wai', 'conjure-anime-wai']`.
- [x] 2.2 In `docs/decisions.md`, D44's bold line, before → after: "`flat color, cel shading, lineart`" → "`flat color,
  cel shading, anime coloring, colorful`", and its **Made by** gains `0090`. Add after D44 `### D46 · A semireal and a
  vivid flow are flat's face chain in other looks`: what each holds, from the style table, chosen by eye.
  Verify: `grep -c '^### D46 · A semireal and a vivid flow are flat' docs/decisions.md` prints `1`, and `grep -c 'cel shading, lineart' docs/decisions.md` prints `0`.
- [x] 2.3 `README.md`'s tree: "and it is immutable" → "pinned by its digest, re-pinned only by a recorded change"; a line
  each for `flows/summon-semireal-anime-wai/` and `flows/summon-vivid-anime-wai/` after flat's.
  Verify: `grep -c 'immutable' README.md` prints `1`, and `grep -c 'summon-vivid-anime-wai' README.md` prints a count above 0.
- [x] 2.4 `AGENTS.md`'s flow list names `summon-semireal-anime-wai` and `summon-vivid-anime-wai`, and "a flat, lined look"
  → "a flat look", per [D4](design.md#d4).
  Verify: `grep -c 'summon-semireal-anime-wai' AGENTS.md` prints `1`, and `grep -c 'flat, lined' AGENTS.md` prints `0`.
