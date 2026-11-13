"""The tattoo library: each tattoo a folder of the library's `.tattoos/`, kept whole.

```
~/isekai/.tattoos/<name>/                an upload
  design.png      the image, upright, no metadata
  tattoo.json     name, kind (image | cut), size, downscaled_from, cut_from, kept
  outline.json    points, closed, white, neutral, depth
  stage1/<digest>.json   pairs, not_on_photo: the tattoo's pairs with one photograph
~/isekai/.tattoos/.cuts/<digest>/<name>/ a cut of that photograph: no design.png
```

A tattoo is one input to many renders in many collections, so it sits beside the
collections and is listed as none of them (D40). A name is resolved by the render's
digest: the uploads and that photograph's cuts are one list. A tattoo is removed and
never renamed. The module takes bytes and paths and imports no other stage; the
surface calls it and writes no file of its own.

Pillow is imported inside the functions that decode, so `python -m isekai`'s import
graph reaches no wheel (D20).
"""

import json
import math
import os
import re
import shutil
import tempfile
import threading
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from isekai.foundation.artifacts import PlacementValues
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import ID_DIGEST_CHARS, REPOSITORY
from isekai.shared.chain import crop_box, flatten, multiply, place, polygon_mask
from isekai.shared.image import dimensions_or_refuse
from isekai.shared.ink import (
    INK_CONFIG_PATH,
    InkConfig,
    extract_ink_grey,
    load_ink_config,
)
from isekai.shared.tattoo import decode_render, png_of

if TYPE_CHECKING:
    from PIL.Image import Image

TATTOOS = ".tattoos"
CUTS = ".cuts"
DESIGN = "design.png"
RECORD = "tattoo.json"
OUTLINE = "outline.json"
STAGE1 = "stage1"
TATTOO_CONFIG = REPOSITORY / "config" / "tattoo.json"
INK_CONFIG = INK_CONFIG_PATH

KEYS = (
    "long_side",
    "outline_min",
    "outline_max",
    "view_quality",
    "floor_stage1",
    "floor_stage2",
    "floor_direct",
    "preview_floor",
    "preview_margin",
    "preview_wait_ms",
    "pair_radius",
    "region_min",
)

# The longest a folder name may be on the filesystems this runs on.
_NAME_BYTES = 255

# A time that sorts as text, to the microsecond.
_TIME = "%Y-%m-%dT%H:%M:%S.%fZ"

# The most a white scale may be: the page's top grey, 255, over the least automatic
# grey the page can scale, 1; a larger scale overflows the float32 skin it multiplies
# and draws solid ink. An automatic grey of 0 (a black fill under a tight outline) is
# not scaled at all: the page says so, and the scale stays 1.
_WHITE_SCALE_MAX = 255.0

_DIGEST = re.compile(f"[0-9a-f]{{{ID_DIGEST_CHARS}}}")

# Held across each change to the library's folders and files, and across the lookup a
# change rests on, so a name is checked and kept, or found and saved to or removed, as
# one step: the server runs routes on threads, and a save must not land in a tattoo a
# removal freed the name of. Re-entrant, for a change that looks a name up.
_LIBRARY = threading.RLock()

Kind = Literal["image", "cut"]
Mode = Literal["cut", "direct", "two-stage"]
Point = tuple[float, float]
Pair = tuple[Point, Point]
Size = tuple[int, int]


@dataclass(frozen=True)
class TattooConfig:
    """The library's bounds: the image, the outline, the view and the placement."""

    long_side: int
    outline_min: int
    outline_max: int
    view_quality: int
    floor_stage1: int
    floor_stage2: int
    floor_direct: int
    preview_floor: int
    preview_margin: int
    preview_wait_ms: int
    pair_radius: int
    region_min: int


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


def _digest_of(digest: object) -> str:
    """Return `digest` as a run digest, or refuse what is none.

    e.g. "0123456789ab" -> "0123456789ab"; "bow", None -> refused
    """
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise Refusal(
            f"{digest!r} is no photograph's digest; it is {ID_DIGEST_CHARS} lowercase "
            "hexadecimal characters, as the render's address shows"
        )
    return digest


