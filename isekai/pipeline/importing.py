"""How a file becomes a source: read, cleaned, verified, and committed into a batch.

A file is read into a staging folder under the library's `.staging/`, cleaned of
everything but its pixels and orientation, and verified by the strip's own walk.
A commit moves the staged files into the batch's `sources/`; a cancel, or a sweep
at start, deletes what was staged. Why each step is this way: 0062 design D1-D3.

Pillow and `pi_heif` are imported inside the functions that decode, so
`python -m isekai`'s import graph reaches no wheel (D20).
"""

import json
import os
import secrets
import shutil
import struct
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REPOSITORY
from isekai.shared.image import metadata_in, photo_resolution, strip_metadata

if TYPE_CHECKING:
    from PIL.Image import Image

UI_CONFIG = REPOSITORY / "config" / "ui.json"
STAGING = ".staging"
SOURCES = "sources"

# The quality a re-encoded JPEG is written at.
JPEG_QUALITY = 95

# A build folder inside a staging folder, named so no staged file can take it:
# a staged name never starts with a dot.
_BUILD = ".batch"

_MB = 1024 * 1024

# How far into a file the RAW signatures are looked for.
_SIGNATURE_BYTES = 64 * 1024

State = Literal["ready", "converted", "not cleaned", "skipped"]


@dataclass(frozen=True)
class Staged:
    """What reading one file left in staging, and what it still carries."""

    name: str
    state: State
    carries: tuple[str, ...] = ()


@dataclass(frozen=True)
class Committed:
    """What a commit wrote into the batch, skipped as a source's bytes, and left out."""

    batch: Path
    written: tuple[str, ...]
    skipped: tuple[str, ...]
    left_out: tuple[str, ...]


def upload_limit(config: Path = UI_CONFIG) -> int:
    """Return the largest file import reads, in bytes, from the UI's configuration."""
    return int(json.loads(config.read_text())["upload_limit_mb"]) * _MB


def stage(library: Path) -> Path:
    """Return a new, empty staging folder under `library`'s `.staging/`."""
    folder = library / STAGING / secrets.token_hex(8)
    folder.mkdir(parents=True)
    return folder


def read(file: Path, staging: Path, limit: int) -> Staged:
    """Clean `file` into `staging` and return what was staged, or refuse it by name.

    A file whose cleaned bytes are already staged is skipped; a staged name that
    is taken by other bytes becomes `<stem>-2`.
    """
    name = file.name
    if not name or name.startswith(".") or "/" in name:
        raise Refusal(f"{name!r}: not a file name import takes; rename it and add it")
    try:
        size = file.stat().st_size
        if size > limit:
            raise Refusal(
                f"{name}: {-(-size // _MB)} MB is past the {limit // _MB} MB limit "
                "`config/ui.json` sets; export a smaller copy and add it again"
            )
        with file.open("rb") as handle:
            _refuse_raw(name, handle.read(_SIGNATURE_BYTES))
    except OSError as unreadable:
        raise Refusal(
            f"{name}: cannot be read ({unreadable.strerror}); check the path and "
            "add it again"
        ) from unreadable
    body, converted = _clean(file)
    suffix = _suffix(body) if converted else Path(name).suffix
    target = _free_name(staging, Path(name).stem, suffix, body)
    if target is None:
        return Staged(name, "skipped")
    try:
        write_atomically(target, body)
        carries = verify(target)
        if carries:
            write_atomically(target, _reencode(body))
            converted = True
            carries = verify(target)
    except Refusal:
        target.unlink(missing_ok=True)
        raise
    if carries:
        return Staged(target.name, "not cleaned", tuple(carries))
    return Staged(target.name, "converted" if converted else "ready")


def verify(path: Path) -> list[str]:
    """Return what the file at `path` still carries beyond its pixels and orientation.

    Refuses a file that does not decode or that render's header check refuses.
    e.g. a camera JPEG -> ["EXIF", "XMP"]; a cleaned one -> []
    """
    _decode(path)
    photo_resolution(path)
    return metadata_in(path.read_bytes())


