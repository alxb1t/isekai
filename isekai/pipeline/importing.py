"""How a file becomes a source: read, cleaned, verified, and committed into a batch.

A file is read into a staging folder under the library's `.staging/`, cleaned of
everything but its pixels and orientation, and verified by the strip's own walk.
An upload waits in the folder until its `Reader` reads it, one file at a time.
A commit moves the staged files into the batch's `sources/`; a cancel, or a sweep
at start, deletes what was staged.

Pillow and `pi_heif` are imported inside the functions that decode, so
`python -m isekai`'s import graph reaches no wheel (D20).
"""

import contextlib
import json
import os
import queue
import re
import secrets
import shutil
import struct
import tempfile
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REPOSITORY
from isekai.shared.image import (
    THUMB_SIDE,
    metadata_in,
    photo_resolution,
    strip_metadata,
    thumbnail_jpeg,
)

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

# Held from picking a staged name until the file under it is written and
# verified, so two files read at once never take one name or both keep one body.
_CLAIM = threading.Lock()

# A staging folder's name: `_STAGING_BYTES` random bytes, in hex.
_STAGING_BYTES = 8
_STAGING_ID = re.compile(f"[0-9a-f]{{{2 * _STAGING_BYTES}}}")

# How long a staging folder goes unwritten before a sweep takes it as left.
_LEFT_AFTER = 60 * 60

# The most pixels import decodes: a photograph's sensor is far below it, and a small
# file declaring more would take gigabytes once decoded and copied.
MAX_PIXELS = 50_000_000

# The largest difference, in 8-bit levels, a profile may make to a colour and
# still be sRGB: a vendor's sRGB profile rounds a level apart from the built-in.
_SRGB_TOLERANCE = 2

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


def past_limit(name: str, size: int, limit: int) -> Refusal:
    """Return the refusal for a file of `size` bytes past `limit`."""
    return Refusal(
        f"{name}: {-(-size // _MB)} MB is past the {limit // _MB} MB limit "
        "`config/ui.json` sets; export a smaller copy and add it again"
    )


def stage(library: Path) -> Path:
    """Return a new, empty staging folder under `library`'s `.staging/`."""
    folder = library / STAGING / secrets.token_hex(_STAGING_BYTES)
    folder.mkdir(parents=True)
    return folder


def read(file: Path, staging: Path, limit: int) -> Staged:
    """Clean `file` into `staging` and return what was staged, or refuse it by name.

    A file whose cleaned bytes are already staged is skipped; a staged name that
    is taken by other bytes becomes `<stem>-2`.
    """
    name = file.name
    _refuse_name(name)
    try:
        size = file.stat().st_size
        if size > limit:
            raise past_limit(name, size, limit)
        with file.open("rb") as handle:
            _refuse_raw(name, handle.read(_SIGNATURE_BYTES))
    except OSError as unreadable:
        raise Refusal(
            f"{name}: cannot be read ({unreadable.strerror}); check the path and "
            "add it again"
        ) from unreadable
    body, converted = _clean(file)
    suffix = _suffix(body) if converted else Path(name).suffix
    with _CLAIM:
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
        except BaseException:
            # Whatever stops the read, nothing of it stays staged behind its refusal.
            target.unlink(missing_ok=True)
            raise
    if carries:
        return Staged(target.name, "not cleaned", tuple(carries))
    return Staged(target.name, "converted" if converted else "ready")


