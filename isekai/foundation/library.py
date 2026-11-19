"""The library's folder names and a collection's, read from the folders alone.

`RUNS` is a collection's runs root and `SOURCES` its photographs' folder; `names.py`'s
`SOURCES` is a flow's. A folder in the library is a collection when it holds
`sources/` (D40), and a dot-folder is never listed.
"""

import os
from collections.abc import Mapping
from pathlib import Path

from isekai.foundation.refusal import Refusal

VARIABLE = "ISEKAI_LIBRARY"
DEFAULT = Path("~/isekai")
RUNS = "runs"
SOURCES = "sources"
LOG = "log.txt"
# The library's thumbnails, a dot-folder so it is listed as no collection.
CACHE = ".cache"


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
