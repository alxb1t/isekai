"""Attribute recall: the approved sheet's scored tags a render reads back.

For each scored field of a flow, the tags the approval asked for are set against
the tags the tagger sees in the render; each miss is named. The tags are counted,
not the renders: a field showing three of its four tags is not a failed render.

The arithmetic is stdlib and `normalise` alone, so it is tested on tag sets
written by hand and never needs the tagger.
"""

from collections.abc import Collection, Mapping, Sequence
from typing import Literal, TypedDict

from isekai.shared.vocabulary import normalise

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
            total["read_back"] += len(field["asked"]) - len(field["missed"])
    return out


def record(rows: Sequence[Row], tagger: Mapping[str, str], floor: float) -> Record:
    """Return the batch's record; `tagger` maps each model's `dest` to its digest."""
    return {
        "tagger": dict(tagger),
        "floor": floor,
        "rows": list(rows),
        "totals": totals(rows),
    }


def _cell(read_back: int, asked: int) -> str:
    """Return `read back / asked`, or `-` where nothing was asked."""
    return f"{read_back} / {asked}" if asked else "-"


def _cell_of(field: FieldRecall) -> str:
    """Return one render's field as a cell."""
    return _cell(len(field["asked"]) - len(field["missed"]), len(field["asked"]))


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
