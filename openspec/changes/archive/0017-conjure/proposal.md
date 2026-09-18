---
version: v0.17
---

## Why

**`summon-v1` is the only flow there is, so *per-flow* is untested by construction.** v0.16 made a flow
five frozen files that share nothing, gave `build_graph` four required roles and seven guarded ones,
made `--flow` required and repeatable, and nested the run layout input-first — all so that **adding a
flow would be a directory and nothing else.** Nothing has tested that claim.

**Now, because the claim decays if it is not tested.** Every version after this one adds surface that a
second flow would have to fit through. **If this version needs a code change, v0.16 was incomplete —
and recording that precisely is the point of the version**, not a failure of it.

## What Changes

- **`flows/conjure-v1/` — five authored files.** A second product: an anime character drawn to a sheet
  of canonical tags, rendered **from the sheet alone**. No identity node, no ControlNet, no photograph
  in the graph. **It makes no identity claim and is not evaluated.**
- **`graph.json` — 14 nodes.** `summon-v1`'s 23 minus nine (`2` LoadImage, `5` `6` `8` InstantID, `7`
  `17` ControlNetLoader, `16` DWPreprocessor, `18` ControlNetApplyAdvanced, `22` ImageScale), with **six
  edges repointed**: both KSamplers (`10`, `34`) take `model` from `CheckpointLoaderSimple(1)` and
  conditioning from `CLIPTextEncode(3)`/`(4)`. Those are the sources InstantID displaced, so the rewiring
  **restores rather than invents**. The hires chain (`30`–`33`, `35`) and `CLIPSetLastLayer(23)` are
  untouched.
- **`flow.json` — `inputs: ["sheet"]`, and `photo` declared on NEITHER side.** `TRANSFERRED_INPUTS`
  (`isekai/foundation/flow.py:91`, checked at `:327`) refuses a manifest that declares the photograph on
  one side only; omitting it from both is the sheet-only case and passes. Seven node roles, **two
  models** (the base checkpoint and the upscaler), and dials minus `ip_weight`,
  `identity_cn_strength` and `openpose_strength`.
- **`schema.json` — 21 fields.** `summon-v1`'s sixteen plus `bangs`, `facial_hair`, `lips`, `nose`,
  `eyelashes`, all `scored: false`. In `summon` the identity and pose legs supply the face; `conjure`
  has neither, so the face reaches the render only as tags.
- **`caption.briefing.md` and `sheet.briefing.md` — both differ.** The caption briefing is richer on the
  face and licenses inference on **named axes only**; *"do not interpret"* is kept and narrowed to the
  identity-bearing fields. The sheet briefing enumerates the fields and prints two worked sheets, so a
  changed field list changes it too.
- **`tests/test_flow.py` — two lines.** `PINNED` gains `conjure-v1` (by design: the pin list is what
  makes adding or removing a flow deliberate). And `:124`'s `assert tracked_flows() == ["summon-v1"]`
  is widened — **an incidental single-flow assumption, and the one defect this change repairs.**
- **No production code changes.** `isekai/`, `scripts/`, `Dockerfile`, `start.sh`, `infra/`, `Makefile`,
  `pyproject.toml`, `.github/` and `openspec/specs/` are untouched.

## Capabilities

**New Capabilities:** none.

**Modified Capabilities:** none — `skip_specs: true`, argued in `no-spec-delta.md`.

## Impact

- **Added:** `flows/conjure-v1/{flow.json,graph.json,schema.json,caption.briefing.md,sheet.briefing.md}`.
- **Modified:** `tests/test_flow.py` (two lines).
- **Provisioning is unaffected.** `conjure-v1` declares two of the manifest's twelve entries, and
  nothing asserts `scripts/models.json ⊆ ∪ flows` — nor can provisioning see a flow at all, since
  `start.sh` runs `download_models.sh` over the whole manifest and the image never copies `flows/`.
- **Seven findings are recorded rather than fixed**, each with a trigger. Two block the evaluation
  version: two flows in one invocation are **not seed-matched** (`isekai/pipeline/generate.py:389-393`
  draws per-directory from one shared `Random` at `isekai/interface/wiring.py:58`), and `generate`
  renders in on-disk order rather than `--flow` order (`generate.py:208`, `:140`).
