"""The placement: a tattoo's stage-1 pairs and the preview, over a temporary library.

Each image is flat colour with one dark square, so where the ink lands is known: the
pairs here are translations, and a translation carries the square by its offset.
"""

import io
import json
import math
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from isekai.foundation.refusal import Refusal
from isekai.pipeline import tattoos
from isekai.pipeline.tattoos import (
    STAGE1,
    TATTOOS,
    cut,
    keep,
    load_tattoo_config,
    mode_of,
    read_stage1,
    save_outline,
    save_stage1,
    stage1_states,
)
from isekai.shared.chain import crop_box

DIGEST = "0123456789ab"
OTHER_DIGEST = "ba9876543210"
SKIN = (200, 150, 120)
FILL = (180, 130, 219, 169)
ARM = (400, 300)
CENTRE = (200, 150)
ONTO_PHOTO = (30, 20)
ONTO_RENDER = (15, 10)


def _arm() -> bytes:
    """Return a PNG of flat skin with one dark square, the ink a ring holds."""
    arm = Image.new("RGB", ARM, SKIN)
    ImageDraw.Draw(arm).rectangle(FILL, fill=(40, 30, 30))
    out = io.BytesIO()
    arm.save(out, "PNG")
    return out.getvalue()


def _around(radius: float, count: int) -> list[list[float]]:
    """Return `count` points on a circle of `radius` round the arm's centre."""
    return [
        [
            CENTRE[0] + radius * math.cos(2 * math.pi * step / count),
            CENTRE[1] + radius * math.sin(2 * math.pi * step / count),
        ]
        for step in range(count)
    ]


def _moved(points: list[list[float]], by: tuple[int, int]) -> list[list[float]]:
    """Return `points` moved by `by`."""
    return [[x + by[0], y + by[1]] for x, y in points]


def _pairs(
    count: int, by: tuple[int, int], origin: tuple[int, int] = (0, 0)
) -> list[list[list[float]]]:
    """Return `count` pairs: a point on a wide circle, and it moved by `by`."""
    first = _moved(_around(60, count), origin)
    return [[a, b] for a, b in zip(first, _moved(first, by), strict=True)]


def _library(tmp_path: Path, name: str = "bow") -> Path:
    """Return a library keeping the upload `name`, its outline closed round the fill."""
    keep(tmp_path, name, _arm())
    save_outline(tmp_path, name, _around(34, 24), True, 1.0, True, 1.6)
    return tmp_path


def _files(tmp_path: Path) -> tuple[Path, Path]:
    """Return a photograph and a render, each 400x300 and written under `tmp_path`."""
    photograph, render = tmp_path / "photo.png", tmp_path / "render.png"
    photograph.write_bytes(_arm())
    Image.new("RGB", ARM, (90, 90, 90)).save(render)
    return photograph, render


def _two_stage(tmp_path: Path, count: int = 6) -> tuple[Path, Path]:
    """Keep `bow` with `count` stage-1 pairs on the photograph; return the files."""
    _library(tmp_path)
    save_stage1(tmp_path, "bow", DIGEST, _pairs(count, ONTO_PHOTO), False)
    return _files(tmp_path)


def _ask(
    tmp_path: Path,
    files: tuple[Path, Path],
    target: str,
    pairs: object,
    name: str = "bow",
    limb: object = None,
    exclusions: object = (),
    digest: str = DIGEST,
) -> tattoos.Preview:
    """Ask the preview of `name` on the photograph or the render."""
    photograph, render = files
    return tattoos.preview(
        tmp_path, name, photograph, digest, render, target, pairs, limb, exclusions
    )


def _shown(made: tattoos.Preview) -> Image.Image:
    """Return the preview's JPEG, decoded."""
    shown = Image.open(io.BytesIO(made.jpeg))
    shown.load()
    return shown


def _at(shown: Image.Image, made: tattoos.Preview, x: int, y: int) -> int:
    """Return the least channel of the preview at the target's pixel (x, y)."""
    pixel = shown.getpixel((x - made.box[0], y - made.box[1]))
    assert isinstance(pixel, tuple)
    return min(pixel)


