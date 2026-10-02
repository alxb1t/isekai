from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from evaluation.face import CROP, TEMPLATE, Face, align, embed, similarity


class _Blind:
    """A detector that finds no face."""

    def find(self, image: Image.Image) -> Face | None:
        return None


class _Unreachable:
    """An encoder no test may reach."""

    def encode(self, crop: Image.Image) -> list[float]:
        raise AssertionError("a face no detector found was encoded")


def _noise(size: tuple[int, int]) -> Image.Image:
    """Return an RGB image of seeded noise, so a moved pixel shows."""
    pixels = np.random.default_rng(0).integers(0, 256, (*size[::-1], 3), np.uint8)
    return Image.fromarray(pixels)


def _moved(a: Image.Image, b: Image.Image) -> int:
    """Return the largest channel difference between two images of one size.

    One level is the bilinear filter's rounding; a pixel moved on noise is far more.
    """
    return int(np.abs(np.asarray(a, np.int16) - np.asarray(b, np.int16)).max())


@pytest.mark.spec("evaluation:encoder:the-crop-is-aligned")
def test_the_template_s_own_points_leave_the_image_unmoved_and_a_shift_is_undone() -> (
    None
):
    identity = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    image = _noise((CROP, CROP))
    shifted = Image.new("RGB", (CROP + 10, CROP + 5))
    shifted.paste(image, (10, 5))

    assert np.allclose(similarity(TEMPLATE), identity)
    assert np.allclose(
        similarity(TEMPLATE + (10.0, 5.0)), identity - [[0, 0, 10.0], [0, 0, 5.0]]
    )
    assert _moved(align(image, TEMPLATE), image) <= 1
    assert _moved(align(shifted, TEMPLATE + (10.0, 5.0)), image) <= 1


@pytest.mark.spec("evaluation:encoder:no-face-is-its-own-outcome")
def test_an_image_with_no_face_found_embeds_to_none(tmp_path: Path) -> None:
    path = tmp_path / "render.png"
    _noise((64, 64)).save(path)

    assert embed(path, _Blind(), _Unreachable()) is None
