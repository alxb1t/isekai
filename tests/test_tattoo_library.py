"""The tattoo library: the store over a temporary library, no server involved.

Each image is built here from flat colour, so what a keep must turn, bound or refuse
is known before it runs.
"""

import io
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image, ImageDraw

from isekai.foundation.refusal import Refusal
from isekai.pipeline import tattoos
from isekai.pipeline.tattoos import (
    DESIGN,
    INK_CONFIG,
    OUTLINE,
    RECORD,
    TATTOO_CONFIG,
    TATTOOS,
    cut,
    defaults,
    design_bytes,
    keep,
    listed,
    load_tattoo_config,
    named,
    read_outline,
    save_outline,
)
from isekai.shared.ink import load_ink_config

START = datetime(2026, 11, 12, 9, 0, tzinfo=UTC)
DIGEST = "0123456789ab"
OTHER_DIGEST = "ba9876543210"
PHOTO = (4000, 3000)


def _at(seconds: int) -> datetime:
    """Return a moment `seconds` after the suite's start."""
    return START + timedelta(seconds=seconds)


def _png(
    size: tuple[int, int] = (40, 20), colour: tuple[int, ...] = (200, 80, 60)
) -> bytes:
    """Return a PNG of one flat colour, RGB or RGBA by the colour's length."""
    out = io.BytesIO()
    Image.new("RGBA" if len(colour) == 4 else "RGB", size, colour).save(out, "PNG")
    return out.getvalue()


def _tilted() -> bytes:
    """Return a 40x20 JPEG, left half red and right half blue, tagged orientation 6.

    Orientation 6 turns the picture a quarter clockwise on display, so upright it
    is 20x40 with the red half on top.
    """
    image = Image.new("RGB", (40, 20), (255, 0, 0))
    image.paste((0, 0, 255), (20, 0, 40, 20))
    exif = Image.Exif()
    exif[0x0112] = 6
    out = io.BytesIO()
    image.save(out, "JPEG", quality=100, subsampling=0, exif=exif)
    return out.getvalue()


def _ring(count: int, size: tuple[int, int] = (40, 20)) -> list[list[float]]:
    """Return `count` points on an ellipse inside an image of `size`."""
    width, height = size
    return [
        [
            width / 2 + width / 3 * math.cos(2 * math.pi * step / count),
            height / 2 + height / 3 * math.sin(2 * math.pi * step / count),
        ]
        for step in range(count)
    ]


def _open(path: Path) -> Image.Image:
    """Return the image at `path`, decoded."""
    image = Image.open(path)
    image.load()
    return image


@pytest.mark.spec("tattoo:library:a-bad-name-is-refused")
@pytest.mark.parametrize(
    "name", ["", "   ", ".hidden", "..", "a/b", "a\\b", "a\0b", "x" * 300]
)
def test_tattoo_names_refuse_what_is_no_folder_name(tmp_path: Path, name: str) -> None:
    with pytest.raises(Refusal, match="choose another name"):
        keep(tmp_path, name, _png())
    with pytest.raises(Refusal, match="choose another name"):
        cut(tmp_path, name, DIGEST, PHOTO)

    assert not (tmp_path / TATTOOS).exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.spec("tattoo:library:a-taken-name-is-refused")
def test_tattoo_names_a_taken_name_is_refused_and_the_tattoo_is_as_it_was(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(colour=(10, 20, 30)), at=_at(0))
    before = (tmp_path / TATTOOS / "bow" / DESIGN).read_bytes()

    with pytest.raises(Refusal, match="bow is kept; choose another name"):
        keep(tmp_path, "bow", _png(colour=(90, 90, 90)), at=_at(1))
    with pytest.raises(Refusal, match="bow is kept; choose another name"):
        cut(tmp_path, "bow", DIGEST, PHOTO, at=_at(2))

    assert (tmp_path / TATTOOS / "bow" / DESIGN).read_bytes() == before
    assert [tattoo.name for tattoo in listed(tmp_path)] == ["bow"]
    assert sorted(item.name for item in (tmp_path / TATTOOS).iterdir()) == ["bow"]


