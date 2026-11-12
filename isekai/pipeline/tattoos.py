"""The tattoo library: each tattoo a folder of the library's `.tattoos/`, kept whole.

```
~/isekai/.tattoos/<name>/
  design.png      the image, upright, no metadata; absent for a cut
  tattoo.json     name, kind (image | cut), size, downscaled_from, cut_from, kept
  outline.json    points, closed, white, neutral, depth
```

A tattoo is one input to many renders in many collections, so it sits beside the
collections and is listed as none of them (D40). Nothing here deletes or renames one.
The module takes bytes and paths and imports no other stage; the surface calls it and
writes no file of its own.

Pillow is imported inside the functions that decode, so `python -m isekai`'s import
graph reaches no wheel (D20).
"""

import json
import math
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import ID_DIGEST_CHARS, REPOSITORY
from isekai.shared.chain import crop_box, polygon_mask
from isekai.shared.ink import (
    INK_CONFIG_PATH,
    InkConfig,
    extract_ink,
    load_ink_config,
    white_grey,
)
from isekai.shared.tattoo import png_of

if TYPE_CHECKING:
    from PIL.Image import Image

TATTOOS = ".tattoos"
DESIGN = "design.png"
RECORD = "tattoo.json"
OUTLINE = "outline.json"
TATTOO_CONFIG = REPOSITORY / "config" / "tattoo.json"
INK_CONFIG = INK_CONFIG_PATH

KEYS = ("long_side", "outline_min", "outline_max", "view_quality")

# The longest a folder name may be on the filesystems this runs on.
_NAME_BYTES = 255

# A time that sorts as text, to the microsecond.
_TIME = "%Y-%m-%dT%H:%M:%S.%fZ"

_DIGEST = re.compile(f"[0-9a-f]{{{ID_DIGEST_CHARS}}}")

Kind = Literal["image", "cut"]
Point = tuple[float, float]
Size = tuple[int, int]


@dataclass(frozen=True)
class TattooConfig:
    """The library's bounds: the image's long side, the outline's points, the view."""

    long_side: int
    outline_min: int
    outline_max: int
    view_quality: int


@dataclass(frozen=True)
class Outline:
    """A tattoo's outline and its ink tone.

    `points` are in the image's pixels, the photograph's for a cut; `white` is a
    scale on the automatic white point, 1.0 being the automatic point itself.
    """

    points: tuple[Point, ...]
    closed: bool
    white: float
    neutral: bool
    depth: float


@dataclass(frozen=True)
class Tattoo:
    """One kept tattoo: its name, kind and size, and whether its outline is closed.

    A cut has no image; `cut_from` is the digest of its photograph. `downscaled_from`
    is the size an upload came with when it was scaled down to the long side.
    """

    name: str
    kind: Kind
    size: Size
    kept: str
    outlined: bool
    downscaled_from: Size | None = None
    cut_from: str | None = None


