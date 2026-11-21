"""The library's folder names and a collection's, and its session records' read side.

`RUNS` is a collection's runs root and `SOURCES` its photographs' folder; `names.py`'s
`SOURCES` is a flow's. A folder in the library is a collection when it holds
`sources/` (D40), and a dot-folder is never listed. A thumbnail's path in the cache
and the digest that names it are here too (D68).
"""

import contextlib
import errno
import fcntl
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from isekai.foundation.artifacts import (
    SESSION_FILE,
    SESSION_ID,
    SESSIONS,
    SessionRecord,
    read,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import ID_DIGEST_CHARS, Run, digest_of

VARIABLE = "ISEKAI_LIBRARY"
DEFAULT = Path("~/isekai")
RUNS = "runs"
SOURCES = "sources"
LOG = "log.txt"
# The library's thumbnails, a dot-folder so it is listed as no collection.
CACHE = ".cache"
# What a filesystem without hard links or advisory locks answers `link` or `flock`.
UNSUPPORTED = frozenset(
    {errno.ENOTSUP, errno.EOPNOTSUPP, errno.EPERM, errno.ENOLCK, errno.ENOSYS}
)


def root(environ: Mapping[str, str] = os.environ) -> Path:
    """Return the library directory `ISEKAI_LIBRARY` names, `~/isekai` when unset."""
    return Path(environ.get(VARIABLE) or DEFAULT).expanduser()


def is_collection(folder: Path) -> bool:
    """Return whether `folder` is a collection: a folder holding `sources/`."""
    return (folder / SOURCES).is_dir()


def listed(library: Path) -> list[Path]:
    """Return every folder of the library, dot-folders left out, by name."""
    if not library.is_dir():
        return []
    return sorted(
        item
        for item in library.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    )


def collection(library: Path, name: str) -> Path:
    """Return the collection folder `name` names, refusing one the library lacks."""
    folder = library / name
    if (
        name in ("", ".", "..")
        or "/" in name
        or name.startswith(".")
        or not (folder.is_dir() and is_collection(folder))
    ):
        raise Refusal(
            f"the library holds no collection named {name!r}; go back to the library "
            "to choose one"
        )
    return folder


def record_running(path: Path) -> bool:
    """Return whether a render process holds this record's lifetime lock.

    The lock file stays in place across releases, so opening it always tests the
    same inode; the kernel releases its lock even when the render is killed. A
    filesystem without locks holds no running render, since `Record.open`
    refuses to start one there.
    """
    try:
        held = path.with_suffix(".lock").open("r")
    except FileNotFoundError:
        return False
    with held:
        try:
            fcntl.flock(held, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        except OSError as failure:
            if failure.errno not in UNSUPPORTED:
                raise
    return False


def running(folder: Path) -> list[dict[str, Any]]:
    """Return collection `folder`'s records a render process holds, newest first.

    Liveness is read from each lock before any record is parsed, so a damaged
    record that no render holds is never read. A held record that does not read
    is left out; a read of that session names its remedy.
    """
    found = []
    for path in (folder / SESSIONS).glob("*.json"):
        if record_running(path):
            with contextlib.suppress(Refusal):
                found.append(_session(path))
    found.sort(key=lambda one: one["started"], reverse=True)
    return [one for one in found if one["outcome"] == "running"]


def collection_held(folder: Path) -> bool:
    """Return whether a render process holds collection `folder`.

    Liveness alone is read, from each session's lock, so a record that does not
    read still counts; a folder with no sessions is held by none.
    e.g. `<lib>/b` with `<lib>/b/sessions/<t>.lock` locked -> True
    """
    return any(record_running(path) for path in (folder / SESSIONS).glob("*.json"))


def render_running(run: Run) -> bool:
    """Return whether a render process holds the runs root `run` sits in.

    A session writes its record beside any runs root, a collection's or not, so
    the folder the root sits in is asked. Liveness alone is read, from each
    session's lock, so a record that does not read still counts.
    e.g. `<dir>/runs/<id>` with `<dir>/sessions/<t>.lock` locked -> True
    """
    return collection_held(run.path.absolute().parent.parent)


def session(folder: Path, name: str) -> dict[str, Any]:
    """Return the session record `name` names, refusing an id no record holds."""
    path = folder / SESSIONS / f"{name}.json"
    if SESSION_ID.fullmatch(name) is None or not path.is_file():
        raise Refusal(f"{folder.name} holds no session {name!r}")
    return _session(path)


def _session(path: Path) -> dict[str, Any]:
    """Return one record as served, a stale `running` read as no outcome."""
    record: SessionRecord = read(
        path, SESSION_FILE, remedy=f"delete {path}: no stage writes it again"
    )
    served: dict[str, Any] = dict(record)
    if record["outcome"] == "running" and not record_running(path):
        served["outcome"] = None
    return served


# A file's digest by what its stat says: reading every photograph on every listing
# would read the whole library each time.
_DIGESTS: dict[tuple[str, int, int, int], str] = {}


def stat_key(path: Path) -> tuple[str, int, int, int]:
    """Return what a file's stat says about whether it changed."""
    info = path.stat()
    return (str(path), info.st_size, info.st_mtime_ns, info.st_ino)


def file_digest(path: Path) -> str:
    """Return the twelve-character digest a run of this file is named by."""
    key = stat_key(path)
    if key not in _DIGESTS:
        _DIGESTS[key] = digest_of(path.read_bytes())[:ID_DIGEST_CHARS]
    return _DIGESTS[key]


def thumbnail_of(library: Path, run: Run, image: Path) -> Path:
    """Return where `image`'s thumbnail sits in `library`'s cache, made or not.

    Under `.cache/<run digest>/` at the image's path in the run, named by the image's
    own digest too: two collections can hold one source rendered at one seed, and only
    the bytes tell them apart. The image must exist, since its bytes name the file.
    e.g. `…/outputs/001/42.png` -> `.cache/0d4b…/…/001/42.<image digest>.jpg`
    """
    within = image.absolute().relative_to(run.path.absolute())
    named = f"{within.stem}.{file_digest(image)}.jpg"
    return library / CACHE / run.digest / within.parent / named


def named_thumbnail(run: Run, image: Path) -> Path | None:
    """Return where `image`'s thumbnail sits in its library's cache, made or not.

    None for a run outside a collection, which has no library. The image must
    exist, since its bytes name the file.
    e.g. `<lib>/b/runs/<id>/…/001/42.png` -> `<lib>/.cache/<digest>/…/001/42.<d>.jpg`
    """
    folder = run.path.absolute()
    if not (folder.parent.name == RUNS and is_collection(folder.parent.parent)):
        return None
    return thumbnail_of(folder.parents[2], run, image)


def drop_thumbnails(run: Run, image: Path) -> list[Path]:
    """Delete `image`'s own thumbnail in its library's cache; return it, if there.

    The library is read from the run's own path, so the verb and the route find one
    cache; a run outside a collection has none. The thumbnail is named by the
    image's digest, so `image` must still exist: another collection's thumbnail of
    the same seed stays.
    e.g. `<lib>/b/runs/<id>/…/001/42.png` -> [`<lib>/.cache/<digest>/…/001/42.<d>.jpg`]
    """
    own = named_thumbnail(run, image)
    if own is None or not own.is_file():
        return []
    own.unlink()
    return [own]