@pytest.mark.spec("tattoo:stage1:pairs-are-saved-as-they-are-sent")
def test_placement_stage1_each_save_replaces_the_file_and_reads_back(
    tmp_path: Path,
) -> None:
    _library(tmp_path)
    pairs = _pairs(6, ONTO_PHOTO)

    first = save_stage1(tmp_path, "bow", DIGEST, pairs, False)
    more = [*pairs, [[10, 10], [20, 20]]]
    save_stage1(tmp_path, "bow", DIGEST, more, False)

    read = read_stage1(tmp_path, "bow", DIGEST)
    assert len(first.pairs) == 6
    assert len(read.pairs) == 7
    assert [[list(a), list(b)] for a, b in read.pairs] == more
    path = tmp_path / TATTOOS / "bow" / STAGE1 / f"{DIGEST}.json"
    assert json.loads(path.read_text()) == {"pairs": more, "not_on_photo": False}
    assert sorted(item.name for item in path.parent.iterdir()) == [path.name]


@pytest.mark.spec("tattoo:stage1:a-photograph-with-no-file-has-no-pairs")
def test_placement_stage1_a_photograph_with_no_file_reads_as_no_pairs(
    tmp_path: Path,
) -> None:
    _library(tmp_path)
    before = sorted(tmp_path.rglob("*"))

    state = read_stage1(tmp_path, "bow", OTHER_DIGEST)

    assert (state.pairs, state.not_on_photo) == ((), False)
    assert sorted(tmp_path.rglob("*")) == before
    assert not (tmp_path / TATTOOS / "bow" / STAGE1).exists()


@pytest.mark.spec("tattoo:stage1:a-bad-point-is-refused")
@pytest.mark.parametrize(
    ("pairs", "match"),
    [
        ([[[1, 1], [2, 2]], [[-1, 5], [4, 4]]], r"pair 2 holds \(-1, 5\)"),
        ([[[1, 1], [2, -2]]], r"pair 1 holds \(2, -2\)"),
        ([[[1, 1], [2, 2]], [["5", 5], [4, 4]]], "pair 2 is"),
        ([[[1, 1], [math.nan, 2]]], "pair 1 is"),
        ([[[1, 1], [math.inf, 2]]], "pair 1 is"),
        ([[[True, 1], [2, 2]]], "pair 1 is"),
        ([[[1, 1], [2, 2]], [[401, 5], [4, 4]]], r"pair 2's tattoo point \(401, 5\)"),
        ([[[1, 301], [2, 2]]], r"pair 1's tattoo point \(1, 301\)"),
        ([[[1, 1]]], "pair 1 is"),
        ("pairs", "list of"),
    ],
)
def test_placement_stage1_a_bad_point_is_refused_naming_the_pair_and_the_file_stays(
    tmp_path: Path, pairs: object, match: str
) -> None:
    _library(tmp_path)
    save_stage1(tmp_path, "bow", DIGEST, _pairs(6, ONTO_PHOTO), False)
    path = tmp_path / TATTOOS / "bow" / STAGE1 / f"{DIGEST}.json"
    before = path.read_bytes()

    with pytest.raises(Refusal, match=match):
        save_stage1(tmp_path, "bow", DIGEST, pairs, False)

    assert path.read_bytes() == before


@pytest.mark.spec("tattoo:stage1:a-bad-point-is-refused")
def test_placement_stage1_a_tattoo_point_on_the_image_edge_is_inside(
    tmp_path: Path,
) -> None:
    _library(tmp_path)

    state = save_stage1(tmp_path, "bow", DIGEST, [[[400, 300], [0, 0]]], False)

    assert state.pairs == (((400.0, 300.0), (0.0, 0.0)),)


@pytest.mark.spec_exempt(
    "structural: a digest that is no photograph's, an unknown tattoo and a flag that "
    "is no boolean are refused"
)
def test_placement_stage1_a_bad_digest_name_or_flag_is_refused(tmp_path: Path) -> None:
    _library(tmp_path)

    for digest in ("", "0123456789a", "0123456789AB", "../../etc/pw"):
        with pytest.raises(Refusal, match="no photograph's digest"):
            save_stage1(tmp_path, "bow", digest, [], False)
        with pytest.raises(Refusal, match="no photograph's digest"):
            read_stage1(tmp_path, "bow", digest)
    with pytest.raises(Refusal, match="ghost"):
        save_stage1(tmp_path, "ghost", DIGEST, [], False)
    with pytest.raises(Refusal, match="true or false"):
        save_stage1(tmp_path, "bow", DIGEST, [], "yes")
    assert not (tmp_path / TATTOOS / "bow" / STAGE1).exists()