@pytest.mark.spec("tattoo:library:the-list-names-each-tattoo")
def test_tattoo_names_are_listed_with_their_kind_and_size_in_the_order_kept(
    tmp_path: Path,
) -> None:
    assert listed(tmp_path) == []
    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(5))
    keep(tmp_path, "bow", _png((40, 20)), at=_at(9))
    keep(tmp_path, "anchor", _png((10, 30)), at=_at(1))
    save_outline(tmp_path, "bow", _ring(24), True, 1.0, False, 1.0)

    rows = [(t.name, t.kind, t.size, t.outlined) for t in listed(tmp_path)]

    assert rows == [
        ("anchor", "image", (10, 30), False),
        ("arm", "cut", PHOTO, False),
        ("bow", "image", (40, 20), True),
    ]


@pytest.mark.spec_exempt(
    "structural: a hidden folder, a folder with no record and a file are no tattoo"
)
def test_tattoo_names_one_folder_each_and_a_dot_folder_is_no_tattoo(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    (tmp_path / TATTOOS / ".keep-left").mkdir()
    (tmp_path / TATTOOS / "empty").mkdir()
    (tmp_path / TATTOOS / "note.txt").write_text("not a tattoo")

    assert [tattoo.name for tattoo in listed(tmp_path)] == ["bow"]


@pytest.mark.spec_exempt(
    "structural: an unknown name and a name that climbs out of the folder are refused"
)
@pytest.mark.parametrize("name", ["ghost", "..", "a/b", ""])
def test_tattoo_names_an_unknown_name_is_refused_by_every_reader(
    tmp_path: Path, name: str
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))

    for reader in (named, read_outline, design_bytes):
        with pytest.raises(Refusal):
            reader(tmp_path, name)
    with pytest.raises(Refusal, match="ghost"):
        named(tmp_path, "ghost")


@pytest.mark.spec_exempt("structural: a cut holds no image, so its design is refused")
def test_tattoo_names_a_cuts_design_is_refused_saying_it_is_cut(tmp_path: Path) -> None:
    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(0))
    keep(tmp_path, "bow", _png(), at=_at(1))

    with pytest.raises(Refusal, match="arm is cut from a photograph"):
        design_bytes(tmp_path, "arm")

    assert (
        design_bytes(tmp_path, "bow")
        == (tmp_path / TATTOOS / "bow" / DESIGN).read_bytes()
    )


