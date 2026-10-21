"""Prepare and Render as jobs: the pipeline's own verbs, run as children, one at a time.

The CLI is the one path, so a job is exactly what the verbs do. Each child runs
in its own session and reports through `--progress json`; its prose is appended
to the batch's `log.txt`. A job outlives the page that started it.

```
Prepare ─▶ probe ─ no answer ─▶ refused, nothing runs
            └ answers ─▶ per flow: tag ─▶ caption ─▶ sheet ─▶ done
Render ─▶ volume up ─ lost ─▶ the volume alert, nothing renders
           └ up ─▶ render --limit … --progress json ─▶ volume down, unless kept
Stop, or the server stopping ─▶ SIGINT to the child ─▶ no later stage starts
a child failing with no line reported ─▶ failed, naming log.txt ─▶ no later stage starts
```
"""

import json
import os
import signal
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.boundary.gpu import Volume
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import ID_DIGEST_CHARS, REPOSITORY
from isekai.interface.render import LOST_EXIT
from isekai.interface.ui.billing import utc_now
from isekai.interface.ui.events import Broadcast
from isekai.interface.ui.library import LOG, RUNS

# The stages Prepare runs for each flow, in order.
PREPARE = ("tag", "caption", "sheet")

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


# How a render is started: the session's limit and the batch's runs root.
RenderCommand = Callable[[int, Path], list[str]]