def _cut_folder(library: Path, digest: str, name: str) -> Path:
    """Return where the cut `name` of the photograph `digest` is, or would be, kept."""
    return library / TATTOOS / CUTS / digest / name


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


def _library_name(folder: Path) -> str:
    """Return a tattoo folder as the library names it.

    e.g. an upload -> ".tattoos/bow"; a cut -> ".tattoos/.cuts/0123456789ab/arm"
    """
    if (
        folder.parent.parent.name == CUTS
        and folder.parent.parent.parent.name == TATTOOS
    ):
        return f"{TATTOOS}/{CUTS}/{folder.parent.name}/{folder.name}"
    return f"{TATTOOS}/{folder.name}"


def _damaged(path: Path, why: object) -> Refusal:
    """Return the refusal for a file of a tattoo that cannot be read."""
    folder = _library_name(path.parent)
    return Refusal(
        f"{folder}/{path.name} cannot be read ({why}); remove the folder {folder} by "
        "hand and keep the tattoo again"
    )


def _document(path: Path) -> dict[str, Any]:
    """Return the JSON object in `path`, refusing naming the tattoo whose file it is."""
    try:
        document = json.loads(path.read_text())
    except (OSError, ValueError) as unreadable:
        raise _damaged(path, unreadable) from unreadable
    if not isinstance(document, dict):
        raise _damaged(path, "it holds no JSON object")
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
        raise _damaged(path, damaged) from damaged


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
        raise _damaged(path, damaged) from damaged
    return tattoo, outline


def _folders(parent: Path) -> list[Path]:
    """Return the folders of `parent` a name can be, or none when it is absent."""
    if not parent.is_dir():
        return []
    return [
        item
        for item in sorted(parent.iterdir())
        if item.is_dir() and not item.name.startswith(".")
    ]


def _cuts_named(library: Path, name: str) -> list[str]:
    """Return the digests whose folder of cuts holds `name`, in order."""
    return [
        photograph.name
        for photograph in _folders(library / TATTOOS / CUTS)
        if (photograph / name).exists()
    ]


def _settle(library: Path) -> None:
    """Move each cut kept at `.tattoos/<name>/` to `.cuts/<cut_from>/<name>/`.

    A folder with a design, an unreadable record or no digest stays where it is for
    the read that follows to refuse; a destination that exists is left alone.
    """
    with _LIBRARY:
        for item in _folders(library / TATTOOS):
            record = item / RECORD
            if (item / DESIGN).exists() or not record.is_file():
                continue
            try:
                document = json.loads(record.read_text())
            except (OSError, ValueError):
                continue
            digest = document.get("cut_from") if isinstance(document, dict) else None
            if (
                not isinstance(document, dict)
                or document.get("kind") != "cut"
                or not isinstance(digest, str)
                or not _DIGEST.fullmatch(digest)
            ):
                continue
            target = _cut_folder(library, digest, item.name)
            if target.exists():
                continue
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                os.rename(item, target)
            except FileNotFoundError:
                continue
            except OSError as failed:
                raise Refusal(
                    f"{_library_name(item)} cannot move to {_library_name(target)} "
                    f"({failed.strerror}); move the folder there by hand"
                ) from failed


def _cut_loaded(folder: Path, digest: str) -> tuple[Tattoo, Outline]:
    """Return the cut in `folder` and its outline, refusing another digest's."""
    tattoo, outline = _load(folder)
    if tattoo.kind != "cut" or tattoo.cut_from != digest:
        raise _damaged(
            folder / RECORD,
            f"it is a cut of {tattoo.cut_from}, kept under the photograph {digest}",
        )
    return tattoo, outline


def _find(library: Path, name: str, digest: str) -> Path:
    """Return the folder of the tattoo `name` on the render of `digest`, or refuse.

    The upload `.tattoos/<name>/` when it holds a record, else the cut
    `.tattoos/.cuts/<digest>/<name>/`. A cut of another photograph is no tattoo here.
    """
    check_name(name)
    _digest_of(digest)
    _settle(library)
    upload = _folder(library, name)
    if (upload / RECORD).is_file():
        return upload
    own = _cut_folder(library, digest, name)
    if (own / RECORD).is_file():
        _cut_loaded(own, digest)
        return own
    elsewhere = _cuts_named(library, name)
    if elsewhere:
        raise Refusal(
            f"{name} is cut from photograph {elsewhere[0]}, not this render's; open "
            "it on a render of that photograph"
        )
    raise Refusal(
        f"no tattoo named {name!r}; pick one the library lists, or keep it first"
    )