@pytest.mark.spec_exempt("structural: a damaged record refuses naming its folder")
def test_tattoo_names_a_damaged_record_is_refused_naming_the_folder(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    (tmp_path / TATTOOS / "bow" / RECORD).write_text("{not json")

    for call in (
        lambda: named(tmp_path, "bow"),
        lambda: listed(tmp_path),
        lambda: read_outline(tmp_path, "bow"),
    ):
        with pytest.raises(Refusal, match=r"\.tattoos/bow"):
            call()

    (tmp_path / TATTOOS / "bow" / RECORD).write_text(
        json.dumps({"kind": "sticker", "size": [1, 1], "kept": "x"})
    )
    with pytest.raises(Refusal, match=r"\.tattoos/bow"):
        named(tmp_path, "bow")

    (tmp_path / TATTOOS / "bow" / RECORD).write_text("[1, 2]")
    with pytest.raises(Refusal, match="no JSON object"):
        named(tmp_path, "bow")


@pytest.mark.spec_exempt(
    "structural: both configs are declared once and the store reads their keys"
)
def test_tattoo_config_reads_the_keys_of_both_configs() -> None:
    config = load_tattoo_config()
    ink = load_ink_config(INK_CONFIG)

    assert json.loads(TATTOO_CONFIG.read_text()) == {
        "long_side": config.long_side,
        "outline_min": config.outline_min,
        "outline_max": config.outline_max,
        "view_quality": config.view_quality,
        "floor_stage1": config.floor_stage1,
        "floor_stage2": config.floor_stage2,
        "floor_direct": config.floor_direct,
        "preview_floor": config.preview_floor,
        "preview_margin": config.preview_margin,
        "preview_wait_ms": config.preview_wait_ms,
        "pair_radius": config.pair_radius,
        "region_min": config.region_min,
    }
    assert (config.long_side, config.outline_min, config.outline_max) == (4096, 20, 120)
    assert config.view_quality == 90
    assert (config.floor_stage1, config.floor_stage2, config.floor_direct) == (6, 8, 6)
    assert (config.preview_floor, config.preview_margin) == (3, 96)
    assert (config.preview_wait_ms, config.pair_radius, config.region_min) == (
        1000,
        8,
        3,
    )
    assert (ink.photo_depth, ink.image_depth) == (1.6, 1.0)
    assert (ink.depth_min, ink.depth_max, ink.reach) == (1.0, 2.0, 64)


def _declared(**changed: object) -> dict[str, object]:
    """Return a whole config document, each key at 1, with `changed` laid over it."""
    return {key: 1 for key in tattoos.KEYS} | changed


@pytest.mark.spec_exempt("structural: a config that is wrong refuses naming its key")
@pytest.mark.parametrize(
    ("document", "match"),
    [
        ({"long_side": 4096}, "declares no outline_min"),
        (_declared(x=1), "declares x"),
        (_declared(long_side="big"), "`long_side`"),
        (_declared(long_side=True), "`long_side`"),
        (_declared(outline_min=30, outline_max=20), "`outline_min`"),
        (_declared(view_quality=101), "`view_quality`"),
        (_declared(preview_floor=0), "`preview_floor`"),
        (_declared(pair_radius="wide"), "`pair_radius`"),
    ],
)
def test_tattoo_config_refuses_a_wrong_key_naming_it(
    tmp_path: Path, document: dict[str, object], match: str
) -> None:
    path = tmp_path / "tattoo.json"
    path.write_text(json.dumps(document))

    with pytest.raises(Refusal, match=match):
        load_tattoo_config(path)


@pytest.mark.spec("tattoo:outline:an-outline-is-saved-as-it-is-sent")
def test_tattoo_outline_is_saved_as_it_is_sent_and_outlined_once_closed(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    ring = _ring(24)

    save_outline(tmp_path, "bow", ring[:5], False, 1.0, False, 1.0)
    assert read_outline(tmp_path, "bow").points == tuple(map(tuple, ring[:5]))
    assert not named(tmp_path, "bow").outlined

    save_outline(tmp_path, "bow", ring[:12], False, 1.0, False, 1.0)
    assert len(read_outline(tmp_path, "bow").points) == 12
    assert not named(tmp_path, "bow").outlined

    saved = save_outline(tmp_path, "bow", ring, True, 0.9, True, 1.4)
    read = read_outline(tmp_path, "bow")

    assert read == saved
    assert (read.closed, read.white, read.neutral, read.depth) == (True, 0.9, True, 1.4)
    assert named(tmp_path, "bow").outlined
    assert [t.outlined for t in listed(tmp_path)] == [True]


@pytest.mark.spec("tattoo:outline:the-defaults-follow-the-kind")
def test_tattoo_outline_defaults_follow_the_kind(tmp_path: Path) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(1))

    uploaded = read_outline(tmp_path, "bow")
    cut_out = read_outline(tmp_path, "arm")

    assert (uploaded.neutral, uploaded.depth) == (False, 1.0)
    assert (cut_out.neutral, cut_out.depth) == (True, 1.6)
    for outline in (uploaded, cut_out):
        assert (outline.points, outline.closed, outline.white) == ((), False, 1.0)
    assert uploaded == defaults("image")
    assert cut_out == defaults("cut")


@pytest.mark.spec("tattoo:outline:the-defaults-follow-the-kind")
def test_tattoo_outline_a_tattoo_with_no_file_reads_the_defaults_of_its_kind(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(1))
    for name in ("bow", "arm"):
        (tmp_path / TATTOOS / name / OUTLINE).unlink()

    assert read_outline(tmp_path, "bow") == defaults("image")
    assert read_outline(tmp_path, "arm") == defaults("cut")


@pytest.mark.spec("tattoo:outline:a-point-outside-the-image-is-refused")
@pytest.mark.parametrize("point", [[41, 5], [-1, 5], [5, 21], [5, -0.5]])
def test_tattoo_outline_a_point_outside_the_image_is_refused_naming_it(
    tmp_path: Path, point: list[float]
) -> None:
    keep(tmp_path, "bow", _png((40, 20)), at=_at(0))
    save_outline(tmp_path, "bow", [[1, 1], [2, 2]], False, 1.0, False, 1.0)
    before = (tmp_path / TATTOOS / "bow" / OUTLINE).read_bytes()

    with pytest.raises(Refusal, match=r"point 3 .* outside the 40x20 image"):
        save_outline(tmp_path, "bow", [[1, 1], [2, 2], point], False, 1.0, False, 1.0)

    assert (tmp_path / TATTOOS / "bow" / OUTLINE).read_bytes() == before


@pytest.mark.spec("tattoo:outline:a-point-outside-the-image-is-refused")
def test_tattoo_outline_the_image_edge_is_inside_and_a_cut_is_bounded_by_its_photograph(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png((40, 20)), at=_at(0))
    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(1))

    save_outline(tmp_path, "bow", [[0, 0], [40, 20]], False, 1.0, False, 1.0)
    save_outline(tmp_path, "arm", [[3999, 2999], [4000, 3000]], False, 1.0, True, 1.6)
    with pytest.raises(Refusal, match="outside the 4000x3000 image"):
        save_outline(tmp_path, "arm", [[4001, 5]], False, 1.0, True, 1.6)


