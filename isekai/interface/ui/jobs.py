"""Prepare and Render as jobs: the pipeline's own verbs, run as children.

One job of each kind runs at a time, the two side by side. The CLI is the one
path, so a job is exactly what the verbs do. Each child runs in its own session and
reports through `--progress json`; its prose is appended to the collection's `log.txt`,
each line naming its job. A job outlives the page that started it.

```
Prepare ─▶ probe ─ no answer ─▶ refused, nothing runs
            └ answers ─▶ per flow: tag ─▶ caption ─▶ sheet ─▶ done
Render ─▶ volume up ─ lost ─▶ the volume alert, nothing renders
           └ up ─▶ render --limit … --session … --progress json
                 ─▶ volume down, unless kept
Stop ─▶ SIGINT to its kind's child ─▶ no later stage of that job starts
the server stopping ─▶ SIGINT to both children at once
the server stopping mid-render ─▶ says so, then waits for the teardown and the
                                  window's close ─ runs out ─▶ names `volume down`
a child failing with no line reported ─▶ failed, naming log.txt ─▶ no later stage starts
```
"""

import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TextIO, get_args

from isekai.boundary.gpu import Say, Volume
from isekai.foundation.artifacts import session_id
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REPOSITORY
from isekai.interface.render import LOST_EXIT, load_timing, progress_line
from isekai.interface.ui.billing import utc_now
from isekai.interface.ui.events import Broadcast
from isekai.interface.ui.library import LOG, RUNS

# The stages Prepare runs for each flow, in order.
PREPARE = ("tag", "caption", "sheet")

# The kinds of job, each with its own slot.
Kind = Literal["prepare", "render"]
KINDS: tuple[Kind, ...] = get_args(Kind)

# What a refusal calls each kind of job.
LABELS: dict[Kind, str] = {"prepare": "Prepare", "render": "Render"}

# How long a child's log lines are read for once it exits: a grandchild that holds
# the pipe open must not hold the job running.
DRAIN_S = 5.0

# How long a stopping server gives a render's window to close once its pod is torn
# down: one gpunit volume verb.
VOLUME_S = 120.0

# What closes a window a stopping server could not wait for; gpunit reads no .env.
VOLUME_DOWN = "uv run --env-file .env gpunit volume down"


def settle_s() -> float:
    """Return how long a stopping server waits for a render: its teardown and a verb."""
    return load_timing().teardown_s + VOLUME_S


# How a stage is started: the verb, the flow, the runs root and the runs.
Command = Callable[[str, str, Path, Sequence[str]], list[str]]


def isekai_command(verb: str, flow: str, runs: Path, ids: Sequence[str]) -> list[str]:
    """Return the verb line a stage runs as. e.g. `python -m isekai tag --flow f …`."""
    return [
        sys.executable,
        "-m",
        "isekai",
        verb,
        "--flow",
        flow,
        "--runs",
        str(runs),
        "--progress",
        "json",
        *ids,
    ]


# How a render is started: the session's limit, the collection's runs root, its id.
RenderCommand = Callable[[int, Path, str], list[str]]


def render_command(limit: int, runs: Path, session: str) -> list[str]:
    """Return the render verb line. e.g. `python -m isekai render --limit 1200 …`."""
    return [
        sys.executable,
        "-m",
        "isekai",
        "render",
        "--limit",
        str(limit),
        "--session",
        session,
        "--progress",
        "json",
        str(runs),
    ]


@dataclass(frozen=True)
class Step:
    """One child: a verb over one flow's runs."""

    flow: str
    verb: str
    runs: tuple[str, ...]


def plan(todo: Mapping[str, Sequence[str]], tagged: Mapping[str, bool]) -> list[Step]:
    """Return the steps that prepare `todo`'s runs, by flow, skipping `tag` if untagged.

    e.g. {"summon": ["r1"]} -> tag, caption, sheet over r1 in summon
    """
    return [
        Step(flow, verb, tuple(ids))
        for flow, ids in todo.items()
        if ids
        for verb in PREPARE
        if verb != "tag" or tagged[flow]
    ]


@dataclass
class _Job:
    collection: str
    steps: tuple[Step, ...]
    kind: Kind = "prepare"
    state: str = "running"
    flow: str | None = None
    stage: str | None = None
    message: str | None = None
    # A render's session as the page draws it: its steps, its images, its limit.
    session: dict[str, Any] | None = None

    started: str | None = None
    accepted: set[tuple[str, str]] = field(default_factory=set)
    completed: set[tuple[str, str]] = field(default_factory=set)

    def describe(self) -> dict[str, Any]:
        described = {
            "kind": self.kind,
            "collection": self.collection,
            "state": self.state,
            "flow": self.flow,
            "stage": self.stage,
            "message": self.message,
        }
        if self.started is not None:
            described["progress"] = {
                "started": self.started,
                "of": len(self.accepted),
                "done": len(self.completed),
            }
        if self.session is not None:
            described["session"] = {
                **self.session,
                "steps": dict(self.session["steps"]),
                "images": list(self.session["images"]),
            }
        return described


