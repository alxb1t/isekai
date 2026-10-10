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
from isekai.foundation.run import REPOSITORY
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
    deferred = []
    for i, request in enumerate(requests):
        late = False
        for j, source in enumerate(requests):
            if request.by_count or source.flow != request.value:
                continue
            if not source.by_count:
                continue
            if j > i:
                raise Refusal(
                    f"'{request}' comes before its source '{source}'; "
                    "put the source first"
                )
            late = True
        deferred.append(late)
    return deferred


def run_ids(runs: Path) -> list[str]:
    """Return every run under `runs`, by id."""
    return sorted(
        child.name for child in runs.iterdir() if (child / "run.json").is_file()
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


def run_session(
    args: argparse.Namespace,
    wired: Wiring,
    generate: Generate,
    *,
    open_session: gpu.OpenSession = gpu.open_session,
    environ: Mapping[str, str] | None = None,
    connect: Callable[[str], ComfyTransport] = ComfyClient,
    busy: Callable[[int], bool] = answers,
    kill: Callable[[], None] = terminate,
    ceiling_s: float = CEILING_S,
    wait_s: float = WAIT_S,
    poll_s: float = POLL_S,
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
            return _session(
                runs,
                list(args.requests),
                logged,
                generate,
                open_session=open_session,
                environ=environ
                if environ is not None
                else os.environ | gpu.read_env(REPOSITORY / ".env"),
                connect=connect,
                busy=busy,
                kill=kill,
                ceiling_s=ceiling_s,
                wait_s=wait_s,
                poll_s=poll_s,
            )
        except Refusal as refused:
            print(f"refused: {refused}", file=logged.err)
            return 1


def _session(
    runs: Path,
    texts: list[str],
    wired: Wiring,
    generate: Generate,
    *,
    open_session: gpu.OpenSession,
    environ: Mapping[str, str],
    connect: Callable[[str], ComfyTransport],
    busy: Callable[[int], bool],
    kill: Callable[[], None],
    ceiling_s: float,
    wait_s: float,
    poll_s: float,
) -> int:
    requests = [parse_request(text) for text in texts]
    deferred = in_session_sources(requests)
    ids = run_ids(runs)
    flows = [arg for request in requests for arg in ("--flow", request.flow)]
    if not ids:
        raise Refusal(
            f"{runs} holds no run; open them from the batch's photographs with: "
            f"uv run python -m isekai tag {' '.join(flows)} --runs {runs} "
            f"{runs.parent}/photos/*"
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

    if busy(PORT):
        raise Refusal(
            f"127.0.0.1:{PORT} already answers, and would be rendered against; "
            f"lsof -iTCP:{PORT} -sTCP:LISTEN shows what holds it"
        )

    again = shlex.join(["uv", "run", "python", "-m", "isekai", "render", str(runs)])
    rest = " ".join(texts)

    def ceiling() -> None:
        print(
            f"refused: the session reached its {ceiling_s:g}s ceiling; renders so "
            f"far are kept, and in a new session `{again} {rest}` renders only "
            "the rest",
            file=wired.err,
        )
        kill()

    # Started before the session opens, so it counts from before the pod (D36).
    watchdog = threading.Timer(ceiling_s, ceiling)
    watchdog.daemon = True
    watchdog.start()
    try:
        return _rendered(
            requests,
            where,
            wired,
            generate,
            open_session=open_session,
            environ=environ,
            connect=connect,
            wait_s=wait_s,
            poll_s=poll_s,
        )
    finally:
        watchdog.cancel()


def _rendered(
    requests: list[Request],
    where: list[str],
    wired: Wiring,
    generate: Generate,
    *,
    open_session: gpu.OpenSession,
    environ: Mapping[str, str],
    connect: Callable[[str], ComfyTransport],
    wait_s: float,
    poll_s: float,
) -> int:
    from gpunit import Lost, Refused, TeardownFailed

    def say(line: str) -> None:
        print(line, file=wired.err)

    try:
        with open_session(REPOSITORY, environ, say) as session:
            server = f"http://127.0.0.1:{session.port(PORT)}"
            client = connect(server)
            await_endpoint(client, server, wait_s, poll_s)
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
    except Lost:
        print(
            "refused: the provider's answer was lost; `uv run gpunit status` shows "
            "what is left",
            file=wired.err,
        )
        return LOST_EXIT
    except TeardownFailed:
        print(
            "refused: the session's teardown failed, and its pod may still bill; "
            "run `uv run gpunit down`",
            file=wired.err,
        )
        return 1
    except Refused:
        # gpunit has written its own `refused:` line through `say`.
        return 1