@pytest.mark.spec("tattoo:outline:a-point-outside-the-image-is-refused")
@pytest.mark.parametrize(
    "points",
    [
        "ab",
        [[1]],
        [[1, 2, 3]],
        [["1", 2]],
        [[True, 2]],
        [[math.nan, 2]],
        [[math.inf, 2]],
        [[10**400, 2]],
        [None],
    ],
)
def test_tattoo_outline_a_point_that_is_not_a_pair_of_numbers_is_refused(
    tmp_path: Path, points: object
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))

    with pytest.raises(Refusal, match=r"point|points"):
        save_outline(tmp_path, "bow", cast("Any", points), False, 1.0, False, 1.0)

    assert read_outline(tmp_path, "bow") == defaults("image")


@pytest.mark.spec("tattoo:outline:the-bounds-are-held")
def test_tattoo_outline_the_bounds_are_held(tmp_path: Path) -> None:
    config = load_tattoo_config()
    keep(tmp_path, "bow", _png((400, 400)), at=_at(0))

    open_up_to_the_ceiling = _ring(config.outline_max, (400, 400))
    save_outline(tmp_path, "bow", open_up_to_the_ceiling, False, 1.0, False, 1.0)
    save_outline(
        tmp_path, "bow", _ring(config.outline_min, (400, 400)), True, 1, False, 1
    )
    save_outline(tmp_path, "bow", open_up_to_the_ceiling, True, 1.0, False, 1.0)

    with pytest.raises(Refusal, match=f"at least {config.outline_min} points"):
        save_outline(
            tmp_path,
            "bow",
            _ring(config.outline_min - 1, (400, 400)),
            True,
            1.0,
            False,
            1.0,
        )
    with pytest.raises(Refusal, match=f"at most {config.outline_max} points"):
        save_outline(
            tmp_path,
            "bow",
            _ring(config.outline_max + 1, (400, 400)),
            False,
            1.0,
            False,
            1.0,
        )
    with pytest.raises(Refusal, match=f"at most {config.outline_max} points"):
        save_outline(
            tmp_path,
            "bow",
            _ring(config.outline_max + 1, (400, 400)),
            True,
            1.0,
            False,
            1.0,
        )
    assert len(read_outline(tmp_path, "bow").points) == config.outline_max
    save_outline(tmp_path, "bow", [], False, 1.0, False, 1.0)