def commit(
    staging: Path,
    library: Path,
    name: str,
    as_is: Iterable[str] = (),
    *,
    add: bool = False,
) -> Committed:
    """Move every staged file that passes `verify` into `<library>/<name>/sources/`.

    A new batch appears in one rename. With `add`, the files join the batch that
    is there. A file that fails `verify` is left out unless named in `as_is`. The
    staging folder is deleted once the files are in; on a refusal it is kept.
    """
    batch = library / name
    _refuse_batch_name(name, batch, add=add)
    chosen = set(as_is)
    staged = sorted(path for path in staging.iterdir() if not path.name.startswith("."))
    left_out = tuple(p.name for p in staged if p.name not in chosen and verify(p))
    taking = [path for path in staged if path.name not in left_out]
    if add:
        written, skipped = _add(taking, batch / SOURCES)
    else:
        if not taking:
            raise Refusal(
                f"{name}: no staged file is ready to import; add a photograph, "
                "or import one that is not cleaned as it is"
            )
        build = staging / _BUILD / SOURCES
        build.mkdir(parents=True)
        for path in taking:
            path.rename(build / path.name)
        os.rename(build.parent, batch)
        written, skipped = tuple(path.name for path in taking), ()
    cancel(staging)
    return Committed(batch, written, skipped, left_out)


def cancel(staging: Path) -> None:
    """Delete a staging folder and everything read into it."""
    shutil.rmtree(staging, ignore_errors=True)
    _drop_empty(staging.parent)


def _drop_empty(root: Path) -> None:
    """Remove `.staging/` once no staging folder is left in it."""
    try:
        root.rmdir()
    except OSError:
        pass


def sweep(library: Path) -> None:
    """Delete every staging folder left in `library` by an import that did not end."""
    shutil.rmtree(library / STAGING, ignore_errors=True)


def _refuse_batch_name(name: str, batch: Path, *, add: bool) -> None:
    """Refuse a batch name that is empty, holds `/`, starts with a dot, or is taken."""
    if not name or "/" in name or name.startswith("."):
        raise Refusal(
            f"{name!r}: not a batch name; give a name with no `/` that does not "
            "start with a dot"
        )
    if add and not (batch / SOURCES).is_dir():
        raise Refusal(f"{name}: no batch of that name to add to; name one that is")
    if not add and batch.exists():
        raise Refusal(f"{name}: a folder of that name is in the library; pick another")


