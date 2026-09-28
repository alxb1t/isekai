---
version: v0.27
backlog: [priv·exif]
---

# 0039 — the photo metadata

The photograph leaves the Mac without its metadata: at upload, only the blocks that decode its pixels and its
orientation are sent. The run's copy, the pixels and the render stay as they are. The first privacy version, before
the pod image and the right machine.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | what each format keeps, where the stripping lives, and how the unchanged render is proved |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `image-generation` |

## Why

**The upload carries everything the camera wrote.** `ComfyClient.upload_image` sends the run's copy byte for byte,
so the rendering pod receives the photograph's GPS position, capture time, device, and any thumbnail, XMP, IPTC,
comment or appended data. It is the one place the photograph leaves the machine; tag and caption stay on the local
Ollama.

## What Changes

- **At upload, a photograph keeps only the blocks that decode its pixels, its colour profile and its orientation**;
  everything else goes, including data after the image's end ([D1](design.md#d1), [D2](design.md#d2)).
- **The stripping works on bytes and never re-encodes**, so the compressed image data and the render are unchanged
  ([D1](design.md#d1)).
- **A photograph the stripper cannot walk is refused, never sent whole** ([D5](design.md#d5)).
- **The transport takes a name and bytes**: `ComfyTransport.upload_image(name, data)` ([D4](design.md#d4)).
- **The run's copy is untouched**, so the run id and resume keep their meaning ([D3](design.md#d3)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation`: ADDED *A photograph leaves the machine without its metadata*.

## Impact

- **Code:** `isekai/shared/image.py`, `isekai/boundary/comfy/contract.py`, `isekai/boundary/comfy/client.py`,
  `isekai/pipeline/generate.py`.
- **Tests:** `tests/test_image.py`, `tests/test_generate.py`, `tests/test_resume.py`, `tests/fakes.py`.
- **Docs:** `isekai/shared/README.md`'s row for `image.py`.
- **Behaviour:** the pod receives a photograph without metadata; the render is unchanged. No format version moves.
- **Dependencies:** none. PyAV is used once, in a build-phase check, from `uv run --with`, and is not declared.

## Not in this change

- **The run's own copy** — it keeps its bytes; it never leaves the machine.
- **What Ollama receives** — it runs on this machine.
- **Re-encoding or transposing pixels**, and how a mirrored orientation renders.
- **The pod, the image and `infra/`** — the render path's privacy is the next version's.
- **An end-to-end render** of a stripped photograph — the pod image version's metered session holds it.
