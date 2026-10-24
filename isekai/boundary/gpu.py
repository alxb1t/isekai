"""The rented GPU: one session through gpunit, its window volume, and the `.env`.

`gpunit` is imported inside each function that calls it, so `python -m isekai`
imports no third-party package at module scope (D20).
"""

import dataclasses
import os
import signal
import socket
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.boundary.comfy import ComfyClient, ComfyTransport
from isekai.foundation.run import REPOSITORY

# How long ComfyUI gets to answer through the tunnel, and how often it is asked.
WAIT_S = 300
POLL_S = 5.0

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


@dataclass(frozen=True)
class Bounds:
    """What `gpunit.toml` bounds, `None` where it sets none.

    A session's seconds, a card's hourly price, and the window volume's seconds.
    """

    ceiling_s: int
    max_hourly: float | None
    volume_ceiling_s: int | None


def bounds(cwd: Path) -> Bounds:
    """Return the bounds `cwd`'s `gpunit.toml` sets."""
    import gpunit

    spec = gpunit.load_spec(cwd / "gpunit.toml")
    return Bounds(spec.ceiling_s, spec.max_hourly, spec.volume_ceiling_s)


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


def answers(port: int) -> bool:
    """Return whether something on this machine already answers on `port`."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def terminate() -> None:
    """Send this process `SIGTERM`; inside a session, gpunit tears down on it."""
    os.kill(os.getpid(), signal.SIGTERM)


@dataclass(frozen=True)
class Seams:
    """What a session reaches the outside world through; a test replaces any of them."""

    open_session: OpenSession = open_session
    # `None` reads this process's environment and the repository's `.env`.
    environ: Mapping[str, str] | None = None
    connect: Callable[[str], ComfyTransport] = ComfyClient
    busy: Callable[[int], bool] = answers
    kill: Callable[[], None] = terminate
    # `None` runs the watchdog at the session's limit.
    watchdog_s: float | None = None
    wait_s: float = WAIT_S
    poll_s: float = POLL_S


# Where each line of gpunit's output goes, without its newline.
Say = Callable[[str], None]

# gpunit's verb line after `gpunit`, and where its output is said -> exit.
Gpunit = Callable[[Sequence[str], Say], int]


def run_gpunit(argv: Sequence[str], say: Say) -> int:
    """Run `gpunit <argv>` in the repository on its `.env`, saying each line it writes.

    gpunit reads no `.env`, where the key lives, so it is handed one. It runs in
    its own session, so a Ctrl-C at the caller's terminal never cuts a create or
    a delete halfway. Its output is handed on line by line, so the caller decides
    how each line reads in its log.
    """
    done = subprocess.run(
        [sys.executable, "-m", "gpunit", *argv],
        cwd=REPOSITORY,
        env=_dotenv(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        start_new_session=True,
    )
    for line in (done.stdout or "").splitlines():
        say(line)
    return done.returncode


@dataclass(frozen=True)
class Volume:
    """The window volume and gpunit's records, through gpunit's own verbs.

    Each returns gpunit's exit: 0 done, 1 refused or failed, 3 a lost create.
    `records` is where gpunit keeps what it created, `.gpunit/` in its directory.
    """

    run: Gpunit = run_gpunit
    records: Path = REPOSITORY / ".gpunit"

    def up(self, say: Say) -> int:
        """Open the window, or extend a live one, agreeing to its price."""
        return self.run(["volume", "up", "--yes"], say)

    def down(self, say: Say) -> int:
        """Close the window."""
        return self.run(["volume", "down"], say)

    def status(self, say: Say) -> int:
        """Ask gpunit what it holds; it sweeps a window past its end."""
        return self.run(["status", "--json"], say)


def _dotenv() -> dict[str, str]:
    """Return this process's environment with the repository's `.env` over it."""
    return os.environ | read_env(REPOSITORY / ".env")


def environ_of(seams: Seams) -> Mapping[str, str]:
    """Return the environment a session on `seams` is handed."""
    return _dotenv() if seams.environ is None else seams.environ


def keyed(seams: Seams) -> bool:
    """Return whether a session on `seams` would be handed a RunPod key."""
    return bool(environ_of(seams).get("RUNPOD_API_KEY"))