class Reader:
    """Read a staging folder's uploads one at a time, in the order they landed.

    Each upload is held in a dot-named folder until its turn. Each change of a
    file's state is published: `waiting`, `converting`, then a `Staged` state or
    `refused`. e.g. `{"file": "a.heic", "state": "converted", "name": "a.jpg"}`
    """

    def __init__(
        self, staging: Path, limit: int, publish: Callable[[dict[str, Any]], None]
    ) -> None:
        """Start the thread that reads what `put` holds."""
        self._staging = staging
        self._limit = limit
        self._publish = publish
        self._lock = threading.Lock()
        self._files: dict[str, dict[str, Any]] = {}
        self._queue: queue.Queue[tuple[str, Path] | None] = queue.Queue()
        self._stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def put(self, name: str, body: bytes) -> dict[str, Any]:
        """Hold an uploaded file's bytes for reading; return its state, `waiting`."""
        _refuse_name(name)
        if self._stopped:
            raise Refusal(
                f"{name}: its import is closed; close the sheet and choose the "
                "files again"
            )
        held = Path(tempfile.mkdtemp(dir=self._staging, prefix=".upload-")) / name
        held.write_bytes(body)
        state = self._set(name, {"state": "waiting"})
        self._queue.put((name, held))
        return state

    def files(self) -> dict[str, dict[str, Any]]:
        """Return every file's state, by the name it was uploaded as."""
        with self._lock:
            return {name: dict(state) for name, state in self._files.items()}

    def refuse_unread(self) -> None:
        """Refuse while any file still waits or converts, naming how many are read."""
        states = self.files().values()
        unread = sum(one["state"] in _UNREAD for one in states)
        if unread:
            raise Refusal(
                f"{len(states) - unread} of {len(states)} files are read; wait for "
                "the rest, then import"
            )

    def halt(self) -> None:
        """Ask the thread to stop once the file being read is done."""
        self._stopped = True
        self._queue.put(None)

    def stop(self) -> None:
        """Stop reading and wait for the file being read; the rest stay unread."""
        self.halt()
        self._thread.join()

    def _run(self) -> None:
        """Read each held upload in turn until stopped."""
        while (item := self._queue.get()) is not None and not self._stopped:
            name, held = item
            self._set(name, {"state": "converting"})
            try:
                staged = read(held, self._staging, self._limit)
                result = {
                    "state": staged.state,
                    "name": staged.name,
                    "carries": list(staged.carries),
                }
            except Refusal as refused:
                result = {"state": "refused", "refusal": str(refused)}
            except Exception as failed:
                # Anything else, a full disk or a decoder's own error, refuses this
                # file alone: the thread lives on to read the next.
                result = {"state": "refused", "refusal": _failed(name, failed)}
            finally:
                shutil.rmtree(held.parent, ignore_errors=True)
            self._set(name, result)

    def _set(self, name: str, state: dict[str, Any]) -> dict[str, Any]:
        """Record and publish `state` for `name`."""
        with self._lock:
            self._files[name] = state
        self._publish({"file": name, **state})
        return state


# The states of a file the reader has not finished with.
_UNREAD = frozenset({"waiting", "converting"})


def _failed(name: str, failed: Exception) -> str:
    """Return the refusal of `name`, whose reading raised `failed`."""
    return (
        f"{name}: reading it failed ({type(failed).__name__}: {failed}); free disk "
        "space if it is full, then add it again, or export a JPEG copy and add that"
    )


