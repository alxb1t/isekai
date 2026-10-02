"""Find a face, align it, and embed it with an encoder the generator does not use.

YuNet finds the face and its five landmarks; the crop is warped onto the 112×112
ArcFace template; SFace embeds it. Both are OpenCV's own models, run on
onnxruntime, and neither is a pin the generator carries (D37).

    uv run python -m evaluation.face <image>…    # one `face x y w h` or `no face` each
"""

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import numpy as np
from PIL import Image, ImageOps

from isekai.boundary.wd14 import silence_onnxruntime

if TYPE_CHECKING:
    from onnxruntime import InferenceSession

# Where the five landmarks land in the encoder's 112×112 input: the eyes, the
# nose, the mouth's corners. OpenCV's `FaceRecognizerSF` template.
TEMPLATE = np.array(
    [
        (38.2946, 51.6963),
        (73.5318, 51.5014),
        (56.0252, 71.7366),
        (41.5493, 92.3655),
        (70.7299, 92.2041),
    ]
)
CROP = 112
SIDE = 640
STRIDES = (8, 16, 32)
SCORE = 0.6


@dataclass(frozen=True)
class Face:
    """One face: its box `(x, y, w, h)` and five landmarks, in image pixels."""

    box: tuple[float, float, float, float]
    landmarks: np.ndarray


class Finds(Protocol):
    """What finds the face in an image."""

    def find(self, image: Image.Image) -> Face | None:
        """Return the highest-scoring face, or None."""
        ...


class Encodes(Protocol):
    """What embeds an aligned crop."""

    def encode(self, crop: Image.Image) -> list[float]:
        """Return the crop's embedding, L2-normalised."""
        ...


def _session(model: Path) -> "InferenceSession":
    """Open `model` on the CPU, its load-time warnings silenced."""
    import onnxruntime

    options = onnxruntime.SessionOptions()
    options.log_severity_level = 3
    return onnxruntime.InferenceSession(
        str(model), options, providers=["CPUExecutionProvider"]
    )


class Detector:
    """YuNet over a letterboxed 640 square: the top face above 0.6, or None."""

    def __init__(self, model: Path) -> None:
        """Open the detector at `model`."""
        silence_onnxruntime()
        self._session = _session(model)

    def find(self, image: Image.Image) -> Face | None:
        """Return the highest-scoring face, mapped back to `image`'s pixels.

        Only the top box is kept, so suppressing its overlaps first changes nothing.
        """
        scale = SIDE / max(image.size)
        fitted = image.resize(
            (round(image.width * scale), round(image.height * scale)),
            Image.Resampling.BILINEAR,
        )
        canvas = Image.new("RGB", (SIDE, SIDE))
        canvas.paste(fitted)
        bgr = np.asarray(canvas, dtype=np.float32)[:, :, ::-1]
        blob = np.ascontiguousarray(bgr.transpose(2, 0, 1)[None])
        names = [o.name for o in self._session.get_outputs()]
        values = self._session.run(None, {"input": blob})
        out: dict[str, np.ndarray] = {
            name: np.asarray(value) for name, value in zip(names, values, strict=True)
        }
        best: tuple[float, Face] | None = None
        for stride in STRIDES:
            cols = SIDE // stride
            score = np.sqrt(
                np.clip(out[f"cls_{stride}"][0, :, 0], 0, 1)
                * np.clip(out[f"obj_{stride}"][0, :, 0], 0, 1)
            )
            idx = int(np.argmax(score))
            if score[idx] < SCORE or (best and score[idx] <= best[0]):
                continue
            row, col = divmod(idx, cols)
            dx, dy, dw, dh = out[f"bbox_{stride}"][0, idx]
            w, h = np.exp(dw) * stride, np.exp(dh) * stride
            cx, cy = (col + dx) * stride, (row + dy) * stride
            kps = out[f"kps_{stride}"][0, idx].reshape(5, 2)
            landmarks = (kps + (col, row)) * stride / scale
            box = (
                float((cx - w / 2) / scale),
                float((cy - h / 2) / scale),
                float(w / scale),
                float(h / scale),
            )
            best = (float(score[idx]), Face(box, landmarks))
        return best[1] if best else None