@pytest.mark.spec("tattoo:outline:a-tone-out-of-range-is-refused")
@pytest.mark.parametrize(
    ("white", "neutral", "depth", "match"),
    [
        (1.0, False, 0.99, "depth 0.99 is outside 1 to 2"),
        (1.0, False, 2.01, "depth 2.01 is outside 1 to 2"),
        (1.0, False, math.nan, "depth nan"),
        (0.0, False, 1.0, "white scale 0"),
        (-0.5, False, 1.0, "white scale -0.5"),
        (math.inf, False, 1.0, "white scale inf"),
        (math.nan, False, 1.0, "white scale nan"),
        (True, False, 1.0, "white scale"),
        (255.5, False, 1.0, "white scale 255.5 .* at most 255"),
        (1e300, False, 1.0, "white scale 1e\\+300 .* at most 255"),
        (10**400, False, 1.0, "white scale 1000"),
        (1.0, False, 10**400, "depth 1000"),
        (1.0, "yes", 1.0, "neutral"),
        (1.0, False, "deep", "depth"),
    ],
)
def test_tattoo_outline_a_tone_out_of_range_is_refused_naming_the_value(
    tmp_path: Path, white: object, neutral: object, depth: object, match: str
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    save_outline(tmp_path, "bow", [[1, 1]], False, 1.0, False, 1.0)
    before = (tmp_path / TATTOOS / "bow" / OUTLINE).read_bytes()

    with pytest.raises(Refusal, match=match):
        tone: Any = (white, neutral, depth)
        save_outline(tmp_path, "bow", [[2, 2]], False, *tone)

    assert (tmp_path / TATTOOS / "bow" / OUTLINE).read_bytes() == before


@pytest.mark.spec("tattoo:outline:a-tone-out-of-range-is-refused")
def test_tattoo_outline_the_depth_bounds_themselves_are_kept(tmp_path: Path) -> None:
    ink = load_ink_config(INK_CONFIG)
    keep(tmp_path, "bow", _png(), at=_at(0))

    for depth in (ink.depth_min, ink.depth_max):
        assert (
            save_outline(tmp_path, "bow", [], False, 0.001, True, depth).depth == depth
        )
    assert save_outline(tmp_path, "bow", [], False, 255, True, 1.0).white == 255.0


@pytest.mark.spec_exempt("structural: saving an outline to no tattoo is refused")
def test_tattoo_outline_saved_for_an_unknown_tattoo_is_refused(tmp_path: Path) -> None:
    with pytest.raises(Refusal, match="ghost"):
        save_outline(tmp_path, "ghost", [], False, 1.0, False, 1.0)

    assert not (tmp_path / TATTOOS).exists()


@pytest.mark.spec("tattoo:library:an-upload-is-kept-upright-and-bounded")
def test_tattoo_keep_turns_the_pixels_upright_and_leaves_no_metadata(
    tmp_path: Path,
) -> None:
    source = _tilted()
    assert Image.open(io.BytesIO(source)).getexif()[0x0112] == 6

    kept = keep(tmp_path, "bow", source, at=_at(0))

    folder = tmp_path / TATTOOS / "bow"
    design = _open(folder / DESIGN)
    assert design.format == "PNG"
    assert design.size == (20, 40)
    assert len(design.getexif()) == 0
    assert set(design.info) <= {"dpi", "gamma"}
    assert b"Exif" not in (folder / DESIGN).read_bytes()
    red, blue = design.getpixel((10, 5)), design.getpixel((10, 35))
    assert isinstance(red, tuple) and isinstance(blue, tuple)
    assert red[0] > 200 and red[2] < 60
    assert blue[2] > 200 and blue[0] < 60
    record = json.loads((folder / RECORD).read_text())
    assert record["size"] == [20, 40]
    assert record["kind"] == "image"
    assert record["downscaled_from"] is None
    assert record["cut_from"] is None
    assert kept.size == (20, 40)
    assert kept == named(tmp_path, "bow")


@pytest.mark.spec("tattoo:library:an-upload-is-kept-upright-and-bounded")
def test_tattoo_keep_writes_the_default_outline_beside_the_image(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))

    folder = tmp_path / TATTOOS / "bow"
    assert sorted(item.name for item in folder.iterdir()) == [DESIGN, OUTLINE, RECORD]
    assert json.loads((folder / OUTLINE).read_text()) == {
        "points": [],
        "closed": False,
        "white": 1.0,
        "neutral": False,
        "depth": 1.0,
    }


@pytest.mark.spec("tattoo:library:an-oversized-upload-is-downscaled")
def test_tattoo_keep_downscales_a_long_side_past_the_declared_one_and_says_so(
    tmp_path: Path,
) -> None:
    long_side = load_tattoo_config().long_side

    kept = keep(tmp_path, "wide", _png((long_side + 704, 600)), at=_at(0))

    design = _open(tmp_path / TATTOOS / "wide" / DESIGN)
    assert design.size == (long_side, round(600 * long_side / (long_side + 704)))
    assert kept.size == design.size
    assert kept.downscaled_from == (long_side + 704, 600)
    record = json.loads((tmp_path / TATTOOS / "wide" / RECORD).read_text())
    assert record["downscaled_from"] == [long_side + 704, 600]
    assert record["size"] == list(design.size)


@pytest.mark.spec("tattoo:library:an-oversized-upload-is-downscaled")
def test_tattoo_keep_an_image_at_the_declared_long_side_is_kept_as_it_is(
    tmp_path: Path,
) -> None:
    long_side = load_tattoo_config().long_side

    kept = keep(tmp_path, "edge", _png((50, long_side)), at=_at(0))

    assert kept.size == (50, long_side)
    assert kept.downscaled_from is None


@pytest.mark.spec("tattoo:library:an-oversized-upload-is-downscaled")
def test_tattoo_keep_a_thin_image_past_the_long_side_keeps_a_pixel_of_width(
    tmp_path: Path,
) -> None:
    long_side = load_tattoo_config().long_side

    kept = keep(tmp_path, "thin", _png((1, long_side * 3)), at=_at(0))

    assert kept.size == (1, long_side)