def _load_named(library: Path, name: str, digest: str) -> tuple[Tattoo, Outline]:
    """Return the tattoo `name` and its outline on the render of `digest`, or refuse."""
    return _load(_find(library, name, digest))


def _every(library: Path, digest: str) -> list[tuple[Tattoo, Outline]]:
    """Return each tattoo a render of `digest` lists and its outline, oldest first."""
    _digest_of(digest)
    _settle(library)
    found = [
        _load(item) for item in _folders(library / TATTOOS) if (item / RECORD).is_file()
    ]
    found += [
        _cut_loaded(item, digest)
        for item in _folders(library / TATTOOS / CUTS / digest)
        if (item / RECORD).is_file()
    ]
    return sorted(found, key=lambda pair: (pair[0].kept, pair[0].name))


def listed(library: Path, digest: str) -> list[Tattoo]:
    """Return the uploads and the cuts of `digest`, in the order kept, later last."""
    return [tattoo for tattoo, _ in _every(library, digest)]


def named(library: Path, name: str, digest: str) -> Tattoo:
    """Return the tattoo `name` on a render of `digest`, refusing a bad name."""
    return _load_named(library, name, digest)[0]


def design_bytes(library: Path, name: str, digest: str) -> bytes:
    """Return the bytes of `name`'s `design.png`, refusing a cut, which has none."""
    tattoo, _ = _load_named(library, name, digest)
    if tattoo.kind == "cut":
        raise Refusal(
            f"{name} is cut from a photograph and holds no image of its own; "
            "open it on a render of that photograph"
        )
    path = _find(library, name, digest) / DESIGN
    try:
        return path.read_bytes()
    except OSError as unreadable:
        raise _damaged(path, unreadable) from unreadable


def read_outline(library: Path, name: str, digest: str) -> Outline:
    """Return `name`'s outline, or its kind's defaults when it holds no file."""
    return _load_named(library, name, digest)[1]


