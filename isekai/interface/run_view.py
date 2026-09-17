"""The inspection command: a run's artifacts, its active versions, its producers.

A filename carries only what resume decides on, which leaves a directory that is
precise and unreadable. This is what a person reads instead -- and it is also the
answer to "where is this run", which is why no progress file ships: nothing but a
human is watching before a review UI exists, and the inspection command is what
that human reads.

**It reads; it never decides.** Every fact here comes out of a file, which is the
opposite rule from the completion tests, and that is the point: control flow uses
listings, and people get the whole record.

Stdlib only.
"""

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.foundation.flow import load_flow
from isekai.foundation.run import (
    APPROVED,
    ARTIFACT,
    CAPTIONS,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    SHEETS,
    Run,
)
from isekai.pipeline.generate import rendered_seeds

# The stages in the order a run passes through them. Every one of them is a
# flow's own now -- the run is input above and flow below -- so there is nothing
# left for a per-flow-ness column to say. Declared once here so the listing cannot
# drift from the layout it describes.
STAGES: tuple[str, ...] = (CAPTIONS, SHEETS, REVIEW, PROMPTS)


@dataclass(frozen=True)
class Listing:
    """One stage's artifacts in one flow of one run, and which of them is active."""

    stage: str
    flow: str
    versions: list[int]
    active: int | None
    approved: list[int]
    producers: dict[int, str]


def _producer_of(path: Path) -> str:
    """Return a one-line description of what produced the artifact at `path`."""
    try:
        body: Any = json.loads(path.read_text())
    except (OSError, ValueError):
        return "unreadable"
    producer = body.get("producer", {})
    parts = [str(producer.get("implementation", "unknown"))]
    models = producer.get("models")
    if models:
        parts.append("+".join(str(model) for model in models))
    if producer.get("pinned") is False:
        parts.append("unpinned")
    briefing = producer.get("briefing")
    if briefing:
        parts.append(f"briefing {str(briefing.get('sha256', ''))[:12]}")
    if producer.get("from") is not None:
        parts.append(f"from {producer['from']:03d}")
    if producer.get("edited") is not None:
        parts.append("edited" if producer["edited"] else "unedited")
    return " · ".join(parts)


def _listing(stage: str, flow: str, directory: Path) -> Listing:
    """Build one stage's listing from a single reading of its directory.

    One `os.listdir`, not three: the versions, the approved ones and each
    version's actual filename all come out of the same pass, so the listing does
    not stat three candidate names per version to find the one that is there.
    """
    names: dict[int, str] = {}
    approved: list[int] = []
    if directory.is_dir():
        for name in sorted(os.listdir(directory)):
            match = ARTIFACT.match(name)
            if match is None:
                continue
            version = int(match.group("version"))
            names[version] = name
            if match.group("label") == APPROVED:
                approved.append(version)
    present = sorted(names)
    # The active version is the highest *approved* one where approval applies,
    # and the highest present one otherwise -- because downstream stages read
    # approval, and a draft is not something to proceed from.
    ranked = sorted(approved) or present
    active = ranked[-1] if ranked else None
    producers = {
        version: _producer_of(directory / names[version]) for version in present
    }
    return Listing(stage, flow, present, active, sorted(approved), producers)


def flows_in(run: Run) -> list[str]:
    """Return the flows this run holds work for: its subdirectories, in order."""
    if not run.path.is_dir():
        return []
    return sorted(path.name for path in run.path.iterdir() if path.is_dir())


def listings(run: Run) -> list[Listing]:
    """Return one listing per stage per flow, in flow order then stage order."""
    return [
        _listing(stage, flow, run.directory(flow, stage))
        for flow in flows_in(run)
        for stage in STAGES
    ]


def rendered(run: Run) -> list[tuple[str, int, list[int]]]:
    """Return each flow's rendered seeds, by sheet version, from filenames alone."""
    return [
        (flow, int(group.name), rendered_seeds(group, load_flow(flow).output_suffix))
        for flow in flows_in(run)
        for group in sorted(_groups(run.directory(flow, OUTPUTS)))
        if group.name.isdigit()
    ]


def _groups(outputs: Path) -> Iterator[Path]:
    """Yield the per-sheet-version directories under one flow's outputs."""
    if outputs.is_dir():
        yield from (path for path in outputs.iterdir() if path.is_dir())


def report(run: Run) -> Iterator[str]:
    """Yield the lines a person reads to answer "where is this run"."""
    frame = run.frame
    photo = frame["photo"]
    yield f"{run.id}"
    yield f"  photo    {photo['name']}  {photo['media_type']}  {photo['bytes']} bytes"
    yield f"           sha256 {photo['sha256']}"

    for listing in listings(run):
        name = f"{listing.flow}/{listing.stage}"
        if not listing.versions:
            yield f"  {name:<22} (none)"
            continue
        yield f"  {name}"
        for version in listing.versions:
            mark = "*" if version == listing.active else " "
            state = " approved" if version in listing.approved else ""
            producer = listing.producers.get(version, "")
            yield f"   {mark} {version:03d}{state}  {producer}"

    for flow, version, seeds in rendered(run):
        yield f"  {flow}/{OUTPUTS}/{version:03d}"
        for seed in seeds:
            yield f"     {seed}"

    yield "  * marks the active version for each stage"
