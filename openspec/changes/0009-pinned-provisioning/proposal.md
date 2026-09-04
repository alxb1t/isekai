---
version: v0.9
---

# Provision the stack from a pinned manifest

## Why

`scripts/download_models.sh` is the only thing that decides which bytes become the models this
repository renders with, and it pins nothing. Seven sources resolve to whatever `main` points at
on the day the pod boots, no checksum is computed, and a file that is already present by name is
skipped without being looked at. Two of those files are code-executing pickle (`ip-adapter.bin`,
and the pose estimator's TorchScript), and one source — `DIAMONIK7777/antelopev2` — is a
third-party mirror. A moved ref or a swapped file cannot be detected, only discovered.

Worse, the script does not describe the stack it claims to provision. `workflows/pipeline.json`
drives `DWPreprocessor` and `LineArtPreprocessor`, and those nodes fetch **four more model files —
386 MB across three Hugging Face repos — at graph-execution time**, unpinned, onto the pod's
ephemeral container disk rather than the volume. Every fresh pod re-downloads them during a
metered render. Nothing in this repository names them, so no reading of the script could reveal
they exist; they were found by reading the graph.

Now, because the next version replaces the checkpoint. A base swap onto a volume whose contents
are unverifiable conflates two failures that must stay separate: "the manifest is wrong" and "the
new base does not work". This version makes the manifest true and provable while the base is the
known-good one, so v0.10 changes exactly one variable. That reorders what `0008-one-path` recorded
— its proposal says v0.9 swaps the checkpoint — and the reorder is the point: the swap moves to
v0.10 and inherits a volume it can trust.

The volume itself is the other reason for the timing. It is 98% full, it carries the orphaned Qwen
weights that v0.8 removed from the script but never from disk, and it is shared with a second
project under a different mount convention. It cannot absorb another checkpoint, and nobody has
looked at it.

## What Changes

- **`scripts/download_models.sh` is replaced** by the design already proven in the operator's
  sibling project: plain `resolve/<commit-sha>/` URLs fetched with `wget`, a SHA-256 constant per
  file, download to `.partial` → verify → `mv`, and **verification on the skip path** so a warm
  volume is re-checked rather than trusted. A mismatch aborts. The `hf` CLI dependency goes.
- **The manifest grows from seven sources to eleven.** The four annotator files
  (`yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`, `sk_model.pth`, `sk_model2.pth`) become
  declared, pinned, verified downloads, and `AUX_ANNOTATOR_CKPTS_PATH` moves them onto the volume
  so they are fetched once rather than on every pod's first render.
- **Every source carries an ordered fallback list**, and a source's hash is pre-flighted from
  Hugging Face's `x-linked-etag` response header before any large transfer begins, so a moved or
  replaced file fails in a second instead of after a multi-gigabyte download.
- **The graph and the manifest are bound by a test.** Every model filename referenced in
  `workflows/pipeline.json` must have a manifest entry. This is the only mechanism that would have
  caught the annotator gap, and the only one that stops it recurring on the next base swap.
- **The volume gains per-project namespaces.** The pod mounts at `/runpod-volume` and symlinks
  `/opt/ComfyUI/models` at `/runpod-volume/isekai`, so one symlink namespaces every custom node's
  model resolution rather than per-folder symlinks that each node may or may not honour. Artifacts
  shared with the sibling project are **duplicated, not shared**: independence is worth 32¢/month.
- **The 62 GB volume is inventoried, replaced and destroyed** — in that order, and only after a
  new volume provisioned *solely by the script* renders the unchanged Animagine path successfully.
- Nothing about the graph, the CLI or the rendered output changes. `pipeline.json`'s
  `ckpt_name` stays Animagine XL 4.0.

## Capabilities

### New Capabilities

- `model-provisioning`: which model artifacts the stack requires, where each comes from, how its
  bytes are proven to be the intended ones, and the binding that keeps the manifest and the
  rendered graph describing the same set of files.

### Modified Capabilities

<!-- None. No requirement of workflow-injection, workflow-mutation, comfy-transport or cli
     changes: the graph, the transport and the command line are untouched by this change. -->

## Impact

- **`scripts/download_models.sh`** — rewritten; `hf` CLI no longer required.
- **New tracked manifest data** plus a stdlib-Python verification module the script invokes, so
  the trust boundary is exercised by `pytest` rather than only by a pod.
- **A re-derivation helper** that regenerates every revision and SHA-256 constant, so an upgrade
  is mechanical rather than eleven manual lookups.
- **`Dockerfile`** — `AUX_ANNOTATOR_CKPTS_PATH`; **`start.sh`** — the namespace symlink;
  **`infra/up.sh`** — `volumeMountPath` moves to `/runpod-volume`.
- **`tests/`** — a new capability's scenarios, the graph↔manifest cross-check, and verification
  unit tests including corrupt-file-exits-non-zero.
- **`.env` in this repository and in the sibling project** — the volume id changes when the
  volume is replaced. The sibling's `.env` currently names a different id than this one while the
  account holds a single volume, so one of the two is already stale.
- **Two metered phases** (⚠️ GPU): the inventory, and the provision-and-render that proves the
  manifest. No CPU-pod tooling is added; the operator brings the pod up with `infra/up.sh`.
- **No runtime dependency changes.** The runtime stays stdlib-only; the verification module uses
  `hashlib`.
