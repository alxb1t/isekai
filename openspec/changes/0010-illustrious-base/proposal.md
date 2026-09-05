---
version: v0.10
---

# Move the one path onto WAI-illustrious-SDXL v17.0

## Why

The base is the last thing in this pipeline nobody chose. Animagine XL 4.0 was picked in v0.2 while
four model paths were still competing, and everything since has been argued *around* it: the
ControlNet stack, the dials, the register. Illustrious-family checkpoints are what the anime SDXL
ecosystem has consolidated on, and WAI v17 is its most-used member. Moving is the point of the
version.

Now, because v0.9 removed the reason to wait. The stack is provisioned from a pinned, checksummed
manifest and the unchanged path has been rendered off a volume whose entire contents were placed by
the script. A base swap performed before that would have conflated *the manifest is wrong* with
*the new base does not work*; performed after, every failure is attributable to the base. That was
`0009-pinned-provisioning`'s whole ordering argument, and this change is the half it was ordering
for.

Three things the swap forces, which are therefore this version's and not a later one's:

- **The register.** `masterpiece, high score, great score` are Animagine-4 ladder tokens and are
  dead weight on Illustrious. WAI's publisher states its own ladder, and states plainly that too
  many quality tags and over-long negatives *degrade* output — so the eighteen-token negative this
  repo carries is not neutral either.
- **`1girl`.** v0.8 recorded it as a defect and named a later version as its owner: it fixes the
  gender of every input photo in a product whose input is "a photo of a person". InstantID's paper
  documents gender as a semantic carried by the *face embedding*, so dropping the tag leaves gender
  to a mechanism already in the graph rather than to a tagger that does not exist.
- **Resolution.** The graph has no resize at all — `VAEEncode` reads `LoadImage` directly, so the
  render happens at whatever the photo's dimensions are. A 4032×3024 phone photo is rendered at
  4032×3024. That has always been true; it becomes urgent here because WAI's guidance names a
  resolution floor and MistoLine requires a short side above 1024, and because "the path runs" is
  otherwise a claim about the two photos that happened to be used.

## What Changes

- **The base becomes WAI-illustrious-SDXL v17.0.** WAI is published on Civitai with no first-party
  Hugging Face repo, so the manifest pulls **bytes** from a pinned mirror revision and verifies them
  against **the SHA-256 Civitai itself publishes**. The digest is what makes the source
  interchangeable, so several byte-identical mirrors are declared as alternates. No Civitai code
  path and no API key go near the pod.
- **Animagine stays declared until the swap is proven**, then leaves in its own phase. The probe
  needs both checkpoints on the volume at once, and a manifest that no longer declares the old one
  would let a re-provision delete the comparison base and the rollback together.
- **BREAKING — the register is rewritten.** The positive becomes WAI's published ladder appended
  last, and **`1girl` is removed**, closing the defect v0.8 recorded. The negative is shortened to
  the publisher's own. Both are pinned by equality, so this is a deliberate test edit.
- **The photo is scaled before anything reads it.** A scale node targets a short side of 1152 with
  aspect preserved and both dimensions multiples of 64, and every consumer — the latent encoder,
  the identity node and both preprocessors — reads the scaled image, so one pixel grid feeds the
  whole graph. The dimensions are computed by injection from the photo itself, because no ComfyUI
  node can derive them.
- **The graph stops CLIP at the second-to-last layer.** Every one of WAI v17's published sample
  images uses clip skip 2 and none of its prose mentions it; shipping without it means shipping a
  configuration the publisher never tested.
- **The tile ControlNet is dropped**, unless a strength-to-zero comparison shows it contributes.
  Its publisher's model card states that it is a realistic training set and that "no comic,
  animation application are promised" — and this repo runs it at strength 0.2 against the card's
  recommended 0.9.
- **`denoise` and `ip_weight` are re-found by eye.** They were tuned on Animagine and do not
  transfer. **This is the last version permitted to settle anything by eye**; the version after
  this one builds the evaluator, and every claim from there is a measured delta against a committed
  baseline.
- **A release-candidate image is published for the metered phases.** The pod provisions from the
  manifest baked into its image, and the WAI entry lands on this branch — so both metered phases run
  a `:v0.10-rc` build and set `RUNPOD_IMAGE` to it. `:latest` is not touched: this repository's CI
  publishes it from a push to `main`, and only from there.

## Capabilities

### New Capabilities

<!-- None. Provisioning, mutation, transport and the CLI all keep their existing contracts; what
     changes is the graph they drive and the register committed to it. -->

### Modified Capabilities

- `workflow-injection`: the committed positive string changes and must assert no gender, not merely
  no pose tag; injection gains the duty of computing a working resolution and writing it into the
  graph; and the graph's conditioning gains a committed CLIP-layer setting.

## Impact

- **`workflows/pipeline.json`** — `ckpt_name`, a `CLIPSetLastLayer`, a scale node rewired into four
  consumers, both prompt strings, and the tile branch removed. **`workflows/pipeline_ui.json`** is
  already marked stale and lags further; it is not regenerated from the API graph.
- **`isekai/workflow.py`** — injection reads the photo's dimensions and writes the scale node's
  width and height. Dimension reading is **stdlib-only** JPEG/PNG header parsing; no dependency is
  added, and the runtime rule is untouched.
- **`isekai/pipeline.py`** — the photo's path reaches `inject`, which previously took only the
  uploaded filename.
- **`scripts/models.json` and `scripts/derive_manifest.py`** — the WAI entry with its alternates
  arrives, the tile entry leaves, and Animagine leaves last.
- **`tests/`** — the pinned register literals, the scale scenarios, the CLIP-layer scenario, and a
  stale comment in `tests/test_workflow_injection.py` that names v0.9 as `1girl`'s owner.
- **Two metered phases** (⚠️ GPU): the probe that answers the ControlNet and dial questions, and
  the final renders. `RUNPOD_IMAGE` must name a current image in both.
- **No new custom nodes.** `ImageScale` and `CLIPSetLastLayer` are core ComfyUI, so the image
  change is a rebuild, not a `Dockerfile` edit.
