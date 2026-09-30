---
version: v0.31.2
backlog: [0039·R3, 0039·S3]
---

# 0050 — the colour profile

The upload carries what decodes the photograph's pixels and its orientation, nothing more. The colour profile and the
colour hints leave it — the endpoint never applies them, so no pixel the render sees moves — and each of the
stripper's refusals the tests never reached gets a case.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the allowlist, and the refusal cases |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `image-generation` |

## Why

**The profile leaves the machine for nothing.** An ICC profile names the device's maker and model and a date, and its
description and an `iCCP` name are free text. The pinned ComfyUI decodes without it, so it changes no pixel.

**The spec and the principle disagree.** The requirement keeps "its colour profile"; the principle says the upload
carries what decodes the image and its orientation, nothing more.

**Most of the stripper's refusals are untested.** The tests that reach it share one photograph, which hits one
refusal; a regression in the others could crash or send the file whole.

## What Changes

- **The JPEG ICC profile and the PNG colour chunks leave the upload's allowlist** ([D1](design.md#d1)).
- **The stripper's untested refusals each get a case** ([D2](design.md#d2)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation`: MODIFIED *A photograph leaves the machine without its metadata* — the SHALL no longer keeps the
  colour profile; gains *no colour profile leaves the machine*.

## Impact

- **Files:** `isekai/shared/image.py`, `tests/test_image.py`, `tests/images.py`.
- **Behaviour:** the uploaded bytes lose the profile and colour chunks; the pixels the endpoint decodes do not change.
- **Formats:** none. No file the image copies changes.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **The renders' own colour** — what the pod writes is untouched.
- **Converting a wide-gamut photograph to sRGB** — the endpoint already reads its numbers as sRGB.
