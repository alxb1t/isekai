"""A person's pose from one box and one crop: a detector, then an estimator.

The detector reads the image fitted into its square input, and its highest-scoring
person box is the one person. The estimator reads that box grown by a quarter, and a
keypoint is the highest value on each of its two axes, mapped back into the image.
Both run through the declared `onnxruntime` on the CPU, after their digests verify.

Stdlib only at module scope: `onnxruntime`, numpy and Pillow are imported inside the
functions that use them (D20), so `python -m isekai` loads no wheel.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from isekai.boundary import provision, unpack
from isekai.boundary.provision import DEFAULT_MODELS_DIR
from isekai.boundary.unpack import PLACEMENT_REMEDY
from isekai.boundary.wd14 import silence_onnxruntime
from isekai.foundation.refusal import Refusal

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    from PIL.Image import Image

DETECTOR_DEST = "dwpose/yolox_l.onnx"
ESTIMATOR_DEST = "dwpose/dw-ll_ucoco_384.onnx"

# The detector's square input, the grey its padding holds, and the strides its rows
# are laid out on, finest first.
DETECTOR_SIZE = 640
PAD = 114.0
STRIDES = (8, 16, 32)

# A detector row is a centre, a size, an objectness and the class scores; the person
# is the first class.
OBJECTNESS = 4
PERSON = 5

# The estimator's input, width then height, and what its input is normalised by.
ESTIMATOR_SIZE = (288, 384)
MEAN = (123.675, 116.28, 103.53)
DEVIATION = (58.395, 57.12, 57.375)

# The estimator's box is grown by this fraction of its size before it is cropped.
GROWTH = 1.25

# Each of its two answers has this many bins to a pixel of its input.
SPLIT_RATIO = 2.0

# The body's keypoints are the first of the estimator's, in COCO order.
BODY = 17

Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class Pose:
    """One person: the box found, the body's points and their scores, in COCO order.

    A point is `(x, y)` in the image's pixels; a score is the lower of its two peaks.
    """

    box: Box
    points: tuple[tuple[float, float], ...]
    scores: tuple[float, ...]


class PoseFinder(Protocol):
    """How an image gives a person's pose. Faked, so the suite needs no model."""

    def find(self, image: "Image") -> Pose | None:
        """Return the one person's pose in `image`, or None when no person is found."""
        ...


class _Named(Protocol):
    """A session's input, of which a feed needs the name."""

    name: str


class _Session(Protocol):
    """The part of an `onnxruntime` session the finder runs."""

    def get_inputs(self) -> Sequence[_Named]:
        """Return the session's inputs."""
        ...

    def run(
        self, outputs: None, feed: Mapping[str, "NDArray[np.float32]"]
    ) -> Sequence["NDArray[np.float32]"]:
        """Return the session's outputs for `feed`."""
        ...


class Runtime(Protocol):
    """The part of `onnxruntime` that opens a session. Faked by a recording runtime."""

    def InferenceSession(  # noqa: N802 - the runtime's own name
        self, path: str, providers: Sequence[str]
    ) -> _Session:
        """Return a session over the model at `path` on `providers`."""
        ...


def verified_paths(models_dir: Path = DEFAULT_MODELS_DIR) -> tuple[Path, Path]:
    """Return the detector's and the estimator's digest-verified paths.

    Both go through `provision.resolve`, so a stale pin is `DigestMismatch` naming the
    file and both digests, before any session over it opens. An absent file is a
    `Refusal` naming the fetch.
    """
    manifest = provision.load_manifest(unpack.PLACEMENT_MANIFEST_PATH)
    resolved: list[Path] = []
    for dest in (DETECTOR_DEST, ESTIMATOR_DEST):
        try:
            resolved.append(provision.resolve(dest, models_dir, manifest))
        except FileNotFoundError as absent:
            raise Refusal(
                f"{dest} is not provisioned under {models_dir}/, and the pose "
                f"cannot be read without it; run `{PLACEMENT_REMEDY}` from the "
                "repository root to fetch and verify it against its pinned manifest"
            ) from absent
    return resolved[0], resolved[1]


def fit(
    image: "Image", size: int = DETECTOR_SIZE
) -> tuple["NDArray[np.float32]", float]:
    """Return `image` fitted into a `size` square and the scale it was fitted by.

    The aspect is kept, the image sits in the top-left corner and the rest is `PAD`.
    The array is RGB, channels first, with a batch axis: (1, 3, size, size).
    """
    import numpy as np
    from PIL import Image as Pillow

    ratio = min(size / image.width, size / image.height)
    fitted = image.convert("RGB").resize(
        (max(1, round(image.width * ratio)), max(1, round(image.height * ratio))),
        Pillow.Resampling.BILINEAR,
    )
    canvas = np.full((size, size, 3), PAD, dtype=np.float32)
    canvas[: fitted.height, : fitted.width] = np.asarray(fitted, dtype=np.float32)
    return canvas.transpose(2, 0, 1)[None], ratio


def person_box(
    rows: "NDArray[np.float32]", ratio: float, size: int = DETECTOR_SIZE
) -> Box | None:
    """Return the highest-scoring person's box in the image's pixels, or None.

    `rows` are the detector's raw rows, one per cell of the grids on `STRIDES`. A
    row's centre is its cell plus its offset, and its size the exponent of its output,
    each times the stride. The person is the one row with the highest objectness times
    person score; no suppression is done. e.g. a row at cell (2, 1) on stride 8 with
    offsets 0.5 gives the centre (20, 12).
    """
    import numpy as np

    if len(rows) == 0:
        return None
    decoded = rows.astype(np.float32).copy()
    first = 0
    for stride in STRIDES:
        cells = size // stride
        across, down = np.meshgrid(np.arange(cells), np.arange(cells))
        grid = np.stack((across, down), axis=2).reshape(-1, 2)
        end = first + len(grid)
        decoded[first:end, :2] = (decoded[first:end, :2] + grid) * stride
        decoded[first:end, 2:4] = np.exp(decoded[first:end, 2:4]) * stride
        first = end
    best = int(np.argmax(decoded[:, OBJECTNESS] * decoded[:, PERSON]))
    centre_x, centre_y, width, height = (float(v) for v in decoded[best, :4])
    return (
        (centre_x - width / 2) / ratio,
        (centre_y - height / 2) / ratio,
        (centre_x + width / 2) / ratio,
        (centre_y + height / 2) / ratio,
    )


