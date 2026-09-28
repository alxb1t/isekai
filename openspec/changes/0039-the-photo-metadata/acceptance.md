# Acceptance — 0039 the photo metadata

The PyAV check [D6](design.md#d6) names: an original and a stripped JPEG and PNG, each with orientation 6, decoded
by PyAV and compared array for array and rotation for rotation.

## How it ran

`uv run --offline --with av==14.4.0` could not resolve: this uv (0.12.19) reads the `wheels-v6` cache, and the
`av 14.4.0` wheel is cached only in the older layout. The same wheel, unpacked in uv's `archive-v0` cache
(`av-14.4.0.dist-info`, tag `cp312-cp312-macosx_12_0_arm64`), was put on the path instead — offline, and declaring
nothing:

```
PYTHONPATH="$(uv cache dir)/archive-v0/<the av-14.4.0 entry>" uv run --offline python pyav_check.py
```

## The script

```python
"""Decode an original and a stripped photograph with PyAV; compare arrays and rotation."""

import io
import sys
import tempfile
from pathlib import Path

import av
import numpy
from PIL import Image

sys.path.insert(0, ".")
from isekai.shared.image import strip_metadata  # noqa: E402


def photo(kind: str) -> bytes:
    ramp = Image.linear_gradient("L").resize((48, 32))
    image = Image.merge("RGB", (ramp, ramp.transpose(Image.Transpose.ROTATE_180), ramp))
    exif = Image.Exif()
    exif[0x0112] = 6
    exif[0x010F] = "a camera"
    out = io.BytesIO()
    if kind == "PNG":
        image.save(out, "PNG", exif=exif)
    else:
        image.save(out, "JPEG", exif=exif, comment=b"a comment")
    return out.getvalue()


def decode(path: Path) -> tuple[numpy.ndarray, float]:
    with av.open(str(path)) as container:
        frame = next(container.decode(video=0))
        return frame.to_ndarray(format="rgb24"), frame.rotation


print(f"av {av.__version__}, libavcodec {av.library_versions['libavcodec']}")
with tempfile.TemporaryDirectory() as scratch:
    for kind, suffix in (("JPEG", ".jpg"), ("PNG", ".png")):
        original = Path(scratch) / f"original{suffix}"
        original.write_bytes(photo(kind))
        stripped = Path(scratch) / f"stripped{suffix}"
        stripped.write_bytes(strip_metadata(original))
        (a, a_rot), (b, b_rot) = decode(original), decode(stripped)
        print(
            f"{kind}: {original.stat().st_size} -> {stripped.stat().st_size} bytes; "
            f"shape {a.shape} vs {b.shape}; rotation {a_rot} vs {b_rot}"
        )
        print(f"identical: {kind} {numpy.array_equal(a, b) and a_rot == b_rot}")
```

## Output

```
av 14.4.0, libavcodec (61, 19, 101)
JPEG: 800 -> 765 bytes; shape (32, 48, 3) vs (32, 48, 3); rotation -90 vs -90
identical: JPEG True
PNG: 204 -> 182 bytes; shape (32, 48, 3) vs (32, 48, 3); rotation 0 vs 0
identical: PNG True
```

## What it shows

- **Both decode to identical arrays**, so the strip changes no pixel PyAV sees.
- **JPEG:** PyAV reads the orientation from the minimal EXIF as it reads it from the camera's: a display matrix of
  -90 on both.
- **PNG:** PyAV reports rotation 0 for the original and the stripped file alike — it surfaces no display matrix
  from a PNG's `eXIf`. The rotation comparison is equal but says nothing about PNG orientation; the tests in
  `tests/test_image.py` hold that, and the pod image version's render holds it end to end.
