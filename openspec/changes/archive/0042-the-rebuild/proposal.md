---
version: v0.29.1
backlog: [0040·S1, 0040·S3, 0040·R2, op·telemetry-in-image, 0033·S3, op·slim-image]
---

# 0042 — the rebuild

The image rebuilt once, for everything that waited on a rebuild. The upload stops spooling to the container disk,
`/dev/shm` is checked to be memory, the telemetry switches live in the image, the build tools are checked by hash,
onnxruntime is the CPU package, which moves DWPose's box detector to OpenCV, and the base is plain Ubuntu. One rc
build, one metered session.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the base, the memory step, the switches, the image project, and the session's evidence |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` |

## Why

**The photograph still touches the container disk.** ComfyUI's upload handler spools each file to `TMPDIR`, which is
unset, so the photograph lands under `/tmp` before it reaches `/dev/shm`. Nothing checks `/dev/shm` is memory, and an
unreadable free figure is reported as "0 KiB free".

**The image carries what it does not use, and trusts what it does not check.** Every pull downloads a CUDA toolkit
that torch's own wheels make redundant. `onnxruntime-gpu` is built for CUDA 13, so it already falls back to the CPU —
but DWPose (`summon-anime-wai` only) runs its box detector through it, and without it runs that detector on OpenCV.
The sdist build tools are fetched by version alone. The telemetry switches live in `up.sh`'s create, not in the image.

## What Changes

- **The base is `ubuntu:22.04`, named by digest**, with `build-essential` and `ca-certificates` in place of apt's
  Python, and the `NVIDIA_*` variables the old base set ([D1](design.md#d1)).
- **ComfyUI's temporary files live in `/dev/shm`**, and the pod holds when `/dev/shm` is not a tmpfs or its free space
  cannot be read ([D2](design.md#d2)).
- **The telemetry switches are the image's `ENV`**, and `up.sh` stops sending them ([D3](design.md#d3)).
- **onnxruntime is the CPU package**, so DWPose's box detector runs on OpenCV rather than onnxruntime; the operator
  ruled on 2026-09-29 that the release stays a patch ([D4](design.md#d4)).
- **The sdist build tools are checked by hash** ([D5](design.md#d5)).
- **0.26.1's changelog bullet states the append-only exception** its design recorded ([D6](design.md#d6)).
- **A new image, built on request and proved on one pod** ([D7](design.md#d7), [D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - MODIFIED *Everything ComfyUI writes lives in the pod's memory* — gains the temporary files, the tmpfs check and
    the unreadable figure.
  - MODIFIED *The image is built only on request, from inputs pinned by digest and a locked environment* — gains the
    build tools checked by hash.
  - MODIFIED *A pod sends no usage report its libraries can be told not to send* — the image carries the switches,
    not the pod-creation script.

## Impact

- **Files:** `Dockerfile`, `start.sh`, `infra/up.sh`, `tools/derive_image_project.py`, `image/pyproject.toml`,
  `image/uv.lock`, `config/image.json`, `tests/test_infra.py`, `docs/pins.md`, `docs/principles.md`, `CHANGELOG.md`.
- **Behaviour:** nothing of the photograph's reaches the container disk. `conjure-anime-wai`'s render is unchanged;
  `summon-anime-wai`'s pose now comes from DWPose's box detector on OpenCV, so the same inputs may give a different
  image. That breaks the patch rule's same-image clause, and the operator ruled the release a patch all the same
  ([D4](design.md#d4)).
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** `onnxruntime` replaces `onnxruntime-gpu` in the image — approved at the grilling.
- **Spend:** one metered session, 45 minutes and ~$0.30 ceiling.

## Not in this change

- **The pod's lifecycle** — the gates, the reconciler and the pod-side stop — the session version.
- **A builder stage**, and **onnxruntime on the GPU**.
- **The rehash at boot**, and **the uv cache in the image**.
- **Deleting old images from GHCR.**
