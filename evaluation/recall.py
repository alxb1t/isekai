"""Attribute recall: the approved sheet's scored tags a render reads back.

For each scored field of a flow, the tags the approval asked for are set against
the tags the tagger sees in the render; each miss is named. The tags are counted,
not the renders: a field showing three of its four tags is not a failed render.

    uv run python -m evaluation.recall <batch>/runs [<run>...]

Every render of every group and seed is read alone, with no cohort, against the
approval its group names. The record is written beside the runs, as
`<batch>/recall.json`, and the table printed; why a row is not read is on stderr.

The arithmetic is stdlib and `normalise` alone, so it is tested on tag sets
written by hand. The reader is the pipeline's own tagger, behind `Read`, so the
suite passes it a fake.
"""

import argparse
import sys
from collections.abc import Callable, Collection, Mapping, Sequence
from pathlib import Path
from typing import Literal, TypedDict

from evaluation.face import UNDECODABLE
from evaluation.record import destination, runs_in
from isekai.boundary import wd14
from isekai.boundary.provision import DigestMismatch
from isekai.foundation.artifacts import (
    APPROVED_FILE,
    require,
    write_json,
)
from isekai.foundation.artifacts import read as read_artifact
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    OUTPUTS,
    REVIEW,
    Run,
    artifact_name,
)
from isekai.interface.run_view import rendered
from isekai.shared.vocabulary import DEFAULT_MODELS_DIR, normalise

Read = Callable[[Path], set[str]]
Outcome = Literal["read", "unreadable", "no approval"]


class FieldRecall(TypedDict):
    """One scored field of one render: the tags asked, and those not read back."""

    asked: list[str]
    missed: list[str]


class Row(TypedDict):
    """One render's outcome, and its fields' counts when it was read."""

    run: str
    flow: str
    group: int
    seed: int
    outcome: Outcome
    fields: dict[str, FieldRecall]


class Total(TypedDict):
    """Tags read back over tags asked, summed over a flow's rows."""

    read_back: int
    asked: int


class Record(TypedDict):
    """One batch's recall: the tagger and its floor, every row, a total per flow."""

    tagger: dict[str, str]
    floor: float
    rows: list[Row]
    totals: dict[str, dict[str, Total]]


def count(
    fields: Mapping[str, Sequence[str]],
    scored: Sequence[str],
    seen: Collection[str],
) -> dict[str, FieldRecall]:
    """Return each scored field's tags asked and tags missed, in `scored` order.

    A field the approval holds no tags for asks nothing. `seen` holds normalised
    tags, e.g. fields `{"eye_colour": ["blue eyes"]}`, scored `("eye_colour",)`,
    seen `{"blue eyes"}` -> `{"eye_colour": {"asked": ["blue eyes"], "missed": []}}`.
    """
    out: dict[str, FieldRecall] = {}
    for name in scored:
        asked = list(fields.get(name, []))
        out[name] = {
            "asked": asked,
            "missed": [tag for tag in asked if normalise(tag) not in seen],
        }
    return out


def _read_back(field: FieldRecall) -> int:
    """Return how many of the field's tags the render shows."""
    return len(field["asked"]) - len(field["missed"])


def totals(rows: Sequence[Row]) -> dict[str, dict[str, Total]]:
    """Return each flow's tags read back over tags asked, per field, from its read rows.

    A flow with no row read has no fields. Flows come sorted, fields in the order
    the first read row holds them.
    """
    out: dict[str, dict[str, Total]] = {
        flow: {} for flow in sorted({r["flow"] for r in rows})
    }
    for row in rows:
        if row["outcome"] != "read":
            continue
        for name, field in row["fields"].items():
            total = out[row["flow"]].setdefault(name, {"read_back": 0, "asked": 0})
            total["asked"] += len(field["asked"])
            total["read_back"] += _read_back(field)
    return out


def record(rows: Sequence[Row], tagger: Mapping[str, str], floor: float) -> Record:
    """Return the batch's record; `tagger` maps each model's `dest` to its digest."""
    return {
        "tagger": dict(tagger),
        "floor": floor,
        "rows": list(rows),
        "totals": totals(rows),
    }


