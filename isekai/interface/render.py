"""`isekai render`: one whole render session on a rented GPU, torn down on every exit.

    python -m isekai render <runs> [<flow>=<count|source> ...]
    e.g. python -m isekai render .data/b1/runs
         python -m isekai render .data/b1/runs summon-anime-wai=1 conjure-anime-wai=1
         python -m isekai render .data/b1/runs control-anime-wai=summon-anime-wai

With no request, every approval short of its count renders what it lacks. A count
draws that many seeds; a source flow renders its latest seeds again. A source
rendered by count in the same line goes first, in the same session. Output is shown
and appended to the batch's log, `<runs>/../log.txt` (D36); with `--progress json`
the prose goes to stderr alone, which the caller keeps, as the app's job does.
"""

import argparse
import contextlib
import dataclasses
import io
import json
import math
import re
import shlex
import signal
import statistics
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO, cast

from isekai.boundary import gpu
from isekai.boundary.comfy import ComfyTransport
from isekai.boundary.gpu import Seams
from isekai.boundary.pod_start import HOLD_SECONDS
from isekai.foundation.flow import Flow, load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    FRAME_NAME,
    REPOSITORY,
    REVIEW,
    SHEETS,
    Run,
    approved_versions,
    latest_artifact,
)
from isekai.interface.compare_view import BATCH_PHOTOS
from isekai.interface.wiring import Wiring
from isekai.pipeline.generate import (
    duration,
    read_runtime,
    render_groups,
    rendered_seeds,
    shortfall,
    sidecars,
)
from isekai.pipeline.review import current_draft

# The port `gpunit.toml` forwards, on both sides; a test holds the two equal.
PORT = 8188
# The figures a session's estimate takes where nothing is recorded (D3).
RENDER_CONFIG = REPOSITORY / "config" / "render.json"
# How many of a flow's newest recorded durations its time per image is the median of.
RECENT = 20
# A pod held for diagnosis stops after its hold ends, never before.
FLOOR_S = HOLD_SECONDS + 300
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
    """Return every run under `runs`, by id; a batch not yet assigned has none."""
    if not runs.is_dir():
        return []
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


class Steps:
    """A session's JSON lines on `out`, one per step, when `enabled`.

    e.g. {"step": "image", "n": 2, "of": 4, "run": "…", "flow": "…", "state": "done"}
    """

    def __init__(self, out: TextIO, enabled: bool) -> None:
        """Print to `out`, or nothing unless `enabled`."""
        self.out = out
        self.enabled = enabled
        self.flag: tuple[str, ...] = ("--progress", "json") if enabled else ()
        self._n = 0

    def step(self, step: str, state: str, **more: object) -> None:
        """Print one step's line."""
        if self.enabled:
            # Flushed: a job reads this from a pipe, line by line, as it happens.
            line = {"step": step, **more, "state": state}
            print(json.dumps(line), file=self.out, flush=True)

    def child(self, total: int = 0) -> TextIO:
        """Return where a `generate` line writes: its image lines become steps."""
        if not self.enabled:
            return self.out
        # A text stream as `_Tee` is; `TextIO` is a type no stream class subclasses.
        return cast("TextIO", _Images(self, total))

    def image(self, item: Mapping[str, Any], total: int) -> None:
        """Print the next image's line, of `total`, naming its run, flow and seed."""
        self._n += 1
        named = {
            key: item.get(key) for key in ("run", "digest", "flow", "version", "seed")
        }
        self.step("image", "done", n=self._n, of=total, **named)


class _Images(io.TextIOBase):
    """Read `generate`'s JSON lines, and print each landed image as a step."""

    def __init__(self, steps: Steps, total: int) -> None:
        """Count images against `total`."""
        self._steps = steps
        self._total = total
        self._held = ""

    def write(self, text: str) -> int:
        """Take `text`, and print a step for each whole render line in it."""
        self._held += text
        *lines, self._held = self._held.split("\n")
        for line in lines:
            item = progress_line(line)
            if item and item.get("stage") == "render" and item.get("state") == "done":
                self._steps.image(item, self._total)
        return len(text)