class Encoder:
    """SFace over an aligned 112×112 crop: a 128-d vector, L2-normalised."""

    def __init__(self, model: Path) -> None:
        """Open the encoder at `model`."""
        silence_onnxruntime()
        self._session = _session(model)

    def encode(self, crop: Image.Image) -> list[float]:
        """Return the crop's embedding.

        RGB, unnormalised, as OpenCV's `FaceRecognizerSF` feeds it.
        """
        rgb = np.asarray(crop.convert("RGB"), dtype=np.float32)
        blob = np.ascontiguousarray(rgb.transpose(2, 0, 1)[None])
        (vector,) = self._session.run(None, {"data": blob})
        flat = np.asarray(vector, dtype=np.float64)[0]
        return (flat / np.linalg.norm(flat)).tolist()


def similarity(landmarks: np.ndarray) -> np.ndarray:
    """Return the 2×3 least-squares similarity carrying `landmarks` onto the template.

    Umeyama's solution, as OpenCV's `FaceRecognizerSF.alignCrop` solves it.
    """
    src, dst = np.asarray(landmarks, dtype=np.float64), TEMPLATE
    src_mean, dst_mean = src.mean(0), dst.mean(0)
    src_c, dst_c = src - src_mean, dst - dst_mean
    covariance = dst_c.T @ src_c / len(src)
    u, s, vt = np.linalg.svd(covariance)
    d = np.array([1.0, -1.0 if np.linalg.det(covariance) < 0 else 1.0])
    rotation = u @ np.diag(d) @ vt
    scale = (s * d).sum() / (src_c**2).sum(1).mean()
    shift = dst_mean - scale * rotation @ src_mean
    return np.hstack([scale * rotation, shift[:, None]])


def align(image: Image.Image, landmarks: np.ndarray) -> Image.Image:
    """Return the 112×112 crop with `landmarks` warped onto the template."""
    forward = np.vstack([similarity(landmarks), (0, 0, 1)])
    # PIL maps each output pixel back to the input, so it takes the inverse.
    inverse = np.linalg.inv(forward)[:2].ravel()
    return image.transform(
        (CROP, CROP),
        Image.Transform.AFFINE,
        tuple(float(v) for v in inverse),
        Image.Resampling.BILINEAR,
    )


def load(path: Path) -> Image.Image:
    """Return the image at `path`, upright and RGB."""
    with Image.open(path) as opened:
        return ImageOps.exif_transpose(opened).convert("RGB")


def embed(path: Path, detector: Finds, encoder: Encodes) -> list[float] | None:
    """Return the face embedding of the image at `path`, or None when none is found."""
    image = load(path)
    face = detector.find(image)
    if face is None:
        return None
    return encoder.encode(align(image, face.landmarks))


def probe(paths: Sequence[Path], detector: Finds) -> list[str]:
    """Return one line per image: `face <x> <y> <w> <h>` or `no face`."""
    lines = []
    for path in paths:
        face = detector.find(load(path))
        if face is None:
            lines.append(f"no face  {path.name}")
        else:
            x, y, w, h = (round(v) for v in face.box)
            lines.append(f"face {x} {y} {w} {h}  {path.name}")
    return lines


def main(argv: Sequence[str]) -> int:
    """Print whether each image's face is found, and where."""
    from evaluation.eval_models import DETECTOR, load_eval_manifest
    from isekai.boundary.provision import resolve
    from isekai.shared.vocabulary import DEFAULT_MODELS_DIR

    model = resolve(DETECTOR, DEFAULT_MODELS_DIR, load_eval_manifest())
    print("\n".join(probe([Path(a) for a in argv], Detector(model))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
