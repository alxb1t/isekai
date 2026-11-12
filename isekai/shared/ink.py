"""Cut a tattoo's ink from a photograph or an image into a Multiply layer.

The ink is what darkens the skin, so the layer is the image divided by the skin
under it: white where there is no ink, the ink's colour where there is. Laid over
a render in Multiply mode it darkens the render as the ink darkened the original,
on any skin tone and in any light.

The skin under the ink is estimated: a max filter wider than the broadest fill
lifts each pixel to the brightest skin near it, and a blur smooths that into the
arm's lighting. Dividing by it flattens the lighting, so the arm's shading does
not travel into the render.

`config/ink.json` holds the numbers. Stdlib only at module scope: Pillow and
numpy are imported inside the functions, so `python -m isekai` loads no wheel.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.refusal import Refusal
from isekai.shared.tattoo import png_of

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    from PIL.Image import Image

INK_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "ink.json"

KEYS = (
    "reach",
    "white",
    "floor",
    "photo_depth",
    "image_depth",
    "depth_min",
    "depth_max",
)

# Rec. 601 luma: the weights of the neutral layer's one grey.
_LUMA = (0.299, 0.587, 0.114)

# Envelope brightness below which a pixel is clothing or shadow, not skin or wall.
_BRIGHT_ENVELOPE = 0.45

# The least the mean of the white point's channels may read, as a share of the skin
# around it. Below it the sample is ink, the outline holds no bare skin, and dividing
# by it erases ink. It is the whole check where no lit ring lies outside the outline.
_MIN_SKIN = 0.7

# How far any one channel of the white point may read below the same channel of the
# skin just outside the outline, as a share of that skin. Past it the sample is ink,
# not skin: a fill short in one channel alone still fills a tight outline and would be
# erased, though the mean of its channels sits close to the skin's.
_SKIN_GAP = 0.05


@dataclass(frozen=True)
class InkConfig:
    """The extraction's numbers: its reach and white point, and the depths it takes."""

    reach: int
    white: float
    floor: float
    photo_depth: float
    image_depth: float
    depth_min: float
    depth_max: float


def _number(path: Path, document: Mapping[str, object], key: str) -> float:
    """Return `key` of `document` as a number, refusing anything else naming the key."""
    value = document[key]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise Refusal(
            f"{path.name}: `{key}` declares {value!r}; it is a number, so write one"
        )
    return float(value)


def load_ink_config(path: Path = INK_CONFIG_PATH) -> InkConfig:
    """Return the ink config, refusing naming the key or the file that is wrong."""
    document: Any = json.loads(path.read_text())
    unknown = sorted(key for key in document if key not in KEYS)
    if unknown:
        raise Refusal(
            f"{path.name} declares {', '.join(unknown)}, which this build does not "
            f"read; the keys it reads are {', '.join(KEYS)} -- correct the spelling"
        )
    missing = [key for key in KEYS if key not in document]
    if missing:
        raise Refusal(
            f"{path.name} declares no {', '.join(missing)}; add the key to {path.name}"
        )
    numbers = {key: _number(path, document, key) for key in KEYS}
    if numbers["reach"] < 1 or numbers["reach"] != int(numbers["reach"]):
        raise Refusal(f"{path.name}: `reach` is a whole number of pixels, at least 1")
    if not 0 < numbers["white"] <= 100:
        raise Refusal(f"{path.name}: `white` is a percentile above 0, at most 100")
    if not 0 <= numbers["floor"] < 1:
        raise Refusal(f"{path.name}: `floor` is at least 0 and below 1")
    low, high = numbers["depth_min"], numbers["depth_max"]
    for key in ("photo_depth", "image_depth"):
        if not low <= numbers[key] <= high:
            raise Refusal(
                f"{path.name}: `{key}` is {numbers[key]}, outside `depth_min` "
                f"{low} to `depth_max` {high}; keep each default in the range"
            )
    return InkConfig(
        reach=int(numbers["reach"]),
        white=numbers["white"],
        floor=numbers["floor"],
        photo_depth=numbers["photo_depth"],
        image_depth=numbers["image_depth"],
        depth_min=low,
        depth_max=high,
    )


