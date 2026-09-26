---
version: v0.24
---

# 0033 — pin and record

Everything that shapes an output is pinned, and every artifact records what shaped it: the pod image by
digest, its Python environment locked, CI's actions by commit, the reader's model checked against its
files; the options, the floor, the flow's digest and the image recorded where they act.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | every choice that settles how, and the premises settled at the cut |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | the pod image, the reader's pins, the records, the runtime a render ran on |

## Why

**The principles say everything that shapes an output is pinned, and the build holds little of it.** The pod
boots `:latest`, rebuilt on every merge from a moving base, a moving `uv` and unlocked requirement files;
CI's actions follow major tags; the reader is an alias whose files nothing checks.

**The records say less than the principle promises.** No artifact records the sampling options, the tagger's
floor, the flow's digest or the image; a render's `sheet_version` repeats the approval's number; the approval,
the prompt and the render drop the field map and the schema document.

**Evaluation will soon publish figures a later version must beat**, and a figure is only comparable if what
produced it is known.

## What Changes

- **BREAKING — the pod boots only the image `config/image.json` pins by digest**; the `RUNPOD_IMAGE` override
  goes; `up.sh` records the booted reference in `.runpod_pod_image` ([D3](design.md#d3)).
- **The image is built on request only**, from a base and `uv` named by digest and a Python environment locked
  as its own uv project, `image/` ([D2](design.md#d2)).
- **CI's actions by commit**, its runner, `uv` and Node pinned ([D1](design.md#d1)).
- **The reader's files get a manifest, `config/reader.json`**, and the model an alias names is checked against
  it before the first call; the caption and the hosted tags then declare their pin ([D4](design.md#d4)).
- **The records** — options, floor, the flow's digest, the sheet's number, the image and the runtime, the
  carried schema document and field map ([D5](design.md#d5)); **new keys are optional under version 1**
  ([D6](design.md#d6)).
- **A boot prints when each step begins** ([D2](design.md#d2)).
- **An acceptance runs the whole flow, both flows, with every pin in place**, on a pod booted by digest
  ([D8](design.md#d8)).

## Capabilities

### New Capabilities

- `pod-image`: the image a rented pod runs — how it is built, named and booted.

### Modified Capabilities

- `caption` · *A hosted model that is not running or not installed is refused before any attempt is spent* —
  also a model built from unpinned files, and a model no entry pins.
- `caption` · *A caption records the files its model was built from and the options it was sampled at* — added.
- `tagging` · *A tagger's producer names what made the artifact, and claims a pin only when it has one* — the
  hosted tagger's pin, its options, the local tagger's floor.
- `tagging` · *Both taggers run for a flow that declares the tagger, …* — an unpinned hosted model refuses
  without costing the local list.
- `sheet` · *The stage fills fields from the tag list …* — records the flow's digest, carries the floor.
- `image-generation` · *A flow is pinned by equality …* — a render shows which side of a re-pin it falls on.
- `image-generation` · *Seeds are explicit or drawn, and an output is named by its seed* — removed; replaced by
  *… under its approval*: the directory is the approval's number.
- `image-generation` · *A prompt and a render record the flow's digest and the sheet they came from* — added.
- `image-generation` · *A render records the image and the runtime it ran on* — added.
- `model-provisioning` · *Manifest derivation is shared …* — says *every deriver*.
- `model-provisioning` · *The tag vocabulary and the model it indexes are provisioned from one manifest* —
  says *every manifest*.
- `model-provisioning` · *The reader's files are provisioned from their own manifest, keyed by the model they
  build* — added.
- `run-directory` · *A record key added under a kind's version is optional to every reader* — added.
- `review` · *A draft carries the sheet's schema document and field map through to its approval* — added.
- `comfy-transport` · *The server's runtime is read from its own report* — added.

## Impact

- **Files:** `Dockerfile`, `image/` (new), `start.sh`, `infra/up.sh`, `infra/down.sh`, `docker-compose.yml`,
  `.env.example`, `.gitignore`, `.github/workflows/`, `pyproject.toml`, `uv.lock`, `Makefile`, `config/`
  (`image.json`, `reader.json`, `joycaption.Modelfile`), `tools/`, `isekai/boundary/` (`ollama.py`,
  `provision.py`, `comfy/`), `isekai/pipeline/`, `isekai/foundation/artifacts.py`, `isekai/interface/`,
  `tests/`, `docs/`, `README.md`, `CLAUDE.md`, `CHANGELOG.md`.
- **Behaviour:** a pod boots one image; a caption or hosted tag list refuses an unpinned model; every artifact
  records more. The renders may move: the lock resolves today's package versions ([D2](design.md#d2)).
- **Operator:** `uv` 0.12.19 on this machine; the models volume grown to 45 GB before the acceptance.
- **Dependencies:** none added to isekai; the image's own are locked, not added.

## Not in this change

- **Pinning apt packages** — the image's digest holds them; a dated archive is a larger mechanism.
- **A runtime base image** (`slim-image`) — it would blur this version's proof.
- **Moving ComfyUI's or a node's commit.**
- **RunPod's REST v2** — its own patch before 2026-11-15; **`P2`, `eu-only`, `exif` and the other privacy cards.**
- **The render's unbounded poll** (`0031 S2`) and **`config/models.json`'s mirror-primary entries**.
- **`show` printing the new records**, and **the evaluator reading the render's `image`.**
