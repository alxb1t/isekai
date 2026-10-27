# Design — 0084 flat summon

Two candidate flows, a prototype the operator judges, and the winner kept. **Verdict: feasible-with-caveats** — the
flows are files; whether either is flat enough and still the person is the prototype's answer, and a failure ships
nothing.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `fe19377` (`v0.56.0`):

- **Summon's manifest:** the trailer `anime screencap, detailed eyes, soft lighting`, the negative `bad quality, worst
  quality, sketch, lens flare, light particles, dust`, `ip_weight 0.9`, `identity_cn_strength 0.8`
  (`flows/summon-anime-wai/flow.json:13–31`).
- **Summon's graph:** `ApplyInstantIDAdvanced` (node `8`) takes the checkpoint (node `1`) and the sheet's conditioning
  (nodes `3`, `4`), `end_at 1` (`flows/summon-anime-wai/graph.json:72–110`); the OpenPose apply (node `18`) takes node
  `8`'s conditioning; the hires sampler (node `34`) takes node `8`'s model and node `18`'s conditioning, denoise
  `0.35` (`:326–335`).
- **Dials** reach the graph through `ROLE_DIALS` (`isekai/foundation/flow.py:141–147`), so a new dial would re-pin
  summon and control.
- **A variant's precedent:** `control-anime-wai`, held equal to summon by `CONTROLS` and its tests
  (`tests/test_flow.py:58–62`, `:958–975`); its approval copied from summon's and its renders on summon's seeds (D38).
- **The pins:** `PINNED` (`tests/test_flow.py:50–57`). The app offers the flows `config/ui.json` names; a flat flow is not among them.
- **The evaluator:** `uv run python -m evaluation <collection>/runs --cohort <cohort>` matches a run to a cohort
  photograph by the digest of its photograph (`evaluation/__main__.py`); a cohort is `<directory>/<person>/<file>`
  (`evaluation/cohort.py:100–112`).
- **The newest decision** is D43 (`docs/decisions.md`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_flow.py` | 55 | `grep -c "def test_" tests/test_flow.py` |

## Goals / Non-Goals

**Goals:** a flatter summon that keeps the person, proven on the operator's photographs. **Non-Goals:** a new model;
a change to summon, conjure or control.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **candidate A** `flows/summon-flat-a-anime-wai/`: summon's files; `flow.json` — the identifier, `ip_weight 0.7`, the trailer `anime screencap, detailed eyes, soft lighting, flat color, cel shading, lineart`, the negative `bad quality, worst quality, sketch, lens flare, light particles, dust, realistic, photorealistic, 3d, semi-realistic`; `graph.json` — node `8`'s `end_at 0.65` | the face set early, the style late; no model | `end_at` as a dial |
| [D2](#d2) | **candidate B** `flows/summon-flat-b-anime-wai/`: A, and node `34`'s `model` `["1", 0]`, `positive` `["3", 0]`, `negative` `["4", 0]` — the hires pass on the plain checkpoint and the sheet's conditioning | the refine restyles without InstantID | a second graph stage |
| [D3](#d3) | **the guard:** `FLATS = {candidate: "summon-anime-wai"}` in `tests/test_flow.py`, beside `CONTROLS`; each flat flow's schema and briefing byte-identical; its graph equal but for node `8`'s `end_at` below one, and, while candidate B stands, node `34`'s inputs; its manifest equal but for the identifier, `ip_weight`, the trailer and the negative, which hold the flat terms; both candidates pinned in `PINNED`, and not offered in `config/ui.json` | a variant differs in the thing under test alone, as a control does; the prototype and the cohort run from the CLI | offering them in the app |
| [D4](#d4) | **the prototype:** the operator puts fifteen photographs of five people, three each, under `.data/flat-summon-prototype/sources/` as `<person>-<n>.<ext>`; the agent assigns them to the three flows under `.data/flat-summon-prototype/runs/`, tags and sheets summon, corrects each draft against its photograph — adding what it shows, removing what it does not — and approves it, copies them to both candidates with `approve --from`, and renders the three in one session on summon's seeds | the same sheet and seed isolate the style (D38); the app copies no approval and draws its own seeds; a good sheet is a good render's precondition, and the copy keeps the sheet equal across the three; a run keeps its photograph's bytes, so a copy by person is the cohort | the app's collection and Render; summon's machine sheets unedited |
| [D5](#d5) | **the verdict:** the agent copies `sources/` into `.data/flat-summon-prototype/cohort/<person>/` by name, runs the evaluator against it and `compare`; the operator judges flatness by eye in `compare.html` and writes `verdict.md` in this change — `winner: summon-flat-a-anime-wai`, `summon-flat-b-anime-wai` or `none`, and each flow's count; a candidate passes when flat by eye and its count is at least summon's, less one | the operator's eye and the cohort count, on one set of photographs | the published 28 / 30 |
| [D6](#d6) | **the winner:** its directory becomes `flows/summon-flat-anime-wai/`, its identifier with it, pinned under that id; the loser's directory deleted; `FLATS` names the winner alone, and `config/ui.json` does not; D44 *A flat flow is summon with the face chain ending early* in `docs/decisions.md`; `AGENTS.md`'s flows and `README.md`'s tree name it; on `winner: none` the build halts, and the operator destroys the branch | nothing deleted before the evidence (A4); a failed experiment ships nothing | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `image-generation:flat:files-equal-the-subject`, `image-generation:flat:the-graph-differs-in-the-face-chains-end`, `image-generation:flat:the-manifest-differs-in-the-style`, each over `FLATS` | `PINNED` gains each flat flow | `tests/test_flow.py` |

**End-to-end runs added:** none. **Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** some of the likeness rides on the shading → the cohort count gates the winner; a failure ships nothing.
- **[Trade-off]** the prototype spends: thirty images in one session → the Render dialog's quote, against the
  configured ceiling, as any render; the phase names the images.

## Verdict

**Feasible, with caveats.** The flows are files; the answer is the prototype's.