def run_session(
    args: argparse.Namespace,
    wired: Wiring,
    generate: Generate,
    seams: Seams | None = None,
) -> int:
    """Run one render session and return its exit status.

    0 every flow rendered · 1 a flow failed or a refusal · 3 the create's answer
    was lost · 128+n a signal ended it. Every refusal reaches the batch's log too,
    through the caller under `--progress json`.
    """
    seams = wired.session if seams is None else seams
    runs = Path(args.runs)
    if not runs.is_dir():
        print(
            f"refused: {runs} is not a directory; give the batch's runs/",
            file=wired.err,
        )
        return 1
    steps = Steps(wired.out, getattr(args, "progress", None) == "json")
    with contextlib.ExitStack() as held:
        logged = wired
        # Under `--progress json` stdout is the caller's channel and stderr its
        # log; teeing here too would write every line twice.
        if not steps.enabled:
            log = held.enter_context(
                (runs.parent / "log.txt").open("a", encoding="utf-8")
            )
            logged = dataclasses.replace(
                wired, out=_Tee(wired.out, log), err=_Tee(wired.err, log)
            )
        try:
            limit = getattr(args, "limit", None)
            return _session(
                runs, list(args.requests), limit, logged, generate, seams, steps
            )
        except Refusal as refused:
            print(f"refused: {refused}", file=logged.err)
            return 1


@dataclass(frozen=True)
class Line:
    """One `generate` line of a session, and how many images it renders."""

    flow: str
    head: tuple[str, ...]
    where: tuple[str, ...]
    images: int


@dataclass(frozen=True)
class Timing:
    """`config/render.json`: a session's figures where nothing is recorded.

    Seconds for the boot, an image and the teardown; the limit's factor over the
    estimate; and the volume's rate per hour.
    """

    boot_s: float
    per_image_s: float
    teardown_s: float
    limit_factor: float
    volume_rate: float


def load_timing(path: Path = RENDER_CONFIG) -> Timing:
    """Return the figures `path` declares, refusing a file that lacks one."""
    restore = f"restore it with `git checkout -- {path.relative_to(REPOSITORY)}`"
    try:
        body = json.loads(path.read_text())
    except (OSError, ValueError) as unread:
        raise Refusal(f"{path}: cannot be read ({unread}); {restore}") from unread
    names = [field.name for field in dataclasses.fields(Timing)]
    missing = [
        name
        for name in names
        if not isinstance(body, dict)
        or isinstance(body.get(name), bool)
        or not isinstance(body.get(name), int | float)
    ]
    if missing:
        raise Refusal(f"{path}: records no {', '.join(missing)} number; {restore}")
    return Timing(**{name: float(body[name]) for name in names})


@dataclass(frozen=True)
class Estimate:
    """A session's estimate and its limit, in seconds."""

    seconds: float
    limit_s: int


def recent(runs: Path, ids: Sequence[str], flow: str) -> list[float]:
    """Return the durations of `flow`'s newest recorded renders under `runs`.

    Newest first by when each was written, so only those `RECENT` takes are read.
    """
    found = [
        path for run_id in ids for path in sidecars(Run(run_id, runs / run_id), flow)
    ]
    found.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    taken: list[float] = []
    for path in found:
        if (seconds := duration(path)) is not None:
            taken.append(seconds)
            if len(taken) == RECENT:
                break
    return taken


def estimate(
    images: Mapping[str, int],
    recorded: Mapping[str, Sequence[float]],
    timing: Timing,
    ceiling_s: int,
) -> Estimate:
    """Return a session's estimate and its limit, both in seconds.

    The limit is the estimate times the factor, at least `FLOOR_S` and at most
    `ceiling_s`.
    e.g. 4 images at a recorded median of 90 s, boot 180, teardown 120, factor 1.5
         -> Estimate(660.0, 1200), the floor
    """
    seconds = timing.boot_s + timing.teardown_s
    for flow, count in images.items():
        seconds += count * statistics.median(recorded.get(flow) or [timing.per_image_s])
    limit = min(ceiling_s, max(FLOOR_S, math.ceil(seconds * timing.limit_factor)))
    return Estimate(seconds, limit)


