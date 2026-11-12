"""A silhouette from one image embedding and a prompt of points: SAM 2.1 on the CPU.

The encoder runs once an image and the decoder once a bone. The mask is the candidate
the decoder scores highest, its logits resized to the image's size and taken above 0.
Both run through the declared `onnxruntime`, after their digests verify.

Stdlib only at module scope: `onnxruntime`, numpy and Pillow are imported inside the
functions that use them (D20), so `python -m isekai` loads no wheel.
"""

from collections.abc import Mapping, Sequence
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

ENCODER_DEST = "sam2/encoder.onnx"
DECODER_DEST = "sam2/decoder.onnx"

# The encoder's square input, and what its pixels, scaled to 0-1, are normalised by.
INPUT_SIZE = 1024
MEAN = (0.485, 0.456, 0.406)
DEVIATION = (0.229, 0.224, 0.225)

# The decoder's low-resolution mask, a side in pixels.
MASK_SIZE = 256

# The names the encoder answers, and the decoder's two answers.
FEATURES = ("image_embed", "high_res_feats_0", "high_res_feats_1")
ANSWERS = ("masks", "iou_predictions")

Size = tuple[int, int]


class _Named(Protocol):
    """A session's input, of which a feed needs the name."""

    name: str


class _Session(Protocol):
    """The part of an `onnxruntime` session the segmenter runs."""

    def get_inputs(self) -> Sequence[_Named]:
        """Return the session's inputs."""
        ...

    def run(
        self, outputs: Sequence[str], feed: Mapping[str, "NDArray[np.float32]"]
    ) -> Sequence["NDArray[np.float32]"]:
        """Return the named outputs, in order, for `feed`."""
        ...


class Runtime(Protocol):
    """The part of `onnxruntime` that opens a session. Faked by a recording runtime."""

    def InferenceSession(  # noqa: N802 - the runtime's own name
        self, path: str, providers: Sequence[str]
    ) -> _Session:
        """Return a session over the model at `path` on `providers`."""
        ...


def prepare(image: "Image") -> "NDArray[np.float32]":
    """Return `image` as the encoder reads it: (1, 3, INPUT_SIZE, INPUT_SIZE).

    The image is scaled to the square, bilinear, and each channel is normalised by the
    ImageNet mean and deviation. The array is RGB, channels first, with a batch axis.
    """
    import numpy as np
    from PIL import Image as Pillow

    square = image.convert("RGB").resize(
        (INPUT_SIZE, INPUT_SIZE), Pillow.Resampling.BILINEAR
    )
    pixels = (np.asarray(square, dtype=np.float32) / 255.0 - MEAN) / DEVIATION
    return pixels.transpose(2, 0, 1)[None].astype(np.float32)


class Embedding:
    """One image's features, kept to prompt a bone at a time without the encoder."""

    def __init__(
        self,
        decoder: _Session,
        features: Mapping[str, "NDArray[np.float32]"],
        size: Size,
    ) -> None:
        """Keep the decoder, the encoder's `features` and the image's `size`."""
        self._decoder = decoder
        self.features = features
        self.size = size

    def mask(
        self,
        positive: Sequence[tuple[float, float]],
        negative: Sequence[tuple[float, float]],
    ) -> "NDArray[np.bool_]":
        """Return the silhouette the points prompt, a boolean array of the image's size.

        Points are `(x, y)` in the image's pixels. The decoder's candidate with the
        highest predicted overlap is the mask; its logits are resized bilinear to the
        image's size, then taken above 0. A declared input with no value is refused.
        """
        import numpy as np
        from PIL import Image as Pillow

        width, height = self.size
        points = [*positive, *negative]
        known: dict[str, NDArray[np.float32]] = {
            **self.features,
            "point_coords": (
                np.array(points, dtype=np.float32)
                * np.array([INPUT_SIZE / width, INPUT_SIZE / height], dtype=np.float32)
            )[None],
            "point_labels": np.array(
                [[1.0] * len(positive) + [0.0] * len(negative)], dtype=np.float32
            ),
            "mask_input": np.zeros((1, 1, MASK_SIZE, MASK_SIZE), dtype=np.float32),
            "has_mask_input": np.zeros(1, dtype=np.float32),
        }
        feed: dict[str, NDArray[np.float32]] = {}
        for declared in self._decoder.get_inputs():
            if declared.name not in known:
                raise Refusal(
                    f"the segmenter's decoder declares the input {declared.name!r}, "
                    "which it has no value for"
                )
            feed[declared.name] = known[declared.name]
        candidates, scores = self._decoder.run(ANSWERS, feed)
        best = candidates[0, int(np.argmax(scores[0]))]
        logits = Pillow.fromarray(best.astype(np.float32), mode="F").resize(
            self.size, Pillow.Resampling.BILINEAR
        )
        return np.asarray(logits) > 0


class Segmenter(Protocol):
    """How an image gives silhouettes. Faked, so the suite needs no model."""

    def embed(self, image: "Image") -> Embedding:
        """Return `image`'s embedding, the encoder run once."""
        ...


class OnnxSegmenter:
    """The real segmenter: the encoder's and the decoder's sessions, on the CPU."""

    def __init__(self, encoder: Path, decoder: Path, runtime: Runtime) -> None:
        """Open both models on the CPU provider alone."""
        providers = ["CPUExecutionProvider"]
        self._encoder = runtime.InferenceSession(str(encoder), providers=providers)
        self._decoder = runtime.InferenceSession(str(decoder), providers=providers)

    def embed(self, image: "Image") -> Embedding:
        """Run the encoder once on `image` and keep its features and its size."""
        name = self._encoder.get_inputs()[0].name
        answered = self._encoder.run(FEATURES, {name: prepare(image)})
        return Embedding(
            self._decoder, dict(zip(FEATURES, answered, strict=True)), image.size
        )


def open_segmenter(
    models_dir: Path = DEFAULT_MODELS_DIR, runtime: Runtime | None = None
) -> OnnxSegmenter:
    """Verify both unpacked files, then open the segmenter over them on the CPU.

    The digests are checked before a session is made, so a stale pin costs a refusal
    and not a load. An absent file is a `Refusal` naming the fetch. `runtime` is
    `onnxruntime` unless a test gives its own.
    """
    manifest = provision.load_manifest(unpack.PLACEMENT_MANIFEST_PATH)
    resolved: list[Path] = []
    for dest in (ENCODER_DEST, DECODER_DEST):
        try:
            resolved.append(unpack.resolve_member(dest, models_dir, manifest))
        except FileNotFoundError as absent:
            raise Refusal(
                f"{dest} is not provisioned under {models_dir}/, and the segmenter "
                f"cannot run without it; run `{PLACEMENT_REMEDY}` from the "
                "repository root to fetch, unpack and verify it against its pinned "
                "manifest"
            ) from absent
    if runtime is None:
        silence_onnxruntime()
        try:
            runtime = cast(Runtime, import_module("onnxruntime"))
        except ModuleNotFoundError as absent:  # pragma: no cover - environment
            raise Refusal(
                "the segmenter's runtime is not installed (onnxruntime is missing); "
                "run `uv sync`"
            ) from absent
    return OnnxSegmenter(resolved[0], resolved[1], runtime)


__all__: Sequence[str] = (
    "DECODER_DEST",
    "ENCODER_DEST",
    "Embedding",
    "OnnxSegmenter",
    "Runtime",
    "Segmenter",
    "open_segmenter",
    "prepare",
)