def _number(value: object) -> float | None:
    """Return `value` as a finite float, or None when it is no such number."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


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
    digest: str,
    points: Sequence[Sequence[float]],
    closed: bool,
    white: float,
    neutral: bool,
    depth: float,
) -> Outline:
    """Replace `name`'s outline with what the page sent, whole or not at all.

    Refused, naming the value, for a point outside the image, more points than the
    ceiling, a closed outline under the floor, a depth outside the ink config's range
    and a white scale of zero or less or past 255; the file is then as it was. The
    tattoo is found and written to under the library lock, so a save cannot land in a
    folder a removal has freed, or in a replacement kept under the same name.
    """
    with _LIBRARY:
        folder = _find(library, name, digest)
        tattoo, _ = _load(folder)
        config = load_tattoo_config()
        ink = load_ink_config(INK_CONFIG)
        checked = _checked_points(points, tattoo.size, config)
        if not isinstance(closed, bool) or not isinstance(neutral, bool):
            raise Refusal("closed and neutral are true or false; send one of them")
        if closed and len(checked) < config.outline_min:
            raise Refusal(
                f"a closed outline holds at least {config.outline_min} points and "
                f"this one has {len(checked)}; add points before closing it"
            )
        scale, tone = _checked_tone(white, depth, ink)
        outline = Outline(checked, closed, scale, neutral, tone)
        write_atomically(folder / OUTLINE, _json_bytes(asdict(outline)))
        return outline


def _checked_tone(white: object, depth: object, ink: InkConfig) -> tuple[float, float]:
    """Return the white scale and the depth as numbers in range, or refuse the value."""
    scale = _number(white)
    if scale is None or not 0 < scale <= _WHITE_SCALE_MAX:
        raise Refusal(
            f"white scale {white!r} must be above zero and at most "
            f"{_WHITE_SCALE_MAX:g}; 1 is the automatic white point"
        )
    tone = _number(depth)
    if tone is None or not ink.depth_min <= tone <= ink.depth_max:
        raise Refusal(
            f"depth {depth!r} is outside {ink.depth_min:g} to {ink.depth_max:g}; give "
            "a depth in that range"
        )
    return scale, tone


def _stamp(at: datetime | None) -> str:
    """Return `at`, now when None, as a time that sorts as text."""
    return (at or datetime.now(UTC)).astimezone(UTC).strftime(_TIME)


def _publish(parent: Path, name: str, files: Mapping[str, bytes]) -> None:
    """Write `files` into a hidden folder of `parent`, then rename it to `name`.

    A reader sees the whole tattoo or none, and a failure leaves no folder behind.
    """
    parent.mkdir(parents=True, exist_ok=True)
    building = Path(tempfile.mkdtemp(dir=parent, prefix=".keep-"))
    try:
        for file, body in files.items():
            write_atomically(building / file, body)
        try:
            os.rename(building, parent / name)
        except OSError:
            if (parent / name).exists():
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


def _refuse_if_taken(library: Path, name: str) -> None:
    """Refuse `name` when an upload or a cut of any photograph already has it."""
    with _LIBRARY:
        _settle(library)
        if _folder(library, name).exists() or _cuts_named(library, name):
            raise _taken(name)


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
    _refuse_if_taken(library, name)
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
    files = {
        DESIGN: png_of(image),
        RECORD: _json_bytes(record),
        OUTLINE: _json_bytes(asdict(defaults("image"))),
    }
    with _LIBRARY:
        # Checked again: a cut of the name may have been kept while the image decoded.
        _refuse_if_taken(library, name)
        _publish(library / TATTOOS, name, files)
        return _load(_folder(library, name))[0]


def _newest_cut_tone(library: Path, digest: str) -> Outline:
    """Return the tone of the newest cut of `digest` with no points, else the defaults.

    Newest is the later `kept` time, and on a tie the later name.
    """
    cuts = [pair for pair in _every(library, digest) if pair[0].cut_from == digest]
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
    _digest_of(digest)
    with _LIBRARY:
        _settle(library)
        if (
            _folder(library, name).exists()
            or _cut_folder(library, digest, name).exists()
        ):
            raise _taken(name)
        try:
            checked = _size(list(size))
        except ValueError as unsized:
            raise Refusal(
                f"the photograph's size is {size!r}; it is a width and a height in "
                "whole pixels"
            ) from unsized
        tone = _newest_cut_tone(library, digest)
        record = _record_document(name, "cut", checked, _stamp(at), None, digest)
        _publish(
            library / TATTOOS / CUTS / digest,
            name,
            {RECORD: _json_bytes(record), OUTLINE: _json_bytes(asdict(tone))},
        )
        return _load(_cut_folder(library, digest, name))[0]


def remove(library: Path, name: str, digest: str) -> None:
    """Remove the tattoo `name` of the render of `digest`, its folder and all it holds.

    The folder is renamed to a hidden one, then deleted, so a reader sees the whole
    tattoo or none. A cut's photograph folder goes when it is left empty. A bad name,
    a bad digest or an unknown tattoo is refused before anything is touched. Found and
    removed under the library lock. When the rename succeeds and the deletion does
    not, the tattoo is gone and its name free, and the refusal names the hidden folder
    that still holds files, for the operator to delete.
    """
    with _LIBRARY:
        folder = _find(library, name, digest)
        parent = folder.parent
        going = Path(tempfile.mkdtemp(dir=parent, prefix=".removed-"))
        try:
            os.rename(folder, going)
        except OSError as failed:
            going.rmdir()
            raise Refusal(
                f"{_library_name(folder)} cannot be removed ({failed.strerror}); "
                "check the folder's permissions"
            ) from failed
        try:
            shutil.rmtree(going)
        except OSError as failed:
            raise Refusal(
                f"{name} is removed from the library, but {_library_name(going)} "
                f"still holds some of its files ({failed.strerror}); fix that "
                "folder's permissions and delete it"
            ) from failed
        if parent != library / TATTOOS:
            with suppress(OSError):
                parent.rmdir()


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
    digest: str,
) -> "Image":
    """Return the pixels the ink is read from: a cut's photograph, else the design."""
    if tattoo.kind == "cut":
        if photograph is None:
            raise Refusal(
                f"{tattoo.name} is cut from a photograph; ask its ink on a render of "
                "that photograph"
            )
        try:
            body = photograph.read_bytes()
        except OSError as unreadable:
            raise Refusal(
                f"the photograph cannot be read ({unreadable}); reload the page"
            ) from unreadable
    else:
        body = design_bytes(library, tattoo.name, digest)
    image = _upright(body)
    if image.size != tattoo.size:
        (width, height), (was_width, was_height) = image.size, tattoo.size
        raise Refusal(
            f"{tattoo.name}: the photograph is {width}x{height}, the cut was made on "
            f"{was_width}x{was_height}; cut the tattoo again"
        )
    return image