def _estimated(
    runs: Path,
    ids: Sequence[str],
    images: Mapping[str, int],
    timing: Timing,
    ceiling_s: int,
) -> Estimate:
    """Return the estimate for `images` from what `runs` has recorded.

    The quote and the session both take it here, so the two cannot disagree.
    """
    recorded = {flow: recent(runs, ids, flow) for flow in images}
    return estimate(images, recorded, timing, ceiling_s)


def progress_line(raw: str) -> dict[str, Any] | None:
    """Return a `--progress json` line as a mapping, or None for any other line."""
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return found if isinstance(found, dict) else None


def _limit(asked: int | None, ceiling_s: int) -> None:
    """Refuse a `--limit` above `ceiling_s` or below the floor, naming the bound."""
    if asked is None:
        return
    if asked > ceiling_s:
        raise Refusal(
            f"--limit {asked}s is above gpunit.toml's ceiling of {ceiling_s}s; give "
            f"at most --limit {ceiling_s}, or none to have it estimated"
        )
    if asked < FLOOR_S:
        raise Refusal(
            f"--limit {asked}s ends before a pod held for diagnosis stops, at "
            f"{FLOOR_S}s; give at least --limit {FLOOR_S}, or none to have it estimated"
        )


@dataclass(frozen=True)
class Short:
    """What a batch lacks of its approvals, what is left out, and what is damaged."""

    lines: list[Line]
    # (run, flow, images), e.g. ("0d4b…_ada", "summon-anime-wai", 2)
    wanted: list[tuple[str, str, int]]
    # (run, flow, reason), e.g. ("0d4b…_ada", "summon-anime-wai", "a draft")
    left_out: list[tuple[str, str, str]]
    refused: list[str]

    @property
    def images(self) -> dict[str, int]:
        """Return how many images each flow renders."""
        return _images(self.lines)

    @property
    def blocked(self) -> str | None:
        """Return why nothing would render, or None while something would."""
        if self.refused:
            return self.refused[0]
        if not self.lines:
            return "Every approved source × flow already has its Count of images."
        return None


def _images(lines: Sequence[Line]) -> dict[str, int]:
    """Return how many images `lines` render, by flow."""
    found: dict[str, int] = {}
    for line in lines:
        found[line.flow] = found.get(line.flow, 0) + line.images
    return found


def short(runs: Path, ids: Sequence[str], wired: Wiring) -> Short:
    """Return a line per flow with approvals short of their count, and what is not.

    A run without a flow's directory is skipped; one holding it unapproved is left
    out. A damaged approval is refused, so the session refuses before renting.
    """
    tracked = tracked_flows(wired.flows_dir)
    loaded: dict[str, Flow] = {}
    wanted: list[tuple[str, str, int]] = []
    left_out: list[tuple[str, str, str]] = []
    refused: list[str] = []
    for run_id in ids:
        run = Run(run_id, runs / run_id)
        for flow in (name for name in run.flows if name in tracked):
            if not approved_versions(run.directory(flow, REVIEW)):
                left_out.append((run_id, flow, _unready(run, flow)))
                continue
            if flow not in loaded:
                loaded[flow] = load_flow(flow, wired.flows_dir)
            try:
                lacking = shortfall(run, loaded[flow])
            except Refusal as damaged:
                refused.append(str(damaged))
                continue
            if lacking:
                wanted.append((run_id, flow, lacking))
    lines = []
    for flow in sorted({flow for _, flow, _ in wanted}):
        held = [(run_id, n) for run_id, named, n in wanted if named == flow]
        where = ("--runs", str(runs), *(run_id for run_id, _ in held))
        lines.append(Line(flow, ("--flow", flow), where, sum(n for _, n in held)))
    return Short(lines, wanted, left_out, refused)


