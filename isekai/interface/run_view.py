"""The inspection command: a run's artifacts, its active versions, its producers.

A filename carries only what resume decides on, which leaves a directory that is
precise and unreadable. This is what a person reads instead -- and it is also the
answer to "where is this run", which is why no progress file ships: a person
reads this command, and the review UI reads the run directory itself.

**It reads; it never decides.** Every fact here comes out of a file, which is the
opposite rule from the completion tests, and that is the point: control flow uses
listings, and people get the whole record.

Stdlib only.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.foundation.artifacts import VERSIONS
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    ARTIFACT,
    CAPTIONS,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    SHEETS,
    TAGS,
    WD14,
    Run,
    is_approved,
)
from isekai.pipeline.generate import rendered_seeds

# The stages in the order a run passes through them. Every one of them is a
# flow's own -- the run is input above and flow below -- so there is nothing for
# a per-flow-ness column to say. Declared once here so the listing cannot drift
# from the layout it describes.
#
# **The tuple is explicit, so a new stage directory is invisible to `show` until
# it is named here.** Shipping a stage `show` cannot see is shipping a verb that
# lies about what a run holds.
STAGES: tuple[str, ...] = (CAPTIONS, WD14, TAGS, SHEETS, REVIEW, PROMPTS)


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
    """Return a one-line description of what produced the artifact at `path`.

    A file this build would refuse to read is marked, never parsed: `show` reads
    a run in any state, so it reports the refusal rather than raising it.
    e.g. `declares version 2; this build reads 1`
    """
    try:
        body: Any = json.loads(path.read_text())
    except (OSError, ValueError):
        return "unreadable"
    schema = body.get("schema") if isinstance(body, dict) else None
    if not isinstance(schema, dict):
        return "unreadable"
    kind, declared = schema.get("name"), schema.get("version")
    if not isinstance(kind, str) or kind not in VERSIONS:
        return f"declares kind {kind!r}, which this build does not read"
    if declared != VERSIONS[kind]:
        return f"declares version {declared!r}; this build reads {VERSIONS[kind]}"
    producer = body.get("producer", {})
    if not isinstance(producer, dict):
        return "unreadable"
    parts = [str(producer.get("implementation", "unknown"))]
    models = producer.get("models")
    if models:
        if not isinstance(models, list):
            return "unreadable"
        parts.append("+".join(str(model) for model in models))
    if producer.get("pinned") is False:
        parts.append("unpinned")
    briefing = producer.get("briefing")
    if briefing:
        if not isinstance(briefing, dict):
            return "unreadable"
        parts.append(f"briefing {str(briefing.get('sha256', ''))[:12]}")
    origin = producer.get("from")
    if origin is not None:
        if not isinstance(origin, int):
            return "unreadable"
        parts.append(f"from {origin:03d}")
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
            if is_approved(name):
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


def listings(run: Run) -> list[Listing]:
    """Return one listing per stage per flow, in flow order then stage order."""
    return [
        _listing(stage, flow, run.directory(flow, stage))
        for flow in run.flows
        for stage in STAGES
    ]


def rendered(run: Run, flows_dir: Path = FLOWS_DIR) -> list[tuple[str, int, list[int]]]:
    """Return each flow's rendered seeds, by approval, from filenames alone.

    The outputs directory is the approval's number, not the sheet's. The flow
    is loaded once, not once per approval, and it is loaded at all
    because what counts as a produced output is the flow's answer rather than an
    extension written in here.

    **`flows_dir` is a parameter because `Wiring` has one**: reading the module
    default instead would send `show` against an injected flows root to `flows/`
    regardless of what was passed, and refuse naming a flow the caller never
    asked about.
    """
    return [
        (flow, int(group.name), rendered_seeds(group, suffix))
        for flow in run.flows
        for suffix in (load_flow(flow, flows_dir).output_suffix,)
        for group in sorted(run.directory(flow, OUTPUTS).glob("*"))
        if group.is_dir() and group.name.isdigit()
    ]


def report(run: Run, flows_dir: Path = FLOWS_DIR) -> list[str]:
    """Return the lines a person reads to answer "where is this run".

    **A list rather than a generator, so no refusal can escape mid-print.**
    `rendered()` loads a flow and a flow refuses, and a generator's body does
    not start until the caller asks for its first line -- so a run holding a
    directory no flow answers for would print lines of record and *then* fail,
    leaving half a report above the refusal. Both callers drain this in full, so
    laziness buys nothing and costs the ordering; a list makes "everything
    refusable is read first" true by construction rather than by a paragraph
    asking the next editor to keep it so.
    """
    lines: list[str] = [run.id]
    # A frame this build cannot read is marked, like an artifact, and the rest
    # listed: `show` reads a run in whatever state it is in.
    try:
        photo = run.photo_record
    except Refusal as unreadable:
        lines.append(f"  photo    {unreadable}")
    else:
        lines.append(
            f"  photo    {photo['name']}  {photo['media_type']}  {photo['bytes']} bytes"
        )
        lines.append(f"           sha256 {photo['sha256']}")
    stages = listings(run)
    outputs = rendered(run, flows_dir)

    for listing in stages:
        name = f"{listing.flow}/{listing.stage}"
        if not listing.versions:
            lines.append(f"  {name:<22} (none)")
            continue
        lines.append(f"  {name}")
        for version in listing.versions:
            mark = "*" if version == listing.active else " "
            state = " approved" if version in listing.approved else ""
            producer = listing.producers.get(version, "")
            lines.append(f"   {mark} {version:03d}{state}  {producer}")

    for flow, version, seeds in outputs:
        lines.append(f"  {flow}/{OUTPUTS}/{version:03d}")
        for seed in seeds:
            lines.append(f"     {seed}")

    lines.append("  * marks the active version for each stage")
    return lines