@dataclass
class _Slot:
    """One kind's job, its child and that child's log writer, and its watcher."""

    job: _Job | None = None
    child: subprocess.Popen[str] | None = None
    tee: threading.Thread | None = None
    stopping: bool = False
    thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        """Return whether the slot holds a running job."""
        return self.job is not None and self.job.state == "running"


class Jobs:
    """A slot per kind of job, and the child running in each."""

    def __init__(
        self,
        broadcast: Broadcast,
        probe: Callable[[], None],
        *,
        command: Command = isekai_command,
        volume: Volume | None = None,
        render: RenderCommand = render_command,
        raise_volume: Callable[[], None] = lambda: None,
        now: Callable[[], str] = utc_now,
        settle: Callable[[], float] = settle_s,
        err: TextIO | None = None,
    ) -> None:
        """Hold an empty slot per kind, each publishing on `broadcast`.

        `volume` opens and closes a render's window; `raise_volume` raises the
        volume alert when either goes unanswered. `settle` is how long a stopping
        server waits for a render, and `err` the terminal it says so on.
        """
        self._broadcast = broadcast
        self._probe = probe
        self._command = command
        self._volume = volume or Volume()
        self._render = render
        self._raise_volume = raise_volume
        self._now = now
        self._settle = settle
        self._err = err if err is not None else sys.stderr
        # One lock guards both slots.
        self._lock = threading.Lock()
        self._slots: dict[Kind, _Slot] = {kind: _Slot() for kind in KINDS}
        # How long a running render is waited for when the server stops.
        self._settle_s = 0.0

    def slot(self, kind: Kind) -> dict[str, Any] | None:
        """Return the job in `kind`'s slot, running or ended, or None."""
        with self._lock:
            job = self._slots[kind].job
            return job.describe() if job else None

    def prepare(
        self,
        collection: str,
        folder: Path,
        steps: Sequence[Step],
        cell: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> dict[str, Any]:
        """Start Prepare over `steps`, or refuse: a Prepare running, or no answer.

        `cell` turns a progress line into the event the page applies, or None.
        """
        self._refuse_running("prepare")
        # Outside the lock: a host that is slow to answer holds up no snapshot.
        self._probe()
        with self._lock:
            self._refuse_running("prepare")
            if not steps:
                raise Refusal(
                    f"{collection} has no assigned cell without a sheet; tick a flow "
                    "for a source, then try again"
                )
            job = _Job(
                collection,
                tuple(steps),
                started=self._now(),
                accepted={(step.flow, run) for step in steps for run in step.runs},
            )
            self._occupy(job, self._run, (job, folder, cell))
        self._publish(job)
        return job.describe()

    def running(self, kind: Kind) -> bool:
        """Return whether a job of `kind` is running."""
        with self._lock:
            return self._slots[kind].running

    def render(
        self,
        collection: str,
        folder: Path,
        *,
        limit: int,
        total: int,
        keep_open: bool,
    ) -> dict[str, Any]:
        """Start a render of `folder`'s runs within `limit` seconds, or refuse."""
        # Read before the job starts, so a stopping server reads no file.
        settle = self._settle()
        with self._lock:
            self._refuse_running("render")
            self._settle_s = settle
            steps = dict.fromkeys(("volume up", "pod", "teardown", "volume down"), "")
            if keep_open:
                steps["volume down"] = "kept"
            session = {
                # The verb's record is named by it, so the page can read that record.
                "id": session_id(datetime.now(UTC)),
                "started": self._now(),
                "limit": limit,
                "of": total,
                "ended": None,
                "steps": steps,
                "images": [],
            }
            job = _Job(collection, (), kind="render", session=session)
            self._occupy(job, self._run_render, (job, folder, limit))
        self._publish(job)
        return job.describe()

    def _occupy(self, job: _Job, target: Callable[..., None], args: tuple) -> None:
        """Put `job` in its slot, and start `target` watching it; hold the lock."""
        slot = self._slots[job.kind]
        slot.job, slot.stopping = job, False
        slot.thread = threading.Thread(target=target, args=args, daemon=True)
        slot.thread.start()

    def _refuse_running(self, kind: Kind) -> None:
        """Refuse while a job of `kind` runs, naming it."""
        job = self._slots[kind].job
        if job is not None and self._slots[kind].running:
            raise Refusal(
                f"a job is running: {LABELS[job.kind]} on {job.collection}; wait for "
                "it to end, or "
                "Stop it, then try again"
            )

    def stop(self, kind: Kind) -> dict[str, Any]:
        """Interrupt `kind`'s running stage and start no other, or refuse: none runs."""
        with self._lock:
            slot = self._slots[kind]
            if slot.job is None or not slot.running:
                raise Refusal(
                    f"no {LABELS[kind]} is running, so there is nothing to stop"
                )
            self._interrupt(slot)
            return slot.job.describe()

    def wait(self, kind: Kind, timeout: float | None = None) -> None:
        """Return once the job in `kind`'s slot has ended, or `timeout` has passed."""
        thread = self._slots[kind].thread
        if thread is not None:
            thread.join(timeout)

    def shutdown(self, timeout: float = 10.0) -> None:
        """Interrupt both running jobs at once, and wait: the server is stopping.

        Prepare is waited for `timeout`, and never past a render's wait. A render is
        waited for through its pod's teardown and the window's close, at most its
        teardown estimate and one volume verb, saying so on the terminal: a stop that
        looks hung invites the kill that would leave the window open. A wait that runs
        out with the window not closed names the command that closes it.
        """
        with self._lock:
            render = self._slots["render"].job
            rendering = self._slots["render"].running
            for slot in self._slots.values():
                if slot.running:
                    self._interrupt(slot)
        if rendering:
            timeout = max(timeout, self._settle_s)
            self._say(
                f"stopping mid-render: waiting up to {timeout:.0f}s for the pod's "
                "teardown and the window's close"
            )
        deadline = time.monotonic() + timeout
        for kind in KINDS:
            self.wait(kind, max(0.0, deadline - time.monotonic()))
        if not rendering:
            return
        assert render is not None and render.session is not None
        with self._lock:
            closed = render.session["steps"]["volume down"]
        if closed not in {"done", "kept"}:
            reason = (
                "the window close failed" if closed == "failed" else "the wait ran out"
            )
            self._say(
                f"{reason}, and the window may still be open: close it with "
                f"`{VOLUME_DOWN}`"
            )

    def _say(self, line: str) -> None:
        """Print one line on the server's terminal."""
        print(f"isekai: {line}", file=self._err, flush=True)

    def _interrupt(self, slot: _Slot) -> None:
        """Send `slot`'s child SIGINT, as a Ctrl-C would; hold the lock."""
        slot.stopping = True
        child = slot.child
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGINT)
            except ProcessLookupError:
                pass

    def _run(
        self,
        job: _Job,
        folder: Path,
        cell: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> None:
        """Run each step's child in turn, publishing each line it reports."""
        slot = self._slots[job.kind]
        try:
            for step in job.steps:
                child = self._start(job, step, folder)
                if child is None:
                    break
                self._publish(job)
                assert child.stdout is not None
                reported = False
                for raw in child.stdout:
                    event = progress_line(raw)
                    reported = reported or event is not None
                    found = cell(event) if event is not None else None
                    if found is not None:
                        self._broadcast.publish("cell", found)
                        assert event is not None
                        identity = (str(event.get("flow")), str(event.get("run")))
                        with self._lock:
                            completed = (
                                event.get("stage") == "sheet"
                                and event.get("state") == "done"
                                and found.get("cell", {}).get("stage")
                                in {"sheet", "draft", "approved", "rendered"}
                                and identity in job.accepted
                                and identity not in job.completed
                            )
                            if completed:
                                job.completed.add(identity)
                        if completed:
                            self._publish(job)
                code = self._reap(slot, child)
                with self._lock:
                    slot.child = None
                    # A child that fails before its first line said nothing the
                    # page can show; its reason is in the log.
                    if code != 0 and not reported and not slot.stopping:
                        job.state = "failed"
                        job.message = (
                            f"{step.verb} on {step.flow} ended before reporting "
                            f"(exit {code}); read {job.collection}/{LOG}, then try "
                            "again"
                        )
                        break
        finally:
            with self._lock:
                if job.state == "running":
                    job.state = "stopped" if slot.stopping else "done"
            self._publish(job)

    def _run_render(self, job: _Job, folder: Path, limit: int) -> None:
        """Open the window, run the render verb, and close the window unless kept."""
        assert job.session is not None
        slot = self._slots[job.kind]
        steps = job.session["steps"]
        opened = False
        try:
            self._mark(job, "volume up", "running")
            code = _named(job.kind, folder, self._volume.up)
            if code != 0:
                self._mark(job, "volume up", "lost" if code == LOST_EXIT else "failed")
                if code == LOST_EXIT:
                    self._raise_volume()
                job.state = "failed"
                job.message = (
                    f"gpunit volume up did not open the window (exit {code}); read "
                    f"{job.collection}/{LOG}, and nothing was rendered"
                )
                return
            opened = True
            self._mark(job, "volume up", "done")
            self._render_child(job, folder, limit)
        except OSError as error:
            # A verb that could not be started, or a log that could not be opened:
            # nothing rendered, and the page says so rather than showing an end.
            if not opened:
                self._mark(job, "volume up", "failed")
            with self._lock:
                slot.child = None
                job.state = "failed"
                job.message = (
                    f"the render job could not run ({error}); read "
                    f"{job.collection}/{LOG}, then try again"
                )
        finally:
            if opened and steps["volume down"] != "kept":
                self._mark(job, "volume down", "running")
                code = _named(job.kind, folder, self._volume.down)
                self._mark(job, "volume down", "done" if code == 0 else "failed")
                if code != 0:
                    self._raise_volume()
            with self._lock:
                if job.state == "running":
                    job.state = "stopped" if slot.stopping else "done"
                job.session["ended"] = self._now()
            self._publish(job)

    def _render_child(self, job: _Job, folder: Path, limit: int) -> None:
        """Run the render verb, reading its steps; start none once Stop was asked."""
        assert job.session is not None
        slot = self._slots[job.kind]
        with self._lock:
            if slot.stopping:
                return
            argv = self._render(limit, folder / RUNS, job.session["id"])
            child = self._spawn(job.kind, argv, folder)
        assert child.stdout is not None
        reported = False
        for raw in child.stdout:
            line = progress_line(raw)
            if line is None:
                continue
            reported = True
            with self._lock:
                if line.get("step") == "image":
                    job.session["images"].append(
                        {
                            key: line.get(key)
                            for key in ("digest", "flow", "version", "seed")
                        }
                    )
                else:
                    job.session["steps"][str(line.get("step"))] = line.get("state")
            self._publish(job)
        code = self._reap(slot, child)
        with self._lock:
            slot.child = None
            if code != 0 and not slot.stopping:
                job.state = "failed"
                job.message = (
                    f"render ended with exit {code}"
                    + ("" if reported else " before reporting")
                    + f"; read {job.collection}/{LOG}"
                )

    def _mark(self, job: _Job, step: str, state: str) -> None:
        """Set one step of a render's session, and tell the page."""
        assert job.session is not None
        with self._lock:
            job.session["steps"][step] = state
        self._publish(job)

    def _start(
        self, job: _Job, step: Step, folder: Path
    ) -> subprocess.Popen[str] | None:
        """Start `step`'s child, or return None once Stop was asked for."""
        with self._lock:
            if self._slots[job.kind].stopping:
                return None
            argv = self._command(step.verb, step.flow, folder / RUNS, step.runs)
            job.flow, job.stage = step.flow, step.verb
            return self._spawn(job.kind, argv, folder)

    def _spawn(
        self, kind: Kind, argv: list[str], folder: Path
    ) -> subprocess.Popen[str]:
        """Start `argv` as `kind`'s child, and the thread writing its prose to the log.

        Hold the lock.
        """
        # Line-buffered, so each line lands whole beside the other job's.
        log = (folder / LOG).open("a", buffering=1)
        try:
            # Its own session, so a Ctrl-C at the terminal reaches the server
            # alone, and the server decides what the child is sent.
            child = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=REPOSITORY,
                text=True,
                start_new_session=True,
            )
        except OSError:
            log.close()
            raise
        assert child.stderr is not None
        slot = self._slots[kind]
        slot.child = child
        slot.tee = threading.Thread(
            target=_tee, args=(child.stderr, log, kind), daemon=True
        )
        slot.tee.start()
        return child

    def _reap(self, slot: _Slot, child: subprocess.Popen[str]) -> int:
        """Return `child`'s exit once it and its log writer have ended."""
        code = child.wait()
        if slot.tee is not None:
            slot.tee.join(DRAIN_S)
        return code

    def _publish(self, job: _Job) -> None:
        with self._lock:
            described = job.describe()
        self._broadcast.publish("job", described)


def _named(kind: Kind, folder: Path, verb: Callable[[Say], int]) -> int:
    """Run a gpunit `verb`, each line it says written to the log naming its job."""
    # Line-buffered, so each line lands whole beside the other job's.
    with (folder / LOG).open("a", buffering=1) as log:
        return verb(lambda line: print(f"[{kind}]", line, file=log))


def _tee(stream: TextIO, log: TextIO, kind: Kind) -> None:
    """Write each line of `stream` to `log`, naming its job. e.g. `[render] …`."""
    with stream, log:
        for line in stream:
            print(f"[{kind}]", line.rstrip("\n"), file=log)
