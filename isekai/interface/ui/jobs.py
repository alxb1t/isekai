"""Prepare as a job: the pipeline's own verbs, run as children, one job at a time.

The CLI is the one path, so a job is exactly what the verbs do. Each child runs
in its own session and reports through `--progress json`; its prose is appended
to the batch's `log.txt`. A job outlives the page that started it.

```
Prepare ─▶ probe ─ no answer ─▶ refused, nothing runs
            └ answers ─▶ per flow: tag ─▶ caption ─▶ sheet ─▶ done
Stop, or the server stopping ─▶ SIGINT to the child ─▶ no later stage starts
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

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REPOSITORY
from isekai.interface.ui.events import Broadcast

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
    state: str = "running"
    flow: str | None = None
    stage: str | None = None

    def describe(self) -> dict[str, Any]:
        return {
            "kind": "prepare",
            "batch": self.batch,
            "state": self.state,
            "flow": self.flow,
            "stage": self.stage,
        }


class Jobs:
    """The one job slot, and the child running in it.

    `cell` turns a progress line into the event the page applies, or None.
    """

    def __init__(
        self,
        broadcast: Broadcast,
        probe: Callable[[], None],
        *,
        command: Command = isekai_command,
    ) -> None:
        """Hold an empty slot that publishes on `broadcast`."""
        self._broadcast = broadcast
        self._probe = probe
        self._command = command
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
        """Start Prepare over `steps`, or refuse: a job running, or no answer."""
        with self._lock:
            if self._job is not None and self._job.state == "running":
                raise Refusal(
                    f"a job is running: Prepare on {self._job.batch}; wait for it "
                    "to end, or Stop it, then try again"
                )
            self._probe()
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

    def stop(self) -> dict[str, Any] | None:
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
                for raw in child.stdout:
                    event = _line(raw)
                    found = cell(event) if event is not None else None
                    if found is not None:
                        self._broadcast.publish("cell", found)
                child.wait()
                with self._lock:
                    self._child = None
        finally:
            with self._lock:
                job.state = "stopped" if self._stopping else "done"
            self._publish(job)

    def _start(
        self, job: _Job, step: Step, folder: Path
    ) -> subprocess.Popen[str] | None:
        """Start `step`'s child, or return None once Stop was asked for."""
        with self._lock:
            if self._stopping:
                return None
            argv = self._command(step.verb, step.flow, folder / "runs", step.runs)
            job.flow, job.stage = step.flow, step.verb
            with (folder / "log.txt").open("a") as log:
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
