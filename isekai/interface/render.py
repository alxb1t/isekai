"""`isekai render`: one whole render session on a rented GPU, torn down on every exit.

    python -m isekai render <runs> <flow>=<count|source> ...
    e.g. python -m isekai render .data/b1/runs summon-anime-wai=1 conjure-anime-wai=1
         python -m isekai render .data/b1/runs control-anime-wai=summon-anime-wai

A count draws that many seeds; a source flow renders its latest seeds again. A source
rendered by count in the same line goes first, in the same session. Output is shown
and appended to the batch's log, `<runs>/../log.txt` (D36).
"""

import argparse
import dataclasses
import io
import os
import re
import shlex
import signal
import socket
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from isekai.boundary import gpu
from isekai.boundary.comfy import ComfyClient, ComfyTransport
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import FRAME_NAME, REPOSITORY
from isekai.interface.compare_view import BATCH_PHOTOS
from isekai.interface.wiring import Wiring
from isekai.pipeline.generate import read_runtime

# The port `gpunit.toml` forwards, on both sides; a test holds the two equal.
PORT = 8188
# CLAUDE.md's 45 minutes, less one for the teardown.
CEILING_S = 2640
# How long ComfyUI gets to answer through the tunnel, and how often it is asked.
WAIT_S = 300
POLL_S = 5.0
# gpunit's exit for a create whose answer was lost.
LOST_EXIT = 3

REQUEST = re.compile(r"([a-z0-9-]+)=([1-9][0-9]*|[a-z][a-z0-9-]*)")
# The bare command a gpunit refusal names: a verb, or `volume` and its action.
REMEDY = re.compile(r"run gpunit ([a-z]+(?: up| down)?)")

# `generate`'s argv and the wiring it runs on -> its exit status.
Generate = Callable[[list[str], Wiring], int]


@dataclass(frozen=True)
class Request:
    """One `<flow>=<count|source>` argument."""

    flow: str
    value: str

    @property
    def by_count(self) -> bool:
        """Return whether this flow draws seeds rather than taking a source's."""
        return self.value.isdigit()

    @property
    def mode(self) -> str:
        """Return the `generate` flag this request renders with."""
        return "--count" if self.by_count else "--seeds-from"

    def __str__(self) -> str:
        """Spell the request as the operator typed it."""
        return f"{self.flow}={self.value}"


def parse_request(text: str) -> Request:
    """Return the request `text` spells, or refuse naming the shape.

    e.g. "control-anime-wai=summon-anime-wai" -> Request("control-anime-wai", ...)
    """
    match = REQUEST.fullmatch(text)
    if match is None:
        raise Refusal(
            f"'{text}' is not <flow>=<count> or <flow>=<source>, "
            "e.g. summon-anime-wai=1"
        )
    return Request(match[1], match[2])


def in_session_sources(requests: Sequence[Request]) -> list[bool]:
    """Return, per request, whether its source renders by count earlier in the line.

    Such a source has no seeds until the pod is up, so its dependent is checked
    against the source's latest approval instead; one placed before its source
    could never be, and is refused.
    """
    counted = {r.flow: i for i, r in enumerate(requests) if r.by_count}
    deferred = []
    for i, request in enumerate(requests):
        j = None if request.by_count else counted.get(request.value)
        if j is not None and j > i:
            raise Refusal(
                f"'{request}' comes before its source '{requests[j]}'; "
                "put the source first"
            )
        deferred.append(j is not None)
    return deferred


def run_ids(runs: Path) -> list[str]:
    """Return every run under `runs`, by id."""
    return sorted(
        child.name for child in runs.iterdir() if (child / FRAME_NAME).is_file()
    )


class _Tee(io.TextIOBase):
    """Write to the terminal's stream and the batch's log alike."""

    def __init__(self, *streams: TextIO) -> None:
        """Write to each of `streams`."""
        self._streams = streams

    def write(self, text: str) -> int:
        """Write `text` to every stream."""
        for stream in self._streams:
            stream.write(text)
            stream.flush()
        return len(text)


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


def await_endpoint(
    client: ComfyTransport, server: str, wait_s: float, poll_s: float
) -> None:
    """Return once the endpoint reports itself; refuse after `wait_s` with no answer.

    The tunnel and ComfyUI come up after the pod does, so a failed ask is asked again.
    """
    deadline = time.monotonic() + wait_s
    while True:
        try:
            read_runtime(client)
            return
        except Refusal:
            if time.monotonic() >= deadline:
                raise Refusal(
                    f"{server}/system_stats did not answer within {wait_s:g}s"
                ) from None
            time.sleep(poll_s)


@dataclass(frozen=True)
class Seams:
    """What a session reaches the outside world through; a test replaces any of them."""

    open_session: gpu.OpenSession = gpu.open_session
    # `None` reads this process's environment and the repository's `.env`.
    environ: Mapping[str, str] | None = None
    connect: Callable[[str], ComfyTransport] = ComfyClient
    busy: Callable[[int], bool] = answers
    kill: Callable[[], None] = terminate
    ceiling_s: float = CEILING_S
    wait_s: float = WAIT_S
    poll_s: float = POLL_S


