"""The real models behind `isekai.evaluate`'s seams.

**This is the only module in the tree that imports the `[eval]` extra**, and it
is imported lazily, from `evaluate.py`'s `main` and nowhere else. Everything the
scorer actually *decides* lives in `isekai.evaluate`, which is stdlib-only and is
therefore tested in CI with this stack absent -- the same division `ComfyTransport`
and `FakeComfyClient` are under.

`ultralytics` is not imported here and is not in the extra. The anime-face
detector's weights are loaded through `onnxruntime`, which is MIT: loading weights
is not linking code, and that is what keeps an AGPL-3.0 detector out of an
Apache-2.0 public repository (design.md D19, `scripts/eval_licences.md`). A test
asserts the absence, because a licence review nobody runs is not a control.

Every artifact is resolved through `isekai.eval_models.resolve`, which verifies
its digest against `scripts/eval_models.json` and refuses on a mismatch. A score
produced by an unverified model is a number from an unknown thing.

**On the `ty: ignore[unresolved-import]` markers below.** The gate runs with the
extra deliberately absent, so the type checker cannot resolve these five modules
-- not because they are missing but because they are *supposed* to be. Each
import is marked on its own line, at the boundary, and nowhere else; every other
diagnostic in this file is still enforced, which is why the `_srgb_to_lab` call
below unpacks its triple explicitly rather than passing a `tuple[float, ...]`.
Whoever installs the extra can run `uv run --extra eval ty check` and get the
resolution these markers stand in for.
"""

from pathlib import Path
from typing import Any

from isekai.ciede2000 import Lab
from isekai.eval_models import RECOGNIZER, resolve
from isekai.evaluate import Box, Canvas, FaceReading, Keypoint, Refusal, Region

# The SegFormer clothes parser's label ids. Only the ones this version measures
# are named; the rest are parsed and ignored rather than deleted, because the
# model emits them either way and naming them is what makes "hair" a choice.
SEGFORMER_HAIR = 2

# `face_detect_v1.4_s` emits one class. Read from the pinned `labels.json` rather
# than assumed, so a repointed manifest cannot silently change what is detected.
ANIMEFACE_CONFIDENCE = 0.25


def _numpy() -> Any:
    """Import numpy on demand, with a message that names the extra."""
    try:
        import numpy  # ty: ignore[unresolved-import]
    except ModuleNotFoundError as absent:  # pragma: no cover - environment
        raise Refusal(
            "the evaluator's stack is not installed; run "
            "`uv sync --extra eval`. It is deliberately not in CI."
        ) from absent
    return numpy


def _pil() -> Any:
    """Import Pillow on demand."""
    try:
        from PIL import Image, ImageOps  # ty: ignore[unresolved-import]
    except ModuleNotFoundError as absent:  # pragma: no cover - environment
        raise Refusal(
            "the evaluator's stack is not installed; run `uv sync --extra eval`."
        ) from absent
    return Image, ImageOps


def load_canvas_pixels(image_path: str, canvas: Canvas) -> Any:
    """Return an image as an RGB array on the canvas, orientation already applied.

    **The transpose happens here and before anything else reads a pixel.**
    `image_dimensions` returns dimensions rather than pixels, and ComfyUI's
    `LoadImage` transposes both JPEG and PNG for a rotating EXIF tag -- measured
    on the pinned build (`probe/README.md`). A photograph parsed upright while the
    render was produced from transposed pixels would place every region in the
    wrong place, silently, with every number still looking plausible.
    """
    image_module, ops = _pil()
    numpy = _numpy()
    with image_module.open(image_path) as handle:
        upright = ops.exif_transpose(handle).convert("RGB")
        if upright.size != canvas.size:
            upright = upright.resize(canvas.size, image_module.LANCZOS)
        return numpy.asarray(upright)


def _srgb_to_lab(rgb: tuple[float, float, float]) -> Lab:
    """Convert an 8-bit sRGB triple to CIE L*a*b* under D65.

    Spelled out rather than pulled in, for the reason `ciede2000.py` is: this is
    two published closed-form transforms, and `scikit-image` would bring scipy,
    networkx and imageio into the lock to supply them.
    """

    def linear(channel: float) -> float:
        c = channel / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(v) for v in rgb)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


