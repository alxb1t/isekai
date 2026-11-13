# The prototype's ink — design

The shipped extractor drops the comparison the prototype never had, and the outline step names the floor a close needs. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The person's second session on *Place a tattoo* at `v0.86.0` ([proposal](proposal.md)) met W2: the right arm's blackwork sleeve, which the prototype extracted, is refused by `extract_ink`. With the check off, `extract_ink` and the prototype's extractor give the same layer to the byte on the sleeve's photograph and mask, run with `--mono`; with it on, both outlines are refused at a mean of 0.646.

```
photo ──▶ envelope ──▶ transmittance ──▶ skin = white percentile, inside the outline
                                           │
                       now:  mean < _MIN_SKIN, or a channel > _SKIN_GAP under the ring ──▶ Refusal
                       then: no pixel lit inside the outline ────────────────────────────▶ Refusal
```

The comparison came from `0119`'s converge: a tight outline over a solid fill makes the fill its own white point and the layer loses its ink. The prototype has the same bound and the person worked inside it. The prototype's *mono dark* is the same layer raised to 1.6, which the shipped `photo_depth` already does, so nothing else differs.

The floor is `outline_min` in `config/tattoo.json`. The page's rules, the server's outline save and its ink view read it. `0121` set it to 20 with no recorded reason. The close line and the forward line name the count and never the floor.