@pytest.mark.spec("tattoo:library:an-upload-is-kept-upright-and-bounded")
def test_tattoo_keep_holds_transparency(tmp_path: Path) -> None:
    keep(tmp_path, "glass", _png((8, 8), (10, 20, 30, 0)), at=_at(0))

    design = _open(tmp_path / TATTOOS / "glass" / DESIGN)
    assert design.mode == "RGBA"
    assert design.getpixel((0, 0)) == (10, 20, 30, 0)


@pytest.mark.spec_exempt("structural: bytes that are no image refuse and leave nothing")
def test_tattoo_keep_bytes_that_are_no_image_are_refused_and_leave_nothing(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))

    with pytest.raises(Refusal, match="cannot be read as an image"):
        keep(tmp_path, "junk", b"not an image")

    assert sorted(item.name for item in (tmp_path / TATTOOS).iterdir()) == ["bow"]


SKIN = (200, 150, 120)
FILL = (180, 130, 219, 169)
ARM = (400, 300)
CENTRE = (200, 150)


def _arm_png() -> bytes:
    """Return flat skin with one dark square fill, the ink a ring of points holds."""
    arm = Image.new("RGB", ARM, SKIN)
    ImageDraw.Draw(arm).rectangle(FILL, fill=(40, 30, 30))
    out = io.BytesIO()
    arm.save(out, "PNG")
    return out.getvalue()


def _around_the_fill(count: int = 24) -> list[list[float]]:
    """Return `count` points on a circle that holds the fill with skin to spare."""
    return [
        [
            CENTRE[0] + 34 * math.cos(2 * math.pi * step / count),
            CENTRE[1] + 34 * math.sin(2 * math.pi * step / count),
        ]
        for step in range(count)
    ]


def _outlined_cut(library: Path, photograph: Path, name: str = "arm") -> list[Any]:
    """Keep a cut of `photograph` with a closed outline round the fill; return it."""
    photograph.write_bytes(_arm_png())
    cut(library, name, DIGEST, ARM, at=_at(0))
    points = _around_the_fill()
    save_outline(library, name, points, True, 1.0, True, 1.6)
    return points


def _view(
    library: Path, photograph: Path, points: list[Any], **tone: float | bool
) -> tattoos.InkView:
    """Ask the ink view of the cut `arm` on `photograph` with the tone's defaults."""
    asked: dict[str, Any] = {"white": 1.0, "neutral": True, "depth": 1.6} | tone
    return tattoos.ink_view(
        library, "arm", photograph, DIGEST, points, asked["white"],
        asked["neutral"], asked["depth"],
    )  # fmt: skip


@pytest.mark.spec("tattoo:ink-view:a-jpeg-on-the-outlines-crop")
def test_ink_view_is_a_jpeg_the_size_of_the_outlines_crop(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)

    view = _view(tmp_path, photograph, points)

    reach = load_ink_config(INK_CONFIG).reach
    x, y, width, height = view.box
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    assert (x, y) == (
        max(0, math.floor(min(xs)) - reach),
        max(0, math.floor(min(ys)) - reach),
    )
    assert x + width == min(ARM[0], math.floor(max(xs)) + 1 + reach)
    assert y + height == min(ARM[1], math.floor(max(ys)) + 1 + reach)
    image = Image.open(io.BytesIO(view.jpeg))
    assert image.format == "JPEG"
    assert image.size == (width, height)
    assert image.size != ARM
    inside = image.getpixel((CENTRE[0] - x, CENTRE[1] - y))
    outside = image.getpixel((2, 2))
    assert isinstance(inside, tuple) and isinstance(outside, tuple)
    assert max(inside) < 128
    assert min(outside) > 250


@pytest.mark.spec("tattoo:ink-view:the-answer-carries-the-automatic-white-point")
def test_ink_view_names_the_automatic_grey_as_a_whole_number(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)

    scaled = _view(tmp_path, photograph, points, white=0.5)
    automatic = _view(tmp_path, photograph, points)

    assert isinstance(automatic.white, int)
    assert 0 <= automatic.white <= 255
    assert scaled.white == automatic.white


@pytest.mark.spec("tattoo:ink-view:the-answer-is-kept-nowhere")
def test_ink_view_writes_no_file(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)
    before = sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*"))

    _view(tmp_path, photograph, points)

    assert sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*")) == before