class OnnxSession:
    """One pinned ONNX artifact, verified and loaded."""

    def __init__(self, dest: str, models_dir: Path) -> None:
        """Verify the pinned artifact's digest, then load it onto the CPU."""
        try:
            import onnxruntime  # ty: ignore[unresolved-import]
        except ModuleNotFoundError as absent:  # pragma: no cover - environment
            raise Refusal(
                "the evaluator's stack is not installed; run `uv sync --extra eval`."
            ) from absent
        # Verified before it is loaded, never after: the digest is the only
        # reason to believe these are the bytes the manifest names.
        path = resolve(dest, models_dir)
        self.session = onnxruntime.InferenceSession(
            str(path), providers=["CPUExecutionProvider"]
        )

    def run(self, feed: dict[str, Any]) -> list[Any]:
        """Run the session on one prepared feed."""
        return self.session.run(None, feed)


class AnimeFaceDetector:
    """The guard's box method: `deepghs/anime_face_detection`, through onnxruntime.

    MIT, and an ONNX export, which is why it is here rather than the detector
    design.md D19 originally named -- that one publishes no ONNX at all and
    declares `library_name: ultralytics`. See `scripts/eval_licences.md`.
    """

    def __init__(self, models_dir: Path, canvas: Canvas) -> None:
        """Load the pinned detector, bound to the canvas it will read at."""
        self.session = OnnxSession("anime_face_detection/model.onnx", models_dir)
        self.canvas = canvas
        self.models_dir = models_dir

    def read_face(self, image_path: str) -> FaceReading:
        """Return the highest-confidence face box, or absence."""
        numpy = _numpy()
        pixels = load_canvas_pixels(image_path, self.canvas)
        # YOLOv8's ONNX graph takes NCHW float32 in [0, 1] at a fixed side.
        side = 640
        image_module, _ = _pil()
        resized = numpy.asarray(
            image_module.fromarray(pixels).resize((side, side), image_module.BILINEAR),
            dtype="float32",
        )
        feed = {
            self.session.session.get_inputs()[0].name: numpy.ascontiguousarray(
                resized.transpose(2, 0, 1)[None] / 255.0
            )
        }
        raw = self.session.run(feed)[0]
        # (1, 4 + classes, anchors) -> (anchors, 4 + classes)
        predictions = numpy.squeeze(raw, 0).T
        scores = predictions[:, 4]
        best = int(numpy.argmax(scores))
        if float(scores[best]) < ANIMEFACE_CONFIDENCE:
            return FaceReading(box=None)
        cx, cy, w, h = (float(v) for v in predictions[best, :4])
        sx = self.canvas.width / side
        sy = self.canvas.height / side
        box: Box = (
            (cx - w / 2) * sx,
            (cy - h / 2) * sy,
            (cx + w / 2) * sx,
            (cy + h / 2) * sy,
        )
        return FaceReading(box=box, landmarks=((cx * sx, cy * sy),))


class SegformerParser:
    """The region parser: `segformer_b2_clothes`, on the photograph only.

    Never handed a render. A human parser is trained on photographs and its
    behaviour on a drawing is unknown, so parsing both sides would make every
    axis a comparison of two parsers as much as of two images (design.md D7).
    """

    def __init__(self, models_dir: Path) -> None:
        """Load the pinned region parser."""
        self.session = OnnxSession("segformer_b2_clothes/model.onnx", models_dir)

    def parse(self, image_path: str, canvas: Canvas) -> dict[str, Region]:
        """Return the photograph's regions, keyed by name."""
        pixels = load_canvas_pixels(image_path, canvas)
        mask = self._segment(pixels, canvas)
        hair = mask == SEGFORMER_HAIR
        area = float(hair.mean())
        return {
            "hair": Region(
                name="hair",
                area=area,
                colour=_dominant_lab(pixels, hair) or (0.0, 0.0, 0.0),
            )
        }

    def _segment(self, pixels: Any, canvas: Canvas) -> Any:
        """Return a per-pixel class map at the canvas's own size."""
        numpy = _numpy()
        image_module, _ = _pil()
        side = 512
        resized = numpy.asarray(
            image_module.fromarray(pixels).resize((side, side), image_module.BILINEAR),
            dtype="float32",
        )
        # The pinned `preprocessor_config.json`'s ImageNet normalisation.
        mean = numpy.array([0.485, 0.456, 0.406], dtype="float32")
        std = numpy.array([0.229, 0.224, 0.225], dtype="float32")
        normalised = ((resized / 255.0) - mean) / std
        feed = {
            self.session.session.get_inputs()[0].name: numpy.ascontiguousarray(
                normalised.transpose(2, 0, 1)[None]
            )
        }
        logits = self.session.run(feed)[0]
        classes = numpy.argmax(logits[0], axis=0).astype("uint8")
        return numpy.asarray(
            image_module.fromarray(classes).resize(canvas.size, image_module.NEAREST)
        )