@pytest.mark.spec("tattoo:stage1:the-flag-keeps-the-pairs")
def test_placement_stage1_the_flag_keeps_the_pairs_it_is_sent_with(
    tmp_path: Path,
) -> None:
    _library(tmp_path)
    pairs = _pairs(6, ONTO_PHOTO)

    flagged = save_stage1(tmp_path, "bow", DIGEST, pairs, True)
    assert read_stage1(tmp_path, "bow", DIGEST) == flagged
    cleared = save_stage1(tmp_path, "bow", DIGEST, pairs, False)

    assert flagged.pairs == cleared.pairs
    assert len(flagged.pairs) == 6
    assert (flagged.not_on_photo, cleared.not_on_photo) == (True, False)
    assert read_stage1(tmp_path, "bow", DIGEST) == cleared


@pytest.mark.spec("tattoo:stage1:the-picker-is-told-each-tattoos-state")
def test_placement_stage1_states_name_each_tattoo_placed_on_the_photograph(
    tmp_path: Path,
) -> None:
    _library(tmp_path, "bow")
    _library(tmp_path, "wing")
    _library(tmp_path, "plain")
    save_stage1(tmp_path, "bow", DIGEST, _pairs(6, ONTO_PHOTO), False)
    save_stage1(tmp_path, "wing", DIGEST, [], True)
    save_stage1(tmp_path, "plain", OTHER_DIGEST, _pairs(6, ONTO_PHOTO), False)

    states = stage1_states(tmp_path, DIGEST)

    assert sorted(states) == ["bow", "wing"]
    assert (len(states["bow"].pairs), states["bow"].not_on_photo) == (6, False)
    assert (len(states["wing"].pairs), states["wing"].not_on_photo) == (0, True)
    assert stage1_states(tmp_path, "ffffffffffff") == {}


@pytest.mark.spec("tattoo:stage1:a-cut-takes-no-stage-1-file")
def test_placement_stage1_a_cut_is_refused_saying_its_ink_is_in_the_photograph(
    tmp_path: Path,
) -> None:
    cut(tmp_path, "arm", DIGEST, ARM)

    with pytest.raises(Refusal, match="already in the photograph's pixels"):
        save_stage1(tmp_path, "arm", DIGEST, _pairs(6, ONTO_PHOTO), False)

    assert not (tmp_path / TATTOOS / "arm" / STAGE1).exists()
    assert read_stage1(tmp_path, "arm", DIGEST).pairs == ()


@pytest.mark.spec_exempt("structural: a damaged stage-1 file refuses naming the file")
def test_placement_stage1_a_damaged_file_is_refused_naming_it(tmp_path: Path) -> None:
    _library(tmp_path)
    path = tmp_path / TATTOOS / "bow" / STAGE1 / f"{DIGEST}.json"
    path.parent.mkdir()
    path.write_text("{not json")

    for call in (
        lambda: read_stage1(tmp_path, "bow", DIGEST),
        lambda: stage1_states(tmp_path, DIGEST),
    ):
        with pytest.raises(Refusal, match=rf"bow/stage1/{DIGEST}\.json cannot be read"):
            call()


@pytest.mark.spec_exempt("structural: the mode is read from the kind and the flag")
@pytest.mark.parametrize(
    ("kind", "flag", "mode"),
    [
        ("cut", False, "cut"),
        ("cut", True, "cut"),
        ("image", True, "direct"),
        ("image", False, "two-stage"),
    ],
)
def test_placement_stage1_mode_is_a_cut_a_flagged_upload_or_two_stages(
    kind: tattoos.Kind, flag: bool, mode: str
) -> None:
    assert mode_of(kind, flag) == mode


@pytest.mark.spec("tattoo:placement-preview:a-jpeg-on-the-crop-of-the-targets-points")
def test_placement_preview_stage_one_is_a_jpeg_on_the_crop_of_the_photograph_points(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path)
    pairs = _pairs(6, ONTO_PHOTO)

    made = _ask(tmp_path, files, "photo", pairs)

    shown = _shown(made)
    points = [(b[0], b[1]) for _, b in pairs]
    margin = load_tattoo_config().preview_margin
    left, top, right, bottom = crop_box(points, margin, ARM)
    assert made.box == (left, top, right - left, bottom - top)
    assert shown.format == "JPEG"
    assert shown.size == made.box[2:]
    assert shown.size != ARM
    assert min(x for x, _ in points) - margin <= left + 1
    assert 0 <= made.white <= 255


@pytest.mark.spec("tattoo:placement-preview:the-ink-is-white-where-nothing-lands")
def test_placement_preview_the_ink_is_white_where_nothing_lands_and_dark_on_the_ink(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path)
    stage2 = _pairs(6, ONTO_RENDER, ONTO_PHOTO)

    made = _ask(tmp_path, files, "render", stage2)

    shown = _shown(made)
    landed = (
        CENTRE[0] + ONTO_PHOTO[0] + ONTO_RENDER[0],
        CENTRE[1] + ONTO_PHOTO[1] + ONTO_RENDER[1],
    )
    assert _at(shown, made, *landed) < 128
    assert _at(shown, made, made.box[0] + 2, made.box[1] + 2) > 250
    assert _at(shown, made, landed[0] + 80, landed[1] + 80) > 250