@dataclass(frozen=True)
class Quote:
    """What a render of a batch would do, how long it may take, and its price."""

    short: Short
    estimate: Estimate
    timing: Timing
    # Dollars: the estimate's price, the limit's, and the window kept open after.
    about: float
    at_most: float
    keep_open: float


def quote(runs: Path, wired: Wiring) -> Quote:
    """Return the quote for rendering what `runs` is short of, as the session would.

    The price is at `gpunit.toml`'s `max_hourly`, which gpunit refuses a card
    above, with the volume at `config/render.json`'s rate (D4).
    """
    bound = gpu.bounds(REPOSITORY)
    if bound.max_hourly is None or bound.volume_ceiling_s is None:
        raise Refusal(
            "gpunit.toml sets no max_hourly or volume_ceiling, so no price is a "
            "bound; restore them with `git checkout -- gpunit.toml`"
        )
    timing = load_timing()
    ids = run_ids(runs)
    found = short(runs, ids, wired)
    estimated = _estimated(runs, ids, found.images, timing, bound.ceiling_s)
    hourly = bound.max_hourly + timing.volume_rate
    return Quote(
        found,
        estimated,
        timing,
        about=estimated.seconds / 3600 * hourly,
        at_most=estimated.limit_s / 3600 * hourly,
        keep_open=bound.volume_ceiling_s / 3600 * timing.volume_rate,
    )


def _unready(run: Run, flow: str) -> str:
    """Return why `flow` is not approved in `run`, as the dialog names it."""
    if current_draft(run.directory(flow, REVIEW)) is not None:
        return "a draft"
    if latest_artifact(run.directory(flow, SHEETS)) is not None:
        return "a sheet not yet reviewed"
    return "not yet prepared"


def _session(
    runs: Path,
    texts: list[str],
    asked: int | None,
    wired: Wiring,
    generate: Generate,
    seams: Seams,
    steps: Steps,
) -> int:
    requests = [parse_request(text) for text in texts]
    deferred = in_session_sources(requests)
    ceiling_s = gpu.bounds(REPOSITORY).ceiling_s
    _limit(asked, ceiling_s)
    timing = load_timing()
    ids = run_ids(runs)
    flows = [arg for request in requests for arg in ("--flow", request.flow)]
    if not ids and requests:
        photos = shlex.quote(str(runs.parent / BATCH_PHOTOS))
        raise Refusal(
            f"{runs} holds no run; open them from the batch's photographs with: "
            f"uv run python -m isekai tag {' '.join(flows)} --runs "
            f"{shlex.quote(str(runs))} {photos}/*"
        )
    where = ("--runs", str(runs), *ids)

    # Free work first: every prompt is assembled, and every source checked, before
    # anything is rented.
    free = dataclasses.replace(wired, client=None, image=None, out=steps.child())
    verb = ["generate", *steps.flag]
    if requests:
        if generate([*verb, *flows, *where], free) != 0:
            return 1
        for request, late in zip(requests, deferred, strict=True):
            if request.by_count:
                continue
            check = "--in-step-with" if late else "--seeds-from"
            argv = [*verb, "--flow", request.flow, check, request.value, *where]
            if generate(argv, free) != 0:
                return 1
        counts = {r.flow: int(r.value) for r in requests if r.by_count}
        lines = [_requested(request, runs, ids, counts, wired) for request in requests]
    else:
        found = short(runs, ids, wired)
        for message in found.refused:
            print(f"refused: {message}", file=wired.err)
        if found.refused:
            return 1
        for run_id, flow, reason in found.left_out:
            print(f"left out: {run_id}: {flow} is {reason}", file=wired.err)
        lines = found.lines
        if not lines:
            print("nothing is short of its count; nothing was rented", file=wired.err)
            return 0
        for line in lines:
            if generate([*verb, *line.head, *line.where], free) != 0:
                return 1

    if seams.busy(PORT):
        raise Refusal(
            f"127.0.0.1:{PORT} already answers, and would be rendered against; "
            f"lsof -iTCP:{PORT} -sTCP:LISTEN shows what holds it"
        )

    limit = asked or _estimated(runs, ids, _images(lines), timing, ceiling_s).limit_s
    again = shlex.join(["uv", "run", "python", "-m", "isekai", "render", str(runs)])
    rest = "".join(f" {text}" for text in texts)

    def reached() -> None:
        print(
            f"refused: the session reached its {limit}s limit; renders so far are "
            f"kept, and in a new session `{again}{rest}` renders only the rest",
            file=wired.err,
        )
        seams.kill()

    print(f"session limit {limit}s", file=wired.err)
    # Started before the session opens, so it counts from before the pod (D36).
    watchdog = threading.Timer(
        limit if seams.watchdog_s is None else seams.watchdog_s, reached
    )
    watchdog.daemon = True
    watchdog.start()
    try:
        return _rendered(lines, limit, wired, generate, seams, steps)
    finally:
        watchdog.cancel()


