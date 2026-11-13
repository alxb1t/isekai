"""The ink: a photograph or an image cut into a Multiply layer, and its verb.

Each image is built here from flat colour, so what the extraction must keep or
whiten is known before it runs.
"""

import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from isekai.foundation.refusal import Refusal
from isekai.interface.cli import build_parser, dispatch
from isekai.shared.ink import (
    INK_CONFIG_PATH,
    extract_ink,
    extract_ink_grey,
    load_ink_config,
    white_grey,
)
from tests.stages import bare_wiring

SKIN = (200, 150, 120)
BLACK_INK = (40, 30, 30)
BLUE_INK = (30, 60, 200)
FILL = (60, 60, 99, 99)
OUTLINE = (50, 50, 109, 109)


def _arm(fill: tuple[int, int, int] = BLACK_INK) -> Image.Image:
    """Return flat skin with one square fill, narrower than the extraction's reach."""
    arm = Image.new("RGB", (160, 160), SKIN)
    ImageDraw.Draw(arm).rectangle(FILL, fill=fill)
    return arm


def _outline() -> Image.Image:
    """Return a mask that is white round the fill and black elsewhere."""
    mask = Image.new("L", (160, 160), 0)
    ImageDraw.Draw(mask).rectangle(OUTLINE, fill=255)
    return mask


def _pixels(layer: Image.Image) -> "np.ndarray":
    """Return the layer's RGBA channels as an array."""
    return np.asarray(layer.convert("RGBA"))


def _at(layer: Image.Image, x: int, y: int) -> tuple[int, ...]:
    """Return one pixel of the layer."""
    return tuple(int(channel) for channel in _pixels(layer)[y, x])


@pytest.mark.spec("edit:ink:bare-skin-is-white")
def test_ink_extract_bare_skin_is_white() -> None:
    layer = extract_ink(_arm(), None, None, None)

    assert _at(layer, 10, 10)[:3] == (255, 255, 255)
    assert _at(layer, 150, 80)[:3] == (255, 255, 255)
    assert max(_at(layer, 80, 80)[:3]) < 255 // 2


@pytest.mark.spec("edit:ink:bare-skin-is-white")
def test_ink_extract_a_fill_is_darker_than_the_skin_at_every_channel() -> None:
    layer = _pixels(extract_ink(_arm(), None, None, None))

    assert (layer[80, 80, :3] < layer[10, 10, :3]).all()


def _tight() -> Image.Image:
    """Return a mask that is white exactly over the fill and black elsewhere."""
    mask = Image.new("L", (160, 160), 0)
    ImageDraw.Draw(mask).rectangle(FILL, fill=255)
    return mask


@pytest.mark.spec("edit:ink:a-tight-outline-over-a-solid-fill-is-cut-by-the-percentile")
@pytest.mark.parametrize("fill", [BLACK_INK, (160, 120, 96), (172, 150, 120)])
def test_ink_extract_a_tight_outline_over_a_solid_fill_is_cut_by_the_percentile(
    fill: tuple[int, int, int],
) -> None:
    layer = extract_ink(_arm(fill), _tight(), None, None)

    assert _at(layer, 80, 80)[:3] == (255, 255, 255)


@pytest.mark.spec("edit:ink:a-tight-outline-over-a-solid-fill-is-cut-by-the-percentile")
def test_ink_extract_a_one_channel_fill_keeps_its_ink_under_a_wider_outline() -> None:
    layer = extract_ink(_arm((172, 150, 120)), _outline(), None, None)

    assert _at(layer, 80, 80)[:3] != (255, 255, 255)


@pytest.mark.spec("edit:ink:bare-skin-is-white")
def test_ink_extract_an_outline_over_bare_skin_beside_a_light_fill_keeps_the_fill() -> (
    None
):
    layer = extract_ink(_arm((160, 120, 96)), _outline(), None, None)

    assert _at(layer, 55, 55)[:3] == (255, 255, 255)
    assert max(_at(layer, 80, 80)[:3]) < 220


@pytest.mark.spec("edit:ink:bare-skin-is-white")
def test_ink_extract_a_transparent_pixel_is_bare_skin_whatever_colour_it_stores() -> (
    None
):
    art = Image.new("RGBA", (160, 160), (255, 255, 255, 0))
    drawn = ImageDraw.Draw(art)
    drawn.rectangle(FILL, fill=(*BLUE_INK, 255))
    drawn.rectangle((10, 10, 29, 29), fill=(0, 0, 0, 0))

    layer = extract_ink(art, None, None, None)

    assert _at(layer, 20, 20)[:3] == (255, 255, 255)
    assert _at(layer, 80, 80)[2] > _at(layer, 80, 80)[0]


