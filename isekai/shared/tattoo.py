"""The maths of an edit's request: the ink a composite holds, and the crop it samples.

A composite is the render with the tattoo multiplied on, so dividing it by the render
leaves the ink, and the ink's darkness says where the tattoo is. From it come the
mask the sampler repaints under, the control that holds the lines, and the box of the
render the pod is sent. The sampled crop is stitched back through the mask, and the
ink's lines are multiplied over it. Each is a function over arrays.

The division is defined on a Multiply composite over a lit pixel, so a composite that
is anything else is refused with the fix, rather than baked as the wrong ink.

Stdlib only at module scope: Pillow and numpy are imported inside the functions, so
`python -m isekai` loads no wheel.
"""

import io
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from isekai.foundation.refusal import Refusal

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    from PIL.Image import Image

# The mask level the crop box and the stitch treat as the tattoo's.
MASK_FLOOR = 8

# A side of the sampled crop is a multiple of this, which SDXL's VAE needs.
SIDE_MULTIPLE = 8

_NO_INK = (
    "the composite carries no ink: no pixel is darker than the render past the "
    "threshold; multiply the tattoo onto the render and export the composite again"
)


@dataclass(frozen=True)
class Derivation:
    """What a composite and its render give: the ink, its darkness, mask and control.

    `ink` is a float per channel in 0 to 1; `darkness`, `mask` and `control` are
    one channel, the last two as 8-bit levels.
    """

    ink: "NDArray[np.float32]"
    darkness: "NDArray[np.float32]"
    mask: "NDArray[np.uint8]"
    control: "NDArray[np.uint8]"


@dataclass(frozen=True)
class Crop:
    """The box of the render a sampling takes, and the size it is sampled at.

    `box` is left, top, right, bottom; `size` is width, height. `widened` and
    `grown` say whether the aspect guard or the upscale guard moved the box.
    """

    box: tuple[int, int, int, int]
    size: tuple[int, int]
    widened: bool
    grown: bool


def decode_render(body: bytes, name: str) -> "NDArray[np.uint8]":
    """Return the render in `body` as RGB levels, refusing bytes that are no image."""
    return _rgb(_decode(body, name, "render"))


def decode_composite(body: bytes) -> "NDArray[np.uint8]":
    """Return the composite in `body` as RGB levels.

    Refused, naming the fix, when it does not decode or any pixel is transparent.
    e.g. a PNG with one transparent pixel -> "the composite carries transparency; …"
    """
    import numpy as np

    image = _decode(body, "the composite", "composite")
    alpha = np.asarray(image.convert("RGBA"))[..., 3]
    if alpha.min() < 255:
        raise Refusal(
            "the composite carries transparency, which has no ink to divide out; "
            "flatten its layers onto the render and export the composite again"
        )
    return _rgb(image)


def _decode(body: bytes, name: str, what: str) -> "Image":
    """Return the decoded image in `body`, or refuse naming `name` and its fix."""
    from PIL import Image

    try:
        with Image.open(io.BytesIO(body)) as opened:
            opened.load()
            return opened.copy()
    except (OSError, Image.DecompressionBombError) as unreadable:
        raise Refusal(
            f"{name} cannot be read as an image ({unreadable}); "
            f"export the {what} as a PNG and give it again"
        ) from unreadable


def _rgb(image: "Image") -> "NDArray[np.uint8]":
    """Return `image` as an array of RGB levels, its colour profile left unapplied."""
    import numpy as np

    return np.asarray(image.convert("RGB"), dtype=np.uint8)


def ink_of(
    render: "NDArray[np.uint8]",
    composite: "NDArray[np.uint8]",
    dials: Mapping[str, Any],
) -> "NDArray[np.float32]":
    """Return the ink: the composite over the render per channel, 1 where unlit.

    A channel of the render at most `lit_floor` has no light to darken, so it reads
    no ink. Refused, naming the fix, when the sizes differ or a pixel is lighter
    than the render by more than `rounding` levels.
    e.g. render 200, composite 100 -> 0.5; render 4, composite 0 -> 1.0
    """
    import numpy as np

    if render.shape != composite.shape:
        raise Refusal(
            f"the composite is {composite.shape[1]}x{composite.shape[0]} and the "
            f"render is {render.shape[1]}x{render.shape[0]}; export the composite "
            "at the render's size, without scaling"
        )
    lighter = composite.astype(np.int16) - render.astype(np.int16) > dials["rounding"]
    if lighter.any():
        y, x = (int(at) for at in np.argwhere(lighter.any(axis=2))[0])
        raise Refusal(
            f"the composite is lighter than the render at ({x}, {y}), which no "
            "Multiply composite is; set the tattoo layer's blend mode to Multiply "
            "and export the composite again"
        )
    lit = render > dials["lit_floor"]
    ratio = composite.astype(np.float32) / np.maximum(render, 1).astype(np.float32)
    return np.where(lit, np.minimum(ratio, 1.0), 1.0).astype(np.float32)