def reading(tagger: wd14.LocalTagger) -> Read:
    """Return a reader of the normalised tags `tagger` sees in an image, at its floor.

    An image that does not decode refuses naming the file, so the command can
    make it a row and read the next.
    """

    def read(path: Path) -> set[str]:
        try:
            found = wd14.scored(path, tagger.session, tagger.labels)
        except UNDECODABLE as undecodable:
            raise Refusal(f"{path} does not decode as an image") from undecodable
        return {normalise(one.tag) for one in found}

    return read


def _reader(models: Path) -> tuple[Read, dict[str, str]]:
    """Return the real reader and the digest of each file it was verified against.

    `wd14.open_session` checks both pins before the graph is opened, so the
    digests returned are those of the bytes read. A file whose bytes do not match
    its pin refuses naming the command that fetches it again.
    """
    try:
        tagger = wd14.open_session(models)
    except DigestMismatch as swapped:
        raise Refusal(
            f"{swapped}; delete that file, run `{wd14.REMEDY}`, then this command again"
        ) from swapped
    return reading(tagger), {dest: pin["sha256"] for dest, pin in tagger.pins.items()}


def _cell(read_back: int, asked: int) -> str:
    """Return `read back / asked`, or `-` where nothing was asked."""
    return f"{read_back} / {asked}" if asked else "-"


def _cell_of(field: FieldRecall) -> str:
    """Return one render's field as a cell."""
    return _cell(_read_back(field), len(field["asked"]))


def _missed(row: Row) -> str:
    """Return the row's misses as `field: tag, tag · field: tag`, or an empty string."""
    return " · ".join(
        f"{name}: {', '.join(field['missed'])}"
        for name, field in row["fields"].items()
        if field["missed"]
    )


def _block(flow: str, rows: Sequence[Row], total: Mapping[str, Total]) -> list[str]:
    """Return one flow's lines: header, a row per render with any misses, the total."""
    names = list(total)
    grid: list[list[str]] = [["run", "group", "seed", *names]]
    notes: dict[int, str] = {}
    for row in rows:
        lead = [row["run"][:12], str(row["group"]), str(row["seed"])]
        if row["outcome"] != "read":
            grid.append([*lead, row["outcome"]])
            continue
        grid.append([*lead, *(_cell_of(row["fields"][name]) for name in names)])
        if missed := _missed(row):
            notes[len(grid) - 1] = missed
    grid.append(
        [
            "total",
            "",
            "",
            *(_cell(total[name]["read_back"], total[name]["asked"]) for name in names),
        ]
    )
    widths = [
        max(len(line[i]) for line in grid if i < len(line))
        for i in range(max(map(len, grid)))
    ]
    lines = [flow]
    for at, line in enumerate(grid):
        lines.append(
            "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(line)).rstrip()
        )
        if at in notes:
            lines.append(f"  missed: {notes[at]}")
    return lines