@pytest.mark.spec(
    "tattoo:placement-preview:the-limb-keeps-the-ink-and-an-exclusion-removes-it"
)
def test_placement_preview_the_limb_keeps_the_ink_and_an_exclusion_removes_it(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path)
    stage2 = _pairs(6, ONTO_RENDER, ONTO_PHOTO)
    landed = (245, 180)
    limb = [
        [landed[0] - 5, landed[1] - 30],
        [275, 150],
        [275, 215],
        [landed[0] - 5, 215],
    ]
    hole = [
        [landed[0] + 8, landed[1] - 5],
        [263, landed[1] - 5],
        [263, 190],
        [253, 190],
    ]

    free = _ask(tmp_path, files, "render", stage2)
    kept = _ask(tmp_path, files, "render", stage2, limb=limb, exclusions=[hole])

    shown, whole = _shown(kept), _shown(free)
    assert _at(whole, free, 225, 165) < 128
    assert _at(shown, kept, 225, 165) > 250
    assert _at(shown, kept, 240, 170) < 128
    assert _at(whole, free, 258, 180) < 128
    assert _at(shown, kept, 258, 180) > 250


@pytest.mark.spec("tattoo:placement-preview:a-cut-is-carried-by-one-stage")
def test_placement_preview_a_cut_lands_on_the_render_with_no_stage_one_file(
    tmp_path: Path,
) -> None:
    cut(tmp_path, "arm", DIGEST, ARM)
    save_outline(tmp_path, "arm", _around(34, 24), True, 1.0, True, 1.6)
    files = _files(tmp_path)

    made = _ask(tmp_path, files, "render", _pairs(4, ONTO_RENDER), "arm")

    shown = _shown(made)
    assert (
        _at(shown, made, CENTRE[0] + ONTO_RENDER[0], CENTRE[1] + ONTO_RENDER[1]) < 128
    )
    assert _at(shown, made, made.box[0] + 2, made.box[1] + 2) > 250
    assert not (tmp_path / TATTOOS / "arm" / STAGE1).exists()
    with pytest.raises(Refusal, match="placed on the render alone"):
        _ask(tmp_path, files, "photo", _pairs(4, ONTO_RENDER), "arm")


@pytest.mark.spec(
    "tattoo:placement-preview:a-direct-tattoo-is-carried-by-the-direct-pairs"
)
def test_placement_preview_a_tattoo_not_on_this_photo_lands_by_the_direct_pairs(
    tmp_path: Path,
) -> None:
    _library(tmp_path)
    save_stage1(tmp_path, "bow", DIGEST, [], True)
    files = _files(tmp_path)

    made = _ask(tmp_path, files, "render", _pairs(6, ONTO_RENDER))

    shown = _shown(made)
    assert (
        _at(shown, made, CENTRE[0] + ONTO_RENDER[0], CENTRE[1] + ONTO_RENDER[1]) < 128
    )
    assert _at(shown, made, made.box[0] + 2, made.box[1] + 2) > 250
    with pytest.raises(Refusal, match="placed on the render alone"):
        _ask(tmp_path, files, "photo", _pairs(6, ONTO_PHOTO))


@pytest.mark.spec("tattoo:placement-preview:a-second-stage-needs-its-first")
def test_placement_preview_a_render_stage_is_refused_while_stage_one_is_short(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path, 4)

    with pytest.raises(Refusal, match=r"stage 1 holds 4 pairs .* needs 6"):
        _ask(tmp_path, files, "render", _pairs(6, ONTO_RENDER, ONTO_PHOTO))


@pytest.mark.spec(
    "tattoo:placement-preview:too-few-pairs-a-lone-point-and-a-short-region-are-refused"
)
@pytest.mark.parametrize(
    ("pairs", "match"),
    [
        (_pairs(2, ONTO_PHOTO), "at least 3 pairs and this holds 2"),
        ([*_pairs(3, ONTO_PHOTO), [[3, 4], None]], "pair 4 has a point with no match"),
        ([[None, [3, 4]], *_pairs(3, ONTO_PHOTO)], "pair 1 has a point with no match"),
        ([*_pairs(3, ONTO_PHOTO), [[3, 4]]], "pair 4 is"),
        ("pairs", "list of"),
    ],
)
def test_placement_preview_too_few_pairs_and_a_lone_point_are_refused(
    tmp_path: Path, pairs: object, match: str
) -> None:
    files = _two_stage(tmp_path)

    with pytest.raises(Refusal, match=match):
        _ask(tmp_path, files, "photo", pairs)


