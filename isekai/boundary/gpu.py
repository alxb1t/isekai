"""The rented GPU: one session through gpunit, and the `.env` it is handed.

`gpunit` is imported inside `open_session`, so `python -m isekai` imports no
third-party package at module scope (D20).
"""

from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

# What `gpunit.session` takes and yields, as `isekai render` calls it.
OpenSession = Callable[
    [Path, Mapping[str, str], Callable[[str], None]], AbstractContextManager[Any]
]


def read_env(path: Path) -> dict[str, str]:
    """Return a `.env` file's `KEY=VALUE` lines, quotes stripped; none if it is absent.

    e.g. `RUNPOD_API_KEY="k"` -> {"RUNPOD_API_KEY": "k"}
    """
    if not path.is_file():
        return {}
    return dict(_pairs(path.read_text(encoding="utf-8").splitlines()))


def _pairs(lines: list[str]) -> Iterator[tuple[str, str]]:
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        yield key.strip(), value


def open_session(
    cwd: Path, environ: Mapping[str, str], say: Callable[[str], None]
) -> AbstractContextManager[Any]:
    """Return gpunit's session on `cwd`'s `gpunit.toml`, its lines sent to `say`."""
    import gpunit

    return gpunit.session(cwd / "gpunit.toml", environ=environ, cwd=cwd, say=say)