def table(rec: Record) -> str:
    """Return the table for a record: one block per flow, flows sorted.

    e.g. `summon-anime-wai`, a header of its scored fields, a row per render, a
    `missed:` line under any row with a miss, then a `total` row.
    """
    blocks = [
        "\n".join(_block(flow, [r for r in rec["rows"] if r["flow"] == flow], total))
        for flow, total in sorted(rec["totals"].items())
    ]
    return "\n\n".join(blocks) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the command line."""
    p = argparse.ArgumentParser(
        prog="python -m evaluation.recall",
        description="Count, per scored field, the approved sheet's tags each render "
        "reads back.",
    )
    p.add_argument("runs", type=Path, help="a batch's runs directory")
    p.add_argument("names", nargs="*", help="read only these runs, by directory name")
    p.add_argument(
        "--models",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="where the pinned tagger lives",
    )
    p.add_argument(
        "--flows", type=Path, default=FLOWS_DIR, help="where the flows are declared"
    )
    return p.parse_args(argv)


def _held(runs: Path, names: Sequence[str]) -> list[Run]:
    """Return the runs under `runs`, narrowed to `names` when given.

    A name no run holds refuses naming it, before any render is read.
    """
    held = runs_in(runs)
    absent = [name for name in names if name not in {run.id for run in held}]
    if absent:
        raise Refusal(
            f"{', '.join(absent)} is not a run under {runs}; name runs by their "
            "directory names there, then this command again"
        )
    return [run for run in held if not names or run.id in names]


def _asked(run: Run, flow: str, group: int) -> dict[str, list[str]]:
    """Return the tags the approval of `group` holds, by field, or refuse naming it.

    A field that is not a list of tags refuses, so a hand-edited string is never
    counted letter by letter.
    """
    path = run.directory(flow, REVIEW, artifact_name(group, APPROVED))
    if not path.is_file():
        raise Refusal(f"{path} is absent; restore it, then this command again")
    remedy = f"restore it in {path} by hand"
    body = read_artifact(path, APPROVED_FILE, remedy=remedy)
    require(path, body, "fields", dict, remedy)
    fields = body["fields"]
    for name, tags in fields.items():
        if not (isinstance(tags, list) and all(isinstance(t, str) for t in tags)):
            raise Refusal(f"{path}: `{name}` is not a list of tags; {remedy}")
    return fields


def _row(
    run: Run,
    flow: str,
    group: int,
    seed: int,
    outcome: Outcome,
    fields: dict[str, FieldRecall],
) -> Row:
    """Return one render's row."""
    return {
        "run": run.id,
        "flow": flow,
        "group": group,
        "seed": seed,
        "outcome": outcome,
        "fields": fields,
    }


def _group_rows(
    run: Run,
    flow: str,
    group: int,
    seeds: Sequence[int],
    suffix: str,
    scored: Sequence[str],
    read_tags: Read,
    notes: list[str],
) -> list[Row]:
    """Return a row per seed of one render group, counted against its approval.

    An approval that cannot be read costs the group its reading; an image that
    does not decode costs only its own.
    """
    try:
        asked = _asked(run, flow, group)
    except Refusal as unapproved:
        notes.append(f"no approval: {run.id}: {unapproved}")
        return [_row(run, flow, group, seed, "no approval", {}) for seed in seeds]
    rows: list[Row] = []
    for seed in seeds:
        try:
            seen = read_tags(
                run.directory(flow, OUTPUTS, f"{group:03d}", f"{seed}{suffix}")
            )
        except Refusal as undecodable:
            notes.append(
                f"unreadable: {undecodable}; render it again or delete it, then "
                "this command again"
            )
            rows.append(_row(run, flow, group, seed, "unreadable", {}))
        else:
            fields = count(asked, scored, seen)
            rows.append(_row(run, flow, group, seed, "read", fields))
    return rows


def survey(
    runs: Sequence[Run], read_tags: Read, flows_dir: Path
) -> tuple[list[Row], list[str]]:
    """Return a row per render of `runs`, and a line saying why one was not read.

    A flow that does not load costs only its own renders; an approval that cannot
    be read and an image that does not decode each cost only the render they
    belong to.
    """
    rows: list[Row] = []
    notes: list[str] = []
    for run in runs:
        for flow in run.flows:
            try:
                loaded = load_flow(flow, flows_dir)
                scored = loaded.schema.scored
                groups = rendered(run, flows_dir, flows=(flow,))
            except Refusal as unloadable:
                notes.append(
                    f"unreadable: {run.id}: {unloadable}; move {run.directory(flow)} "
                    "out of the run, then this command again"
                )
                continue
            for _, group, seeds in groups:
                rows += _group_rows(
                    run,
                    flow,
                    group,
                    seeds,
                    loaded.output_suffix,
                    scored,
                    read_tags,
                    notes,
                )
    return rows, notes


def main(argv: Sequence[str]) -> int:
    """Read the batch, write its record beside the runs, and print the table."""
    args = parse_args(argv)
    try:
        target = destination(args.runs, "recall.json")
        held = _held(args.runs, args.names)
        read_tags, pins = _reader(args.models)
        rows, notes = survey(held, read_tags, args.flows)
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
    rec = record(rows, pins, wd14.FLOOR)
    write_json(target, rec)
    print(table(rec), end="")
    for note in notes:
        print(note, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