def _dominant_lab(pixels: Any, mask: Any) -> Lab | None:
    """Return the dominant CIE L*a*b* colour under a mask, or None if it is empty.

    The *mode* of a coarse RGB histogram rather than the mean, because a mean of
    a dark base and a bright underlayer is a colour that appears nowhere in the
    image. The limitation this leaves is stated in `ciede2000.py` and in
    design.md D5, and is not fixed here: a render that dropped the underlayer
    entirely scores unchanged if the mode did not move.
    """
    numpy = _numpy()
    selected = pixels[mask]
    if selected.size == 0:
        return None
    # 32 levels per channel: coarse enough that near-identical pixels land in one
    # bin, fine enough that a base colour and an underlayer do not.
    quantised = (selected // 8).astype("int32")
    keys = quantised[:, 0] * 1024 + quantised[:, 1] * 32 + quantised[:, 2]
    values, counts = numpy.unique(keys, return_counts=True)
    winner = values[int(numpy.argmax(counts))]
    red, green, blue = (float(v) for v in selected[keys == winner].mean(axis=0))
    return _srgb_to_lab((red, green, blue))


class MaskSampler:
    """Reads a colour out of a mask that was derived from the photograph.

    Re-parses the photograph to recover the mask rather than carrying pixels
    across the seam, so the render is still never handed to a parser.
    """

    def __init__(
        self, parser: SegformerParser, photo_path: str, canvas: Canvas
    ) -> None:
        """Derive the photograph's mask once, so the render is never parsed."""
        self.parser = parser
        self.canvas = canvas
        pixels = load_canvas_pixels(photo_path, canvas)
        self.mask = self.parser._segment(pixels, canvas) == SEGFORMER_HAIR

    def dominant_colour(self, image_path: str, region: Region) -> Lab | None:
        """Return the render's dominant colour inside the photograph's own mask."""
        return _dominant_lab(load_canvas_pixels(image_path, self.canvas), self.mask)


class StyleIdEncoder:
    """The primary face axis: StyleID, a CLIP image encoder with LoRA merged.

    Non-commercial research use, a recorded deviation, and the reason the rule
    "a model whose licence is restrictive may not be the sole carrier of an axis"
    matters: it ships beside ArcFace or not at all.

    It is the thing being calibrated, not the thing calibrating. Its training
    pairs were stylized with InstantID and IP-Adapter -- this exact generator
    family -- which is why the operator's eye is the reference (design.md D8, D10).
    """

    def __init__(self, models_dir: Path, canvas: Canvas) -> None:
        """Verify every pinned StyleID artifact, then load the encoder."""
        try:
            import torch  # ty: ignore[unresolved-import]
            from transformers import (  # ty: ignore[unresolved-import]
                CLIPImageProcessor,
                CLIPModel,
            )
        except ModuleNotFoundError as absent:  # pragma: no cover - environment
            raise Refusal(
                "the evaluator's stack is not installed; run `uv sync --extra eval`."
            ) from absent
        for dest in (
            "styleid/model.safetensors",
            "styleid/config.json",
            "styleid/preprocessor_config.json",
        ):
            resolve(dest, models_dir)
        root = models_dir / "styleid"
        self.torch = torch
        self.model = CLIPModel.from_pretrained(root).eval()
        self.processor = CLIPImageProcessor.from_pretrained(root)
        self.canvas = canvas

    def embed(self, image_path: str, box: Box) -> tuple[float, ...] | None:
        """Return the unit-normalised embedding of the face crop, or None."""
        image_module, _ = _pil()
        pixels = load_canvas_pixels(image_path, self.canvas)
        crop = image_module.fromarray(pixels).crop(tuple(int(v) for v in box))
        if crop.width < 2 or crop.height < 2:
            return None
        inputs = self.processor(images=crop, return_tensors="pt")
        with self.torch.no_grad():
            features = self.model.get_image_features(**inputs)[0]
        return tuple(float(v) for v in features)


class ArcFaceEncoder:
    """The sanity channel: `glintr100`, the generator's own recognizer.

    **This may only falsify.** It is the encoder InstantID injects identity with,
    so a high cosine on the output is evidence that the adapter did the thing it
    optimises, measured by the loss it optimises against; it asserts nothing about
    identity. A low value on a run that should have preserved identity is a real
    finding. The asymmetry is printed beside the number (design.md D8).

    The pin is the graph's own, byte for byte, or the claim above would be about
    two different models.
    """

    def __init__(self, models_dir: Path, canvas: Canvas) -> None:
        """Load the graph's own pinned recognizer, byte for byte."""
        self.session = OnnxSession(RECOGNIZER, models_dir)
        self.canvas = canvas

    def embed(self, image_path: str, box: Box) -> tuple[float, ...] | None:
        """Return the unit-normalised 512-d embedding of the face crop, or None."""
        numpy = _numpy()
        image_module, _ = _pil()
        pixels = load_canvas_pixels(image_path, self.canvas)
        crop = image_module.fromarray(pixels).crop(tuple(int(v) for v in box))
        if crop.width < 2 or crop.height < 2:
            return None
        resized = numpy.asarray(
            crop.resize((112, 112), image_module.BILINEAR), dtype="float32"
        )
        feed = {
            self.session.session.get_inputs()[0].name: numpy.ascontiguousarray(
                ((resized - 127.5) / 127.5).transpose(2, 0, 1)[None]
            )
        }
        return tuple(float(v) for v in self.session.run(feed)[0][0])


class DwPoseReader:
    """The pose axis: DWPose, Apache-2.0, reusing the graph's own pins.

    Returns None rather than an empty result when the model reads nothing at all,
    so the axis reports **its own absence** rather than a zero. A pose model that
    failed to run and a render whose pose is completely wrong are not the same
    finding, and one number cannot say both.
    """

    def __init__(self, models_dir: Path, canvas: Canvas) -> None:
        """Verify and load the pinned DWPose TorchScript module."""
        try:
            import torch  # ty: ignore[unresolved-import]
        except ModuleNotFoundError as absent:  # pragma: no cover - environment
            raise Refusal(
                "the evaluator's stack is not installed; run `uv sync --extra eval`."
            ) from absent
        dest = (
            "annotator_ckpts/hr16/DWPose-TorchScript-BatchSize5/"
            "dw-ll_ucoco_384_bs5.torchscript.pt"
        )
        self.torch = torch
        self.model = torch.jit.load(str(resolve(dest, models_dir)))
        self.model.eval()
        self.canvas = canvas

    def keypoints(self, image_path: str) -> tuple[Keypoint, ...] | None:
        """Return the keypoints read, or None if the model read none at all."""
        numpy = _numpy()
        image_module, _ = _pil()
        pixels = load_canvas_pixels(image_path, self.canvas)
        resized = numpy.asarray(
            image_module.fromarray(pixels).resize((288, 384), image_module.BILINEAR),
            dtype="float32",
        )
        batch = self.torch.from_numpy(
            numpy.ascontiguousarray(
                ((resized - 127.5) / 127.5).transpose(2, 0, 1)[None]
            )
        )
        try:
            with self.torch.no_grad():
                output = self.model(batch)
        except RuntimeError:
            # The axis reports its own absence rather than a zero. That this
            # happens at all is a phase-8 finding, not a caught-and-ignored error.
            return None
        heatmaps = numpy.asarray(output[0] if isinstance(output, tuple) else output)
        if heatmaps.ndim != 4 or heatmaps.shape[1] == 0:
            return None
        points: list[Keypoint] = []
        _, joints, height, width = heatmaps.shape
        for j in range(joints):
            plane = heatmaps[0, j]
            flat = int(numpy.argmax(plane))
            y, x = divmod(flat, width)
            points.append(
                Keypoint(
                    x=float(x) / width * self.canvas.width,
                    y=float(y) / height * self.canvas.height,
                    confidence=float(plane.flat[flat]),
                )
            )
        return tuple(points)
