"""`isekai render`: one whole render session on a rented GPU, torn down on every exit.

    python -m isekai render <runs>… [<flow>=<count|source> ...]
    e.g. python -m isekai render .data/b1/runs
         python -m isekai render .data/b1/runs .data/b2/runs
         python -m isekai render .data/b1/runs summon-anime-wai=1 conjure-anime-wai=1
         python -m isekai render .data/b1/runs control-anime-wai=summon-anime-wai
         python -m isekai render .data/b1/runs --without .data/b1/runs/<run-id>/<flow>

With no request, every approval short of its count renders what it lacks, in each
collection named, less each `--without`, on one pod. A count draws that many seeds;
a source flow renders its latest seeds again; a request takes one collection, and
no `--without`. A source rendered by count
in the same line goes first, in the same session. Output is shown and appended to
each collection's log, `<runs>/../log.txt` (D36); with `--progress json` the prose
goes to stderr alone, which the caller keeps, as the app's job does. Once the pod
is asked for, each collection keeps the session's record at
`<runs>/../sessions/<id>.json`.
"""

import argparse
import contextlib
import dataclasses
import fcntl
import io
import re
import shlex
import signal
import threading
import time
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from isekai.boundary import gpu
from isekai.boundary.comfy import ComfyTransport, read_runtime
from isekai.boundary.gpu import Seams
from isekai.boundary.pod_start import HOLD_SECONDS as HOLD_SECONDS
from isekai.foundation.artifacts import (
    SESSION_FILE,
    SESSIONS,
    SessionPlan,
    SessionRecord,
    create,
    replace,
    session_id,
)
from isekai.foundation.flow import load_flow, tracked_flows
from isekai.foundation.library import UNSUPPORTED
from isekai.foundation.library import record_running as record_running
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    REPOSITORY,
    Run,
    command,
    render_groups,
    rendered_seeds,
    runs_in,
)
from isekai.interface.compare_view import COLLECTION_PHOTOS
from isekai.interface.plan import (
    FLOOR_S,
    Edits,
    Line,
    Quote,
    _images,
    _plan,
    edits_of,
    estimated,
    load_timing,
    short,
)

# These moved to `plan.py` and stay importable from here.
from isekai.interface.plan import NOTHING_SHORT as NOTHING_SHORT
from isekai.interface.plan import RECENT as RECENT
from isekai.interface.plan import RENDER_CONFIG as RENDER_CONFIG
from isekai.interface.plan import Estimate as Estimate
from isekai.interface.plan import Short as Short
from isekai.interface.plan import Timing as Timing
from isekai.interface.plan import Work as Work
from isekai.interface.plan import _unready as _unready
from isekai.interface.plan import edit_records as edit_records
from isekai.interface.plan import estimate as estimate
from isekai.interface.plan import pending_edits as pending_edits
from isekai.interface.plan import recent as recent
from isekai.interface.plan import recent_edits as recent_edits

# The tests import `_Images` and `progress_line` from here.
from isekai.interface.progress import ARGUMENT, FORMAT, Steps
from isekai.interface.progress import _Images as _Images
from isekai.interface.progress import progress_line as progress_line
from isekai.interface.wiring import Wiring

