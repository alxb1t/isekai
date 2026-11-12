"""Place a tattoo's ink on a target image through thin-plate splines.

A stage is a `Spline` fitted backwards, from the target's pixels to the pixels of the
image before it, so each target pixel looks up the ink it shows and the warp leaves no
hole. `lookup` runs the stages and samples the ink; `clip` keeps it inside a limb
and out of the exclusions; `multiply` lays it over the render.

Images are float arrays in 0..1, `(height, width, channels)`; ink is RGBA. Stdlib
only at module scope: numpy and Pillow are imported inside the functions, so
`python -m isekai` loads no wheel.
"""

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from isekai.foundation.refusal import Refusal

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# The least pairs the thin-plate system solves: its affine part has three unknowns.
MIN_PAIRS = 3

# Points a spline maps at once, so a large grid never holds its whole kernel.
CHUNK = 16384

Points = Sequence[tuple[float, float]]


def _kernel(
    a: "NDArray[np.float64]", b: "NDArray[np.float64]"
) -> "NDArray[np.float64]":
    """Return the thin-plate kernel r² log r² between each point of `a` and of `b`."""
    import numpy as np

    dx = a[:, None, 0] - b[None, :, 0]
    dy = a[:, None, 1] - b[None, :, 1]
    r2 = dx * dx + dy * dy
    return np.where(r2 > 0, r2 * np.log(np.where(r2 > 0, r2, 1.0)), 0.0)


class Spline:
    """A 2-D thin-plate spline from `source` points to `target` points, exact at them.

    e.g. pairs that differ by (5, 0) throughout -> a point (7, 3) maps to (12, 3)
    """

    def __init__(
        self,
        source: "NDArray[np.float64] | Points",
        target: "NDArray[np.float64] | Points",
        smooth: float = 0.0,
    ) -> None:
        """Fit the spline to the pairs; `smooth` above 0 trades exactness for ease."""
        import numpy as np

        points = np.asarray(source, dtype=np.float64).reshape(-1, 2)
        mapped = np.asarray(target, dtype=np.float64).reshape(-1, 2)
        if len(points) != len(mapped):
            raise Refusal(
                f"{len(points)} source points and {len(mapped)} target points; "
                "give one target point for each source point"
            )
        if len(points) < MIN_PAIRS:
            raise Refusal(
                f"a spline needs at least {MIN_PAIRS} pairs, got {len(points)}; "
                "click more pairs"
            )
        if len(np.unique(points, axis=0)) != len(points):
            raise Refusal("two pairs share a source point; move one of them")
        if np.linalg.matrix_rank(points - points.mean(axis=0)) < 2:
            raise Refusal(
                f"a spline needs at least {MIN_PAIRS} pairs that do not lie on a "
                "line; the pairs lie on a line, so click one off it"
            )

        count = len(points)
        system = np.zeros((count + 3, count + 3))
        affine = np.hstack([np.ones((count, 1)), points])
        system[:count, :count] = _kernel(points, points) + smooth * np.eye(count)
        system[:count, count:] = affine
        system[count:, :count] = affine.T
        right = np.zeros((count + 3, 2))
        right[:count] = mapped
        self._source = points
        self._weights = np.linalg.solve(system, right)

    def __call__(self, points: "NDArray[np.float64]") -> "NDArray[np.float64]":
        """Return `points`, an (n, 2) array, as the target's (n, 2) array."""
        import numpy as np

        count = len(self._source)
        mapped = np.empty((len(points), 2), dtype=np.float64)
        for start in range(0, len(points), CHUNK):
            chunk = points[start : start + CHUNK]
            affine = np.hstack([np.ones((len(chunk), 1)), chunk])
            mapped[start : start + CHUNK] = (
                _kernel(chunk, self._source) @ self._weights[:count]
                + affine @ self._weights[count:]
            )
        return mapped


def _sample(
    image: "NDArray[np.float64]", xy: "NDArray[np.float64]"
) -> "NDArray[np.float64]":
    """Return the bilinear samples of `image` at float (x, y).

    Outside the image a sample is transparent white.
    """
    import numpy as np

    height, width = image.shape[:2]
    x, y = xy[:, 0], xy[:, 1]
    inside = (x >= 0) & (y >= 0) & (x <= width - 1) & (y <= height - 1)
    x0 = np.clip(np.floor(x).astype(int), 0, max(width - 2, 0))
    y0 = np.clip(np.floor(y).astype(int), 0, max(height - 2, 0))
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    top = image[y0, x0] * (1 - fx) + image[y0, x1] * fx
    bottom = image[y1, x0] * (1 - fx) + image[y1, x1] * fx
    values = top * (1 - fy) + bottom * fy
    values[~inside] = np.array([1.0, 1.0, 1.0, 0.0])[: image.shape[2]]
    return values


def lookup(
    ink: "NDArray[np.float64]", stages: Sequence[Spline], size: tuple[int, int]
) -> "NDArray[np.float64]":
    """Return the ink as it shows on a target of `size` (width, height).

    The target's pixel grid goes through each stage in turn, ending in the ink's
    pixels, where the ink is sampled; a pixel that lands outside the ink is
    transparent white.
    e.g. a stage shifting by (15, 10) -> target pixel (0, 0) shows ink pixel (15, 10)
    """
    import numpy as np

    width, height = size
    grid = np.stack(np.meshgrid(np.arange(width), np.arange(height)), axis=-1)
    points = grid.reshape(-1, 2).astype(np.float64)
    for stage in stages:
        points = stage(points)
    return _sample(ink, points).reshape(height, width, ink.shape[2])


def polygon_mask(points: Points, size: tuple[int, int]) -> "NDArray[np.uint8]":
    """Return the polygon of `points` filled into a (height, width) mask, 255 inside."""
    import numpy as np
    from PIL import Image, ImageDraw

    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([tuple(point) for point in points], fill=255)
    return np.asarray(mask)


def clip(
    ink: "NDArray[np.float64]", polygon: Points, exclusions: Sequence[Points] = ()
) -> "NDArray[np.float64]":
    """Return `ink` kept inside `polygon`, softened by a pixel, gone in `exclusions`."""
    import numpy as np
    from PIL import Image, ImageFilter

    height, width = ink.shape[:2]
    mask = Image.fromarray(polygon_mask(polygon, (width, height)))
    softened = np.asarray(mask.filter(ImageFilter.GaussianBlur(1)), dtype=np.float64)
    clipped = ink.copy()
    clipped[..., 3] *= softened / 255.0
    for exclusion in exclusions:
        clipped[polygon_mask(exclusion, (width, height)) > 0, 3] = 0.0
    return clipped


def multiply(
    render: "NDArray[np.float64]", layer: "NDArray[np.float64]"
) -> "NDArray[np.float64]":
    """Return the render darkened by the RGBA `layer` in Multiply mode."""
    alpha = layer[..., 3:]
    return render * (1.0 - alpha + alpha * layer[..., :3])


def crop_box(
    points: Points, margin: int, size: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Return the points' box grown by `margin`, clipped to `size`.

    The box is (left, top, right, bottom), its right and bottom edges exclusive.
    e.g. points (10.5, 20.2), (30.7, 40.9), margin 5, size (100, 100) -> (5, 15, 36, 46)
    """
    if not points:
        raise Refusal("a crop needs at least one point; give the outline's points")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    width, height = size
    return (
        max(0, math.floor(min(xs)) - margin),
        max(0, math.floor(min(ys)) - margin),
        min(width, math.floor(max(xs)) + 1 + margin),
        min(height, math.floor(max(ys)) + 1 + margin),
    )