def _requested(
    request: Request,
    runs: Path,
    ids: Sequence[str],
    counts: Mapping[str, int],
    wired: Wiring,
) -> Line:
    """Return a request's line, with the most images it renders across `ids`.

    `counts` is each by-count request's count, by flow. A count renders at most
    that many per run; a source renders its latest seeds, or its own count where
    it renders first in this session.
    """
    if request.by_count:
        images = counts[request.flow] * len(ids)
    elif request.value in counts:
        images = counts[request.value] * len(ids)
    else:
        suffix = load_flow(request.value, wired.flows_dir).output_suffix
        images = 0
        for run_id in ids:
            groups = render_groups(Run(run_id, runs / run_id), request.value)
            images += len(rendered_seeds(groups[-1], suffix)) if groups else 0
    head = ("--flow", request.flow, request.mode, request.value)
    return Line(request.flow, head, ("--runs", str(runs), *ids), images)


def _rendered(
    lines: list[Line],
    limit: int,
    wired: Wiring,
    generate: Generate,
    seams: Seams,
    steps: Steps,
) -> int:
    from gpunit import Lost, Refused, TeardownFailed

    def say(line: str) -> None:
        print(line, file=wired.err)

    try:
        environ = gpu.environ_of(seams)
        steps.step("pod", "starting")
        with seams.open_session(REPOSITORY, environ, say, limit) as session:
            server = f"http://127.0.0.1:{session.port(PORT)}"
            client = seams.connect(server)
            await_endpoint(client, server, seams.wait_s, seams.poll_s)
            steps.step("pod", "ready")
            out = steps.child(sum(line.images for line in lines))
            live = dataclasses.replace(
                wired, client=client, image=session.image, out=out
            )
            # One flow failing does not cost the next its render; the exit says so.
            failed = False
            for line in lines:
                argv = [
                    "generate",
                    *steps.flag,
                    *line.head,
                    "--server",
                    server,
                    *line.where,
                ]
                failed |= generate(argv, live) != 0
        steps.step("teardown", "done")
        return int(failed)
    except KeyboardInterrupt as stopped:
        # gpunit deletes the pod on every exit, an interrupt included.
        steps.step("teardown", "done")
        # gpunit's `Interrupted` carries the signal; a bare Ctrl-C is SIGINT.
        return 128 + int(getattr(stopped, "signal", signal.SIGINT))
    # gpunit's CLI reads no .env, where the key lives, so each remedy loads it.
    except Lost:
        steps.step("pod", "lost")
        print(
            "refused: the provider's answer was lost; "
            "`uv run --env-file .env gpunit status` shows what is left, "
            "and `uv run --env-file .env gpunit down` deletes it",
            file=wired.err,
        )
        return LOST_EXIT
    except TeardownFailed:
        steps.step("teardown", "failed")
        print(
            "refused: the session's teardown failed, and its pod may still bill; "
            "run `uv run --env-file .env gpunit down`",
            file=wired.err,
        )
        return 1
    except Refused as refused:
        steps.step("pod", "refused")
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