@pytest.mark.spec("edit:ink:an-outline-with-no-bare-skin-is-refused")
def test_ink_extract_refuses_an_image_with_no_skin() -> None:
    dark = Image.new("RGB", (64, 64), (5, 5, 5))

    with pytest.raises(Refusal, match="no bare skin"):
        extract_ink(dark, Image.new("L", (64, 64), 255), None, None)


@pytest.mark.spec_exempt("structural: the dark image's refusal")
def test_ink_extract_reads_a_lit_image_the_dark_one_is_refused_beside() -> None:
    lit = Image.new("RGB", (64, 64), SKIN)

    assert _at(extract_ink(lit, None, None, None), 5, 5)[:3] == (255, 255, 255)


@pytest.mark.spec_exempt("structural: the config's numbers are read by name")
def test_ink_extract_reads_the_config_the_prototype_ran_on() -> None:
    config = load_ink_config()

    assert (config.reach, config.white, config.floor) == (64, 80, 0.04)
    assert (config.photo_depth, config.image_depth) == (1.6, 1.0)
    assert (config.depth_min, config.depth_max) == (1.0, 2.0)


def _config(tmp_path: Path, **changes: object) -> Path:
    """Return a copy of `config/ink.json` with `changes` applied."""
    document = json.loads(INK_CONFIG_PATH.read_text())
    document.update(changes)
    for key in [key for key, value in changes.items() if value is None]:
        del document[key]
    path = tmp_path / "ink.json"
    path.write_text(json.dumps(document))
    return path


@pytest.mark.spec_exempt("structural: a config with a key this build does not read")
def test_ink_extract_refuses_a_key_it_does_not_read(tmp_path: Path) -> None:
    with pytest.raises(Refusal, match="declares glow"):
        load_ink_config(_config(tmp_path, glow=1))


@pytest.mark.spec_exempt("structural: a config with a key missing")
def test_ink_extract_refuses_a_key_the_config_lacks(tmp_path: Path) -> None:
    with pytest.raises(Refusal, match="declares no floor"):
        load_ink_config(_config(tmp_path, floor=None))


@pytest.mark.spec_exempt("structural: a default depth outside its own range")
def test_ink_extract_refuses_a_default_depth_outside_the_range(tmp_path: Path) -> None:
    with pytest.raises(Refusal, match="photo_depth"):
        load_ink_config(_config(tmp_path, photo_depth=3))


@pytest.mark.spec("edit:ink:a-photograph-with-an-outline")
def test_ink_flags_an_outline_is_the_alpha_and_the_channels_are_equal() -> None:
    outline = _outline()
    layer = _pixels(extract_ink(_arm(), outline, None, None))

    assert (layer[..., 3] == np.asarray(outline)).all()
    assert (layer[..., 0] == layer[..., 1]).all()
    assert (layer[..., 1] == layer[..., 2]).all()


@pytest.mark.spec("edit:ink:a-photograph-with-an-outline")
def test_ink_flags_an_outline_deepens_the_ink_past_depth_one() -> None:
    outline = _outline()
    deeper = _pixels(extract_ink(_arm(), outline, None, None))
    plain = _pixels(extract_ink(_arm(), outline, True, 1.0))

    assert deeper[80, 80, 0] < plain[80, 80, 0]


@pytest.mark.spec("edit:ink:a-tattoo-image-keeps-its-colour")
def test_ink_flags_an_image_with_no_outline_is_opaque_and_keeps_its_colour() -> None:
    layer = _pixels(extract_ink(_arm(BLUE_INK), None, None, None))

    assert (layer[..., 3] == 255).all()
    assert layer[80, 80, 2] > layer[80, 80, 0]


@pytest.mark.spec("edit:ink:a-tattoo-image-keeps-its-colour")
def test_ink_flags_an_image_with_no_outline_is_at_depth_one() -> None:
    image = _arm(BLUE_INK)

    assert extract_ink(image, None, None, None).tobytes() == (
        extract_ink(image, None, False, 1.0).tobytes()
    )


