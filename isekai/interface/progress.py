"""The lines a child prints under `--progress json`, and the flag that asks for them.

One JSON line per event on stdout, its prose on stderr. Three kinds:

    item   {"run": "0d4b…_ada", "flow": "summon-anime-wai", "stage": "sheet",
            "state": "done"}
    step   {"step": "pod", "state": "ready"}
    image  {"step": "image", "n": 1, "of": 2, "run": "0d4b…_ada", "digest": "ab12",
            "flow": "summon-anime-wai", "version": 2, "seed": "42", "state": "done"}

A verb writes an item line through `Reporter.item`; a render session writes step and
image lines through `Steps`, which reads each child's render line back through
`_Images`. The app's job loops read all three through `progress_line`.
This module imports the standard library alone: `python -m isekai` loads it under `-S`.
"""

import io
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, NotRequired, Protocol, TextIO, TypedDict, cast

FLAG = "--progress"
FORMAT = "json"
ARGUMENT = (FLAG, FORMAT)

TAG = "tag"
CAPTION = "caption"
SHEET = "sheet"
RENDER = "render"
EDIT = "edit"
Stage = Literal["tag", "caption", "sheet", "render", "edit", "review", "approve"]

# The stages Prepare counts, in order. Its one child takes each photograph through
# them in turn: tag and caption once, naming no flow, since every flow reads the
# one description (D17); then sheet for each of its cells.
PREPARE = (TAG, CAPTION, SHEET)

START = "start"
DONE = "done"
REFUSED = "refused"
ItemState = Literal["start", "done", "refused"]

POD = "pod"
TEARDOWN = "teardown"
IMAGE = "image"
StepName = Literal["pod", "teardown", "image"]
StepState = Literal["starting", "ready", "lost", "refused", "done", "failed"]

# What an image line names of the image a render landed, after its run.
LANDED = ("digest", "flow", "version", "seed")


class ItemLine(TypedDict):
    """A verb's line for one item, in print order, naming what it did."""

    run: str
    flow: NotRequired[str]
    stage: Stage
    state: ItemState
    digest: NotRequired[str]
    version: NotRequired[int]
    seed: NotRequired[str]
    file: NotRequired[str]
    message: NotRequired[str]


class StepLine(TypedDict):
    """A session's line for a step of its own, such as the pod."""

    step: StepName
    state: StepState


class ImageLine(TypedDict):
    """A session's line for the next image a render landed, of the session's total."""

    step: Literal["image"]
    n: int
    of: int
    run: str | None
    digest: str | None
    flow: str | None
    version: int | None
    seed: str | None
    state: Literal["done"]


class Recorder(Protocol):
    """What `Steps` keeps a session's steps and images in."""

    def step(self, step: str, state: str) -> None:
        """Record `step` at `state`."""

    def image(self, item: Mapping[str, Any], runs: Path) -> None:
        """Record the image a `generate` line over `runs` landed."""


def emit(out: TextIO, line: Mapping[str, object]) -> None:
    """Print `line` as one JSON line on `out`, flushed."""
    # Flushed: a job reads this from a pipe, line by line, as it happens.
    print(json.dumps(line), file=out, flush=True)


def progress_line(raw: str) -> dict[str, Any] | None:
    """Return a `--progress json` line as a mapping, or None for any other line."""
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return found if isinstance(found, dict) else None


class Steps:
    """A session's JSON lines on `out`, one per step, when `enabled`.

    Each step and image reaches `record` too, whether or not it is printed.
    e.g. {"step": "image", "n": 2, "of": 4, "run": "…", "flow": "…", "state": "done"}
    """

    def __init__(self, out: TextIO, enabled: bool) -> None:
        """Print to `out`, or nothing unless `enabled`."""
        self.out = out
        self.enabled = enabled
        self.flag: tuple[str, ...] = ARGUMENT if enabled else ()
        self.record: Recorder | None = None
        self._n = 0

    def step(self, step: str, state: str) -> None:
        """Print one step's line, and record it."""
        if self.record is not None:
            self.record.step(step, state)
        self._line(step=step, state=state)

    def _line(self, **line: object) -> None:
        if self.enabled:
            emit(self.out, line)

    def child(self, total: int = 0, runs: Path | None = None) -> TextIO:
        """Return where a `generate` line over `runs` writes: its images become steps.

        Once a record is kept, every image reaches its collection's, printed or not.
        """
        if not (self.enabled or self.record):
            return self.out
        # A text stream as `_Tee` is; `TextIO` is a type no stream class subclasses.
        return cast("TextIO", _Images(self, total, runs))

    def image(self, item: Mapping[str, Any], total: int, runs: Path | None) -> None:
        """Print the next image's line, of `total`, naming its run, flow and seed."""
        if self.record is not None and runs is not None:
            self.record.image(item, runs)
        self._n += 1
        named = {key: item.get(key) for key in ("run", *LANDED)}
        self._line(step=IMAGE, n=self._n, of=total, **named, state=DONE)


class _Images(io.TextIOBase):
    """Read `generate`'s JSON lines, and print each landed image as a step."""

    def __init__(self, steps: Steps, total: int, runs: Path | None) -> None:
        """Count images against `total`, each landed under `runs`."""
        self._steps = steps
        self._total = total
        self._runs = runs
        self._held = ""

    def write(self, text: str) -> int:
        """Take `text`, and print a step for each whole render line in it."""
        self._held += text
        *lines, self._held = self._held.split("\n")
        for line in lines:
            item = progress_line(line)
            if item and item.get("stage") == RENDER and item.get("state") == DONE:
                self._steps.image(item, self._total, self._runs)
        return len(text)