@pytest.mark.spec_exempt("structural: an upload's ink view reads its design.png")
def test_ink_view_of_an_upload_reads_its_design_not_a_photograph(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _arm_png(), at=_at(0))
    points = _around_the_fill()
    save_outline(tmp_path, "bow", points, True, 1.0, False, 1.0)

    view = tattoos.ink_view(tmp_path, "bow", None, None, points, 1.0, False, 1.0)

    assert Image.open(io.BytesIO(view.jpeg)).size == view.box[2:]


@pytest.mark.spec("tattoo:ink-view:an-open-outline-is-refused")
def test_ink_view_refuses_an_open_outline_saying_so(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)
    save_outline(tmp_path, "arm", points, False, 1.0, True, 1.6)

    with pytest.raises(Refusal, match="outline is open"):
        _view(tmp_path, photograph, points)


@pytest.mark.spec("tattoo:ink-view:an-open-outline-is-refused")
def test_ink_view_refuses_points_too_few_to_close_saying_so(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)

    with pytest.raises(Refusal, match="outline is open"):
        _view(tmp_path, photograph, points[:3])


@pytest.mark.spec("tattoo:ink-view:an-unknown-tattoo-is-refused")
def test_ink_view_refuses_an_unknown_tattoo_naming_it(tmp_path: Path) -> None:
    with pytest.raises(Refusal, match="ghost"):
        tattoos.ink_view(
            tmp_path, "ghost", None, None, _around_the_fill(), 1.0, False, 1.0
        )


@pytest.mark.spec("tattoo:cut:a-cut-serves-only-its-own-photograph")
def test_ink_view_refuses_a_cut_asked_on_another_digest(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)

    with pytest.raises(
        Refusal, match=f"cut from photograph {DIGEST}, not this render's"
    ):
        tattoos.ink_view(
            tmp_path, "arm", photograph, OTHER_DIGEST, points, 1.0, True, 1.6
        )
    with pytest.raises(Refusal, match="cut from a photograph"):
        tattoos.ink_view(tmp_path, "arm", None, None, points, 1.0, True, 1.6)


@pytest.mark.spec_exempt("structural: a photograph that moved on refuses its cut")
def test_ink_view_refuses_a_photograph_of_another_size_than_the_cut(
    tmp_path: Path,
) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)
    Image.new("RGB", (80, 80), SKIN).save(photograph)

    with pytest.raises(Refusal, match="is 80x80, the cut was made on 400x300"):
        _view(tmp_path, photograph, points)


@pytest.mark.spec_exempt(
    "structural: a view of no bare skin is the extraction's refusal"
)
def test_ink_view_passes_the_extractions_refusal_on(tmp_path: Path) -> None:
    photograph = tmp_path / "photo.png"
    points = _outlined_cut(tmp_path, photograph)
    Image.new("RGB", ARM, (10, 10, 10)).save(photograph)

    with pytest.raises(Refusal, match="no bare skin"):
        _view(tmp_path, photograph, points)


@pytest.mark.spec_exempt("structural: a failed write leaves no half-kept tattoo")
def test_tattoo_keep_a_failed_write_leaves_no_folder_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))

    written = tattoos.write_atomically

    def breaks_on_the_outline(path: Path, body: bytes, **options: bool) -> None:
        if path.name == OUTLINE:
            raise OSError("disk full")
        written(path, body, **options)

    monkeypatch.setattr(tattoos, "write_atomically", breaks_on_the_outline)
    with pytest.raises(OSError, match="disk full"):
        keep(tmp_path, "next", _png(), at=_at(1))
    with pytest.raises(OSError, match="disk full"):
        cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(2))

    assert sorted(item.name for item in (tmp_path / TATTOOS).iterdir()) == ["bow"]


@pytest.mark.spec("tattoo:cut:a-cut-holds-no-image")
def test_tattoo_cut_holds_a_record_naming_the_photograph_and_no_image(
    tmp_path: Path,
) -> None:
    made = cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(0))

    folder = tmp_path / TATTOOS / "arm"
    assert sorted(item.name for item in folder.iterdir()) == [OUTLINE, RECORD]
    record = json.loads((folder / RECORD).read_text())
    assert record["kind"] == "cut"
    assert record["cut_from"] == DIGEST
    assert record["size"] == list(PHOTO)
    assert record["downscaled_from"] is None
    assert made == named(tmp_path, "arm")
    assert (made.kind, made.cut_from, made.size) == ("cut", DIGEST, PHOTO)