def darkness_of(ink: "NDArray[np.float32]") -> "NDArray[np.float32]":
    """Return one minus the least channel of the ink, per pixel."""
    import numpy as np

    return (1.0 - ink.min(axis=2)).astype(np.float32)


def mask_of(
    darkness: "NDArray[np.float32]", dials: Mapping[str, Any]
) -> "NDArray[np.uint8]":
    """Return the mask: darkness past `ink_threshold`, grown, then feathered.

    The growth is `grow` pixels and the feather `feather`. White (255) is repainted,
    black kept; the feather leaves levels between.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    inked = (darkness > dials["ink_threshold"]).astype(np.uint8) * 255
    mask = Image.fromarray(inked)
    for _ in range(int(dials["grow"])):
        mask = mask.filter(ImageFilter.MaxFilter(3))
    if dials["feather"]:
        mask = mask.filter(ImageFilter.GaussianBlur(dials["feather"]))
    return np.asarray(mask, dtype=np.uint8)


def control_of(
    darkness: "NDArray[np.float32]", dials: Mapping[str, Any]
) -> "NDArray[np.uint8]":
    """Return the control: darkness times `control_gain`, clipped, white on black."""
    import numpy as np

    held = np.clip(darkness * dials["control_gain"], 0.0, 1.0)
    return (held * 255.0 + 0.5).astype(np.uint8)


def _extend(low: int, high: int, target: int, limit: int) -> tuple[int, int]:
    """Return `low..high` lengthened about its middle to `target`, inside `0..limit`.

    A span already `target` long, or longer, is returned as it is.
    e.g. (90, 110, 40, 200) -> (80, 120); (0, 20, 40, 200) -> (0, 40)
    """
    target = min(target, limit)
    if target <= high - low:
        return low, high
    start = low - (target - (high - low)) // 2
    start = min(max(start, 0), limit - target)
    return start, start + target


def _multiple(length: float) -> int:
    """Return `length` as the nearest multiple of `SIDE_MULTIPLE`, at least one."""
    return max(SIDE_MULTIPLE, round(length / SIDE_MULTIPLE) * SIDE_MULTIPLE)


def plan_crop(mask: "NDArray[np.uint8]", dials: Mapping[str, Any]) -> Crop:
    """Return the crop box of the mask's tattoo, and the size it is sampled at.

    The box is the mask's own (levels above `MASK_FLOOR`) plus `margin`, clipped to the
    image; widened to an aspect no thinner than `min_aspect`; then grown until the
    scale to `long_side` is at most `max_upscale`. The size is the box scaled to
    `long_side` on its long side, each side a multiple of 8. Refused, naming the fix,
    for a box the image cannot grow to that.
    e.g. a 40x40 tattoo in a 2000x2000 render -> a 304x304 box, sampled at 1216x1216
    """
    import numpy as np

    height, width = mask.shape
    rows = np.flatnonzero((mask > MASK_FLOOR).any(axis=1))
    columns = np.flatnonzero((mask > MASK_FLOOR).any(axis=0))
    if not rows.size:
        raise Refusal(_NO_INK)
    margin = int(dials["margin"])
    left, right = (
        max(int(columns[0]) - margin, 0),
        min(int(columns[-1]) + 1 + margin, width),
    )
    top, bottom = max(int(rows[0]) - margin, 0), min(int(rows[-1]) + 1 + margin, height)
    box = (left, top, right, bottom)

    long_side = int(dials["long_side"])
    thin = math.ceil(max(right - left, bottom - top) * dials["min_aspect"])
    if min(right - left, bottom - top) < thin:
        left, right = _extend(left, right, thin, width)
        top, bottom = _extend(top, bottom, thin, height)
    widened = (left, top, right, bottom) != box
    widened_box = (left, top, right, bottom)

    long = max(right - left, bottom - top)
    needed = math.ceil(long_side / dials["max_upscale"])
    if long < needed:
        scale = needed / long
        left, right = _extend(left, right, math.ceil((right - left) * scale), width)
        top, bottom = _extend(top, bottom, math.ceil((bottom - top) * scale), height)
        if max(right - left, bottom - top) < needed:
            raise Refusal(
                f"the tattoo's crop is {long} px on its long side and the "
                f"{width}x{height} render cannot grow it to the {needed} px that "
                f"keeps the sampling within {dials['max_upscale']}x; draw the "
                "tattoo larger, or make the edit on a larger render"
            )
    grown = (left, top, right, bottom) != widened_box

    scale = long_side / max(right - left, bottom - top)
    return Crop(
        box=(left, top, right, bottom),
        size=(_multiple((right - left) * scale), _multiple((bottom - top) * scale)),
        widened=widened,
        grown=grown,
    )


def _png(image: "Image") -> bytes:
    """Return `image` as a PNG that carries no profile and no metadata."""
    body = io.BytesIO()
    image.save(body, "PNG")
    return body.getvalue()


def sampling_images(
    composite: "NDArray[np.uint8]", derived: Derivation, crop: Crop
) -> tuple[bytes, bytes, bytes]:
    """Return the PNGs the pod is sent: the composite's crop, its mask and its control.

    Each is the box of the render scaled to the sampling size, so the pod sees the
    tattoo's crop and nothing of the rest of the image.
    e.g. a 304 px box sampled at 1216 -> three 1216x1216 PNGs
    """
    from PIL import Image

    left, top, right, bottom = crop.box

    def scaled(array: "NDArray[np.uint8]", resample: "Image.Resampling") -> bytes:
        box = Image.fromarray(array[top:bottom, left:right])
        return _png(box.resize(crop.size, resample))

    return (
        scaled(composite, Image.Resampling.LANCZOS),
        scaled(derived.mask, Image.Resampling.BILINEAR),
        scaled(derived.control, Image.Resampling.BILINEAR),
    )


def stitch(
    composite: "NDArray[np.uint8]",
    sampled: bytes,
    derived: Derivation,
    crop: Crop,
    lines: float,
) -> "NDArray[np.uint8]":
    """Return the composite with the sampled crop blended in and the lines multiplied.

    The crop is scaled to its box and blended over the composite by the mask; the
    result is multiplied by one minus `lines` times the ink's darkness. A mask of
    nothing leaves the composite, and `lines` of 0 multiplies nothing back.
    e.g. mask 255, lines 0.4, darkness 0.5 -> the sampled pixel times 0.8
    """
    import numpy as np
    from PIL import Image

    left, top, right, bottom = crop.box
    try:
        body = _decode(sampled, "the sampled crop", "sampled crop")
    except Refusal as unreadable:
        raise Refusal(
            "the endpoint's image for the sampled crop cannot be read; check the "
            "pod's ComfyUI log"
        ) from unreadable
    resized = body.convert("RGB").resize(
        (right - left, bottom - top), Image.Resampling.LANCZOS
    )
    weight = derived.mask[top:bottom, left:right].astype(np.float32) / 255.0
    weight = weight[..., np.newaxis]
    out = composite.astype(np.float32)
    out[top:bottom, left:right] = (
        out[top:bottom, left:right] * (1.0 - weight)
        + np.asarray(resized, dtype=np.float32) * weight
    )
    out *= (1.0 - lines * derived.darkness)[..., np.newaxis]
    return np.clip(out + 0.5, 0.0, 255.0).astype(np.uint8)


def derive(
    render: "NDArray[np.uint8]",
    composite: "NDArray[np.uint8]",
    dials: Mapping[str, Any],
) -> Derivation:
    """Return the ink, mask and control of `composite` over `render`, or refuse.

    Refused, naming the fix, for each case `ink_of` refuses and for a composite with
    no pixel darker than `ink_threshold`.
    """
    ink = ink_of(render, composite, dials)
    darkness = darkness_of(ink)
    if not (darkness > dials["ink_threshold"]).any():
        raise Refusal(_NO_INK)
    return Derivation(
        ink=ink,
        darkness=darkness,
        mask=mask_of(darkness, dials),
        control=control_of(darkness, dials),
    )