@dataclass(frozen=True)
class InkLayer:
    """The ink's RGBA layer on its crop, the crop's corner `origin` and the grey."""

    image: "Image"
    origin: tuple[int, int]
    white: int


def ink_layer(
    library: Path,
    name: str,
    photograph: Path | None,
    digest: str,
    points: Sequence[Sequence[float]],
    white: float,
    neutral: bool,
    depth: float,
) -> InkLayer:
    """Return `name`'s ink as the Multiply layer on the crop of its outline.

    The crop is the outline's box grown by the extraction's reach; `origin` is its
    corner in the tattoo's pixels, the photograph's for a cut. `photograph` and
    `digest` are the render's, for a cut only; an upload reads its `design.png`.
    Refused for an open outline, an unknown tattoo and a cut asked on another
    photograph. Nothing is written.
    """
    from PIL import Image

    tattoo, outline = _load_named(library, name, digest)
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
    layer, grey = extract_ink_grey(crop, mask, neutral, tone, ink, white=scale)
    return InkLayer(layer.convert("RGBA"), (left, top), grey)


def _jpeg(flat: "Image", quality: int) -> bytes:
    """Return `flat` as a JPEG of `quality`."""
    out = BytesIO()
    flat.save(out, "JPEG", quality=quality)
    return out.getvalue()