@pytest.mark.spec(
    "tattoo:placement-preview:too-few-pairs-a-lone-point-and-a-short-region-are-refused"
)
def test_placement_region_a_short_limb_or_exclusion_is_refused_naming_it(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path)
    floor = load_tattoo_config().region_min
    short = [[10, 10], [20, 10]]
    whole = [[10, 10], [60, 10], [60, 60]]
    pairs = _pairs(3, ONTO_PHOTO)

    with pytest.raises(Refusal, match=rf"limb .*2 points.* at least {floor}"):
        _ask(tmp_path, files, "photo", pairs, limb=short)
    with pytest.raises(Refusal, match=rf"exclusion 2 .*2 points.* at least {floor}"):
        _ask(tmp_path, files, "photo", pairs, exclusions=[whole, short])

    made = _ask(tmp_path, files, "photo", pairs, limb=whole, exclusions=[whole])
    assert made.jpeg


@pytest.mark.spec("tattoo:placement-preview:a-cut-on-another-photograph-is-refused")
def test_placement_preview_a_cut_on_another_photograph_is_refused_naming_its_own(
    tmp_path: Path,
) -> None:
    cut(tmp_path, "arm", DIGEST, ARM)
    save_outline(tmp_path, "arm", _around(34, 24), True, 1.0, True, 1.6)
    files = _files(tmp_path)

    with pytest.raises(Refusal, match=f"cut from photograph {DIGEST}"):
        _ask(
            tmp_path,
            files,
            "render",
            _pairs(4, ONTO_RENDER),
            "arm",
            digest=OTHER_DIGEST,
        )


@pytest.mark.spec("tattoo:placement-preview:the-answer-is-kept-nowhere")
def test_placement_preview_writes_no_file_to_the_library_or_beside_it(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path)
    before = {item: item.read_bytes() for item in tmp_path.rglob("*") if item.is_file()}

    _ask(tmp_path, files, "photo", _pairs(6, ONTO_PHOTO))
    _ask(tmp_path, files, "render", _pairs(6, ONTO_RENDER, ONTO_PHOTO))

    assert {
        item: item.read_bytes() for item in tmp_path.rglob("*") if item.is_file()
    } == before


@pytest.mark.spec_exempt(
    "structural: an open outline, an unknown tattoo and a bad target are refused"
)
def test_placement_preview_an_open_outline_an_unknown_tattoo_and_a_bad_target_refuse(
    tmp_path: Path,
) -> None:
    files = _two_stage(tmp_path)
    pairs = _pairs(6, ONTO_PHOTO)

    with pytest.raises(Refusal, match="ghost"):
        _ask(tmp_path, files, "photo", pairs, "ghost")
    with pytest.raises(Refusal, match="`photo` or `render`"):
        _ask(tmp_path, files, "sky", pairs)
    save_outline(tmp_path, "bow", _around(34, 24), False, 1.0, True, 1.6)
    with pytest.raises(Refusal, match="outline is open"):
        _ask(tmp_path, files, "photo", pairs)


@pytest.mark.spec_exempt("structural: points off the target leave no crop to answer")
def test_placement_preview_points_off_the_target_are_refused(tmp_path: Path) -> None:
    files = _two_stage(tmp_path)
    off = [[[a[0], a[1]], [b[0] + 5000, b[1]]] for a, b in _pairs(6, ONTO_PHOTO)]

    with pytest.raises(Refusal, match="outside the 400x300 target"):
        _ask(tmp_path, files, "photo", off)


@pytest.mark.spec("tattoo:ink-view:a-jpeg-on-the-outlines-crop")
def test_placement_preview_ink_view_is_the_layer_flattened_on_white(
    tmp_path: Path,
) -> None:
    _library(tmp_path)
    outline = tattoos.read_outline(tmp_path, "bow")

    layer = tattoos.ink_layer(
        tmp_path, "bow", None, None, outline.points, 1.0, True, 1.6
    )
    view = tattoos.ink_view(tmp_path, "bow", None, None, outline.points, 1.0, True, 1.6)

    assert layer.image.mode == "RGBA"
    assert (*layer.origin, *layer.image.size) == view.box
    assert layer.white == view.white