class Imports:
    """Every open import of a library, each a staging folder and its reader.

    A reader starts when its import opens and stops before a commit or a
    cancel touches the folder.
    """

    def __init__(
        self, library: Path, limit: int, publish: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """Hold no import yet; `publish` takes an import's id and a file's state."""
        self._library = library
        self._limit = limit
        self._publish = publish
        self._lock = threading.Lock()
        self._open: dict[str, tuple[Path, Reader]] = {}

    def open(self) -> str:
        """Open an import: a new staging folder and its reader; return its id."""
        folder = stage(self._library)
        staged = folder.name
        reader = Reader(folder, self._limit, lambda one: self._publish(staged, one))
        with self._lock:
            self._open[staged] = (folder, reader)
        return staged

    def folder(self, staged: str) -> Path:
        """Return the staging folder of the open import `staged`, or refuse."""
        return self._named(staged)[0]

    def reader(self, staged: str) -> Reader:
        """Return the reader of the open import `staged`, or refuse."""
        return self._named(staged)[1]

    def commit(
        self, staged: str, name: str, as_is: Iterable[str] = (), *, add: bool = False
    ) -> Committed:
        """Commit import `staged` as `commit` does, once every file is read."""
        folder, reader = self._named(staged)
        reader.refuse_unread()
        done = commit(folder, self._library, name, as_is, add=add)
        self._close(staged)
        return done

    def cancel(self, staged: str) -> None:
        """Stop import `staged`'s reader, then delete its staging folder."""
        folder = self._close(staged)
        cancel(folder)

    def close(self) -> None:
        """Stop every reader, each finishing the file it is reading."""
        with self._lock:
            readers = [reader for _, reader in self._open.values()]
            self._open.clear()
        for reader in readers:
            reader.halt()
        for reader in readers:
            reader.stop()

    def _named(self, staged: str) -> tuple[Path, Reader]:
        """Return the folder and reader of the open import `staged`, or refuse."""
        with self._lock:
            found = self._open.get(staged)
        if found is None:
            raise Refusal(
                f"no import {staged!r} is open; close the sheet and choose the "
                "files again"
            )
        return found

    def _close(self, staged: str) -> Path:
        """Forget import `staged` and stop its reader; return its folder."""
        folder, reader = self._named(staged)
        with self._lock:
            self._open.pop(staged, None)
        reader.stop()
        return folder


def preview(staging: Path, name: str) -> bytes:
    """Return a staged file upright, as `thumbnail_jpeg` makes it.

    Made from the file each time and kept nowhere: it goes with its staging folder.
    """
    from PIL import Image, ImageOps

    _refuse_name(name)
    staged = staging / name
    if not staged.is_file():
        raise Refusal(f"{name}: not staged in this import; choose it again")
    try:
        with Image.open(staged) as opened:
            # A JPEG decodes at the smallest scale that still covers the side.
            opened.draft("RGB", (THUMB_SIDE, THUMB_SIDE))
            return thumbnail_jpeg(ImageOps.exif_transpose(opened))
    except OSError as unread:
        raise Refusal(
            f"{name}: its preview cannot be made ({unread}); choose it again"
        ) from unread


def _refuse_name(name: str) -> None:
    """Refuse a name that is empty, starts with a dot, or holds a path separator."""
    if not name or name.startswith(".") or "/" in name or "\\" in name:
        raise Refusal(f"{name!r}: not a file name import takes; rename it and add it")


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
    # `.staging/` goes once no staging folder is left in it.
    with contextlib.suppress(OSError):
        staging.parent.rmdir()


def sweep(library: Path) -> None:
    """Delete every staging folder left in `library` by an import that did not end.

    A folder goes only when `stage` could have named it and nothing has written
    to it within `_LEFT_AFTER`; a fresher one belongs to an import still open,
    perhaps in another process.
    """
    folder = library / STAGING
    if not folder.is_dir():
        return
    left_before = time.time() - _LEFT_AFTER
    for one in folder.iterdir():
        with contextlib.suppress(OSError):
            if _STAGING_ID.fullmatch(one.name) and one.stat().st_mtime < left_before:
                shutil.rmtree(one)
    with contextlib.suppress(OSError):
        folder.rmdir()


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
            # The size first, so only a file that could match is read.
            same = present.is_file() and present.stat().st_size == len(body)
            if same and present.read_bytes() == body:
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
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise Refusal(
                f"{name}: {width}x{height} is past the {MAX_PIXELS // 1_000_000} MP "
                "limit import decodes; export a smaller copy and add it again"
            )
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
    if image.format in ("JPEG", "MPO", "PNG") and _is_srgb(image, file.name):
        try:
            return strip_metadata(file), False
        except Refusal:
            pass
    return _encode(image, file.name), True


def _suffix(body: bytes) -> str:
    """Return the suffix encoded bytes are named with: `.png` or `.jpg`."""
    return ".png" if body.startswith(b"\x89PNG") else ".jpg"


def _reencode(body: bytes) -> bytes:
    """Return `body` encoded again from its decoded pixels, in its own format."""
    image = _decode(body)
    return _encode(image, "the cleaned file")


def _encode(image: "Image", name: str) -> bytes:
    """Return `image` upright, in sRGB, as PNG when it was one or is transparent.

    Refuses `name` when Pillow cannot convert or encode the image's mode.
    """
    try:
        return _converted(image, name)
    except (OSError, ValueError) as unconvertible:
        raise Refusal(
            f"{name}: cannot be converted to JPEG or PNG ({unconvertible}); export "
            "it as an 8-bit JPEG and add it again"
        ) from unconvertible


def _converted(image: "Image", name: str) -> bytes:
    """Return `image` upright, in sRGB, encoded as `_encode` describes."""
    import io

    from PIL import ImageCms, ImageOps

    upright = _eight_bit(ImageOps.exif_transpose(image))
    transparent = _is_transparent(upright)
    profile = image.info.get("icc_profile")
    mode = "RGBA" if transparent else "RGB"
    if profile and not _is_srgb(image, name):
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
                f"{name}: its colour profile cannot be applied ({broken}); export "
                "it as sRGB JPEG and add it again"
            ) from broken
    pixels = upright.convert(mode)
    # The PNG writer falls back to the image's own profile, and the pixels are sRGB
    # by now, so nothing of the decoded file's info reaches the encoder.
    pixels.info.clear()
    out = io.BytesIO()
    if image.format == "PNG" or transparent:
        pixels.save(out, "PNG")
    else:
        pixels.save(out, "JPEG", quality=JPEG_QUALITY)
    return out.getvalue()