# The port `gpunit.toml` forwards, on both sides; a test holds the two equal.
PORT = 8188
# gpunit's exit for a create whose answer was lost.
LOST_EXIT = 3
# gpunit's exits for a refusal with a kind, and how the terminal and the drawer name it.
REFUSALS = {4: "no card in stock", 5: "no card fits max_hourly / vram_gb"}

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

    Such a source has no seeds until the pod is up, so its dependent has no check
    before the pod; one placed before its source could never take its seeds, and
    is refused. So is a request whose source is another source request's flow, in
    either order: its seeds are the ones that request takes, so it names them.
    """
    counted = {r.flow: i for i, r in enumerate(requests) if r.by_count}
    sourced = {r.flow: r for r in requests if not r.by_count}
    deferred = []
    for i, request in enumerate(requests):
        chain = None if request.by_count else sourced.get(request.value)
        if chain is not None and chain is not request:
            raise Refusal(
                f"'{request}' takes its seeds from '{chain}', itself a source "
                f"request; write '{request.flow}={chain.value}' for the same seeds"
            )
        j = None if request.by_count else counted.get(request.value)
        if j is not None and j > i:
            raise Refusal(
                f"'{request}' comes before its source '{requests[j]}'; "
                "put the source first"
            )
        deferred.append(j is not None)
    return deferred


def again(roots: Sequence[Path], without: Sequence[Path] = ()) -> str:
    """Return the command that renders what each of `roots` lacks, in one session.

    Each of `without` stays out of it, as its `--without`.
    """
    argv = ["uv", "run", "python", "-m", "isekai", "render", *map(str, roots)]
    return shlex.join([*argv, *without_flags(without)])


def without_flags(without: Sequence[Path]) -> list[str]:
    """Return a `--without` per path, as `isekai render` takes them.

    e.g. [Path("b/runs/r1/f")] -> ["--without", "b/runs/r1/f"]
    """
    return [arg for path in without for arg in ("--without", str(path))]


def _taken(roots: Sequence[Path], without: Sequence[Path]) -> list[Path]:
    """Return each of `without` under the one of `roots` it names, as that is named.

    Refuse a path under no root, or naming no run's flow there.
    e.g. roots [Path("b/runs")], without [Path("./b/runs/r1/f")] -> [b/runs/r1/f]
    """
    named = {runs.resolve(): runs for runs in roots}
    taken = []
    for path in without:
        runs = named.get(path.parent.parent.resolve())
        if runs is None:
            raise Refusal(
                f"--without {path} is under no runs root this session names; "
                "name its collection's runs/ too, or drop it"
            )
        run_id, flow = path.parent.name, path.name
        if run_id not in run_ids(runs) or flow not in Run(run_id, runs / run_id).flows:
            raise Refusal(
                f"--without {path} names no run's flow; give <runs>/<run-id>/<flow>"
            )
        taken.append(runs / run_id / flow)
    return taken


def run_ids(runs: Path) -> list[str]:
    """Return every run under `runs`, by id; a collection not yet assigned has none."""
    return [run.id for run in runs_in(runs)]


class _Tee(io.TextIOBase):
    """Write to the terminal's stream and the collection's log alike."""

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


def _utc(moment: datetime) -> str:
    """Return `moment` as the record spells a time, e.g. 2026-10-24T09:12:00Z."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class Record:
    """A session's record in `folder`, written whole at each change once opened.

    Nothing is written before `open`, so a session refused before renting leaves
    no record (D2).
    """

    def __init__(
        self,
        folder: Path,
        given: str | None,
        limit: int,
        asked: Mapping[str, int],
        planned: Sequence[SessionPlan] = (),
        others: Sequence[str] = (),
        order: Sequence[str] = (),
    ) -> None:
        """Name the record by `given`, else by its start, once it opens.

        `others` names the session's other collections; a session of one has none.
        `order` names all collections in traversal order, including this one.
        """
        self._folder = folder
        self._given = given
        # Where the record is, once open: the one sign it is written.
        self._path: Path | None = None
        self._held: TextIO | None = None
        self._body: SessionRecord = {
            "schema": SESSION_FILE.schema,
            "id": "",
            "started": "",
            "ended": None,
            "limit": limit,
            "asked": dict(asked),
            "planned": list(planned),
            "steps": {},
            "images": [],
            "outcome": "running",
            "message": None,
        }
        if others:
            self._body["collections"] = list(others)
        if order:
            self._body["collection_order"] = list(order)

    def open(self, started: datetime | None = None) -> None:
        """Write the record as running, started now unless `started` is given."""
        started = started or datetime.now(UTC)
        name = self._given or session_id(started)
        self._body["id"], self._body["started"] = name, _utc(started)
        path = self._folder / f"{name}.json"
        self._folder.mkdir(parents=True, exist_ok=True)
        self._held = path.with_suffix(".lock").open("a")
        try:
            fcntl.flock(self._held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            create(path, SESSION_FILE, self._body)
        except (BlockingIOError, FileExistsError):
            self.close()
            raise Refusal(
                f"session {name} already exists; choose another --session id "
                "or wait until the next second and render again"
            ) from None
        except OSError as failure:
            self.close()
            if failure.errno not in UNSUPPORTED:
                raise
            raise Refusal(
                f"{self._folder} cannot hold a session record: its filesystem has "
                f"no hard links or file locks ({failure.strerror}); keep the "
                "collection on a disk with both, such as the default .data/, and "
                "render again"
            ) from None
        except BaseException:
            self.close()
            raise
        self._path = path

    def close(self) -> None:
        """Release the process's liveness lock without inventing an outcome."""
        if self._held is not None:
            self._held.close()
            self._held = None

    def withdraw(self) -> None:
        """Delete the record this process opened, and release its lock."""
        if self._path is not None:
            self._path.unlink(missing_ok=True)
            self._path = None
        self.close()

    def step(self, step: str, state: str) -> None:
        """Record `step` at `state`."""
        self._body["steps"][step] = state
        self._write()

    def image(self, item: Mapping[str, Any]) -> None:
        """Record the image a `generate` line landed."""
        self._body["images"].append(
            {
                "digest": item["digest"],
                "flow": item["flow"],
                "version": item["version"],
                "seed": item["seed"],
            }
        )
        self._write()

    def end(self, outcome: str, message: str | None = None) -> None:
        """Record the session ended at `outcome`."""
        self._body["ended"] = _utc(datetime.now(UTC))
        self._body["outcome"] = outcome
        self._body["message"] = message
        self._write()

    def _write(self) -> None:
        if self._path is not None:
            replace(self._path, SESSION_FILE, self._body)


class Records:
    """A session's records, one per collection it renders, all of one id.

    The pod's and the teardown's steps and the outcome reach every record; an
    image reaches its own collection's alone.
    """

    def __init__(self, held: Mapping[Path, Record]) -> None:
        """Keep a record per runs root."""
        self._held = dict(held)
        # Why the session is ending, when the watchdog ends it.
        self.note: str | None = None

    def open(self) -> None:
        """Write every record as running, or none: a refused one withdraws the rest."""
        started = datetime.now(UTC)
        opened: list[Record] = []
        try:
            for record in self._held.values():
                record.open(started)
                opened.append(record)
        except BaseException:
            for record in opened:
                record.withdraw()
            raise

    def close(self) -> None:
        """Release every record's lock."""
        for record in self._held.values():
            record.close()

    def step(self, step: str, state: str) -> None:
        """Record `step` at `state` in every record."""
        for record in self._held.values():
            record.step(step, state)

    def image(self, item: Mapping[str, Any], runs: Path) -> None:
        """Record the image a `generate` line over `runs` landed, in its record."""
        self._held[runs].image(item)

    def end(self, outcome: str, message: str | None = None) -> None:
        """Record the session ended at `outcome` in every record."""
        for record in self._held.values():
            record.end(outcome, message)


def run_session(
    args: argparse.Namespace,
    wired: Wiring,
    generate: Generate,
    seams: Seams | None = None,
) -> int:
    """Run one render session and return its exit status.

    0 every flow rendered · 1 a flow failed or a refusal · 3 the create's answer
    was lost · 4 no card in stock · 5 no card fits · 128+n a signal ended it.
    Every refusal reaches the collection's log too, through the caller under
    `--progress json`.
    """
    seams = wired.session if seams is None else seams
    roots = [Path(runs) for runs in args.runs]
    for runs in roots:
        if not runs.is_dir():
            print(
                f"refused: {runs} is not a directory; give the collection's runs/",
                file=wired.err,
            )
            return 1
    without = list(getattr(args, "without", None) or [])
    once = list(dict.fromkeys(runs.resolve() for runs in roots))
    if len(once) < len(roots):
        try:
            retry = again(once, _taken(once, without))
        except Refusal as refused:
            print(f"refused: {refused}", file=wired.err)
            return 1
        print(
            f"refused: a collection's runs/ is named twice; name each once: `{retry}`",
            file=wired.err,
        )
        return 1
    json_lines = getattr(args, "progress", None) == FORMAT
    with contextlib.ExitStack() as held:
        logged = wired
        # Under `--progress json` stdout is the caller's channel and stderr its
        # log; teeing here too would write every line twice.
        if not json_lines:
            logs = [
                held.enter_context(
                    (runs.parent / "log.txt").open("a", encoding="utf-8")
                )
                for runs in roots
            ]
            logged = dataclasses.replace(
                wired, out=_Tee(wired.out, *logs), err=_Tee(wired.err, *logs)
            )
        # On the teed stream, so each `generate` line reaches the log as well.
        steps = Steps(logged.out, json_lines)
        try:
            limit = getattr(args, "limit", None)
            given = getattr(args, "session", None)
            return _session(
                roots,
                list(args.requests),
                without,
                limit,
                given,
                logged,
                generate,
                seams,
                steps,
            )
        except Refusal as refused:
            print(f"refused: {refused}", file=logged.err)
            return 1


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


def quote(
    roots: Sequence[Path], wired: Wiring, without: Collection[Path] = ()
) -> Quote:
    """Return the quote for one session over what each of `roots` is short of.

    As the session would: one boot over every collection's images and pending
    edits, less each `<runs>/<run-id>/<flow>` in `without`. The price is
    at `gpunit.toml`'s `max_hourly`, which gpunit refuses a card above, with the
    volume at `config/render.json`'s rate (D26).
    """
    bound = gpu.bounds(REPOSITORY)
    if bound.max_hourly is None or bound.volume_ceiling_s is None:
        raise Refusal(
            "gpunit.toml sets no max_hourly or volume_ceiling, so no price is a "
            "bound; restore them with `git checkout -- gpunit.toml`"
        )
    timing = load_timing()
    ids = {runs: run_ids(runs) for runs in roots}
    found = {runs: short(runs, ids[runs], wired, without) for runs in roots}
    tracked = tracked_flows(wired.flows_dir)
    held = {runs: edits_of(runs, ids[runs], tracked, without) for runs in roots}
    shorts = {
        runs: one
        for runs, one in found.items()
        if one.lines or one.refused or held[runs].count
    }
    work = [(runs, ids[runs], one.images) for runs, one in shorts.items()]
    pending_count = {runs: held[runs].count for runs in shorts}
    guess = estimated(work, timing, bound.ceiling_s, pending_count)
    hourly = bound.max_hourly + timing.volume_rate
    return Quote(
        shorts,
        held,
        guess,
        timing,
        bound.ceiling_s,
        about=guess.seconds / 3600 * hourly,
        at_most=guess.limit_s / 3600 * hourly,
        keep_open=bound.volume_ceiling_s / 3600 * timing.volume_rate,
    )


def _session(
    roots: list[Path],
    texts: list[str],
    without: list[Path],
    asked: int | None,
    given: str | None,
    wired: Wiring,
    generate: Generate,
    seams: Seams,
    steps: Steps,
) -> int:
    requests = [parse_request(text) for text in texts]
    if requests and without:
        raise Refusal(
            "--without takes a run's flow out of what each approval lacks, and a "
            "request names what renders; give one or the other"
        )
    deferred = in_session_sources(requests)
    taken = _taken(roots, without)
    retry = again(roots, taken)
    if requests and len(roots) > 1:
        raise Refusal(
            f"{requests[0]} renders one collection's runs; render each collection "
            f"apart, or what every one lacks with `{retry}`"
        )
    ceiling_s = gpu.bounds(REPOSITORY).ceiling_s
    _limit(asked, ceiling_s)
    timing = load_timing()
    ids = {runs: run_ids(runs) for runs in roots}

    # Free work first: every prompt is assembled, and every source and pending edit
    # checked, before anything is rented. A request names renders and runs no edit.
    free = dataclasses.replace(wired, client=None, image=None, out=steps.child())
    verb = ["generate", *steps.flag]
    edits: dict[Path, Edits] = {}
    if requests:
        (runs,) = roots
        lines = _asked(runs, ids[runs], requests, deferred, free, verb, generate)
        if lines is None:
            return 1
    else:
        lines: list[Line] = []
        refused = False
        tracked = tracked_flows(wired.flows_dir)
        for runs in roots:
            found = short(runs, ids[runs], wired, taken)
            for message in found.refused:
                print(f"refused: {message}", file=wired.err)
            for run_id, flow, reason in found.left_out:
                print(f"left out: {run_id}: {flow} is {reason}", file=wired.err)
            refused |= bool(found.refused)
            lines += found.lines
            edits[runs] = edits_of(runs, ids[runs], tracked, taken)
        if refused:
            return 1
        if not lines and not any(held.cells for held in edits.values()):
            print("nothing is short of its count; nothing was rented", file=wired.err)
            return 0
        for line in lines:
            if generate([*verb, *line.head, *line.where], free) != 0:
                return 1
        for runs, held in edits.items():
            if held.cells and generate(_edit_argv(runs, held, steps.flag), free) != 0:
                return 1

    if seams.busy(PORT):
        raise Refusal(
            f"127.0.0.1:{PORT} already answers, and would be rendered against; "
            f"lsof -iTCP:{PORT} -sTCP:LISTEN shows what holds it"
        )

    held = {
        runs: its
        for runs in roots
        if (its := [li for li in lines if li.runs == runs])
        or (runs in edits and edits[runs].cells)
    }
    work = [(runs, ids[runs], _images(its)) for runs, its in held.items()]
    pending_count = {runs: edits[runs].count for runs in held if runs in edits}
    limit = asked or estimated(work, timing, ceiling_s, pending_count).limit_s
    rest = "".join(f" {text}" for text in texts)
    names = [runs.parent.name for runs in held]
    record = Records(
        {
            runs: Record(
                runs.parent / SESSIONS,
                given,
                limit,
                _images(its),
                _plan(runs, its),
                [name for name in names if name != runs.parent.name],
                order=names,
            )
            for runs, its in held.items()
        }
    )
    steps.record = record

    def reached() -> None:
        ended = (
            f"the session reached its {limit}s limit; renders so far are "
            f"kept, and in a new session `{retry}{rest}` renders only the rest"
        )
        record.note = ended
        print(f"refused: {ended}", file=wired.err)
        seams.kill()

    print(f"session limit {limit}s", file=wired.err)
    # Started before the session opens, so it counts from before the pod (D36).
    watchdog = threading.Timer(
        limit if seams.watchdog_s is None else seams.watchdog_s, reached
    )
    watchdog.daemon = True
    watchdog.start()
    try:
        return _rendered(lines, edits, limit, wired, generate, seams, steps, record)
    finally:
        watchdog.cancel()
        record.close()


def _asked(
    runs: Path,
    ids: Sequence[str],
    requests: Sequence[Request],
    deferred: Sequence[bool],
    free: Wiring,
    verb: Sequence[str],
    generate: Generate,
) -> list[Line] | None:
    """Return the requests' lines over `runs` once their free checks pass, else None."""
    flows = [arg for request in requests for arg in ("--flow", request.flow)]
    if not ids:
        photos = shlex.quote(str(runs.parent / COLLECTION_PHOTOS))
        asked = command(
            "assign", " ".join(flows), "--runs", shlex.quote(str(runs)), f"{photos}/*"
        )
        raise Refusal(
            f"{runs} holds no run; open them from the collection's photographs with: "
            f"uv run {asked}"
        )
    where = ("--runs", str(runs), *ids)
    if generate([*verb, *flows, *where], free) != 0:
        return None
    for request, late in zip(requests, deferred, strict=True):
        if request.by_count or late:
            continue
        argv = [*verb, "--flow", request.flow, "--seeds-from", request.value, *where]
        if generate(argv, free) != 0:
            return None
    counts = {r.flow: int(r.value) for r in requests if r.by_count}
    return [_requested(request, runs, ids, counts, free) for request in requests]


def _requested(
    request: Request,
    runs: Path,
    ids: Sequence[str],
    counts: Mapping[str, int],
    wired: Wiring,
) -> Line:
    """Return a request's line, planned per run in `ids`.

    `counts` is each by-count request's count, by flow. A by-count request plans
    its count; a source request plans the count of a by-count source in the line,
    else the images its source holds now. A source of a source never reaches it.
    """
    if request.by_count:
        planned = [(run_id, counts[request.flow]) for run_id in ids]
    elif request.value in counts:
        planned = [(run_id, counts[request.value]) for run_id in ids]
    else:
        suffix = load_flow(request.value, wired.flows_dir).output_suffix
        planned = []
        for run_id in ids:
            groups = render_groups(Run(run_id, runs / run_id), request.value)
            seeds = rendered_seeds(groups[-1], suffix) if groups else []
            planned.append((run_id, len(seeds)))
    head = ("--flow", request.flow, request.mode, request.value)
    where = ("--runs", str(runs), *ids)
    return Line(runs, request.flow, head, where, tuple(planned))


def _edit_argv(
    runs: Path, held: Edits, flag: Sequence[str], server: str | None = None
) -> list[str]:
    """Return the `edit --pending` line over `held`'s cells, on `server` when given.

    e.g. ("r1/f",) -> edit --pending r1/f --runs <runs>; with a server, only the
    checks are skipped and the edits are sampled
    """
    where = ["--server", server] if server is not None else []
    return ["edit", *flag, "--pending", *held.cells, *where, "--runs", str(runs)]


def _rendered(
    lines: list[Line],
    edits: Mapping[Path, Edits],
    limit: int,
    wired: Wiring,
    generate: Generate,
    seams: Seams,
    steps: Steps,
    record: Records,
) -> int:
    from gpunit import Lost, Refused, TeardownFailed

    def say(line: str) -> None:
        print(line, file=wired.err)

    def refuse(message: str) -> None:
        record.end("failed", message)
        print(f"refused: {message}", file=wired.err)

    opened = False
    try:
        environ = gpu.environ_of(seams)
        record.open()
        steps.step("pod", "starting")
        with seams.open_session(REPOSITORY, environ, say, limit) as session:
            opened = True
            server = f"http://127.0.0.1:{session.port(PORT)}"
            client = seams.connect(server)
            await_endpoint(client, server, seams.wait_s, seams.poll_s)
            steps.step("pod", "ready")
            total = sum(line.images for line in lines)
            # One flow failing does not cost the next its render; the exit says so.
            failed = False
            for line in lines:
                live = dataclasses.replace(
                    wired,
                    client=client,
                    image=session.image,
                    out=steps.child(total, line.runs),
                )
                # JSON whatever the session prints, so each image reaches the record;
                # its prose goes to stderr, which the log tees.
                argv = [
                    "generate",
                    *ARGUMENT,
                    *line.head,
                    "--server",
                    server,
                    *line.where,
                ]
                failed |= generate(argv, live) != 0
            # After the renders, in the pod they were rendered in; an edit's own
            # record says what it did, and the session's stay a render's.
            for runs, held in edits.items():
                if not held.cells:
                    continue
                live = dataclasses.replace(
                    wired, client=client, image=session.image, out=steps.child(0, runs)
                )
                argv = _edit_argv(runs, held, ARGUMENT, server)
                failed |= generate(argv, live) != 0
        steps.step("teardown", "done")
        if failed:
            record.end("failed", "a flow failed; the collection's log names it")
        else:
            record.end("done")
        return int(failed)
    except KeyboardInterrupt as stopped:
        # gpunit deletes the pod on every exit, an interrupt included.
        steps.step("teardown", "done")
        record.end("stopped", record.note)
        # gpunit's `Interrupted` carries the signal; a bare Ctrl-C is SIGINT.
        return 128 + int(getattr(stopped, "signal", signal.SIGINT))
    # gpunit's CLI reads no .env, where the key lives, so each remedy loads it.
    except Lost:
        steps.step("pod", "lost")
        refuse(
            "the provider's answer was lost; "
            "`uv run --env-file .env gpunit status` shows what is left, "
            "and `uv run --env-file .env gpunit down` deletes it"
        )
        return LOST_EXIT
    except TeardownFailed as failed:
        steps.step("teardown", "failed")
        if isinstance(failed.__cause__, Refusal):
            print(f"refused: {failed.__cause__}", file=wired.err)
        refuse(
            "the session's teardown failed, and its pod may still bill; "
            "run `uv run --env-file .env gpunit down`"
        )
        return 1
    except Refused as refused:
        steps.step("pod", "refused")
        record.end("failed", str(refused))
        # gpunit has written its own `refused:` line through `say`, so its kind
        # follows it. Where it names a bare `gpunit <verb>`, the line after it is
        # that command loading the key; a note, not a second refusal.
        if lead := REFUSALS.get(refused.code):
            print(
                f"{lead}, per gpunit's line above; "
                "its skipped lines name each card it passed",
                file=wired.err,
            )
        if remedy := REMEDY.search(str(refused)):
            print(
                "gpunit reads no .env, where the key lives: "
                f"run `uv run --env-file .env gpunit {remedy[1]}`",
                file=wired.err,
            )
        return refused.code
    except Exception as failure:
        # A refusal inside the session, an endpoint that never answered among them,
        # leaves through gpunit's teardown, which a failure would have raised.
        if opened:
            steps.step("teardown", "done")
        record.end("failed", str(failure))
        raise