@pytest.mark.spec("edit:ink:a-flag-overrides-the-default")
def test_ink_flags_no_neutral_and_a_depth_override_the_outline_defaults() -> None:
    outline = _outline()
    image = _arm(BLUE_INK)
    layer = _pixels(extract_ink(image, outline, False, 1.2))
    base = _pixels(extract_ink(image, outline, False, 1.0))

    assert layer[80, 80, 2] > layer[80, 80, 0]
    expected = np.round((base[..., :3] / 255.0) ** 1.2 * 255.0)
    assert np.abs(layer[..., :3] - expected).max() <= 2


@pytest.mark.spec("edit:ink:a-flag-overrides-the-default")
def test_ink_flags_neutral_and_a_depth_override_the_image_defaults() -> None:
    image = _arm(BLUE_INK)
    layer = _pixels(extract_ink(image, None, True, 1.6))

    assert (layer[..., 0] == layer[..., 1]).all()
    assert layer[80, 80, 0] < _pixels(extract_ink(image, None, True, 1.0))[80, 80, 0]


@pytest.mark.spec("edit:ink:a-depth-out-of-range-is-refused")
@pytest.mark.parametrize("depth", [0.9, 2.1])
def test_ink_flags_a_depth_out_of_range_is_refused(depth: float) -> None:
    with pytest.raises(Refusal, match="1.0 to 2.0"):
        extract_ink(_arm(), None, None, depth)


@pytest.mark.spec("edit:ink:a-depth-out-of-range-is-refused")
@pytest.mark.parametrize("depth", [1.0, 2.0])
def test_ink_flags_a_depth_at_the_range_ends_is_taken(depth: float) -> None:
    assert extract_ink(_arm(), None, None, depth).size == (160, 160)


PALE_PATCH = (190, 140, 110)
PALE_AT = (110, 110, 129, 129)


def _arm_with_pale_patch() -> Image.Image:
    """Return `_arm()` with a pale patch beside its dark fill."""
    arm = _arm()
    ImageDraw.Draw(arm).rectangle(PALE_AT, fill=PALE_PATCH)
    return arm


@pytest.mark.spec("tattoo:white:a-scale-of-one-changes-nothing")
def test_ink_white_a_scale_of_one_changes_nothing() -> None:
    image = _arm_with_pale_patch()
    outline = _outline()

    assert extract_ink(image, outline, None, None, white=1.0).tobytes() == (
        extract_ink(image, outline, None, None).tobytes()
    )
    assert extract_ink(image, None, None, None, white=1.0).tobytes() == (
        extract_ink(image, None, None, None).tobytes()
    )


@pytest.mark.spec("tattoo:white:a-lower-scale-whitens-paler-ink")
def test_ink_white_a_lower_scale_whitens_paler_ink() -> None:
    image = _arm_with_pale_patch()
    automatic = _pixels(extract_ink(image, None, None, None))
    lowered = _pixels(extract_ink(image, None, None, None, white=0.8))

    assert lowered[120, 120, 0] > automatic[120, 120, 0]
    assert lowered[80, 80, 0] < lowered[120, 120, 0]


@pytest.mark.spec_exempt("structural: a scale of zero or less would divide by nothing")
@pytest.mark.parametrize("white", [0.0, -0.5])
def test_ink_white_a_scale_of_zero_or_less_is_refused(white: float) -> None:
    with pytest.raises(Refusal, match="white scale"):
        extract_ink(_arm(), None, None, None, white=white)


def _striped(dark: tuple[int, int, int]) -> Image.Image:
    """Return skin with a lit band at the start of each period and `dark` elsewhere.

    A band lies within the extraction's reach of every dark column, so the skin
    around reads `SKIN` throughout and most of the image reads `dark` against it.
    """
    pixels = np.empty((160, 160, 3), dtype=np.uint8)
    pixels[:, :] = dark
    pixels[:, np.arange(160) % 64 < 8] = SKIN
    return Image.fromarray(pixels)


@pytest.mark.spec("tattoo:white:the-automatic-point-is-one-grey")
def test_ink_grey_the_automatic_point_is_one_whole_number_of_8_bits() -> None:
    grey = white_grey(_striped((160, 120, 96)), Image.new("L", (160, 160), 255))

    assert isinstance(grey, int)
    assert grey == 204


@pytest.mark.spec("tattoo:white:the-automatic-point-is-one-grey")
def test_ink_grey_lit_skin_reads_the_top_of_the_scale() -> None:
    assert white_grey(_arm(), _outline()) == 255


