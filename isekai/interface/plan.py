"""The plan of a render session: its timing, its estimate and its pending edits.

It reads folders and config, never a process, and never imports `render.py`, which
imports it.
"""

import dataclasses
import json
import math
import statistics
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from isekai.boundary.pod_start import HOLD_SECONDS
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REPOSITORY, Run, render_groups, sidecars
from isekai.pipeline.edit import duration_of, pending, records
from isekai.pipeline.generate import duration

# A session's figures, and the least time an image is quoted at (D26).
RENDER_CONFIG = REPOSITORY / "config" / "render.json"
# How many of a flow's newest recorded durations its median is taken over.
RECENT = 20
# A pod held for diagnosis stops after its hold ends, never before.
FLOOR_S = HOLD_SECONDS + 300


@dataclass(frozen=True)
class Timing:
    """`config/render.json`: the figures, and the least time an image is quoted at.

    Seconds for the boot, an image, an edit and the teardown; the limit's factor
    over the estimate; and the volume's rate per hour.
    """

    boot_s: float
    per_image_s: float
    per_edit_s: float
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
    """A session's estimate and limit, in seconds; `capped` if the ceiling cut it."""

    seconds: float
    limit_s: int
    capped: bool = False


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


def recent_edits(runs: Path, ids: Sequence[str]) -> list[float]:
    """Return the durations of the newest recorded edits under `runs`.

    Newest first by when each record was written, so only those `RECENT` takes are
    read. A request that has not run records none.
    """
    found = [
        record
        for run_id in ids
        for flow in Run(run_id, runs / run_id).flows
        for record in edit_records(Run(run_id, runs / run_id), flow)
    ]
    found.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    taken: list[float] = []
    for path in found:
        if (seconds := duration_of(path)) is not None:
            taken.append(seconds)
            if len(taken) == RECENT:
                break
    return taken


def estimate[K, E](
    images: Mapping[K, int],
    recorded: Mapping[K, Sequence[float]],
    timing: Timing,
    ceiling_s: int,
    edits: Mapping[E, int] | None = None,
    edit_recorded: Mapping[E, Sequence[float]] | None = None,
) -> Estimate:
    """Return a session's estimate and its limit, both in seconds.

    `images` and `recorded` share a key: a flow, or a collection's flow; `edits` and
    `edit_recorded` share another: a collection. The limit is the estimate times the
    factor, at least `FLOOR_S` and at most `ceiling_s`. Each key's images take its
    recorded median or `per_image_s`, whichever is higher, and its edits the same
    with `per_edit_s`.
    e.g. 4 images at a recorded median of 90 s, per image 95, boot 480,
         teardown 120, factor 1.5 -> Estimate(980.0, 1470, False)
    """
    seconds = timing.boot_s + timing.teardown_s
    for key, count in images.items():
        median = statistics.median(recorded.get(key) or [timing.per_image_s])
        seconds += count * max(median, timing.per_image_s)
    for held, count in (edits or {}).items():
        median = statistics.median(
            (edit_recorded or {}).get(held) or [timing.per_edit_s]
        )
        seconds += count * max(median, timing.per_edit_s)
    wanted = max(FLOOR_S, math.ceil(seconds * timing.limit_factor))
    return Estimate(seconds, min(ceiling_s, wanted), wanted > ceiling_s)


# A collection's runs root, its run ids, and the images it renders by flow.
Work = tuple[Path, Sequence[str], Mapping[str, int]]


def estimated(
    work: Sequence[Work],
    timing: Timing,
    ceiling_s: int,
    edits: Mapping[Path, int] | None = None,
) -> Estimate:
    """Return one session's estimate for every collection's images in `work`.

    One boot and one teardown; each collection's images at its own recorded
    durations, and its pending edits, `edits` by runs root, at its own recorded
    edit durations. The quote and the session both take it here, so the two cannot
    disagree.
    """
    images = {(runs, flow): n for runs, _, found in work for flow, n in found.items()}
    recorded = {
        (runs, flow): recent(runs, ids, flow)
        for runs, ids, found in work
        for flow in found
    }
    held = {runs: ids for runs, ids, _ in work}
    edit_recorded = {
        runs: recent_edits(runs, held.get(runs, [])) for runs in edits or {}
    }
    return estimate(images, recorded, timing, ceiling_s, edits, edit_recorded)


@dataclass(frozen=True)
class Edits:
    """A collection's pending edits: the cells that hold them, and how many.

    `records` is each pending edit's record, by run, flow, then chain.
    """

    cells: tuple[str, ...]
    count: int
    records: tuple[Path, ...] = ()


def edits_of(
    runs: Path, ids: Sequence[str], tracked: Collection[str], without: Collection[Path]
) -> Edits:
    """Return the pending edits of each tracked flow of `ids` under `runs`.

    Each `<run-id>/<flow>` in `without` is left out.
    e.g. r1 holding f's 42.edit-1.json and 42.edit-2.json with no images
         -> Edits(("r1/f",), 2)
    """
    cells: list[str] = []
    found: list[Path] = []
    for run_id in ids:
        run = Run(run_id, runs / run_id)
        for flow in (name for name in run.flows if name in tracked):
            held = [] if runs / run_id / flow in without else pending_edits(run, flow)
            if held:
                cells.append(f"{run_id}/{flow}")
                found += held
    return Edits(tuple(cells), len(found), tuple(found))


def edit_records(run: Run, flow: str) -> list[Path]:
    """Return every edit record of `flow` in `run`, by group then chain."""
    return [record for group in render_groups(run, flow) for record in records(group)]


def pending_edits(run: Run, flow: str) -> list[Path]:
    """Return the records of `flow`'s pending edits in `run`, by group then chain.

    e.g. outputs/001/42.edit-1.json, then outputs/002/7.edit-1.json
    """
    return [record for group in render_groups(run, flow) for record in pending(group)]
