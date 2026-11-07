"""Copy a run's per-flow description into `photo/`, once.

A run written before the description was shared holds its caption and tag lists
under each flow. `migrate` copies each kind `photo/` lacks there, byte for byte,
and never deletes a source: the per-flow copies stay until the operator removes
them, or a delete leaves the flow no approval (D50). A list keeps its number, so
a sheet's `from` names the same list under `photo/` and no kind's meaning moves
(D32).

Stdlib only, and on `python -m isekai`'s import graph.
"""

import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

from isekai.foundation.artifacts import (
    TAGS_FILE,
    WD14_FILE,
    Artifact,
    Tags,
    Wd14,
    read,
    require,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    CAPTIONS,
    DESCRIPTION,
    PHOTO,
    TAGS,
    WD14,
    Run,
    artifact_name,
    latest_artifact,
    migrate_command,
    versions,
)

_LISTS: Mapping[str, Artifact[Wd14] | Artifact[Tags]] = {
    WD14: WD14_FILE,
    TAGS: TAGS_FILE,
}

# A source file, and the name its copy takes under `photo/<kind>/`.
Copy = tuple[Path, str]


def migrate(run: Run) -> str:
    """Copy each kind of `run`'s description `photo/` lacks, and return the outcome.

    Every kind is checked before any is copied, so a refused run is left as it was.
    e.g. flows holding a caption and a WD14 list -> "migrated captions, wd14"
    """
    held = False
    planned: list[tuple[str, list[Copy]]] = []
    for kind in DESCRIPTION:
        holders = [flow for flow in run.flows if versions(run.directory(flow, kind))]
        if not holders:
            continue
        held = True
        target = run.directory(PHOTO, kind)
        if versions(target):
            continue
        if target.exists() and any(target.iterdir()):
            raise Refusal(
                f"{run.id}: {PHOTO}/{kind}/ holds files but no {kind} artifact; move "
                f"them out of the run, then run `{migrate_command(run)}` again"
            )
        copies = (
            _caption(run, holders) if kind == CAPTIONS else _lists(run, kind, holders)
        )
        planned.append((kind, copies))
    if not held:
        return "nothing to migrate"
    if not planned:
        return "already migrated"
    for kind, copies in planned:
        _copy(run, kind, copies)
    return f"migrated {', '.join(kind for kind, _ in planned)}"


def _caption(run: Run, holders: Sequence[str]) -> list[Copy]:
    """Return the newest of the holders' latest captions, a tie to the first by id."""
    latest = [
        path
        for flow in holders
        if (path := latest_artifact(run.directory(flow, CAPTIONS))) is not None
    ]
    newest = max(latest, key=lambda path: path.stat().st_mtime_ns)
    return [(newest, artifact_name(1))]


def _lists(run: Run, kind: str, holders: Sequence[str]) -> list[Copy]:
    """Return the first holder's lists of `kind`, refusing holders that disagree."""
    first = holders[0]
    numbers = versions(run.directory(first, kind))
    agree = all(
        versions(run.directory(flow, kind)) == numbers
        and all(
            _tags(run, flow, kind, n) == _tags(run, first, kind, n) for n in numbers
        )
        for flow in holders[1:]
    )
    if not agree:
        raise Refusal(
            f"{run.id}: its {kind} lists differ between {', '.join(holders)}; keep "
            f"one — delete the others' <flow>/{kind}/ — then run "
            f"`{migrate_command(run)}` again"
        )
    return [
        (run.directory(first, kind) / artifact_name(n), artifact_name(n))
        for n in numbers
    ]


def _tags(run: Run, flow: str, kind: str, number: int) -> object:
    """Return the `tags` of `flow`'s list of `kind` numbered `number`.

    A list that cannot be read, or holds no `tags`, refuses the run by name; the
    remedy drops that flow's copies, so the other holders' lists are copied.
    """
    path = run.directory(flow, kind) / artifact_name(number)
    remedy = f"delete {flow}/{kind}/, then run `{migrate_command(run)}` again"
    body = read(path, _LISTS[kind], remedy=remedy)
    require(path, body, "tags", list, remedy)
    return body["tags"]


def _copy(run: Run, kind: str, copies: Sequence[Copy]) -> None:
    """Write `copies` into `photo/<kind>/` whole, through a partial directory."""
    partial = run.directory(PHOTO, f".{kind}.partial")
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    for source, name in copies:
        (partial / name).write_bytes(source.read_bytes())
    partial.rename(run.directory(PHOTO, kind))