@pytest.mark.spec("tattoo:cut:a-first-cut-starts-from-the-defaults")
def test_tattoo_cut_a_first_cut_starts_from_the_photographs_defaults(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    save_outline(tmp_path, "bow", [], False, 0.5, True, 1.9)
    cut(tmp_path, "other", OTHER_DIGEST, PHOTO, at=_at(1))
    save_outline(tmp_path, "other", [], False, 0.7, False, 1.3)

    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(2))

    assert read_outline(tmp_path, "arm") == defaults("cut")
    assert json.loads((tmp_path / TATTOOS / "arm" / OUTLINE).read_text()) == {
        "points": [],
        "closed": False,
        "white": 1.0,
        "neutral": True,
        "depth": 1.6,
    }


@pytest.mark.spec("tattoo:cut:a-second-cut-starts-from-the-first-cuts-tone")
def test_tattoo_cut_a_second_cut_starts_from_the_first_cuts_tone(
    tmp_path: Path,
) -> None:
    cut(tmp_path, "first", DIGEST, PHOTO, at=_at(0))
    save_outline(tmp_path, "first", _ring(30, PHOTO), True, 0.9, False, 1.2)

    cut(tmp_path, "second", DIGEST, PHOTO, at=_at(1))

    second = read_outline(tmp_path, "second")
    assert (second.neutral, second.depth, second.white) == (False, 1.2, 0.9)
    assert (second.points, second.closed) == ((), False)
    assert read_outline(tmp_path, "first").closed


@pytest.mark.spec("tattoo:cut:a-second-cut-starts-from-the-first-cuts-tone")
def test_tattoo_cut_the_newest_cut_gives_the_tone_and_a_tie_goes_to_the_later_name(
    tmp_path: Path,
) -> None:
    cut(tmp_path, "older", DIGEST, PHOTO, at=_at(0))
    save_outline(tmp_path, "older", [], False, 0.8, False, 1.1)
    cut(tmp_path, "newer", DIGEST, PHOTO, at=_at(10))
    save_outline(tmp_path, "newer", [], False, 0.6, True, 1.5)

    cut(tmp_path, "third", DIGEST, PHOTO, at=_at(20))
    assert read_outline(tmp_path, "third").white == 0.6

    cut(tmp_path, "tie-a", DIGEST, PHOTO, at=_at(30))
    save_outline(tmp_path, "tie-a", [], False, 0.3, False, 1.7)
    cut(tmp_path, "tie-b", DIGEST, PHOTO, at=_at(30))
    save_outline(tmp_path, "tie-b", [], False, 0.4, False, 1.8)

    cut(tmp_path, "after-tie", DIGEST, PHOTO, at=_at(40))
    tone = read_outline(tmp_path, "after-tie")
    assert (tone.white, tone.depth) == (0.4, 1.8)


@pytest.mark.spec("tattoo:cut:a-second-cut-starts-from-the-first-cuts-tone")
def test_tattoo_cut_another_photograph_and_an_upload_give_no_tone(
    tmp_path: Path,
) -> None:
    keep(tmp_path, "bow", _png(), at=_at(0))
    save_outline(tmp_path, "bow", [], False, 0.5, True, 1.9)
    cut(tmp_path, "elsewhere", OTHER_DIGEST, PHOTO, at=_at(1))
    save_outline(tmp_path, "elsewhere", [], False, 0.7, False, 1.3)

    cut(tmp_path, "arm", DIGEST, PHOTO, at=_at(2))

    assert read_outline(tmp_path, "arm") == defaults("cut")


@pytest.mark.spec_exempt(
    "structural: a digest or size naming no photograph is refused, nothing written"
)
@pytest.mark.parametrize(
    ("digest", "size"),
    [
        ("", PHOTO),
        ("0123456789a", PHOTO),
        ("0123456789AB", PHOTO),
        ("../../etc/pw", PHOTO),
        (DIGEST, (0, 10)),
        (DIGEST, (10, -1)),
        (DIGEST, (10.5, 10)),
        (DIGEST, (True, 10)),
    ],
)
def test_tattoo_cut_a_digest_or_size_that_names_no_photograph_is_refused(
    tmp_path: Path, digest: str, size: tuple[int, int]
) -> None:
    with pytest.raises(Refusal):
        cut(tmp_path, "arm", digest, size)

    assert not (tmp_path / TATTOOS).exists()
