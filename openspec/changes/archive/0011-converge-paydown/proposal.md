---
version: v0.11
---

## Why

Two converge passes — `0009-pinned-provisioning` and `0010-illustrious-base`, both `verdict: clean`,
both `open_blocking: 0` — exported **twenty non-blocking findings** on 2026-09-05. They were correctly
not fixed under a release deadline, and they are correctly not carried forever: a nit that survives two
releases stops being a nit and becomes the repository's normal state. Six of them sit inside guards
whose whole purpose is to fail, and the round-2 notes establish that four of `provision.py`'s manifest
checks have **no runtime caller at all** — they are commit-time assertions that cannot bite on a pod.

This version pays all twenty down, adds one defect found while planning it, and ends on the metered
session that `make gate` cannot substitute for. It ships **no new product capability**: the CLI's
surface, the graph, the register and every dial are untouched.

## What Changes

**It adds no product behaviour. It does add nine enforcement guarantees**, because a guard that is
not spec-bound is a comment. Those are named in `## Capabilities` and are the honest reading of
"stabilization" — nothing new for the operator, several new things the code refuses.

- **`start.sh` and `infra/up.sh`** — the twenty-line namespace block and the provisioning guard.
  `up.sh` refuses to create a pod when `RUNPOD_VOLUME_ID` is empty and passes it into the container;
  `start.sh` refuses to provision onto anything that is not the network volume, refuses to `rm -rf` a
  non-empty models tree, extends the reachability hold to cover namespace setup, bounds that hold at
  900 s, writes a failure marker to container disk, and stops describing the ComfyUI models tree as
  empty. *(0009: R3 R4 R8 S4 S7)*
- **`Dockerfile`** — ComfyUI's core is pinned to a commit, the last unpinned link in the change whose
  thesis was pinning. The commit is **the one `:v0.10-rc` was built from**, recovered from the image
  still in GHCR — so the pin records what already ran rather than importing an untested core.
  *(0009: S5)*
- **`isekai/provision.py` and `scripts/download_models.sh`** — `plan` emits an already-resolved
  absolute target so the shell joins no paths; `decide` rejects a `dest` that escapes the models root,
  a source that is not a pinned whitespace-free URL, and an entry declaring no sources at all; the
  graph↔manifest binding covers `InstantIDFaceAnalysis` rather than only `*Preprocessor` classes; the
  driver reads the URL list into an array instead of word-splitting it. *(0009: R6 R7 S1 S6)*
- **`isekai/workflow.py`** — three stated ceilings where there were none: a long side, a PNG header
  dimension, and a byte bound on the JPEG marker walk. Each refuses by naming the file and the limit.
  *(0010: R6 S1 S5)*
- **`.github/workflows/build-image.yml`** — the `latest`-protection the header comment asserts becomes
  a check the workflow runs, and the dispatch default stops naming a two-version-old tag.
  *(0009: R5 S2)*
- **⚠️ A metered smoke test** — one pod, four renders and two loader probes at input shapes v0.10
  explicitly left untested. See `design.md` D10 for what it may and may not conclude.
- **The PNG `eXIf` question** — found while planning this change, not exported by either converge pass.
  `_png_dimensions` reads IHDR and stops, while `LoadImage` may transpose a PNG carrying an `eXIf`
  Orientation — the same defect v0.10 called blocking, in the codec branch that was not fixed. The
  smoke test's loader probe decides it; the phase after the pod writes either the fix or the finding
  that IHDR-only is correct.
- **`scripts/derive_manifest.py`** — WAI's SHA-256 stops being hand-transcribed and is derived from
  Civitai's API like every other digest, making the module's own "derived, never transcribed" claim
  true without exception. *(0010: S4)*
- **The change record and the suite's labels** — the unreconciled 1152, the pose preprocessor's
  separate pixel grid, the two indistinguishable probe artifacts, and a `spec_exempt` reason that
  calls a by-eye value pin "structural". *(0010: R4 R5 R7 R8)*

**Deliberately not here.** No register change: v0.10 named `realistic, photorealistic` as the first
thing to check next, and that — with the unmeasured quality ladder — waits for the evaluator version,
because changing a register now moves the floor the evaluator is about to measure against. `0010:R4`
is recorded, not re-tested: which reading of MistoLine's card is right is a rendering question, and
rendering questions wait for the evaluator. `0009:S3` stays on the unscheduled track with its trigger,
as `0009`'s `design.md` already argued.

## Capabilities

### New Capabilities

None. No capability is introduced; this change ships no new product behaviour.

### Modified Capabilities

- `workflow-injection`: `working-resolution` gains stated ceilings — a computed target beyond a
  long-side bound, a PNG header dimension beyond a stated maximum, and a JPEG marker walk beyond a
  stated byte budget are each refused rather than carried onto a metered pod. Its
  `scale-precedes-every-consumer` scenario is corrected: the shipped text claims no control hint is
  registered against a different pixel grid, and `DWPreprocessor` derives its hint at 512 while the
  graph works at 1024, so the claim is false as written and is narrowed to what the suite proves.
- `model-provisioning`: `immutable-pins` gains runtime enforcement where it had commit-time
  assertions — a destination that escapes the models root, a source that is not a pinned URL, and an
  entry with no sources are each refused by the module rather than only by the suite. `reachability`
  gains the volume guarantee (the pod refuses to provision unless the models namespace is on the
  network volume it was created with) and bounds the failure hold. `namespace` extends the
  graph↔manifest binding to the graph's other self-fetching node.

### Removed Capabilities

None.

## Impact

- **Code** — `start.sh`, `infra/up.sh`, `Dockerfile`, `isekai/provision.py`,
  `isekai/workflow.py`, `scripts/download_models.sh`, `scripts/derive_manifest.py`,
  `.github/workflows/build-image.yml`, `tests/`.
- **Not touched** — `workflows/pipeline.json`, `isekai/mutate.py`, `isekai/overrides.py`,
  `isekai/comfy_client.py`, `isekai/cli.py`, `convert.py`. The graph, the register, every dial and the
  CLI's surface are unchanged.
- **`scripts/models.json`** — re-derived and **byte-identical**: the transcribed WAI digest was
  verified against Civitai's API before this change was cut and agrees exactly, bytes included. No
  manifest entry moves and no volume is re-provisioned.
- **Dependencies** — none added. The runtime stays stdlib-only; `provision.py` stays outside
  `convert.py`'s import graph.
- **Money** — one metered pod session, budgeted at ~15 min ≈ $0.19 against a 24-minute / ~$0.30 wall.
- **Image** — one `:v0.11-rc` build, published by `workflow_dispatch`. `:latest` is untouched until
  the release merges.
</content>