def crop_for(box: Box, size: tuple[int, int] = ESTIMATOR_SIZE) -> Box:
    """Return the region of the image the estimator reads for `box`.

    The box is grown by `GROWTH` about its centre, then widened or heightened to the
    aspect of `size`, width then height. e.g. (100, 100, 200, 300) at 288 by 384 gives
    (56.25, 75.0, 243.75, 325.0).
    """
    centre_x = (box[0] + box[2]) / 2
    centre_y = (box[1] + box[3]) / 2
    width = (box[2] - box[0]) * GROWTH
    height = (box[3] - box[1]) * GROWTH
    aspect = size[0] / size[1]
    if width > height * aspect:
        height = width / aspect
    else:
        width = height * aspect
    return (
        centre_x - width / 2,
        centre_y - height / 2,
        centre_x + width / 2,
        centre_y + height / 2,
    )


def crop_input(
    image: "Image", crop: Box, size: tuple[int, int] = ESTIMATOR_SIZE
) -> "NDArray[np.float32]":
    """Return `crop` of `image` scaled to `size` and normalised: (1, 3, height, width).

    Pixels the crop takes from outside the image are black, as the affine transform
    leaves them.
    """
    import numpy as np
    from PIL import Image as Pillow

    width, height = size
    left, top, right, bottom = crop
    moved = image.convert("RGB").transform(
        size,
        Pillow.Transform.AFFINE,
        ((right - left) / width, 0.0, left, 0.0, (bottom - top) / height, top),
        Pillow.Resampling.BILINEAR,
    )
    pixels = (np.asarray(moved, dtype=np.float32) - MEAN) / DEVIATION
    return pixels.transpose(2, 0, 1)[None].astype(np.float32)


def read_keypoints(
    across: "NDArray[np.float32]",
    down: "NDArray[np.float32]",
    crop: Box,
    size: tuple[int, int] = ESTIMATOR_SIZE,
) -> tuple[tuple[tuple[float, float], ...], tuple[float, ...]]:
    """Return the body's points in the image's pixels and their scores.

    `across` and `down` are the estimator's two answers, a row of bins to a keypoint.
    A keypoint sits at the highest bin of each, divided by `SPLIT_RATIO` and mapped
    back through `crop`; its score is the lower of the two highest values.
    """
    import numpy as np

    left, top, right, bottom = crop
    x_bins = np.argmax(across[:BODY], axis=1) / SPLIT_RATIO
    y_bins = np.argmax(down[:BODY], axis=1) / SPLIT_RATIO
    scores = np.minimum(across[:BODY].max(axis=1), down[:BODY].max(axis=1))
    xs = left + x_bins / size[0] * (right - left)
    ys = top + y_bins / size[1] * (bottom - top)
    points = tuple((float(x), float(y)) for x, y in zip(xs, ys, strict=True))
    return points, tuple(float(score) for score in scores)


class OnnxPoseFinder:
    """The real finder: the detector's and the estimator's sessions, on the CPU."""

    def __init__(self, detector: Path, estimator: Path, runtime: Runtime) -> None:
        """Open both models on the CPU provider alone."""
        providers = ["CPUExecutionProvider"]
        self._detector = runtime.InferenceSession(str(detector), providers=providers)
        self._estimator = runtime.InferenceSession(str(estimator), providers=providers)

    def find(self, image: "Image") -> Pose | None:
        """Return the one person's pose in `image`, or None when no row is answered."""
        fitted, ratio = fit(image)
        rows = self._detector.run(None, {self._detector.get_inputs()[0].name: fitted})
        box = person_box(rows[0][0], ratio)
        if box is None:
            return None
        crop = crop_for(box)
        answers = self._estimator.run(
            None,
            {self._estimator.get_inputs()[0].name: crop_input(image, crop)},
        )
        points, scores = read_keypoints(answers[0][0], answers[1][0], crop)
        return Pose(box=box, points=points, scores=scores)


def open_pose(
    models_dir: Path = DEFAULT_MODELS_DIR, runtime: Runtime | None = None
) -> OnnxPoseFinder:
    """Verify both files, then open the finder over them on the CPU.

    The digests are checked before a session is made, so a stale pin costs a refusal
    and not a load. `runtime` is `onnxruntime` unless a test gives its own.
    """
    detector, estimator = verified_paths(models_dir)
    if runtime is None:
        silence_onnxruntime()
        try:
            runtime = cast(Runtime, import_module("onnxruntime"))
        except ModuleNotFoundError as absent:  # pragma: no cover - environment
            raise Refusal(
                "the pose finder's runtime is not installed (onnxruntime is missing); "
                "run `uv sync`"
            ) from absent
    return OnnxPoseFinder(detector, estimator, runtime)


__all__: Sequence[str] = (
    "DETECTOR_DEST",
    "ESTIMATOR_DEST",
    "OnnxPoseFinder",
    "Pose",
    "PoseFinder",
    "Runtime",
    "crop_for",
    "crop_input",
    "fit",
    "open_pose",
    "person_box",
    "read_keypoints",
    "verified_paths",
)