def run_session(
    args: argparse.Namespace,
    wired: Wiring,
    generate: Generate,
    seams: Seams = Seams(),
) -> int:
    """Run one render session and return its exit status.

    0 every flow rendered · 1 a flow failed or a refusal · 3 the create's answer
    was lost · 128+n a signal ended it. Every refusal reaches the batch's log too.
    """
    runs = Path(args.runs)
    if not runs.is_dir():
        print(
            f"refused: {runs} is not a directory; give the batch's runs/",
            file=wired.err,
        )
        return 1
    with (runs.parent / "log.txt").open("a", encoding="utf-8") as log:
        logged = dataclasses.replace(
            wired, out=_Tee(wired.out, log), err=_Tee(wired.err, log)
        )
        try:
            return _session(runs, list(args.requests), logged, generate, seams)
        except Refusal as refused:
            print(f"refused: {refused}", file=logged.err)
            return 1


def _session(
    runs: Path, texts: list[str], wired: Wiring, generate: Generate, seams: Seams
) -> int:
    requests = [parse_request(text) for text in texts]
    deferred = in_session_sources(requests)
    ids = run_ids(runs)
    flows = [arg for request in requests for arg in ("--flow", request.flow)]
    if not ids:
        photos = shlex.quote(str(runs.parent / BATCH_PHOTOS))
        raise Refusal(
            f"{runs} holds no run; open them from the batch's photographs with: "
            f"uv run python -m isekai tag {' '.join(flows)} --runs "
            f"{shlex.quote(str(runs))} {photos}/*"
        )
    where = ["--runs", str(runs), *ids]

    # Free work first: every prompt is assembled, and every source checked, before
    # anything is rented.
    free = dataclasses.replace(wired, client=None, image=None)
    if generate(["generate", *flows, *where], free) != 0:
        return 1
    for request, late in zip(requests, deferred, strict=True):
        if request.by_count:
            continue
        check = "--in-step-with" if late else "--seeds-from"
        argv = ["generate", "--flow", request.flow, check, request.value, *where]
        if generate(argv, free) != 0:
            return 1

    if seams.busy(PORT):
        raise Refusal(
            f"127.0.0.1:{PORT} already answers, and would be rendered against; "
            f"lsof -iTCP:{PORT} -sTCP:LISTEN shows what holds it"
        )

    again = shlex.join(["uv", "run", "python", "-m", "isekai", "render", str(runs)])
    rest = " ".join(texts)

    def ceiling() -> None:
        print(
            f"refused: the session reached its {seams.ceiling_s:g}s ceiling; renders "
            f"so far are kept, and in a new session `{again} {rest}` renders only "
            "the rest",
            file=wired.err,
        )
        seams.kill()

    # Started before the session opens, so it counts from before the pod (D36).
    watchdog = threading.Timer(seams.ceiling_s, ceiling)
    watchdog.daemon = True
    watchdog.start()
    try:
        return _rendered(requests, where, wired, generate, seams)
    finally:
        watchdog.cancel()


def _rendered(
    requests: list[Request],
    where: list[str],
    wired: Wiring,
    generate: Generate,
    seams: Seams,
) -> int:
    from gpunit import Lost, Refused, TeardownFailed

    def say(line: str) -> None:
        print(line, file=wired.err)

    try:
        environ = seams.environ
        if environ is None:
            environ = os.environ | gpu.read_env(REPOSITORY / ".env")
        with seams.open_session(REPOSITORY, environ, say) as session:
            server = f"http://127.0.0.1:{session.port(PORT)}"
            client = seams.connect(server)
            await_endpoint(client, server, seams.wait_s, seams.poll_s)
            live = dataclasses.replace(wired, client=client, image=session.image)
            # One flow failing does not cost the next its render; the exit says so.
            failed = False
            for request in requests:
                argv = [
                    "generate",
                    "--flow",
                    request.flow,
                    request.mode,
                    request.value,
                    "--server",
                    server,
                    *where,
                ]
                failed |= generate(argv, live) != 0
            return int(failed)
    except KeyboardInterrupt as stopped:
        # gpunit's `Interrupted` carries the signal; a bare Ctrl-C is SIGINT.
        return 128 + int(getattr(stopped, "signal", signal.SIGINT))
    # gpunit's CLI reads no .env, where the key lives, so each remedy loads it.
    except Lost:
        print(
            "refused: the provider's answer was lost; "
            "`uv run --env-file .env gpunit status` shows what is left, "
            "and `uv run --env-file .env gpunit down` deletes it",
            file=wired.err,
        )
        return LOST_EXIT
    except TeardownFailed:
        print(
            "refused: the session's teardown failed, and its pod may still bill; "
            "run `uv run --env-file .env gpunit down`",
            file=wired.err,
        )
        return 1
    except Refused as refused:
        # gpunit has written its own `refused:` line through `say`. Where it names a
        # bare `gpunit <verb>`, the line after it is that command loading the key; a
        # note, not a second refusal.
        if remedy := REMEDY.search(str(refused)):
            print(
                "gpunit reads no .env, where the key lives: "
                f"run `uv run --env-file .env gpunit {remedy[1]}`",
                file=wired.err,
            )
        return 1