def _add(taking: list[Path], sources: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Move `taking` into an existing `sources/`; return what was written, skipped."""
    written: list[str] = []
    skipped: list[str] = []
    for path in taking:
        body = path.read_bytes()
        target = _free_name(sources, path.stem, path.suffix, body)
        if target is None:
            skipped.append(path.name)
            continue
        path.rename(target)
        written.append(target.name)
    return tuple(written), tuple(skipped)


def _free_name(folder: Path, stem: str, suffix: str, body: bytes) -> Path | None:
    """Return where `body` goes in `folder`, or None when a file there holds it.

    Bytes, not names, decide sameness: a taken name gets `-2`, then `-3`.
    e.g. `portrait.jpg` taken by other bytes -> `portrait-2.jpg`
    """
    if folder.is_dir():
        for present in folder.iterdir():
            if present.is_file() and present.read_bytes() == body:
                return None
    target = folder / f"{stem}{suffix}"
    count = 1
    while target.exists():
        count += 1
        target = folder / f"{stem}-{count}{suffix}"
    return target


# RAW formats, by what their first bytes hold. Each but CR2 is a TIFF, told apart
# by a tag in its first directory: DNG by its version tag, NEF and ARW by Make.
_DNG_VERSION_TAG = 0xC612
_MAKE_TAG = 0x010F
_RAW_MAKES = ((b"NIKON", "NEF"), (b"SONY", "ARW"))


def _refuse_raw(name: str, head: bytes) -> None:
    """Refuse a RAW photograph by its signature, naming the fix of exporting it."""
    kind = _raw_kind(head)
    if kind is not None:
        raise Refusal(
            f"{name}: a {kind} RAW photograph, which import does not develop; "
            "export it as JPEG and add it again"
        )


def _raw_kind(head: bytes) -> str | None:
    """Return the RAW format `head` opens, or None. e.g. a Canon CR2 -> "CR2"."""
    order = {b"II*\x00": "<", b"MM\x00*": ">"}.get(head[:4])
    if order is None:
        return None
    if head[8:10] == b"CR":
        return "CR2"
    try:
        (offset,) = struct.unpack(f"{order}I", head[4:8])
        (count,) = struct.unpack(f"{order}H", head[offset : offset + 2])
        for index in range(count):
            at = offset + 2 + index * 12
            tag, kind, length, value = struct.unpack(f"{order}HHII", head[at : at + 12])
            if tag == _DNG_VERSION_TAG:
                return "DNG"
            if tag == _MAKE_TAG and kind == 2:
                make = head[value : value + length] if length > 4 else head[at + 8 :]
                for prefix, raw in _RAW_MAKES:
                    if make.upper().startswith(prefix):
                        return raw
    except struct.error:
        return None
    return None


def _decode(source: Path | bytes) -> "Image":
    """Return the one image a file holds, decoded, or refuse it by name."""
    import io

    import pi_heif
    from PIL import Image, UnidentifiedImageError
    from PIL.Image import DecompressionBombError

    pi_heif.register_heif_opener()
    name = source.name if isinstance(source, Path) else "the cleaned file"
    try:
        image = Image.open(source if isinstance(source, Path) else io.BytesIO(source))
        # A JPEG's MPF images are a gain map or a depth map behind the photograph,
        # and the strip drops them; any other second frame is a second picture.
        if image.format != "MPO" and getattr(image, "n_frames", 1) > 1:
            raise Refusal(
                f"{name}: holds more than one image; export the one you want as "
                "JPEG and add it again"
            )
        image.load()
    except (
        UnidentifiedImageError,
        DecompressionBombError,
        OSError,
        SyntaxError,
        ValueError,
    ) as broken:
        raise Refusal(
            f"{name}: does not decode as an image ({broken}); export it as JPEG "
            "and add it again"
        ) from broken
    return image


def _clean(file: Path) -> tuple[bytes, bool]:
    """Return `file`'s cleaned bytes, and whether they were encoded again.

    A JPEG or PNG in sRGB or with no profile is stripped byte for byte; any other,
    and one the strip cannot walk, is decoded, turned upright, brought to sRGB
    and encoded again.
    """
    image = _decode(file)
    if image.format in ("JPEG", "MPO", "PNG") and _is_srgb(image):
        try:
            return strip_metadata(file), False
        except Refusal:
            pass
    return _encode(image, png=image.format == "PNG"), True


def _suffix(body: bytes) -> str:
    """Return the suffix encoded bytes are named with: `.png` or `.jpg`."""
    return ".png" if body.startswith(b"\x89PNG") else ".jpg"


def _reencode(body: bytes) -> bytes:
    """Return `body` encoded again from its decoded pixels, in its own format."""
    image = _decode(body)
    return _encode(image, png=image.format == "PNG")


def _encode(image: "Image", *, png: bool) -> bytes:
    """Return `image` upright, in sRGB, as PNG when asked or transparent, else JPEG."""
    import io

    from PIL import ImageCms, ImageOps

    upright = ImageOps.exif_transpose(image)
    transparent = _is_transparent(upright)
    profile = image.info.get("icc_profile")
    mode = "RGBA" if transparent else "RGB"
    if profile and not _is_srgb(image):
        if upright.mode not in ("RGB", "RGBA", "CMYK", "L"):
            upright = upright.convert(mode)
        try:
            converted = ImageCms.profileToProfile(
                upright,
                ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")),
                outputMode=mode,
            )
            upright = converted or upright
        except ImageCms.PyCMSError as broken:
            raise Refusal(
                f"its colour profile cannot be applied ({broken}); export it as "
                "sRGB JPEG and add it again"
            ) from broken
    pixels = upright.convert(mode)
    out = io.BytesIO()
    if png or transparent:
        pixels.save(out, "PNG")
    else:
        pixels.save(out, "JPEG", quality=JPEG_QUALITY)
    return out.getvalue()


def _is_srgb(image: "Image") -> bool:
    """Return whether `image` has no colour profile, or an sRGB one."""
    import io

    from PIL import ImageCms

    profile = image.info.get("icc_profile")
    if not profile:
        return True
    try:
        described = ImageCms.getProfileDescription(
            ImageCms.ImageCmsProfile(io.BytesIO(profile))
        )
    except ImageCms.PyCMSError:
        return False
    return "sRGB" in described


def _is_transparent(image: "Image") -> bool:
    """Return whether any pixel of `image` is less than opaque."""
    if image.mode == "P" and "transparency" in image.info:
        image = image.convert("RGBA")
    if image.mode not in ("RGBA", "LA", "PA"):
        return False
    low = image.getchannel("A").getextrema()[0]
    return isinstance(low, int | float) and low < 255