The patch rules of [CONTRIBUTING](../../../CONTRIBUTING.md#how-a-change-lands) hold: no format version moves, no verb or flag is deprecated, and each behaviour change is under an existing requirement, one scenario added or replaced and no requirement added. An input the shipped extractor accepted gives the same layer to the byte, because the removed check only raised.

## Goals / Non-Goals

Goals:

- The sleeve's outline is cut, to the prototype's layer.
- The screen shows the floor while an outline is short of it.
- Card `0119·R5` is paid: the refusal it says D15 promises is gone with the check.

Non-Goals:

- A white point picked by a click on bare skin, and the field editable after a refusal.
- A reach for broad fills.
- A new message in place of the refusal: the ink view is the judge.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | W2: the shipped extractor is the prototype's. `_MIN_SKIN`, `_SKIN_GAP` and the ring sample beside the outline go; the empty refusal stays | the person, 2026-11-12: the prototype proved the approach on this sleeve, and the check is all that differs | a looser `_MIN_SKIN`; a check that reads the ring only |
| [D2](#d2) | W1: the screen shows the floor while an outline is below it | the person, 2026-11-12 | a floor kept out of sight |
| [D3](#d3) | The floor is 3: `outline_min` 20 → 3 in `config/tattoo.json`, the server's checks and the page's rules reading it as today | the least points that close a shape; the screen shows the count, so the person picks the precision; 20 had no recorded reason | a floor of 20; no floor |
| [D4](#d4) | Below the floor the close line reads *add N more points to close · K of F*; at or past it, *close the outline on its first point · K points*. The forward line reads *outline open · K of F points* below the floor, *outline open · K points* past it | the person sees the floor and what is left before the close works | the floor named in the controls' wait |
| [D5](#d5) | `0119·R5` is paid here: the refusal D15 of `0119` promises goes with the check, and [D57](../../../docs/decisions.md#d57--the-white-point-is-the-prototypes-percentile) of `docs/decisions.md` says the white point is the prototype's percentile | the card is about the refusal this patch removes | amending the frozen design of `0119` |
| [D6](#d6) | `after: 0131-the-nets-holes`: the patch waits for the test-audit series | the MacBook's CPU load; the person tests it the next morning | `beside` |
| [D7](#d7) | The floor reaches `closeLine` and `forwardOf` as an argument, read by `OutlineStep.vue` from `props.limits.outline_min` | the page already holds one source for the limits; `startStep` takes its floor the same way | a constant in `ui/src`; a second read of the config |

### D1

`_automatic_point` in `isekai/shared/ink.py` keeps its empty refusal, *no bare skin to read the ink against*, and reads `skin = np.percentile(transmittance[kept], config.white, axis=0)`. It returns at once after that line. `_MIN_SKIN`, `_SKIN_GAP` and `_skin_beside` are deleted; no reader is left outside the archive (`facts.py readers`, in the cut's notes).

**The bound accepted.** An outline fitted to a solid fill reads the fill as its own white point, and the layer is white there. The prototype has the same bound. The ink view shows the result and the operator widens the outline over the skin.

### D2

The floor is on the screen while an outline is short of it, and says what is left. Past it the lines read as before.

### D3

`config/tattoo.json` holds `"outline_min": 3`. `isekai/pipeline/tattoos.py` reads it at its closed-outline check and its ink-view check, and `isekai/interface/ui/app.py` carries it in the limits. None of them changes.

A saved outline of 20 points or more is still closed.

### D4

Both lines take the floor `F` and the count `K`. `N` is `F - K`, and one point reads *1 more point*, as the lines' existing singular does.

| K points, floor 3 | close line | forward line |
|---|---|---|
| 0 | `add 3 more points to close · 0 of 3` | `outline open · 0 of 3 points` |
| 1 | `add 2 more points to close · 1 of 3` | `outline open · 1 of 3 points` |
| 2 | `add 1 more point to close · 2 of 3` | `outline open · 2 of 3 points` |
| 3 | `close the outline on its first point · 3 points` | `outline open · 3 points` |
| 27 | `close the outline on its first point · 27 points` | `outline open · 27 points` |

### D5

D15 of `0119`'s design is archived and frozen. `docs/decisions.md` gains D57, which says what holds now; the card's fix, an amended D15, is not made because the decision it amends is gone. `mf-release` deletes the card.

D57 is the next free id after the test-audit series' D56, so the page needs no renumbering when that series lands.

### D6

The test-audit series `0127`–`0131` is the live line. This patch opens none of its files but the spec bindings: a MODIFIED requirement in the [edit delta](specs/edit/spec.md) re-keys one scenario, and `tests/test_spec_bindings.py` reads the active delta's keys.

### D7

`stages.ts` and `tattoos.ts` stay pure functions of their arguments. `OutlineStep.vue` already reads `props.limits.outline_min` for its rules, and passes the same value to both lines.

## Tests

The extraction's tests are unit tests at the lowest layer (T1); the lines are vitest tests. No end-to-end test is added or changed: `git grep -l -e outline_min -e "outline open" -e "close the outline" -- tests/e2e` prints nothing.

| measure | command | prints |
|---|---|---|
| tests bound to the key the delta drops | `git grep -c "an-outline-with-no-bare-skin-is-refused" -- tests/test_ink.py` | `tests/test_ink.py:4` |
| tests that match the removed message | `git grep -c "no bare skin inside the outline" -- tests/test_ink.py` | `tests/test_ink.py:3` |

Added and removed, by layer:

| layer | added | removed | end-to-end runs added |
|---|---|---|---|
| pytest unit | the parametrized test below, in `tests/test_ink.py` | the refusal tests below | none |
| vitest | a `spec` for each new key, in `ui/src/tattoos.test.ts` and `ui/src/stages.test.ts` | none | none |

| test removed, merged or changed | maps to |
|---|---|
| `test_ink_extract_an_outline_that_holds_no_bare_skin_is_refused_naming_the_fix` | merged into `test_ink_extract_a_tight_outline_over_a_solid_fill_is_cut_by_the_percentile`, its black-ink case; the refusal is retired by [D1](#d1) |
| `test_ink_extract_a_tight_outline_over_a_light_fill_is_refused_naming_the_fix` | merged into the same test, its light-fill case |
| `test_ink_extract_a_tight_outline_over_a_fill_short_in_one_channel_is_refused` | merged into the same test, its one-channel case |
| `test_ink_extract_a_one_channel_fill_keeps_its_ink_under_a_wider_outline` | kept, its marker moved to `edit:ink:a-tight-outline-over-a-solid-fill-is-cut-by-the-percentile` |
| `test_ink_extract_refuses_an_image_with_no_skin` | kept; it reads a dark image under a full outline, and its `spec_exempt` becomes the marker of `edit:ink:an-outline-with-no-bare-skin-is-refused`, narrowed to the empty refusal |
| `test_ink_grey_an_outline_with_no_bare_skin_is_refused` | kept by name; it reads a dark image under an outline, so it holds the empty refusal through `white_grey` |
| the `spec('ui:outline-step:one-line-says-how-to-close', …)` body | rewritten at a floor of 3; its case below the floor moves to the new `the-line-names-the-floor-while-the-outline-is-short` |
| the `outline open · 1 point` and `· 0 points` assertions of `ui:stages:forward-waits-for-a-closed-outline` | moved to the new `forward-names-the-floor-while-the-outline-is-short` |

`test_ink_extract_a_tight_outline_over_a_solid_fill_is_cut_by_the_percentile` carries the one `spec` marker of the new edit scenario. The fills of the merged tests are its parameters, and it asserts the pixel at (80, 80) is white under `_tight()`. It is red before the extractor change and green after it.

Pins of the floor change from 20 to 3 in `tests/test_tattoo_library.py` and `tests/test_ui_tattoo.py`. No test is deleted for that. One test reads a count that the new floor closes: `test_ink_view_refuses_points_too_few_to_close_saying_so` passes `points[:3]` and now takes `points[:2]`, below the floor under the same marker.

## Dependencies

None.

## Risks / Trade-offs

- A tight outline over a solid fill is cut to a layer with no ink in it, and nothing refuses. The person accepted the bound at the grilling; the ink view is where it shows.
- A floor of 3 lets a triangle close. The close line shows the count, so the operator picks the precision.
- The patch removes a refusal and so changes what an input does that was refused before. Every input accepted before gives the same layer to the byte.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). The decisions are the person's, and the one detail the cut chose, the singular of *1 more point*, follows the lines' existing rule.