def render_command(limit: int, runs: Path) -> list[str]:
    """Return the render verb line. e.g. `python -m isekai render --limit 1200 …`."""
    return [
        sys.executable,
        "-m",
        "isekai",
        "render",
        "--limit",
        str(limit),
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
    batch: str
    steps: tuple[Step, ...]
    kind: str = "prepare"
    state: str = "running"
    flow: str | None = None
    stage: str | None = None
    message: str | None = None
    # A render's session as the page draws it: its steps, its images, its limit.
    session: dict[str, Any] | None = None

    def describe(self) -> dict[str, Any]:
        described = {
            "kind": self.kind,
            "batch": self.batch,
            "state": self.state,
            "flow": self.flow,
            "stage": self.stage,
            "message": self.message,
        }
        if self.session is not None:
            described["session"] = {
                **self.session,
                "steps": dict(self.session["steps"]),
                "images": list(self.session["images"]),
            }
        return described


class Jobs:
    """The one job slot, and the child running in it."""

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
    ) -> None:
        """Hold an empty slot that publishes on `broadcast`.

        `volume` opens and closes a render's window; `raise_volume` raises the
        volume alert when either goes unanswered.
        """
        self._broadcast = broadcast
        self._probe = probe
        self._command = command
        self._volume = volume or Volume()
        self._render = render
        self._raise_volume = raise_volume
        self._now = now
        self._lock = threading.Lock()
        self._job: _Job | None = None
        self._child: subprocess.Popen[str] | None = None
        self._stopping = False
        self._thread: threading.Thread | None = None

    def slot(self) -> dict[str, Any] | None:
        """Return the job in the slot, running or ended, or None."""
        with self._lock:
            return self._job.describe() if self._job else None

    def prepare(
        self,
        batch: str,
        folder: Path,
        steps: Sequence[Step],
        cell: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> dict[str, Any]:
        """Start Prepare over `steps`, or refuse: a job running, or no answer.

        `cell` turns a progress line into the event the page applies, or None.
        """
        self._refuse_running()
        # Outside the lock: a host that is slow to answer holds up no snapshot.
        self._probe()
        with self._lock:
            self._refuse_running()
            if not steps:
                raise Refusal(
                    f"{batch} has no assigned cell without a sheet; tick a flow for "
                    "a source, then try again"
                )
            job = _Job(batch, tuple(steps))
            self._job, self._stopping = job, False
            self._thread = threading.Thread(
                target=self._run, args=(job, folder, cell), daemon=True
            )
            self._thread.start()
        self._publish(job)
        return job.describe()

    def rendering(self) -> bool:
        """Return whether a render job runs."""
        with self._lock:
            job = self._job
            return job is not None and job.kind == "render" and job.state == "running"

    def running(self) -> str | None:
        """Return the running job's kind, or None."""
        with self._lock:
            job = self._job
            return job.kind if job is not None and job.state == "running" else None

    def render(
        self,
        batch: str,
        folder: Path,
        *,
        limit: int,
        total: int,
        keep_open: bool,
        started: str,
    ) -> dict[str, Any]:
        """Start a render of `folder`'s runs within `limit` seconds, or refuse."""
        with self._lock:
            self._refuse_running()
            steps = dict.fromkeys(("volume up", "pod", "teardown", "volume down"), "")
            if keep_open:
                steps["volume down"] = "kept"
            session = {
                "started": started,
                "limit": limit,
                "of": total,
                "keep_open": keep_open,
                "ended": None,
                "steps": steps,
                "images": [],
            }
            job = _Job(batch, (), kind="render", session=session)
            self._job, self._stopping = job, False
            self._thread = threading.Thread(
                target=self._run_render, args=(job, folder, limit), daemon=True
            )
            self._thread.start()
        self._publish(job)
        return job.describe()

    def _refuse_running(self) -> None:
        """Refuse while a job runs, naming it."""
        job = self._job
        if job is not None and job.state == "running":
            kind = "Render" if job.kind == "render" else "Prepare"
            raise Refusal(
                f"a job is running: {kind} on {job.batch}; wait for it to end, or "
                "Stop it, then try again"
            )

    def stop(self) -> dict[str, Any]:
        """Interrupt the running stage and start no other, or refuse: none runs."""
        with self._lock:
            if self._job is None or self._job.state != "running":
                raise Refusal("no job is running, so there is nothing to stop")
            self._interrupt()
            return self._job.describe()

    def wait(self, timeout: float | None = None) -> None:
        """Return once the job in the slot has ended, or `timeout` has passed."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def shutdown(self, timeout: float = 10.0) -> None:
        """Interrupt a running job and wait for it: the server is stopping."""
        with self._lock:
            if self._job is not None and self._job.state == "running":
                self._interrupt()
        self.wait(timeout)

    def _interrupt(self) -> None:
        """Send the child SIGINT, as a Ctrl-C would; hold the lock."""
        self._stopping = True
        child = self._child
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
        try:
            for step in job.steps:
                child = self._start(job, step, folder)
                if child is None:
                    break
                self._publish(job)
                assert child.stdout is not None
                reported = False
                for raw in child.stdout:
                    event = _line(raw)
                    reported = reported or event is not None
                    found = cell(event) if event is not None else None
                    if found is not None:
                        self._broadcast.publish("cell", found)
                code = child.wait()
                with self._lock:
                    self._child = None
                    # A child that fails before its first line said nothing the
                    # page can show; its reason is in the log.
                    if code != 0 and not reported and not self._stopping:
                        job.state = "failed"
                        job.message = (
                            f"{step.verb} on {step.flow} ended before reporting "
                            f"(exit {code}); read {job.batch}/{LOG}, then try again"
                        )
                        break
        finally:
            with self._lock:
                if job.state == "running":
                    job.state = "stopped" if self._stopping else "done"
            self._publish(job)

    def _run_render(self, job: _Job, folder: Path, limit: int) -> None:
        """Open the window, run the render verb, and close the window unless kept."""
        assert job.session is not None
        steps = job.session["steps"]
        log = folder / LOG
        opened = False
        try:
            self._mark(job, "volume up", "running")
            code = self._volume.up(log)
            if code != 0:
                self._mark(job, "volume up", "lost" if code == LOST_EXIT else "failed")
                if code == LOST_EXIT:
                    self._raise_volume()
                job.state = "failed"
                job.message = (
                    f"gpunit volume up did not open the window (exit {code}); read "
                    f"{job.batch}/{LOG}, and nothing was rendered"
                )
                return
            opened = True
            self._mark(job, "volume up", "done")
            self._render_child(job, folder, limit)
        finally:
            if opened and steps["volume down"] != "kept":
                self._mark(job, "volume down", "running")
                code = self._volume.down(log)
                self._mark(job, "volume down", "done" if code == 0 else "failed")
                if code != 0:
                    self._raise_volume()
            with self._lock:
                if job.state == "running":
                    job.state = "stopped" if self._stopping else "done"
                job.session["ended"] = self._now()
            self._publish(job)

    def _render_child(self, job: _Job, folder: Path, limit: int) -> None:
        """Run the render verb, reading its steps; start none once Stop was asked."""
        assert job.session is not None
        with self._lock:
            if self._stopping:
                return
            argv = self._render(limit, folder / RUNS)
            with (folder / LOG).open("a") as log:
                self._child = subprocess.Popen(
                    argv,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    cwd=REPOSITORY,
                    text=True,
                    start_new_session=True,
                )
            child = self._child
        assert child.stdout is not None
        reported = False
        for raw in child.stdout:
            line = _line(raw)
            if line is None:
                continue
            reported = True
            with self._lock:
                if line.get("step") == "image":
                    found = {
                        key: line.get(key)
                        for key in ("n", "of", "run", "flow", "version", "seed")
                    }
                    found["digest"] = str(found["run"])[:ID_DIGEST_CHARS]
                    job.session["images"].append(found)
                else:
                    job.session["steps"][str(line.get("step"))] = line.get("state")
            self._publish(job)
        code = child.wait()
        with self._lock:
            self._child = None
            if code != 0 and not self._stopping:
                job.state = "failed"
                job.message = (
                    f"render ended with exit {code}"
                    + ("" if reported else " before reporting")
                    + f"; read {job.batch}/{LOG}"
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
            if self._stopping:
                return None
            argv = self._command(step.verb, step.flow, folder / RUNS, step.runs)
            job.flow, job.stage = step.flow, step.verb
            with (folder / LOG).open("a") as log:
                # Its own session, so a Ctrl-C at the terminal reaches the server
                # alone, and the server decides what the child is sent.
                self._child = subprocess.Popen(
                    argv,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    cwd=REPOSITORY,
                    text=True,
                    start_new_session=True,
                )
            return self._child

    def _publish(self, job: _Job) -> None:
        with self._lock:
            described = job.describe()
        self._broadcast.publish("job", described)


def _line(raw: str) -> dict[str, Any] | None:
    """Return a progress line as a mapping, or None for a line that is not one."""
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return found if isinstance(found, dict) else None
