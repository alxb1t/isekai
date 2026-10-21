"""The rented GPU: one session through gpunit, and the `.env` it is handed.

`gpunit` is imported inside `open_session`, so `python -m isekai` imports no
third-party package at module scope (D20).
"""

import dataclasses
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

# What `gpunit.session` takes and yields, as `isekai render` calls it: the
# repository, the environment, where its lines go, and the session's limit.
OpenSession = Callable[
    [Path, Mapping[str, str], Callable[[str], None], int], AbstractContextManager[Any]
]


def read_env(path: Path) -> dict[str, str]:
    """Return a `.env` file's `KEY=VALUE` lines, quotes stripped; none if it is absent.

    e.g. `RUNPOD_API_KEY="k"` -> {"RUNPOD_API_KEY": "k"}
    """
    if not path.is_file():
        return {}
    pairs = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        pairs[key.strip()] = value
    return pairs


def ceiling_s(cwd: Path) -> int:
    """Return the hard maximum `cwd`'s `gpunit.toml` sets on a session, in seconds."""
    import gpunit

    return gpunit.load_spec(cwd / "gpunit.toml").ceiling_s


def open_session(
    cwd: Path, environ: Mapping[str, str], say: Callable[[str], None], limit_s: int
) -> AbstractContextManager[Any]:
    """Return gpunit's session on `cwd`'s `gpunit.toml`, stopping at `limit_s`.

    The limit is the pod's own stop, `GPUNIT_CEILING`; its lines go to `say`.
    """
    import gpunit

    spec = gpunit.load_spec(cwd / "gpunit.toml")
    limited = dataclasses.replace(spec, ceiling_s=limit_s)
    return gpunit.session(limited, environ=environ, cwd=cwd, say=say)