@pytest.mark.spec("tattoo:white:the-automatic-point-is-one-grey")
def test_ink_grey_follows_the_point_extract_ink_divides_by() -> None:
    image = _striped((160, 120, 96))
    outline = Image.new("L", (160, 160), 255)
    layer = _pixels(extract_ink(image, outline, False, 1.0))

    assert white_grey(image, outline) == 204
    assert layer[10, 10, 0] == 255


@pytest.mark.spec_exempt(
    "structural: the layer and the grey from one read are the two reads' answers"
)
def test_ink_grey_with_the_layer_is_what_each_asked_alone_gives() -> None:
    image = _striped((160, 120, 96))
    outline = Image.new("L", (160, 160), 255)

    layer, grey = extract_ink_grey(image, outline, False, 1.0, white=0.8)

    assert (
        layer.tobytes() == extract_ink(image, outline, False, 1.0, white=0.8).tobytes()
    )
    assert grey == white_grey(image, outline) == 204


@pytest.mark.spec_exempt(
    "structural: the grey is read through the extraction's refusals"
)
def test_ink_grey_an_outline_with_no_bare_skin_is_refused() -> None:
    with pytest.raises(Refusal, match="no bare skin"):
        white_grey(Image.new("RGB", (160, 160), (5, 5, 5)), _tight())


def _saved(tmp_path: Path) -> tuple[Path, Path]:
    """Write the arm and its outline into `tmp_path`, returning their paths."""
    photo, outline = tmp_path / "arm.png", tmp_path / "outline.png"
    _arm().save(photo)
    _outline().save(outline)
    return photo, outline


@pytest.mark.spec("edit:ink:a-photograph-with-an-outline")
def test_ink_verb_writes_the_layer_of_a_photograph_and_its_outline(
    tmp_path: Path,
) -> None:
    photo, outline = _saved(tmp_path)
    out = tmp_path / "layers" / "ink.png"
    wired = bare_wiring()

    args = build_parser().parse_args(
        ["ink", str(photo), str(out), "--outline", str(outline)]
    )

    assert dispatch(args, wired) == 0
    assert isinstance(wired.out, io.StringIO)
    assert f"ink wrote {out}" in wired.out.getvalue()
    with Image.open(out) as written:
        assert written.mode == "RGBA"
        assert written.getchannel("A").tobytes() == _outline().tobytes()


@pytest.mark.spec("edit:ink:a-flag-overrides-the-default")
def test_ink_verb_reads_each_flag_and_leaves_an_unset_one_to_the_input() -> None:
    parse = build_parser().parse_args

    unset = parse(["ink", "a.jpg", "b.png"])
    given = parse(["ink", "a.jpg", "b.png", "--no-neutral", "--depth", "1.2"])

    assert (unset.neutral, unset.depth) == (None, None)
    assert (given.neutral, given.depth) == (False, 1.2)
    assert parse(["ink", "a.jpg", "b.png", "--neutral"]).neutral is True


@pytest.mark.spec("edit:ink:a-depth-out-of-range-is-refused")
@pytest.mark.parametrize("depth", ["0.9", "2.1"])
def test_ink_verb_refuses_a_depth_out_of_range_before_it_reads_an_image(
    depth: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "ink.png"

    with pytest.raises(SystemExit) as refused:
        build_parser().parse_args(
            ["ink", str(tmp_path / "absent.png"), str(out), "--depth", depth]
        )

    assert refused.value.code == 2
    assert "outside 1.0 to 2.0" in capsys.readouterr().err
    assert not out.exists()


@pytest.mark.spec("edit:ink:a-depth-out-of-range-is-refused")
@pytest.mark.parametrize("depth", ["1.0", "2.0"])
def test_ink_verb_takes_a_depth_at_the_range_ends(depth: str) -> None:
    args = build_parser().parse_args(["ink", "a.png", "b.png", "--depth", depth])

    assert args.depth == float(depth)


@pytest.mark.spec_exempt(
    "structural: an unreadable image is refused and writes nothing"
)
def test_ink_verb_refuses_an_image_it_cannot_read_and_writes_nothing(
    tmp_path: Path,
) -> None:
    broken = tmp_path / "broken.png"
    broken.write_bytes(b"not a png")
    out = tmp_path / "ink.png"
    wired = bare_wiring()

    args = build_parser().parse_args(["ink", str(broken), str(out)])

    assert dispatch(args, wired) == 1
    assert isinstance(wired.err, io.StringIO)
    assert "refused: broken.png: cannot be read as an image" in wired.err.getvalue()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["broken.png"]