def _whole(path: Path, document: Mapping[str, object], key: str) -> int:
    """Return `key` of `document` as a whole number of at least 1, or refuse it."""
    value = document[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise Refusal(
            f"{path.name}: `{key}` declares {value!r}; it is a whole number, at "
            "least 1, so write one"
        )
    return value


def load_tattoo_config(path: Path = TATTOO_CONFIG) -> TattooConfig:
    """Return the tattoo config, refusing naming the key or the file that is wrong."""
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
    numbers = {key: _whole(path, document, key) for key in KEYS}
    if numbers["outline_min"] > numbers["outline_max"]:
        raise Refusal(
            f"{path.name}: `outline_min` is {numbers['outline_min']}, above "
            f"`outline_max` {numbers['outline_max']}; keep the floor at or below "
            "the ceiling"
        )
    if numbers["view_quality"] > 100:
        raise Refusal(
            f"{path.name}: `view_quality` is {numbers['view_quality']}; a JPEG "
            "quality is 1 to 100"
        )
    return TattooConfig(**numbers)


def check_name(name: str) -> None:
    """Refuse a name that is not a folder name, naming the fix.

    e.g. "bow" -> None; ".hidden", "a/b", "" -> refused
    """
    if not isinstance(name, str) or not name.strip():
        reason = "is empty"
    elif name.startswith("."):
        reason = "starts with a dot"
    elif any(separator in name for separator in ("/", "\\", "\0")):
        reason = "holds a separator or a NUL"
    elif len(name.encode()) > _NAME_BYTES:
        reason = f"is longer than {_NAME_BYTES} bytes"
    else:
        return
    raise Refusal(f"{name!r} is not a folder name: it {reason}; choose another name")


def _taken(name: str) -> Refusal:
    """Return the refusal for a name a kept tattoo has."""
    return Refusal(f"{name} is kept; choose another name")


def _folder(library: Path, name: str) -> Path:
    """Return the folder `name` is, or would be, kept in."""
    return library / TATTOOS / name


def defaults(kind: Kind) -> Outline:
    """Return the outline a new tattoo of `kind` starts with: no points, its tone.

    e.g. an upload -> neutral off at `image_depth`; a cut -> neutral on at `photo_depth`
    """
    ink = load_ink_config(INK_CONFIG)
    is_cut = kind == "cut"
    return Outline(
        points=(),
        closed=False,
        white=1.0,
        neutral=is_cut,
        depth=ink.photo_depth if is_cut else ink.image_depth,
    )


def _damaged(path: Path, library_name: str, why: object) -> Refusal:
    """Return the refusal for a file of a tattoo that cannot be read."""
    return Refusal(
        f"{TATTOOS}/{library_name}/{path.name} cannot be read ({why}); remove the "
        f"folder {TATTOOS}/{library_name} by hand and keep the tattoo again"
    )


def _document(path: Path) -> dict[str, Any]:
    """Return the JSON object in `path`, refusing naming the tattoo whose file it is."""
    try:
        document = json.loads(path.read_text())
    except (OSError, ValueError) as unreadable:
        raise _damaged(path, path.parent.name, unreadable) from unreadable
    if not isinstance(document, dict):
        raise _damaged(path, path.parent.name, "it holds no JSON object")
    return document


def _side(value: object) -> int:
    """Return `value` as a whole number of at least 1, or raise `ValueError`."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"side {value!r}")
    return value


def _size(value: object) -> Size:
    """Return `value` as a width and height of at least 1, or raise `ValueError`."""
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"size {value!r}")
    return _side(value[0]), _side(value[1])


def _outline_of(folder: Path, kind: Kind) -> Outline:
    """Return the outline in `folder`, or its kind's defaults when there is no file."""
    path = folder / OUTLINE
    if not path.is_file():
        return defaults(kind)
    document = _document(path)
    try:
        closed, neutral = document["closed"], document["neutral"]
        if not isinstance(closed, bool) or not isinstance(neutral, bool):
            raise TypeError("closed and neutral are true or false")
        return Outline(
            points=tuple((float(x), float(y)) for x, y in document["points"]),
            closed=closed,
            white=float(document["white"]),
            neutral=neutral,
            depth=float(document["depth"]),
        )
    except (KeyError, TypeError, ValueError) as damaged:
        raise _damaged(path, folder.name, damaged) from damaged


def _load(folder: Path) -> tuple[Tattoo, Outline]:
    """Return the tattoo in `folder` and its outline, or refuse a damaged record."""
    path = folder / RECORD
    document = _document(path)
    try:
        kind = document["kind"]
        if kind not in ("image", "cut"):
            raise ValueError(f"kind {kind!r}")
        cut_from = document["cut_from"]
        if cut_from is not None and not isinstance(cut_from, str):
            raise TypeError("cut_from is a digest or null")
        scaled = document["downscaled_from"]
        outline = _outline_of(folder, kind)
        tattoo = Tattoo(
            name=folder.name,
            kind=kind,
            size=_size(document["size"]),
            kept=str(document["kept"]),
            outlined=outline.closed,
            downscaled_from=None if scaled is None else _size(scaled),
            cut_from=cut_from,
        )
    except (KeyError, TypeError, ValueError) as damaged:
        raise _damaged(path, folder.name, damaged) from damaged
    return tattoo, outline


def _load_named(library: Path, name: str) -> tuple[Tattoo, Outline]:
    """Return the tattoo `name` and its outline, or refuse an unknown name."""
    check_name(name)
    folder = _folder(library, name)
    if not (folder / RECORD).is_file():
        raise Refusal(
            f"no tattoo named {name!r}; pick one the library lists, or keep it first"
        )
    return _load(folder)


def _every(library: Path) -> list[tuple[Tattoo, Outline]]:
    """Return each kept tattoo and its outline, in the order kept."""
    root = library / TATTOOS
    if not root.is_dir():
        return []
    found = [
        _load(item)
        for item in root.iterdir()
        if item.is_dir() and not item.name.startswith(".") and (item / RECORD).is_file()
    ]
    return sorted(found, key=lambda pair: (pair[0].kept, pair[0].name))


def listed(library: Path) -> list[Tattoo]:
    """Return each kept tattoo, in the order kept, the later name first on a tie."""
    return [tattoo for tattoo, _ in _every(library)]


def named(library: Path, name: str) -> Tattoo:
    """Return the tattoo `name`, refusing a name that is bad or unknown."""
    return _load_named(library, name)[0]


def design_bytes(library: Path, name: str) -> bytes:
    """Return the bytes of `name`'s `design.png`, refusing a cut, which has none."""
    tattoo, _ = _load_named(library, name)
    if tattoo.kind == "cut":
        raise Refusal(
            f"{name} is cut from a photograph and holds no image of its own; "
            "open it on a render of that photograph"
        )
    path = _folder(library, name) / DESIGN
    try:
        return path.read_bytes()
    except OSError as unreadable:
        raise _damaged(path, name, unreadable) from unreadable


def read_outline(library: Path, name: str) -> Outline:
    """Return `name`'s outline, or its kind's defaults when it holds no file."""
    return _load_named(library, name)[1]


def _number(value: object) -> float | None:
    """Return `value` as a finite float, or None when it is no such number."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def _pair(point: object) -> Point | None:
    """Return `point` as two finite numbers, or None when it is not that."""
    if not isinstance(point, list | tuple) or len(point) != 2:
        return None
    x, y = _number(point[0]), _number(point[1])
    return None if x is None or y is None else (x, y)


def _checked_points(
    points: object, size: Size, config: TattooConfig
) -> tuple[Point, ...]:
    """Return `points` as pairs inside `size` and within the ceiling, or refuse."""
    width, height = size
    if not isinstance(points, list | tuple):
        raise Refusal(
            "points is a list of [x, y] pairs in the image's pixels; send that list"
        )
    pairs: list[Point] = []
    for index, point in enumerate(points, 1):
        pair = _pair(point)
        if pair is None:
            raise Refusal(
                f"point {index} is {point!r}; a point is two numbers, x and y in the "
                "image's pixels"
            )
        x, y = pair
        if not (0 <= x <= width and 0 <= y <= height):
            raise Refusal(
                f"point {index} ({x:g}, {y:g}) lies outside the {width}x{height} "
                "image; click inside the image"
            )
        pairs.append(pair)
    if len(pairs) > config.outline_max:
        raise Refusal(
            f"an outline holds at most {config.outline_max} points and this one has "
            f"{len(pairs)}; remove points"
        )
    return tuple(pairs)


def save_outline(
    library: Path,
    name: str,
    points: Sequence[Sequence[float]],
    closed: bool,
    white: float,
    neutral: bool,
    depth: float,
) -> Outline:
    """Replace `name`'s outline with what the page sent, whole or not at all.

    Refused, naming the value, for a point outside the image, more points than the
    ceiling, a closed outline under the floor, a depth outside the ink config's range
    and a white scale of zero or less; the file is then as it was.
    """
    tattoo, _ = _load_named(library, name)
    config = load_tattoo_config()
    ink = load_ink_config(INK_CONFIG)
    checked = _checked_points(points, tattoo.size, config)
    if not isinstance(closed, bool) or not isinstance(neutral, bool):
        raise Refusal("closed and neutral are true or false; send one of them")
    if closed and len(checked) < config.outline_min:
        raise Refusal(
            f"a closed outline holds at least {config.outline_min} points and this "
            f"one has {len(checked)}; add points before closing it"
        )
    scale, tone = _checked_tone(white, depth, ink)
    outline = Outline(checked, closed, scale, neutral, tone)
    write_atomically(
        _folder(library, name) / OUTLINE, _json_bytes(_outline_document(outline))
    )
    return outline


def _checked_tone(white: object, depth: object, ink: InkConfig) -> tuple[float, float]:
    """Return the white scale and the depth as numbers in range, or refuse the value."""
    scale = _number(white)
    if scale is None or scale <= 0:
        raise Refusal(
            f"white scale {white!r} must be above zero; 1 is the automatic white point"
        )
    tone = _number(depth)
    if tone is None or not ink.depth_min <= tone <= ink.depth_max:
        raise Refusal(
            f"depth {depth!r} is outside {ink.depth_min:g} to {ink.depth_max:g}; give "
            "a depth in that range"
        )
    return scale, tone


def _outline_document(outline: Outline) -> dict[str, Any]:
    """Return `outline` as the document `outline.json` holds."""
    return {
        "points": [list(point) for point in outline.points],
        "closed": outline.closed,
        "white": outline.white,
        "neutral": outline.neutral,
        "depth": outline.depth,
    }


def _stamp(at: datetime | None) -> str:
    """Return `at`, now when None, as a time that sorts as text."""
    return (at or datetime.now(UTC)).astimezone(UTC).strftime(_TIME)


def _publish(library: Path, name: str, files: Mapping[str, bytes]) -> None:
    """Write `files` into a hidden folder, then rename it to `name` in one step.

    A reader sees the whole tattoo or none, and a failure leaves no folder behind.
    """
    root = library / TATTOOS
    root.mkdir(parents=True, exist_ok=True)
    building = Path(tempfile.mkdtemp(dir=root, prefix=".keep-"))
    try:
        for file, body in files.items():
            write_atomically(building / file, body)
        try:
            os.rename(building, root / name)
        except OSError:
            if (root / name).exists():
                raise _taken(name) from None
            raise
    except BaseException:
        shutil.rmtree(building, ignore_errors=True)
        raise


def _json_bytes(document: Mapping[str, Any]) -> bytes:
    """Return `document` in the one JSON form the library writes."""
    return (json.dumps(document, indent=2) + "\n").encode()


def _record_document(
    name: str,
    kind: Kind,
    size: Size,
    kept: str,
    downscaled_from: Size | None,
    cut_from: str | None,
) -> dict[str, Any]:
    """Return the document `tattoo.json` holds."""
    return {
        "name": name,
        "kind": kind,
        "size": list(size),
        "downscaled_from": None if downscaled_from is None else list(downscaled_from),
        "cut_from": cut_from,
        "kept": kept,
    }


def _upright(body: bytes) -> "Image":
    """Return the pixels in `body` turned upright, with no metadata, or refuse."""
    from PIL import Image, ImageOps

    try:
        with Image.open(BytesIO(body)) as opened:
            turned = ImageOps.exif_transpose(opened)
            alpha = turned.mode in ("RGBA", "LA", "PA") or "transparency" in turned.info
            flat = turned.convert("RGBA" if alpha else "RGB")
            return Image.frombytes(flat.mode, flat.size, flat.tobytes())
    except (OSError, Image.DecompressionBombError) as unreadable:
        raise Refusal(
            f"the file cannot be read as an image ({unreadable}); add it again as a "
            "PNG or JPEG"
        ) from unreadable


def keep(
    library: Path, name: str, body: bytes, *, at: datetime | None = None
) -> Tattoo:
    """Keep the image in `body` as the tattoo `name`: upright, bounded, no metadata.

    `body` is a staged file, cleaned to its pixels and orientation. A long side past
    `long_side` is scaled down with its aspect held, and the record says what the
    image came with. The default outline is written beside it.
    e.g. a 5000x3000 upload -> a 4096x2458 `design.png`, `downscaled_from` 5000x3000
    """
    from PIL import Image

    check_name(name)
    if _folder(library, name).exists():
        raise _taken(name)
    image = _upright(body)
    came_with = image.size
    long_side = load_tattoo_config().long_side
    scaled_from = None
    if max(came_with) > long_side:
        factor = long_side / max(came_with)
        image = image.resize(
            (
                max(1, round(came_with[0] * factor)),
                max(1, round(came_with[1] * factor)),
            ),
            Image.Resampling.LANCZOS,
        )
        scaled_from = came_with
    stamp = _stamp(at)
    record = _record_document(name, "image", image.size, stamp, scaled_from, None)
    _publish(
        library,
        name,
        {
            DESIGN: png_of(image),
            RECORD: _json_bytes(record),
            OUTLINE: _json_bytes(_outline_document(defaults("image"))),
        },
    )
    return _load(_folder(library, name))[0]


def _newest_cut_tone(library: Path, digest: str) -> Outline:
    """Return the tone of the newest cut of `digest` with no points, else the defaults.

    Newest is the later `kept` time, and on a tie the later name.
    """
    cuts = [pair for pair in _every(library) if pair[0].cut_from == digest]
    if not cuts:
        return defaults("cut")
    return replace(cuts[-1][1], points=(), closed=False)


def cut(
    library: Path, name: str, digest: str, size: Size, *, at: datetime | None = None
) -> Tattoo:
    """Keep a cut named `name`: a tattoo with no image, in the photograph's pixels.

    `digest` is the twelve-character run digest the URLs carry, and `size` the
    photograph's. The tone starts from the newest cut of that photograph.
    """
    check_name(name)
    if _folder(library, name).exists():
        raise _taken(name)
    if not _DIGEST.fullmatch(digest):
        raise Refusal(
            f"{digest!r} is no photograph's digest; it is {ID_DIGEST_CHARS} lowercase "
            "hexadecimal characters, as the render's address shows"
        )
    try:
        checked = _size(list(size))
    except ValueError as unsized:
        raise Refusal(
            f"the photograph's size is {size!r}; it is a width and a height in whole "
            "pixels"
        ) from unsized
    tone = _newest_cut_tone(library, digest)
    record = _record_document(name, "cut", checked, _stamp(at), None, digest)
    _publish(
        library,
        name,
        {RECORD: _json_bytes(record), OUTLINE: _json_bytes(_outline_document(tone))},
    )
    return _load(_folder(library, name))[0]


@dataclass(frozen=True)
class InkView:
    """The ink view: a JPEG, its crop `(x, y, width, height)` and the automatic grey."""

    jpeg: bytes
    box: tuple[int, int, int, int]
    white: int


def _view_image(
    library: Path,
    tattoo: Tattoo,
    photograph: Path | None,
    digest: str | None,
) -> "Image":
    """Return the pixels the ink is read from: a cut's photograph, else the design."""
    if tattoo.kind == "cut":
        if photograph is None or digest is None:
            raise Refusal(
                f"{tattoo.name} is cut from a photograph; ask its ink on a render of "
                "that photograph"
            )
        if tattoo.cut_from != digest:
            raise Refusal(
                f"{tattoo.name} is cut from another photograph than this render's; "
                "open it on a render of its own photograph"
            )
        try:
            body = photograph.read_bytes()
        except OSError as unreadable:
            raise Refusal(
                f"the photograph cannot be read ({unreadable}); reload the page"
            ) from unreadable
    else:
        body = design_bytes(library, tattoo.name)
    image = _upright(body)
    if image.size != tattoo.size:
        (width, height), (was_width, was_height) = image.size, tattoo.size
        raise Refusal(
            f"{tattoo.name}: the photograph is {width}x{height}, the cut was made on "
            f"{was_width}x{was_height}; cut the tattoo again"
        )
    return image


def ink_view(
    library: Path,
    name: str,
    photograph: Path | None,
    digest: str | None,
    points: Sequence[Sequence[float]],
    white: float,
    neutral: bool,
    depth: float,
) -> InkView:
    """Return `name`'s ink on the crop of its outline, as a JPEG flattened on white.

    The crop is the outline's box grown by the extraction's reach. `photograph` and
    `digest` are the render's, for a cut only; an upload reads its `design.png`.
    Refused for an open outline, an unknown tattoo and a cut asked on another
    photograph. Nothing is written.
    e.g. a closed outline over a 160x160 photograph -> a JPEG of the box it names
    """
    from PIL import Image

    tattoo, outline = _load_named(library, name)
    config = load_tattoo_config()
    ink = load_ink_config(INK_CONFIG)
    image = _view_image(library, tattoo, photograph, digest)
    checked = _checked_points(points, tattoo.size, config)
    if not outline.closed:
        raise Refusal(
            f"the outline is open; {name}'s ink is read inside a closed outline, so "
            "close it on its first point"
        )
    if len(checked) < config.outline_min:
        raise Refusal(
            f"the outline is open; it holds {len(checked)} points and a closed one "
            f"holds at least {config.outline_min}"
        )
    if not isinstance(neutral, bool):
        raise Refusal("neutral is true or false; send one of them")
    scale, tone = _checked_tone(white, depth, ink)

    left, top, right, bottom = crop_box(checked, ink.reach, image.size)
    crop = image.crop((left, top, right, bottom))
    inside = polygon_mask([(x - left, y - top) for x, y in checked], crop.size)
    mask = Image.fromarray(inside)
    layer = extract_ink(crop, mask, neutral, tone, ink, white=scale)
    grey = white_grey(crop, mask, ink)

    page = Image.new("RGBA", layer.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(page, layer.convert("RGBA")).convert("RGB")
    out = BytesIO()
    flat.save(out, "JPEG", quality=config.view_quality)
    return InkView(out.getvalue(), (left, top, right - left, bottom - top), grey)