# The raw layout each 16-bit greyscale mode is read back into 32-bit `I` with:
# `point` scales only `I` and `I;16`, and `convert` clips an `I;16N` to 255.
_SIXTEEN_BIT = {"I;16": "I;16", "I;16L": "I;16", "I;16B": "I;16B", "I;16N": "I;16N"}


def _eight_bit(image: "Image") -> "Image":
    """Return a 16-bit greyscale `image` with its values scaled to 8 bits.

    A conversion clips each value to 255, which turns a 16-bit scan white.
    e.g. a value of 20000 -> 77
    """
    from PIL import Image

    if image.mode in _SIXTEEN_BIT:
        raw = _SIXTEEN_BIT[image.mode]
        image = Image.frombytes("I", image.size, image.tobytes(), "raw", raw)
    if image.mode == "I":
        return image.point(lambda value: value / 257).convert("L")
    return image


def _is_srgb(image: "Image", name: str) -> bool:
    """Return whether `image` has no colour profile, or one whose colours are sRGB's.

    The profile's content decides, never its name: every level of a grid of
    colours is taken through it to sRGB and must come back within
    `_SRGB_TOLERANCE`. e.g. a linear-light profile named "Linear sRGB" -> False.
    Refuses `name` when the profile cannot be read.
    """
    import io

    from PIL import ImageChops, ImageCms

    profile = image.info.get("icc_profile")
    if not profile:
        return True
    try:
        read = ImageCms.ImageCmsProfile(io.BytesIO(profile))
    except (ImageCms.PyCMSError, OSError) as unreadable:
        raise Refusal(
            f"{name}: its colour profile cannot be read ({unreadable}); export it "
            "as sRGB JPEG and add it again"
        ) from unreadable
    if read.profile.xcolor_space != "RGB ":
        return False
    grid = _colour_grid()
    try:
        through = ImageCms.profileToProfile(
            grid,
            read,
            ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")),
            renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
        )
    except ImageCms.PyCMSError:
        return False
    # `profileToProfile` returns None only when asked to convert in place.
    if through is None:
        return False
    return max(ImageChops.difference(grid, through).tobytes()) <= _SRGB_TOLERANCE


def _colour_grid() -> "Image":
    """Return one pixel for each colour whose levels are each a multiple of 32, or 255.

    A primary's own hue, a grey and a mix are all in it, so a profile that moves
    any of the three moves a pixel.
    """
    import itertools

    from PIL import Image

    levels = (*range(0, 256, 32), 255)
    colours = list(itertools.product(levels, repeat=3))
    flat = bytes(level for colour in colours for level in colour)
    return Image.frombytes("RGB", (len(colours), 1), flat)


def _is_transparent(image: "Image") -> bool:
    """Return whether any pixel of `image` is less than opaque."""
    if image.mode == "P" and "transparency" in image.info:
        image = image.convert("RGBA")
    if image.mode not in ("RGBA", "LA", "PA"):
        return False
    low = image.getchannel("A").getextrema()[0]
    return isinstance(low, int | float) and low < 255
