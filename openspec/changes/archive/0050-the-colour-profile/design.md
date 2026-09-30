# Design — 0050 the colour profile

Which blocks leave the upload's allowlist, and which refusals get a case. **Verdict: feasible** — two constants, a
docstring and tests.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`e08e775`):

- **The allowlist:** `_JPEG_KEPT_APPS` keeps APP2 `ICC_PROFILE` (`isekai/shared/image.py:353`), every segment of a
  split profile copied whole; `_PNG_KEPT_CHUNKS` keeps `gAMA`, `cHRM`, `sRGB`, `iCCP`, `sBIT` and `cICP` (`:364-367`).
  `strip_metadata`'s docstring says the profile is kept verbatim (`:377`).
- **Dropping is already safe:** APP2 falls in `_JPEG_DROPPED` (`:359`) once it is not kept; every PNG colour chunk is
  ancillary, so `_strip_png` drops it rather than refusing (`:465-469`).
- **The endpoint ignores the profile:** the pinned ComfyUI's `LoadImage` decodes with PyAV, which converts no
  transfer or primaries unless asked, and its Pillow fallback's `convert("RGB")` never reads `icc_profile`.
- **The refusals:** `strip_metadata` wraps each reason (`:386-396`); `_strip_jpeg` and `_strip_png` raise them
  (`:398-470`). `tests/test_image.py` expects none; the `an-unwalkable-photograph-is-refused` tests in
  `tests/test_generate.py` (`:1026`, `:1044`, `:1066`) share `_UNWALKABLE` (`:1023`), a scan with no end.
- **The allowlist test** `test_no_block_outside_the_allowlist_survives` (`tests/test_image.py:434-452`) asserts
  `iCCP` and APP2 kept.

## Goals / Non-Goals

**Goals:** the upload carries no colour metadata; every refusal named below is reached by a test.

**Non-Goals:** the renders' colour; converting pixels; any file the image copies.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | APP2 leaves `_JPEG_KEPT_APPS`; `gAMA`, `cHRM`, `sRGB`, `iCCP`, `sBIT` and `cICP` leave `_PNG_KEPT_CHUNKS`; `PLTE` and `tRNS` stay | the endpoint decodes without them; the allowlist then matches the principle | scrubbing the profile's text, which parses ICC for no pixel |
| [D2](#d2) | one parametrised test in `tests/test_image.py` calls `strip_metadata` on each untested refusal | a refusal no test reaches can regress into a crash or a whole upload | one test per refusal |

### D1

**The allowlist.** Before → after:

```
_JPEG_KEPT_APPS  = {0xE0: JFIF, 0xE2: ICC_PROFILE, 0xEE: Adobe}   →  {0xE0: JFIF, 0xEE: Adobe}
_PNG_KEPT_CHUNKS = IHDR PLTE IDAT IEND tRNS gAMA cHRM sRGB iCCP sBIT cICP
                                                                 →  IHDR PLTE IDAT IEND tRNS
```

`strip_metadata`'s docstring says the pixel data and the orientation are kept. `test_no_block_outside_the_allowlist_survives`
asserts no profile survives. A new test, `test_no_colour_profile_leaves`, strips a JPEG with a profile and a PNG with
a profile and each colour chunk, and asserts none survives and the decoded pixels match.

### D2

**The refusals.** Each case builds a photograph with `tests/images.py`'s helpers and expects a `Refusal` that starts
with the photograph's name and names what stops the walk:

```
a truncated PNG chunk         "the chunk at byte … runs past the file"
a first chunk not IHDR        "its first chunk is not IHDR"
an unknown critical chunk     "it carries critical chunk …, which is not known"
an unknown JPEG marker        "it carries marker 0x…, which is not known"
a too-short length word       "the segment at byte … runs past the file"
neither a JPEG nor a PNG      "it is neither a JPEG nor a PNG"
```

## Dependencies

None.

## Risks / Trade-offs

- **A future endpoint applies colour profiles** → a wide-gamut photograph would then shift; the upload names no
  profile, so it reads as sRGB, as today's endpoint reads it.
- **A CMYK JPEG** → APP14 `Adobe` stays, so its colour transform still decodes.

## Verdict

**feasible** — two constants and tests; the pixels the endpoint decodes do not change.
