# Design — 0039 the photo metadata

What a photograph keeps when it is uploaded, where the stripping lives, and how the unchanged render is proved.
**Verdict: feasible** — a stdlib byte walk beside the header reader that already exists, and a narrower transport
call.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`984a74f`):

- **The one exit:** `ComfyClient.upload_image` (`isekai/boundary/comfy/client.py:32-57`) sends
  `Path(path).read_bytes()` under `Path(path).name`, from `render` (`isekai/pipeline/generate.py:464-466`). The
  `ComfyTransport` protocol declares `upload_image(self, path: str) -> str` (`isekai/boundary/comfy/contract.py:38`);
  `FakeComfyClient.upload_image` records the path (`tests/fakes.py:73`).
- **The run's copy** is the operator's file byte for byte, named `photo.jpg` or `photo.png`
  (`isekai/foundation/run.py:351`); its digest is the run id (D16).
- **The header reader:** `isekai/shared/image.py` is stdlib-only (`:260-261`, held by the `-S` guard in
  `tests/test_pipeline_cli.py`). It walks JPEG segments to the first SOF (`:196-254`) and PNG chunks to `IDAT`
  (`:101-149`), and reads the orientation from IFD0 (`_tiff_orientation`, `:159-193`).
- **The pod's loader** decodes with PyAV and rotates by the orientation; the probe at `image.py:104-107` found PNG
  orientation applied as JPEG's is.
- **The test photographs** in `tests/images.py` are built by hand and cannot be decoded: `jpeg_bytes` is
  SOI, APP0, SOF0, EOI with no scan; `png_bytes` is a signature and an `IHDR` with a zero CRC and no `IEND`. They
  reach `render` through the `photo` fixture.
- **Signature callers** of `upload_image(path)` in the suite: `tests/test_generate.py:1028` and the wrapper at
  `tests/test_resume.py:560-566`.

## Goals / Non-Goals

**Goals:** nothing leaves the machine but what decodes the pixels, the colour profile and the orientation; the
render unchanged; a photograph that cannot be walked refused.

**Non-Goals:** the run's copy; Ollama's input; re-encoding; mirrored orientations; the pod.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | an allowlist per format: keep what decoding needs, drop the rest and everything after the image's end | a guarantee by construction, not a filter; it also catches appended videos, depth maps and provenance chunks | a list of metadata blocks to drop — it misses what it does not name |
| [D2](#d2) | an orientation other than upright is written back as a minimal EXIF | the pod's loader rotates by it | transposing the pixels — re-encodes, changes the render |
| [D3](#d3) | `strip_metadata(photo)` in `isekai/shared/image.py`; the run's copy untouched | beside the reader that walks the same bytes; stdlib, on the entry point's graph | stripping at intake — changes what the run id means |
| [D4](#d4) | `ComfyTransport.upload_image(name, data)` | the transport carries bytes and knows nothing about images | the transport stripping — the boundary would own an image rule |
| [D5](#d5) | a photograph that cannot be walked to its end is refused and recorded | never send a file whole because it could not be read | sending it unstripped |
| [D6](#d6) | proved by tests on decodable photographs made with Pillow, by a PyAV check, and later by a render | the pod decodes with PyAV, not Pillow | a unit test alone |

### D1

**Keep what decodes; drop everything else.** The walk copies an allowed block verbatim, drops any other, and ends
at the image's end:

| format | kept | dropped | ends at |
|---|---|---|---|
| JPEG | SOI; `APP0` whose payload starts `JFIF\0`, cut to its 14 fixed bytes with no thumbnail; `APP2` whose payload starts `ICC_PROFILE\0`; `APP14` whose payload starts `Adobe`, cut to its 12 fixed bytes; DQT, DHT, DAC, DRI, every SOF; each SOS with its scan data; EOI | every other `APPn` (EXIF, XMP, MPF, JFXX, …), COM | the first EOI — anything after it goes |
| PNG | the signature; `IHDR`, `PLTE`, `IDAT`, `IEND`; `tRNS`, `gAMA`, `cHRM`, `sRGB`, `iCCP`, `sBIT`, `cICP` | every other chunk (`eXIf`, `tEXt`, `iTXt`, `zTXt`, `tIME`, …) | `IEND` — anything after it goes |

- **Between scans** of a progressive JPEG, the walk resumes at the next marker that is not a restart marker or a
  stuffed `0xFF00`, and applies the same table.
- **An unknown marker before a scan, or an unknown critical PNG chunk,** is refused per [D5](#d5): dropping it could
  change the pixels.
- **A file that ends cleanly** after a complete block, without EOI or `IEND`, is copied as far as it goes — the test
  photographs in `tests/images.py` end that way. CRCs are copied, never checked, as the header reader does.

### D2

**The orientation comes back as a minimal EXIF.** The walk reads the orientation the header reader reads
(`_exif_orientation`, `_tiff_orientation`). When it is 2 to 8, the output carries one block holding it alone: a
big-endian TIFF, IFD0 with the single entry `0x0112`, SHORT, count 1 — the shape `tests/images.py`'s `_exif_tiff`
already builds.

- **JPEG:** an `APP1` of `Exif\0\0` and that TIFF, after SOI and any `JFIF` `APP0`.
- **PNG:** an `eXIf` chunk of that TIFF with its CRC, right after `IHDR`.
- **Upright or unreadable:** no block at all.

### D3

**`strip_metadata(photo: Path) -> bytes` in `isekai/shared/image.py`**, stdlib only, so the `-S` guard holds.
`render` uploads `strip_metadata(run.photo)` under `run.photo.name`; the run's copy is only read.

### D4

**The seam takes a name and bytes.** `ComfyTransport.upload_image(self, name: str, data: bytes) -> str`;
`ComfyClient` builds its multipart part from them; `FakeComfyClient` records the name and the data it was handed.
The calls at `tests/test_generate.py:1028` and `tests/test_resume.py:560-566` move to the new signature.

### D5

**Refused, never sent whole.** A photograph the walk cannot read to its end — a block that runs past the file, an
unknown marker before a scan, an unknown critical chunk — raises a `Refusal` naming the photograph and the render
path's existing remedy for an unreadable photograph. Assembly walks it first, for a flow that uploads a photograph,
so the refusal is recorded there before anything is rented; it is raised again inside `render`'s upload `try`, so
`_recorded` records it as permanent and nothing is uploaded.

### D6

**Proved by tests, by PyAV, and by a render.**

- **Tests**, with photographs made in the test by Pillow (imported inside the test, as a runtime dependency already
  is): the stripped JPEG and PNG decode to the same pixels; no EXIF, XMP, IPTC, MPF, comment, text chunk or trailing
  data survives; orientation 6 survives and upright leaves no block. The hand-built photographs in `tests/images.py`
  still walk.
- **PyAV, once:** `uv run --offline --with av==14.4.0` decodes an original and a stripped JPEG and PNG with
  orientation 6, and compares the arrays and the rotation. The output goes into this change's `acceptance.md`; no
  dependency is declared.
- **A render**, end to end, in the pod image version's metered session.

`isekai/shared/README.md`'s row for `image.py` gains "and strips a photograph's metadata for upload".

## Dependencies

None.

## Risks / Trade-offs

- **A rare JPEG with an unknown marker is refused** → honest, and the remedy names the fix; hierarchical and
  arithmetic JPEGs are rare from cameras.
- **PyAV reads the minimal EXIF differently** → the PyAV check fails in the build, before anything ships.
- **A mirrored orientation still renders un-mirrored** → unchanged from today; the pod's loader rotates only.

## Verdict

**feasible** — a byte walk, a narrower seam and tests on real, decodable photographs.