def ink_view(
    library: Path,
    name: str,
    photograph: Path | None,
    digest: str,
    points: Sequence[Sequence[float]],
    white: float,
    neutral: bool,
    depth: float,
) -> InkView:
    """Return `name`'s ink on the crop of its outline, as a JPEG flattened on white.

    The values are the page's, so the view follows the sliders before they are saved;
    refusals are `ink_layer`'s. Nothing is written.
    e.g. a closed outline over a 160x160 photograph -> a JPEG of the box it names
    """
    from PIL import Image

    layer = ink_layer(library, name, photograph, digest, points, white, neutral, depth)
    page = Image.new("RGBA", layer.image.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(page, layer.image).convert("RGB")
    width, height = layer.image.size
    return InkView(
        _jpeg(flat, load_tattoo_config().view_quality),
        (*layer.origin, width, height),
        layer.white,
    )


@dataclass(frozen=True)
class Stage1:
    """A tattoo's pairs on one photograph, the tattoo's point first, and its flag."""

    pairs: tuple[Pair, ...]
    not_on_photo: bool


def _stage1_path(library: Path, name: str, digest: str) -> Path:
    """Return where `name`'s stage-1 file on the photograph `digest` is, or would be."""
    return _find(library, name, digest) / STAGE1 / f"{digest}.json"


def _placed_pairs(pairs: object) -> tuple[Pair, ...]:
    """Return `pairs` as pairs of two finite, non-negative points, or refuse the pair.

    e.g. [[[3, 4], [30, 40]]] -> (((3.0, 4.0), (30.0, 40.0)),)
    """
    if not isinstance(pairs, list | tuple):
        raise Refusal("pairs is a list of [[x, y], [x, y]] pairs; send that list")
    checked: list[Pair] = []
    for number, pair in enumerate(pairs, 1):
        sides = pair if isinstance(pair, list | tuple) and len(pair) == 2 else None
        if sides is not None and sum(side is None for side in sides) == 1:
            raise Refusal(
                f"pair {number} has a point with no match; click its other point or "
                "delete it"
            )
        first = None if sides is None else _pair(sides[0])
        second = None if sides is None else _pair(sides[1])
        if first is None or second is None:
            raise Refusal(
                f"pair {number} is {pair!r}; a pair is two points, [[x, y], [x, y]], "
                "each two finite numbers"
            )
        for x, y in (first, second):
            if x < 0 or y < 0:
                raise Refusal(
                    f"pair {number} holds ({x:g}, {y:g}); a coordinate is zero or "
                    "more, so click inside the image"
                )
        checked.append((first, second))
    return tuple(checked)


def read_stage1(library: Path, name: str, digest: str) -> Stage1:
    """Return `name`'s pairs and flag on the photograph `digest`.

    A photograph with no file holds no pairs and the tattoo on the photograph;
    nothing is written.
    """
    path = _stage1_path(library, name, digest)
    if not path.is_file():
        return Stage1((), False)
    return _stage1_of(path)


def _stage1_of(path: Path) -> Stage1:
    """Return the stage-1 file at `path`, or refuse a damaged one naming the file."""
    try:
        document = json.loads(path.read_text())
        flag = document["not_on_photo"]
        if not isinstance(flag, bool):
            raise TypeError("not_on_photo is true or false")
        return Stage1(_placed_pairs(document["pairs"]), flag)
    except (OSError, KeyError, TypeError, ValueError, Refusal) as damaged:
        raise Refusal(
            f"{_library_name(path.parent.parent)}/{STAGE1}/{path.name} cannot be read "
            f"({damaged}); "
            "delete that file and place the tattoo again"
        ) from damaged


def save_stage1(
    library: Path,
    name: str,
    digest: str,
    pairs: object,
    not_on_photo: object,
) -> Stage1:
    """Replace `name`'s pairs and flag on the photograph `digest`, whole or not at all.

    Refused, naming the pair, for a coordinate that is no finite non-negative number
    and a tattoo-side point outside the tattoo's image; refused for a cut, whose ink
    is already in the photograph's pixels. The file is then as it was. The tattoo is
    found and written to under the library lock, as `save_outline`'s is.
    """
    with _LIBRARY:
        tattoo, _ = _load_named(library, name, digest)
        path = _stage1_path(library, name, digest)
        if tattoo.kind == "cut":
            raise Refusal(
                f"{name} is cut from a photograph, so its ink is already in the "
                "photograph's pixels; place it on a render with the pairs of the "
                "photograph and the render"
            )
        if not isinstance(not_on_photo, bool):
            raise Refusal("not_on_photo is true or false; send one of them")
        checked = _placed_pairs(pairs)
        width, height = tattoo.size
        for number, ((x, y), _) in enumerate(checked, 1):
            if x > width or y > height:
                raise Refusal(
                    f"pair {number}'s tattoo point ({x:g}, {y:g}) lies outside the "
                    f"{width}x{height} image; click inside the tattoo"
                )
        state = Stage1(checked, not_on_photo)
        write_atomically(path, _json_bytes(asdict(state)))
        return state


def stage1_states(library: Path, digest: str) -> dict[str, Stage1]:
    """Return each tattoo's pairs and flag on the photograph `digest`, by name.

    A tattoo placed on no such photograph is left out, and so is one whose file is
    damaged: it costs only its own row, and `read_stage1` still refuses it by name.
    """
    states: dict[str, Stage1] = {}
    for tattoo in listed(library, digest):
        path = _stage1_path(library, tattoo.name, digest)
        if path.is_file():
            with suppress(Refusal):
                states[tattoo.name] = _stage1_of(path)
    return states


def mode_of(kind: Kind, not_on_photo: bool) -> Mode:
    """Return how a tattoo is placed: a cut, directly on a render, or in two stages.

    e.g. an upload flagged not on this photo -> "direct"
    """
    if kind == "cut":
        return "cut"
    return "direct" if not_on_photo else "two-stage"


@dataclass(frozen=True)
class Preview:
    """The placement preview: a JPEG of the ink on white, its crop and the grey."""

    jpeg: bytes
    box: tuple[int, int, int, int]
    white: int


def _preview_pairs(pairs: object, floor: int) -> tuple[Pair, ...]:
    """Return the pairs of a stage, refusing a lone point and fewer than `floor`."""
    checked = _placed_pairs(pairs)
    if len(checked) < floor:
        raise Refusal(
            f"a preview needs at least {floor} pairs and this holds {len(checked)}; "
            "click more pairs"
        )
    return checked


def _region(points: object, label: str, floor: int) -> tuple[Point, ...]:
    """Return a region's points, refusing a bad point and fewer than `floor`."""
    if not isinstance(points, list | tuple):
        raise Refusal(f"the {label} is a list of [x, y] points; send that list")
    found: list[Point] = []
    for number, point in enumerate(points, 1):
        pair = _pair(point)
        if pair is None:
            raise Refusal(
                f"the {label}'s point {number} is {point!r}; a point is two numbers, "
                "x and y"
            )
        found.append(pair)
    if len(found) < floor:
        raise Refusal(
            f"the {label} holds {len(found)} points and a region needs at least "
            f"{floor}; draw more points or remove it"
        )
    return tuple(found)


def _regions(
    limb: object, exclusions: object, config: TattooConfig
) -> tuple[tuple[Point, ...] | None, list[tuple[Point, ...]]]:
    """Return the limb, or None for none, and each exclusion, refusing a short one."""
    shape = _region(limb, "limb", config.region_min) if limb else None
    holes = [
        _region(one, f"exclusion {n}", config.region_min)
        for n, one in enumerate(_listed(exclusions), 1)
    ]
    return shape, holes


def _first_stage_held(name: str, held: Stage1, config: TattooConfig) -> None:
    """Refuse a second stage whose first holds fewer pairs than its floor."""
    if len(held.pairs) < config.floor_stage1:
        raise Refusal(
            f"stage 1 holds {len(held.pairs)} pairs and the render stage needs "
            f"{config.floor_stage1}; pair {name} with the photograph first"
        )


def _stages(
    placed: Sequence[Pair], held: Stage1, chained: bool
) -> list[tuple[list[Point], list[Point]]]:
    """Return the stages `place` takes, the one nearest the target first.

    A stage's target side is each pair's second point and its source side the first;
    `chained` adds the tattoo's pairs with the photograph behind the stage's own.
    """
    stages = [([b for _, b in placed], [a for a, _ in placed])]
    if chained:
        stages.append(([b for _, b in held.pairs], [a for a, _ in held.pairs]))
    return stages


def preview(
    library: Path,
    name: str,
    photograph: Path,
    digest: str,
    target_path: Path,
    target: str,
    pairs: object,
    limb: object,
    exclusions: object,
) -> Preview:
    """Return `name`'s warped ink on white, as a JPEG on a crop of the target.

    `target` is `photo` for stage 1 and `render` for every other stage; `pairs` are
    the stage's, `a` the earlier image's point and `b` the target's. The crop is the
    box of the target-side points and the limb, grown by the preview margin. Refused
    for fewer pairs than the preview floor, a lone point, a limb or an exclusion with
    fewer points than the region floor, a second stage whose first is short of its
    floor, a cut on another photograph and an open outline. Nothing is written.
    """
    import numpy as np
    from PIL import Image

    tattoo, outline = _load_named(library, name, digest)
    config = load_tattoo_config()
    held = (
        Stage1((), False)
        if tattoo.kind == "cut"
        else read_stage1(library, name, digest)
    )
    mode = mode_of(tattoo.kind, held.not_on_photo)
    if target not in ("photo", "render"):
        raise Refusal(f"target {target!r} is `photo` or `render`; send one of them")
    if target == "photo" and mode != "two-stage":
        raise Refusal(
            f"{name} is placed on the render alone, with no stage on the "
            "photograph; ask it with the target `render`"
        )
    placed = _preview_pairs(pairs, config.preview_floor)
    shape, holes = _regions(limb, exclusions, config)
    chained = mode == "two-stage" and target == "render"
    if chained:
        _first_stage_held(name, held, config)
    size = dimensions_or_refuse(
        photograph if target == "photo" else target_path,
        "the preview reads the target's own header -- reload the page",
    )
    stages = _stages(placed, held, chained)
    layer = ink_layer(
        library,
        name,
        photograph,
        digest,
        outline.points,
        outline.white,
        outline.neutral,
        outline.depth,
    )
    left, top, right, bottom = crop_box(
        [*stages[0][0], *(shape or ())], config.preview_margin, size
    )
    if right <= left or bottom <= top:
        raise Refusal(
            f"the points lie outside the {size[0]}x{size[1]} target; click inside it"
        )
    box = (left, top, right - left, bottom - top)
    ink = np.asarray(layer.image, dtype=np.float32) / 255.0
    flat = flatten(place(ink, layer.origin, stages, box, shape, holes))
    return Preview(_jpeg(Image.fromarray(flat), config.view_quality), box, layer.white)


@dataclass(frozen=True)
class Composite:
    """A bake's composite as PNG bytes, and the placement values it was made from."""

    png: bytes
    values: PlacementValues


def _lists(pairs: Sequence[Pair]) -> list[list[list[float]]]:
    """Return `pairs` as the lists a record holds, the tattoo's point first."""
    return [[[*first], [*second]] for first, second in pairs]


def composite(
    library: Path,
    name: str,
    photograph: Path,
    digest: str,
    render: Path,
    pairs: object,
    limb: object,
    exclusions: object,
) -> Composite:
    """Return `render` with `name`'s warped ink multiplied on, over its whole grid.

    `render` is the image the bake is placed on and `pairs` are the stage's own, `a`
    the earlier image's point and `b` the render's. `values` is every field of the
    placement but `places_on` and the schema. Refused for fewer pairs than the stage's
    floor, a lone point, a short region, a second stage whose first is short, a cut
    on another photograph, an open outline and a render that cannot be read. Nothing
    is written.
    """
    import numpy as np
    from PIL import Image

    tattoo, outline = _load_named(library, name, digest)
    config = load_tattoo_config()
    held = (
        Stage1((), False)
        if tattoo.kind == "cut"
        else read_stage1(library, name, digest)
    )
    mode = mode_of(tattoo.kind, held.not_on_photo)
    floor = config.floor_direct if mode == "direct" else config.floor_stage2
    placed = _placed_pairs(pairs)
    if len(placed) < floor:
        raise Refusal(
            f"a bake needs at least {floor} pairs on the render and this holds "
            f"{len(placed)}; click more pairs"
        )
    shape, holes = _regions(limb, exclusions, config)
    chained = mode == "two-stage"
    if chained:
        _first_stage_held(name, held, config)
    try:
        body = render.read_bytes()
    except OSError as unreadable:
        raise Refusal(
            f"the render {render.name} cannot be read ({unreadable.strerror}); "
            "reload the page"
        ) from unreadable
    skin = decode_render(body, render.name)
    height, width = skin.shape[:2]
    layer = ink_layer(
        library,
        name,
        photograph,
        digest,
        outline.points,
        outline.white,
        outline.neutral,
        outline.depth,
    )
    ink = np.asarray(layer.image, dtype=np.float32) / 255.0
    over = place(
        ink,
        layer.origin,
        _stages(placed, held, chained),
        (0, 0, width, height),
        shape,
        holes,
    )
    darkened = multiply(skin.astype(np.float64), over)
    kept = Image.fromarray(np.clip(darkened + 0.5, 0.0, 255.0).astype(np.uint8))
    values: PlacementValues = {
        "tattoo": name,
        "kind": tattoo.kind,
        "cut_from": tattoo.cut_from,
        "mode": mode,
        "outline": {
            "points": [[*point] for point in outline.points],
            "white": outline.white,
            "neutral": outline.neutral,
            "depth": outline.depth,
        },
        "stage1": _lists(held.pairs) if chained else None,
        "pairs": _lists(placed),
        "limb": [[*point] for point in shape] if shape else None,
        "exclusions": [[[*point] for point in hole] for hole in holes],
    }
    return Composite(png_of(kept), values)


def _listed(value: object) -> list[object]:
    """Return `value` as a list, refusing what is none."""
    if not isinstance(value, list | tuple):
        raise Refusal("exclusions is a list of regions; send that list")
    return list(value)
