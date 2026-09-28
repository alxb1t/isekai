---
version: v0.28
backlog: [priv·memory-only, op·render-metadata, op·baked-host-keys, 0033·image-layers, priv·purge, priv·logs]
---

# 0040 — the pod image

The pod keeps nothing on disk, and each pod has its own identity: everything ComfyUI writes lives in memory, no
render carries its prompt, and each pod makes its own SSH host key and prints its fingerprint. One image rebuild,
proved by one metered session that also renders a stripped, rotated photograph end to end.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the image, the start script, the rebuild and the session's evidence |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` |

## Why

**The pod keeps the photograph on a disk nobody can wipe.** ComfyUI writes the upload and every render to the
container disk, whose erasure after teardown RunPod does not document, and embeds the whole prompt in each render.

**Every pod presents the same host key, and anyone holds it.** The public image ships `/etc/ssh/ssh_host_*`,
private halves included, so a host-key check could prove nothing.

## What Changes

- **Everything ComfyUI writes lives in `/dev/shm`**: its input, output, temp and user directories; a pod with too
  little memory holds instead of starting ComfyUI ([D2](design.md#d2)).
- **No render carries metadata**: ComfyUI starts with `--disable-metadata` ([D3](design.md#d3)).
- **The image ships no host key; each boot makes an Ed25519 key, serves SSH with it alone, and prints
  `isekai host key: SHA256:<fingerprint>`** ([D1](design.md#d1)).
- **`uv sync` runs before the node clones**, so a node bump stops rebuilding torch ([D4](design.md#d4)).
- **A new image, built on request and proved on one pod** ([D5](design.md#d5), [D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - ADDED *A pod makes its own host key and prints its fingerprint*.
  - ADDED *Everything ComfyUI writes lives in the pod's memory*.
  - ADDED *No render carries metadata*.

## Impact

- **Files:** `Dockerfile`, `start.sh`, `config/image.json`, `tests/test_infra.py`.
- **Behaviour:** the render is unchanged; the pod writes nothing of the photograph's to its disk, and its host key is
  its own.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.
- **Spend:** one metered session, 45 minutes and ~$0.30 ceiling.

## Not in this change

- **The client's fingerprint check** (`op·P2`), **EU-only data centres** and **the privacy principles** — the next
  privacy version.
- **A slimmer base image** (`op·slim-image`) and **hashed build tools** (`0033·S3`) — the session version.
- **A check that the pinned image matches the tree** (`0033·R6`) — the pool.
- **`up.sh`, `render.sh` and the transport.**
- **Deleting old images from GHCR.**