def _flattened(image: "Image") -> "Image":
    """Return `image` as opaque RGB, its transparency laid over white.

    White is Multiply's neutral, so a transparent pixel is bare skin whatever colour
    it stores, and only what the image shows is read as ink.
    """
    from PIL import Image

    rgba = image.convert("RGBA")
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, rgba).convert("RGB")


def _skin_envelope(rgb: "Image", reach: int) -> "NDArray[np.float32]":
    """Return each pixel's nearby bare-skin colour, as floats in 0..1."""
    import numpy as np
    from PIL import Image, ImageFilter

    factor = max(1, reach // 16)
    small = rgb.resize(
        (max(1, rgb.width // factor), max(1, rgb.height // factor)),
        Image.Resampling.BOX,
    )
    size = max(3, (reach // factor) | 1)
    lifted = small.filter(ImageFilter.MaxFilter(size))
    lifted = lifted.filter(ImageFilter.GaussianBlur(size / 2))
    envelope = lifted.resize(rgb.size, Image.Resampling.BICUBIC)
    return np.asarray(envelope, dtype=np.float32) / 255.0


def _skin_beside(
    alpha: "Image",
    envelope: "NDArray[np.float32]",
    transmittance: "NDArray[np.float32]",
    config: InkConfig,
) -> "NDArray[np.float32] | None":
    """Return the white point's channels in a ring of lit pixels just outside `alpha`.

    The ring is the bare skin the outline stands in; None when the outline has none
    beside it (it covers the image, or the ring is dark), so nothing is compared.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    factor = max(1, config.reach // 16)
    inside = alpha.point(lambda value: 255 if value > 127 else 0)
    small = inside.resize(
        (max(1, inside.width // factor), max(1, inside.height // factor)),
        Image.Resampling.BOX,
    )
    grown = small.filter(ImageFilter.MaxFilter(max(3, (config.reach // factor) | 1)))
    reached = np.asarray(grown.resize(inside.size, Image.Resampling.NEAREST)) > 0
    ring = (
        reached & ~(np.asarray(inside) > 0) & (envelope.mean(axis=2) > _BRIGHT_ENVELOPE)
    )
    if not ring.any():
        return None
    return np.percentile(transmittance[ring], config.white, axis=0)


def _automatic_point(
    image: "Image", outline: "Image | None", config: InkConfig
) -> "tuple[NDArray[np.float32], Image, NDArray[np.float32]]":
    """Return the transmittance, the outline's alpha and the automatic white point.

    The point is the skin's transmittance per channel, read at the config's percentile
    inside the outline; a point that reads ink, not skin, is refused.
    """
    import numpy as np
    from PIL import Image

    rgb = _flattened(image)
    pixels = np.asarray(rgb, dtype=np.float32) / 255.0
    envelope = _skin_envelope(rgb, config.reach)
    transmittance = np.clip(pixels / np.maximum(envelope, 1e-3), 0.0, 1.0)

    if outline is not None:
        alpha = outline.convert("L").resize(rgb.size, Image.Resampling.BILINEAR)
    else:
        alpha = Image.new("L", rgb.size, 255)

    kept = (np.asarray(alpha) > 127) & (envelope.mean(axis=2) > _BRIGHT_ENVELOPE)
    if not kept.any():
        raise Refusal(
            "no bare skin to read the ink against: the outline is empty or the image "
            "is dark; widen the outline over the skin, or light the photograph"
        )
    skin = np.percentile(transmittance[kept], config.white, axis=0)
    beside = _skin_beside(alpha, envelope, transmittance, config)
    if skin.mean() < _MIN_SKIN or (
        beside is not None and (skin < beside - _SKIN_GAP).any()
    ):
        raise Refusal(
            "no bare skin inside the outline to read the ink against: its pixels "
            "are all darker than the skin around them, so the ink would be taken "
            "for skin and washed out; widen the outline over the skin"
        )
    return transmittance, alpha, skin


def extract_ink(
    image: "Image",
    outline: "Image | None",
    neutral: bool | None,
    depth: float | None,
    config: InkConfig | None = None,
    *,
    white: float = 1.0,
) -> "Image":
    """Return the Multiply layer of `image`: bare skin white, the ink its colour.

    With an outline the layer keeps the ink inside it, as its alpha, neutral and at
    `photo_depth`; without one it keeps the whole image, in colour at `image_depth`.
    A `neutral` or a `depth` that is not None overrides its default, and `white` scales
    the automatic white point: below 1.0 the paler ink turns white.
    e.g. a photograph and its outline, no flags -> grey ink at depth 1.6
    """
    return extract_ink_grey(image, outline, neutral, depth, config, white=white)[0]


def extract_ink_grey(
    image: "Image",
    outline: "Image | None",
    neutral: bool | None,
    depth: float | None,
    config: InkConfig | None = None,
    *,
    white: float = 1.0,
) -> "tuple[Image, int]":
    """Return `extract_ink`'s layer and `white_grey`'s grey, the skin read once.

    e.g. a photograph and its outline, no flags -> the grey layer and 204
    """
    import numpy as np
    from PIL import Image

    config = config or load_ink_config()
    outlined = outline is not None
    neutral = outlined if neutral is None else neutral
    if depth is None:
        depth = config.photo_depth if outlined else config.image_depth
    if not config.depth_min <= depth <= config.depth_max:
        raise Refusal(
            f"depth {depth} is outside {config.depth_min} to {config.depth_max}; "
            "give a depth in that range"
        )
    if white <= 0:
        raise Refusal(f"white scale {white} is not above 0; give a scale above 0")

    transmittance, alpha, skin = _automatic_point(image, outline, config)
    grey = _grey(skin)
    skin = skin * white
    transmittance = np.clip(transmittance / np.maximum(skin, 1e-3), 0.0, 1.0)
    transmittance = np.clip(transmittance / (1.0 - config.floor), 0.0, 1.0)
    if neutral:
        luminance = transmittance @ np.array(_LUMA, dtype=np.float32)
        transmittance = np.repeat(luminance[..., None], 3, axis=2)
    transmittance = transmittance**depth

    layer = Image.fromarray((transmittance * 255.0 + 0.5).astype(np.uint8))
    layer.putalpha(alpha)
    return layer, grey


def _grey(skin: "NDArray[np.float32]") -> int:
    """Return the point `skin`'s luminance as a whole number, 0 to 255.

    e.g. a point that reads 0.8 at every channel -> 204
    """
    import numpy as np

    luminance = float(skin @ np.array(_LUMA, dtype=np.float32))
    return min(255, max(0, round(luminance * 255.0)))


def white_grey(
    image: "Image", outline: "Image | None", config: InkConfig | None = None
) -> int:
    """Return the automatic white point's luminance as a whole number, 0 to 255.

    The weights are the neutral layer's, so the grey is the one the layer divides by.
    e.g. skin that reads 0.8 of its lit neighbours at every channel -> 204
    """
    _, _, skin = _automatic_point(image, outline, config or load_ink_config())
    return _grey(skin)


def _open(path: Path) -> "Image":
    """Return the image at `path` turned as its orientation says, decoded."""
    from PIL import Image, ImageOps

    try:
        with Image.open(path) as opened:
            return ImageOps.exif_transpose(opened)
    except (OSError, Image.DecompressionBombError) as unreadable:
        raise Refusal(
            f"{path.name}: cannot be read as an image ({unreadable}); "
            "re-export it as a PNG or JPEG"
        ) from unreadable


def cut_ink(
    image: Path,
    out: Path,
    outline: Path | None,
    neutral: bool | None,
    depth: float | None,
) -> None:
    """Write the Multiply layer of the image at `image` to `out`, as a PNG.

    The file is written whole or not at all.
    """
    layer = extract_ink(
        _open(image), _open(outline) if outline else None, neutral, depth
    )
    write_atomically(out, png_of(layer))
